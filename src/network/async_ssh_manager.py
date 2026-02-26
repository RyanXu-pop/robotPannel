import asyncio
import hashlib
import logging
import os
import tempfile
import time
import glob
from typing import Optional, Tuple

import paramiko

from src.core.constants import SSH_CONFIG, MQTT_CONFIG


class AsyncSSHManager:
    """
    异步版本的 SSH 管理器，使用 asyncio.to_thread 包装 Paramiko 阻塞调用，
    从而避免 UI 卡顿并消除 QThread 带来的回调地狱。
    """
    # 默认的 ROS 2 MQTT桥接脚本位置
    DEFAULT_BRIDGE_LOCAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ros", "mqtt_bridge_ros2.py")
    
    # 无车调试模式开关：由 UI 层的 "启动仿真" 按钮统一控制
    # 默认 False（安全优先）
    
    def __init__(self):
        self.ssh_client: Optional[paramiko.SSHClient] = None
        self.container_id: Optional[str] = None
        self.mock_mode: bool = False  # 由主界面 toggle_simulation 控制
        # 连接互斥锁，防止并发连接
        self._connect_lock = asyncio.Lock()

    # ---------- 异步基础 ----------
    async def _connect_async(self) -> None:
        if self.mock_mode:
            return
        async with self._connect_lock:
            if self.ssh_client:
                return
            logging.info("初始化 SSH 客户端 (Async)...")
            
            def do_connect():
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    SSH_CONFIG["host"],
                    SSH_CONFIG["port"],
                    SSH_CONFIG["username"],
                    SSH_CONFIG["password"],
                    timeout=10,
                )
                return client
            
            self.ssh_client = await asyncio.to_thread(do_connect)
            logging.info("SSH 连接成功")

    async def _run_host_async(self, command: str, timeout: int = 15) -> Tuple[int, str, str]:
        """在宿主机异步执行命令，返回 (exit, out, err)"""
        if not self.ssh_client:
            raise RuntimeError("SSH 未连接")
        
        def run_cmd():
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            out = stdout.read().decode("utf-8", errors="ignore")
            err = stderr.read().decode("utf-8", errors="ignore")
            return exit_code, out, err
            
        return await asyncio.to_thread(run_cmd)

    async def _ensure_container_id_async(self) -> str:
        if self.container_id:
            return self.container_id
        
        cmd_yahboom = r"""docker ps --format '{{.ID}} {{.Image}}' | grep 'yahboomtechnology/ros-humble' | head -n1 | awk '{print $1}'"""
        code, out, err = await self._run_host_async(cmd_yahboom)
        cid = out.strip()
        
        if code != 0 or not cid:
            cmd_fallback = r"""docker ps --format '{{.ID}} {{.Image}}' | grep -Ei '(humble|ros)' | head -n1 | awk '{print $1}'"""
            code, out, err = await self._run_host_async(cmd_fallback)
            cid = out.strip()
        
        if code != 0 or not cid:
            raise RuntimeError(f"未找到运行中的 ROS2 容器. err: {err}")
        
        self.container_id = cid
        logging.info(f"✅ 找到 ROS2 容器: {cid}")
        return cid

    async def _exec_in_container_async(self, command: str, detach: bool = False, timeout: int = 20) -> Tuple[int, str, str]:
        cid = await self._ensure_container_id_async()
        dash_d = "-d" if detach else ""
        wrapped = (
            f'docker exec {dash_d} {cid} bash -c '
            f'"source /root/.bashrc 2>/dev/null || true; '
            f'source /opt/ros/humble/setup.bash 2>/dev/null || true; '
            f'source /root/yahboomcar_ws/install/setup.bash 2>/dev/null || true; '
            f'export ROS_DOMAIN_ID=20; '
            f'{command}"'
        )
        return await self._run_host_async(wrapped, timeout=timeout)

    # ---------- 业务编排 (纯 async) ----------
    async def start_chassis_async(self) -> Tuple[bool, str]:
        """启动底盘 Bringup（官方文档 Page 3）"""
        if self.mock_mode:
            await asyncio.sleep(1)
            return True, "[Mock] 底盘 Bringup 启动成功"
        await self._connect_async()
        try:
            await self._exec_in_container_async("pkill -f yahboomcar_bringup_launch.py || true", detach=False, timeout=5)
            await asyncio.sleep(1)
            
            cmd = "ros2 launch yahboomcar_bringup yahboomcar_bringup_launch.py"
            code, out, err = await self._exec_in_container_async(cmd, detach=True)
            if code != 0:
                return False, f"底盘 Bringup 启动命令执行失败: {err or out}"
            
            logging.info("等待底盘 Bringup 启动...")
            await asyncio.sleep(5)
            
            check_proc_cmd = "pgrep -f yahboomcar_bringup_launch.py || echo 'NOT_FOUND'"
            code_proc, out_proc, _ = await self._exec_in_container_async(check_proc_cmd, detach=False, timeout=5)
            if "NOT_FOUND" in out_proc or not out_proc.strip():
                return False, "底盘进程未检测到，可能启动失败"
            
            return True, "底盘 Bringup 启动成功（进程运行中）"
        except Exception as e:
            logging.error(f"启动底盘 Bringup 异常: {e}")
            return False, f"启动底盘 Bringup 异常: {e}"

    async def stop_chassis_async(self):
        if not self.ssh_client:
            return
        try:
            await self._exec_in_container_async("pkill -f yahboomcar_bringup_launch.py || true", detach=False, timeout=8)
            logging.info("底盘 Bringup 已请求停止（容器内）")
        except Exception as e:
            logging.error(f"停止底盘 Bringup 异常: {e}")

    # ---------- Gmapping 建图 ----------
    async def start_gmapping_async(self) -> Tuple[bool, str]:
        """启动 Gmapping 建图（参考官方文档 Gmapping建图.pdf）"""
        if self.mock_mode:
            await asyncio.sleep(1)
            return True, "[Mock] Gmapping 建图已启动！\n\n请移动机器人探索环境"
        await self._connect_async()
        try:
            # 检查底盘是否已启动
            check_cmd = "pgrep -f yahboomcar_bringup_launch.py || echo 'NOT_RUNNING'"
            code_check, out_check, _ = await self._exec_in_container_async(check_cmd, detach=False, timeout=5)
            if "NOT_RUNNING" in out_check:
                return False, "请先启动底盘 (Bringup)，建图需要底盘数据"
            
            logging.info("检查激光雷达 /scan 话题...")
            scan_check_cmd = "timeout 3 ros2 topic echo /scan --once --qos-reliability best_effort 2>&1 | head -3"
            code_s, out_s, _ = await self._exec_in_container_async(scan_check_cmd, detach=False, timeout=10)
            if "ranges" not in out_s.lower():
                logging.warning("激光雷达 /scan 话题可能无数据")
            else:
                logging.info("激光雷达 /scan 话题正常")
            
            # 启动 Gmapping
            cmd = "ros2 launch yahboomcar_nav map_gmapping_launch.py"
            code, out, err = await self._exec_in_container_async(cmd, detach=True)
            if code != 0:
                return False, f"Gmapping 启动失败: {err or out}"
            
            logging.info("Gmapping 建图已启动（容器内），等待初始化...")
            await asyncio.sleep(3)
            
            map_check_cmd = "ros2 topic list 2>/dev/null | grep '/map' || echo 'NO_MAP_TOPIC'"
            code_m, out_m, _ = await self._exec_in_container_async(map_check_cmd, detach=False, timeout=10)
            
            if "NO_MAP_TOPIC" in out_m:
                logging.warning("/map 话题尚未出现，可能需要移动机器人")
                return True, "Gmapping 已启动！\n\n⚠️ 注意：/map 话题尚未出现\n请移动机器人以生成地图数据"
            
            return True, "Gmapping 建图已启动！\n\n/map 话题已就绪，请移动机器人探索环境"
        except Exception as e:
            logging.error(f"启动 Gmapping 异常: {e}")
            return False, f"启动 Gmapping 异常: {e}"

    async def stop_gmapping_async(self):
        if not self.ssh_client:
            return
        try:
            await self._exec_in_container_async("pkill -f map_gmapping_launch.py || true", detach=False, timeout=8)
            await self._exec_in_container_async("pkill -f slam_gmapping || true", detach=False, timeout=8)
            logging.info("Gmapping 建图已请求停止（容器内）")
        except Exception as e:
            logging.error(f"停止 Gmapping 异常: {e}")

    # ---------- Navigation 导航 ----------
    async def start_navigation_async(self) -> Tuple[bool, str]:
        """启动 Navigation2 导航"""
        if self.mock_mode:
            await asyncio.sleep(1)
            return True, "[Mock] Navigation2 导航已启动！\n\n下一步：\n1. 在地图上点击设置初始位姿\n2. 然后点击设置导航目标\n"
        await self._connect_async()
        try:
            logging.info("检查底盘状态...")
            check_chassis_cmd = "pgrep -f yahboomcar_bringup_launch.py || echo ''"
            code_c, out_c, _ = await self._exec_in_container_async(check_chassis_cmd, detach=False, timeout=5)
            if code_c != 0 or not out_c.strip():
                return False, "底盘未启动！请先点击「启动底盘」"
            
            map_path = "/root/yahboomcar_ws/src/yahboomcar_nav/maps/yahboom_map.yaml"
            logging.info(f"检查地图文件: {map_path}")
            check_map_cmd = f"test -f {map_path} && echo 'MAP_EXISTS' || echo 'NO_MAP'"
            code_m, out_m, _ = await self._exec_in_container_async(check_map_cmd, detach=False, timeout=5)
            if "NO_MAP" in out_m:
                return False, f"地图文件不存在: {map_path}\n\n请先建图并保存地图，保存时会自动同步到导航目录"
            
            logging.info("清理旧的导航进程...")
            await self._exec_in_container_async("pkill -f navigation_dwb_launch.py || true", detach=False, timeout=5)
            await self._exec_in_container_async("pkill -f nav2_bringup || true", detach=False, timeout=5)
            await asyncio.sleep(1)
            
            logging.info("启动 Navigation2 导航...")
            cmd = "nohup ros2 launch yahboomcar_nav navigation_dwb_launch.py > /root/navigation.log 2>&1 &"
            code, out, err = await self._exec_in_container_async(cmd, detach=True, timeout=10)
            
            logging.info("等待导航节点启动...")
            await asyncio.sleep(5)
            
            check_nav_cmd = "ros2 node list 2>/dev/null | grep -E 'amcl|controller_server|planner_server' | head -3"
            for attempt in range(3):
                code_n, out_n, _ = await self._exec_in_container_async(check_nav_cmd, detach=False, timeout=10)
                if "amcl" in out_n or "controller_server" in out_n:
                    logging.info(f"✅ 检测到导航节点: {out_n.strip()}")
                    break
                await asyncio.sleep(3)
            else:
                log_cmd = "tail -20 /root/navigation.log 2>/dev/null || echo 'No log'"
                _, log_out, _ = await self._exec_in_container_async(log_cmd, detach=False, timeout=5)
                return False, f"导航节点启动超时\n\n日志:\n{log_out[:500]}"
            
            logging.info("验证导航服务状态...")
            check_amcl_cmd = "ros2 lifecycle get /amcl 2>/dev/null | grep -i 'active' && echo 'AMCL_ACTIVE' || echo 'AMCL_NOT_ACTIVE'"
            code_amcl, out_amcl, _ = await self._exec_in_container_async(check_amcl_cmd, detach=False, timeout=10)
            
            if "AMCL_ACTIVE" in out_amcl:
                logging.info("✅ Navigation2 导航启动成功（AMCL 已激活）")
                return True, "Navigation2 导航已启动！\n\n下一步：\n1. 在地图上点击设置初始位姿\n2. 然后点击设置导航目标\n"
            else:
                logging.info("✅ Navigation2 导航节点已启动，等待 AMCL 初始化")
                return True, "导航节点已启动（AMCL 正在初始化...）\n\n请点击「设置初始位姿」按钮设置机器人位置"
                
        except Exception as e:
            logging.error(f"启动导航异常: {e}")
            return False, f"启动导航异常: {e}"

    async def stop_navigation_async(self):
        if not self.ssh_client:
            return
        stop_cmds = [
            "pkill -f navigation_dwb_launch.py || true",
            "pkill -f nav2_bringup || true",
            "pkill -f amcl || true",
            "pkill -f controller_server || true",
            "pkill -f planner_server || true",
            "pkill -f bt_navigator || true",
            "pkill -f map_server || true",
            "pkill -f lifecycle_manager || true",
        ]
        for cmd in stop_cmds:
            await self._exec_in_container_async(cmd, detach=False, timeout=3)
        logging.info("导航已请求停止（容器内）")

    # ---------- 地图保存与下载 ----------
    YAHBOOM_MAP_DIR = "/root/yahboomcar_ws/src/yahboomcar_nav/maps"
    YAHBOOM_DEFAULT_MAP_NAME = "yahboom_map"
    
    async def save_map_async(self, map_name: str = "my_map") -> Tuple[bool, str]:
        """保存地图"""
        if self.mock_mode:
            await asyncio.sleep(1)
            return True, f"[Mock] 地图已保存: {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm"
        await self._connect_async()
        try:
            logging.info("检查 /map 话题状态...")
            check_topic_cmd = "ros2 topic list 2>/dev/null | grep -q '/map' && echo 'TOPIC_EXISTS' || echo 'NO_TOPIC'"
            code_t, out_t, _ = await self._exec_in_container_async(check_topic_cmd, detach=False, timeout=10)
            if "NO_TOPIC" in out_t:
                return False, "❌ /map 话题不存在！\n\n请确保：\n1. Gmapping 已启动\n2. 机器人已移动过"
            
            cleanup_cmd = f"rm -f {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml"
            await self._exec_in_container_async(cleanup_cmd, detach=False, timeout=5)
            await self._exec_in_container_async("pkill -f 'save_map_launch.py' || true", detach=False, timeout=5)
            await self._exec_in_container_async("pkill -f 'map_saver' || true", detach=False, timeout=5)
            logging.info("已清理旧地图文件和进程")
            
            save_cmd = "ros2 launch yahboomcar_nav save_map_launch.py"
            nohup_cmd = f"nohup bash -c 'source /opt/ros/humble/setup.bash && source /root/yahboomcar_ws/install/setup.bash 2>/dev/null && export ROS_DOMAIN_ID=20 && {save_cmd}' > /root/save_map.log 2>&1 &"
            code, out, err = await self._exec_in_container_async(nohup_cmd, detach=False, timeout=10)
            
            if code != 0:
                return False, f"启动保存地图命令失败: {err or out}"
            
            logging.info("等待 save_map_launch.py 完成保存...")
            max_wait = 15
            check_interval = 2
            waited = 0
            map_saved = False
            
            while waited < max_wait:
                verify_cmd = f"test -f {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm && test -f {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml && echo 'FILES_EXIST'"
                code_v, out_v, _ = await self._exec_in_container_async(verify_cmd, detach=False, timeout=5)
                
                if "FILES_EXIST" in out_v:
                    map_saved = True
                    break
                await asyncio.sleep(check_interval)
                waited += check_interval
            
            await self._exec_in_container_async("pkill -f save_map_launch.py || true", detach=False, timeout=5)
            
            if not map_saved:
                log_cmd = "cat /root/save_map.log 2>/dev/null | tail -30"
                _, log_out, _ = await self._exec_in_container_async(log_cmd, detach=False, timeout=5)
                return False, f"地图文件未生成（等待超时 {max_wait} 秒）\n\n日志:\n{log_out[:600] if log_out else '无日志'}"
            
            if map_name != self.YAHBOOM_DEFAULT_MAP_NAME:
                custom_dir = "/root/maps"
                await self._exec_in_container_async(f"mkdir -p {custom_dir}", detach=False, timeout=5)
                src_pgm = f"{self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm"
                src_yaml = f"{self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml"
                dst_pgm = f"{custom_dir}/{map_name}.pgm"
                dst_yaml = f"{custom_dir}/{map_name}.yaml"
                
                await self._exec_in_container_async(f"cp {src_pgm} {dst_pgm}", detach=False, timeout=10)
                await self._exec_in_container_async(f"sed 's/image: {self.YAHBOOM_DEFAULT_MAP_NAME}.pgm/image: {map_name}.pgm/' {src_yaml} > {dst_yaml}", detach=False, timeout=10)
                
                return True, f"地图已保存并重命名:\n副本: {custom_dir}/{map_name}.*"
            
            return True, f"地图已保存: {self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm"
        except Exception as e:
            logging.error(f"保存地图异常: {e}")
            try:
                await self._exec_in_container_async("pkill -f save_map_launch.py || true", detach=False, timeout=5)
            except:
                pass
            return False, f"保存地图异常: {e}"

    async def download_map_async(self, map_name: str, local_dir: str) -> Tuple[bool, str]:
        """从容器下载地图文件到本地"""
        await self._connect_async()
        try:
            cid = await self._ensure_container_id_async()
            search_paths = [
                (f"/root/maps/{map_name}", map_name), 
                (f"{self.YAHBOOM_MAP_DIR}/{self.YAHBOOM_DEFAULT_MAP_NAME}", self.YAHBOOM_DEFAULT_MAP_NAME),
            ]
            
            found_path = None
            found_name = None
            for path, name in search_paths:
                check_cmd = f"test -f {path}.pgm && echo 'EXISTS' || echo 'NOT_FOUND'"
                code, out, _ = await self._exec_in_container_async(check_cmd, detach=False, timeout=5)
                if "EXISTS" in out:
                    found_path = path
                    found_name = name
                    break
            
            if not found_path:
                return False, f"未找到地图文件。请先保存地图。"
            
            host_tmp_dir = "/tmp/map_download"
            await self._run_host_async(f"mkdir -p {host_tmp_dir}", timeout=5)
            
            for ext in [".pgm", ".yaml"]:
                container_file = f"{found_path}{ext}"
                host_file = f"{host_tmp_dir}/{map_name}{ext}"
                cp_cmd = f"docker cp {cid}:{container_file} {host_file}"
                code, out, err = await self._run_host_async(cp_cmd, timeout=30)
                if code != 0:
                    return False, f"复制 {ext} 文件失败: {err or out}"
            
            if found_name != map_name:
                modify_yaml_cmd = f"sed -i 's/image: {found_name}.pgm/image: {map_name}.pgm/' {host_tmp_dir}/{map_name}.yaml"
                await self._run_host_async(modify_yaml_cmd, timeout=5)
            
            os.makedirs(local_dir, exist_ok=True)
            
            def do_sftp_download():
                sftp = self.ssh_client.open_sftp()
                try:
                    for ext in [".pgm", ".yaml"]:
                        host_file = f"{host_tmp_dir}/{map_name}{ext}"
                        local_file = os.path.join(local_dir, f"{map_name}{ext}")
                        sftp.get(host_file, local_file)
                finally:
                    sftp.close()
                    
            await asyncio.to_thread(do_sftp_download)
            await self._run_host_async(f"rm -rf {host_tmp_dir}", timeout=5)
            
            return True, f"地图已下载到: {local_dir}/{map_name}.pgm"
        except Exception as e:
            logging.error(f"下载地图异常: {e}")
            return False, f"下载地图异常: {e}"

    async def upload_map_async(self, local_pgm_path: str, local_yaml_path: str) -> Tuple[bool, str]:
        """上传地图文件到容器"""
        await self._connect_async()
        if not os.path.exists(local_pgm_path) or not os.path.exists(local_yaml_path):
            return False, "本地 PGM 或 YAML 文件不存在"
            
        try:
            cid = await self._ensure_container_id_async()
            host_tmp_dir = "/tmp/map_upload"
            await self._run_host_async(f"mkdir -p {host_tmp_dir}", timeout=5)
            
            def do_upload():
                sftp = self.ssh_client.open_sftp()
                try:
                    host_pgm = f"{host_tmp_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm"
                    sftp.put(local_pgm_path, host_pgm)
                    
                    with open(local_yaml_path, 'r') as f:
                        yaml_content = f.read()
                    import re
                    yaml_content = re.sub(
                        r'image:\s*\S+\.pgm',
                        f'image: {self.YAHBOOM_DEFAULT_MAP_NAME}.pgm',
                        yaml_content
                    )
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                        tmp.write(yaml_content)
                        tmp_yaml_path = tmp.name
                    
                    try:
                        host_yaml = f"{host_tmp_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml"
                        sftp.put(tmp_yaml_path, host_yaml)
                    finally:
                        os.unlink(tmp_yaml_path)
                finally:
                    sftp.close()
                    
            await asyncio.to_thread(do_upload)
            
            target_dir = self.YAHBOOM_MAP_DIR
            for ext in [".pgm", ".yaml"]:
                host_file = f"{host_tmp_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}{ext}"
                container_file = f"{target_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}{ext}"
                cp_cmd = f"docker cp {host_file} {cid}:{container_file}"
                code, out, err = await self._run_host_async(cp_cmd, timeout=30)
                if code != 0:
                    return False, f"复制 {ext} 文件到容器失败: {err or out}"
            
            await self._run_host_async(f"rm -rf {host_tmp_dir}", timeout=5)
            
            verify_cmd = f"test -f {target_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm && test -f {target_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml && echo 'OK' || echo 'FAILED'"
            code, out, _ = await self._exec_in_container_async(verify_cmd, detach=False, timeout=5)
            
            if "OK" not in out:
                return False, "上传后验证失败：容器内文件不存在"
            
            return True, f"地图已上传到容器:\n{target_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.pgm\n{target_dir}/{self.YAHBOOM_DEFAULT_MAP_NAME}.yaml"
        except Exception as e:
            logging.error(f"上传地图异常: {e}")
            return False, f"上传地图异常: {e}"

    # ---------- MQTT 桥接部署 ----------
    async def _upload_bridge_script_async(self, local_file_path: Optional[str] = None) -> str:
        if not self.ssh_client:
            raise RuntimeError("SSH 未连接")
        src_path = local_file_path or self.DEFAULT_BRIDGE_LOCAL_PATH
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"本地桥接脚本不存在: {src_path}")

        def do_upload():
            with open(src_path, "r", encoding="utf-8") as rf:
                content = rf.read()
            local_fd, local_path = tempfile.mkstemp(prefix="mqtt_bridge_ros2_", suffix=".py")
            with os.fdopen(local_fd, "w", encoding="utf-8") as wf:
                wf.write(content)
            remote_tmp = "/tmp/mqtt_bridge.py"
            try:
                sftp = self.ssh_client.open_sftp()
                sftp.put(local_path, remote_tmp)
                sftp.close()
            finally:
                os.remove(local_path)
            return remote_tmp
            
        return await asyncio.to_thread(do_upload)

    async def _copy_into_container_async(self, remote_tmp: str, target_path: str = "/root/mqtt_bridge_ros2.py"):
        cid = await self._ensure_container_id_async()
        check_src_cmd = f"test -f {remote_tmp} && echo 'EXISTS' || echo 'NOT_FOUND'"
        code_src, out_src, _ = await self._run_host_async(check_src_cmd, timeout=5)
        if "NOT_FOUND" in out_src:
            raise RuntimeError(f"源文件不存在: {remote_tmp}")
        
        await self._run_host_async(f"docker exec {cid} rm -f {target_path}", timeout=5)
        
        cmd = f"docker cp {remote_tmp} {cid}:{target_path}"
        code, out, err = await self._run_host_async(cmd, timeout=30)
        
        if code != 0:
            raise RuntimeError(f"docker cp 失败: {err or out}")
        
        verify_cmd = f"docker exec {cid} test -f {target_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
        code_verify, out_verify, _ = await self._run_host_async(verify_cmd, timeout=10)
        if "NOT_FOUND" in out_verify:
            raise RuntimeError(f"验证失败: 容器内文件不存在 {target_path}")
            
        await self._run_host_async(f"rm -f {remote_tmp}", timeout=5)

    async def _install_paho_dependency_async(self) -> Tuple[bool, str]:
        try:
            logging.info("开始安装 paho-mqtt 依赖...")
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            wheel_pattern = os.path.join(project_root, "scripts", "paho_mqtt*.whl")
            wheel_files = glob.glob(wheel_pattern)
            
            if not wheel_files:
                return False, f"未找到 paho_mqtt*.whl 文件: {project_root}"
            wheel_path = wheel_files[0]
            
            def do_upload_wheel():
                remote_tmp = "/tmp/paho_mqtt.whl"
                sftp = self.ssh_client.open_sftp()
                try:
                    sftp.put(wheel_path, remote_tmp)
                finally:
                    sftp.close()
                return remote_tmp
                
            remote_tmp = await asyncio.to_thread(do_upload_wheel)
            
            cid = await self._ensure_container_id_async()
            container_wheel_path = "/root/paho_mqtt.whl"
            copy_cmd = f"docker cp {remote_tmp} {cid}:{container_wheel_path}"
            code, out, err = await self._run_host_async(copy_cmd, timeout=30)
            if code != 0:
                return False, f"复制 wheel 文件到容器失败: {err}"
            
            install_script = f'''import sys
import os
import zipfile

wheel_path = "{container_wheel_path}"
site_packages = None
for path in sys.path:
    if "site-packages" in path or "dist-packages" in path:
        site_packages = path
        break

if not site_packages:
    python_version = f"{{sys.version_info.major}}.{{sys.version_info.minor}}"
    common_paths = [
        f"/usr/local/lib/python{{python_version}}/site-packages",
        f"/usr/lib/python{{python_version}}/site-packages",
        f"/usr/lib/python{{python_version}}/dist-packages",
    ]
    for path in common_paths:
        if os.path.exists(path):
            site_packages = path
            break

if not site_packages:
    print("ERROR: 无法找到 site-packages 目录")
    sys.exit(1)

try:
    with zipfile.ZipFile(wheel_path, 'r') as wheel:
        wheel.extractall(site_packages)
except Exception as e:
    print(f"ERROR: 提取失败: {{e}}")
    sys.exit(1)
print("✅ 安装完成")
'''
            host_script_path = "/tmp/install_paho.py"
            
            def do_upload_script():
                sftp = self.ssh_client.open_sftp()
                try:
                    with sftp.file(host_script_path, 'w') as f:
                        f.write(install_script)
                finally:
                    sftp.close()
            
            await asyncio.to_thread(do_upload_script)
            
            container_script_path = "/root/install_paho.py"
            copy_script_cmd = f"docker cp {host_script_path} {cid}:{container_script_path}"
            code, out, err = await self._run_host_async(copy_script_cmd, timeout=10)
            
            install_cmd = f"python3 {container_script_path}"
            code, out, err = await self._exec_in_container_async(install_cmd, detach=False, timeout=60)
            
            cleanup_cmd1 = f"docker exec {cid} rm -f {container_script_path} {container_wheel_path}"
            cleanup_cmd2 = f"rm -f {remote_tmp} {host_script_path}"
            await self._run_host_async(cleanup_cmd1, timeout=5)
            await self._run_host_async(cleanup_cmd2, timeout=5)
            
            if code == 0:
                return True, "paho-mqtt 已安装"
            return False, f"paho-mqtt 安装失败: {err or out}"
            
        except Exception as e:
            logging.error(f"安装 paho-mqtt 异常: {e}")
            return False, str(e)

    async def start_mqtt_bridge_async(self) -> Tuple[bool, str]:
        if self.mock_mode:
            await asyncio.sleep(1)
            return True, "[Mock] MQTT 桥接节点已启动"
        await self._connect_async()
        try:
            logging.info("[MQTT桥接] 步骤 1/5: 清理旧的 MQTT 桥接进程...")
            await self._exec_in_container_async("pkill -9 -f mqtt_bridge_ros2.py || true", detach=False, timeout=8)
            await self._exec_in_container_async("pkill -9 -f run_bridge.sh || true", detach=False, timeout=8)
            await asyncio.sleep(2)
            await self._exec_in_container_async("rm -f /root/mqtt_bridge_ros2.log", detach=False, timeout=5)
            logging.info("[MQTT桥接] 步骤 1/5: ✅ 旧进程已清理")
            
            logging.info("[MQTT桥接] 步骤 2/5: 安装 paho-mqtt 依赖到容器中...")
            paho_ok, paho_msg = await self._install_paho_dependency_async()
            if not paho_ok:
                return False, f"paho-mqtt 安装失败: {paho_msg}"
            logging.info("[MQTT桥接] 步骤 2/5: ✅ paho-mqtt 依赖就绪")
            
            # 动态读取最新配置，防止修改 IP 后仍然使用旧的内存单例
            from src.core.constants import load_config
            latest_config = load_config(strict=False)
            mqtt_conf = latest_config.get("mqtt", {})
            mqtt_host = mqtt_conf.get("host", "")
            mqtt_port = int(mqtt_conf.get("port", 1883))
            
            if not mqtt_host or mqtt_host == "127.0.0.1":
                logging.warning("[MQTT桥接] ⚠️ 注意：检测到 MQTT_HOST 是空或 127.0.0.1，如果机器人和控制面板不在同一台电脑，请在设置中修改真实 IP 否则收不到数据！")
            if not mqtt_host:
                raise RuntimeError("MQTT 配置中的 host 为空")

            logging.info(f"[MQTT桥接] 目标 Broker 配置: {mqtt_host}:{mqtt_port}")
            logging.info("[MQTT桥接] 步骤 3/5: 上传桥接脚本到容器中...")
            cid = await self._ensure_container_id_async()
            await self._exec_in_container_async("rm -f /root/mqtt_bridge_ros2.py /root/run_bridge.sh || true", detach=False, timeout=5)
            
            remote_tmp = await self._upload_bridge_script_async(self.DEFAULT_BRIDGE_LOCAL_PATH)
            await self._copy_into_container_async(remote_tmp, target_path="/root/mqtt_bridge_ros2.py")
            logging.info("[MQTT桥接] 步骤 3/5: ✅ 桥接脚本已部署")
            
            wrapper_script = f'''#!/bin/bash
export MQTT_HOST='{mqtt_host}'
export MQTT_PORT='{mqtt_port}'
export ROS_DOMAIN_ID=20

if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
elif [ -f /opt/ros/humble/install/setup.bash ]; then
    source /opt/ros/humble/install/setup.bash
else
    exit 1
fi
cd /root
python3 /root/mqtt_bridge_ros2.py >> /root/mqtt_bridge_ros2.log 2>&1
'''
            wrapper_path = "/tmp/run_bridge.sh"
            
            def do_upload_wrapper():
                sftp = self.ssh_client.open_sftp()
                try:
                    with sftp.file(wrapper_path, 'w') as f:
                        f.write(wrapper_script)
                finally:
                    sftp.close()
                    
            await asyncio.to_thread(do_upload_wrapper)
            
            container_wrapper = "/root/run_bridge.sh"
            copy_wrapper_cmd = f"docker cp {wrapper_path} {cid}:{container_wrapper}"
            code_copy, _, err_copy = await self._run_host_async(copy_wrapper_cmd, timeout=10)
            
            logging.info("[MQTT桥接] 步骤 4/5: 启动 MQTT 桥接进程...")
            cmd = "chmod +x /root/mqtt_bridge_ros2.py /root/run_bridge.sh && nohup bash /root/run_bridge.sh &"
            code, out, err = await self._exec_in_container_async(cmd, detach=False)
            await self._run_host_async(f"rm -f {wrapper_path}", timeout=5)
            
            if code == 0:
                logging.info("[MQTT桥接] 步骤 5/5: 验证桥接进程状态（等待启动）...")
                await asyncio.sleep(3)
                check_cmd = "head -n 30 /root/mqtt_bridge_ros2.log 2>&1 || echo 'No log'"
                code2, log_out, _ = await self._exec_in_container_async(check_cmd, detach=False, timeout=5)
                
                if "RuntimeError" in log_out or "ImportError" in log_out:
                    logging.error(f"[MQTT桥接] ❌ 桥接脚本运行出错:\n{log_out}")
                    return False, f"MQTT 桥接启动失败: {log_out}"
                
                success_markers = ["bridge fully initialized", "bridge started", "subscribed:"]
                log_lower = log_out.lower()
                for marker in success_markers:
                    if marker in log_lower:
                        logging.info("[MQTT桥接] 步骤 5/5: ✅ MQTT 桥接节点启动成功！")
                        return True, "MQTT 桥接节点已启动"
                
                # 如果没找到成功标记，但也不是明显的 Python 异常，打出来看看是什么情况
                logging.warning(f"[桥接诊断] 容器内 mqtt_bridge_ros2.log 输出内容:\n{log_out}")

                await asyncio.sleep(2)
                proc_check = "pgrep -f mqtt_bridge_ros2.py && echo 'PROCESS_RUNNING'"
                code3, proc_out, _ = await self._exec_in_container_async(proc_check, detach=False, timeout=5)
                if "PROCESS_RUNNING" in proc_out:
                    logging.info(f"[MQTT桥接] 步骤 5/5: ✅ MQTT 桥接节点启动成功（进程运行中）\n[诊断] pgrep 输出: {proc_out.strip()}")
                    return True, "MQTT 桥接节点已启动（进程运行中）"
                
                logging.warning("[MQTT桥接] ⚠️ 无法确认桥接进程状态")
                return False, f"MQTT 桥接启动状态未知: {log_out[:300]}"
            return False, f"MQTT 桥接启动失败: {err or out}"
        except Exception as e:
            logging.error(f"启动 MQTT 桥接异常: {e}")
            return False, f"启动 MQTT 桥接异常: {e}"

    async def stop_mqtt_bridge_async(self):
        if not self.ssh_client:
            return
        try:
            await self._exec_in_container_async("pkill -f mqtt_bridge_ros2.py || true", detach=False, timeout=8)
            await self._exec_in_container_async("pkill -f run_bridge.sh || true", detach=False, timeout=8)
            await asyncio.sleep(1)
            logging.info("MQTT 桥接已请求停止")
        except Exception as e:
            logging.error(f"停止 MQTT 桥接异常: {e}")

    async def close_async(self, stop_services: bool = True):
        """关闭连接"""
        if self.ssh_client:
            if stop_services:
                await self.stop_navigation_async()
                await self.stop_gmapping_async()
                await self.stop_chassis_async()
            self.ssh_client.close()
            logging.info("SSH 客户端已关闭")
