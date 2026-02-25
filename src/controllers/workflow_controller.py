import asyncio
import logging
import os
from typing import Optional

from PySide6.QtCore import QObject, Signal

from src.network.async_ssh_manager import AsyncSSHManager
from src.controllers.map_manager import MapManager


class WorkflowController(QObject):
    """
    负责基于 async_ssh_manager 编排复杂的长流程任务。
    例如“保存地图 -> 下载地图 -> 更新前端画布”的整套流水线。
    利用 async/await 可以将过去杂乱的回调变为直线逻辑。
    """

    # 流程状态更新，用于绑定到 UI 的状态栏或气泡提示
    status_message = Signal(str)
    
    # 地图同步完成信号 (png_path, yaml_path)
    map_synced = Signal(str, str)
    
    # 流程完成信号 (操作名称, 是否成功, 详情信息)
    workflow_finished = Signal(str, bool, str)

    def __init__(self, async_ssh: AsyncSSHManager, map_mgr: MapManager, parent=None):
        super().__init__(parent)
        self.async_ssh = async_ssh
        self.map_mgr = map_mgr

    async def save_and_sync_map_async(self, map_name: str, local_maps_dir: str):
        """
        完整流程：
        1. 容器内保存地图
        2. 下载 yaml 和 pgm
        3. 利用 MapManager 的 convert 工具生成前端 png
        4. 发送信号更新 UI
        """
        try:
            self.status_message.emit("开始保存地图...")
            
            # 1. 容器内保存地图
            success_save, msg_save = await self.async_ssh.save_map_async(map_name)
            if not success_save:
                self.workflow_finished.emit("save_map", False, f"保存失败: {msg_save}")
                return
                
            self.status_message.emit("地图保存成功，开始下载...")
            
            # 2. 下载地图文件到本地 local_maps_dir
            success_dl, msg_dl = await self.async_ssh.download_map_async(map_name, local_maps_dir)
            if not success_dl:
                self.workflow_finished.emit("save_map", False, f"下载失败: {msg_dl}")
                return

            self.status_message.emit("下载成功，正在生成前端预览图...")
            
            # 3. 转换生成前端 PNG
            local_pgm = os.path.join(local_maps_dir, f"{map_name}.pgm")
            local_yaml = os.path.join(local_maps_dir, f"{map_name}.yaml")
            local_png = os.path.join(local_maps_dir, f"{map_name}.png")
            
            def convert_map():
                import cv2
                import numpy as np
                from PIL import Image
                
                # 读取 PGM (通常包含特殊字符，需使用 cv2 结合 numpy 读取)
                with open(local_pgm, 'rb') as f:
                    data = np.frombuffer(f.read(), dtype=np.uint8)
                img = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
                
                if img is None:
                    raise IOError(f"无法读取 PGM 文件: {local_pgm}")
                
                # OpenCV to PIL
                img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                pil_img = Image.fromarray(img_rgb)
                pil_img.save(local_png, "PNG")

            await asyncio.to_thread(convert_map)
            
            self.status_message.emit("地图已同步并准备就绪")
            
            # 4. 通知更新
            self.map_synced.emit(local_png, local_yaml)
            self.workflow_finished.emit("save_map", True, msg_save)
            
        except Exception as e:
            err_str = f"地图同步流水线异常: {e}"
            logging.error(err_str)
            self.workflow_finished.emit("save_map", False, err_str)

    # ---------- 服务启停流水线 ----------
    async def start_service_async(self, service_name: str):
        """通用入口：启动指定服务，并将结果发给 workflow_finished 信号"""
        try:
            self.status_message.emit(f"正在启动 {service_name}...")
            
            if service_name == "chassis":
                success, msg = await self.async_ssh.start_chassis_async()
            elif service_name == "navigation":
                success, msg = await self.async_ssh.start_navigation_async()
            elif service_name == "gmapping":
                success, msg = await self.async_ssh.start_gmapping_async()
            elif service_name == "mqtt":
                success, msg = await self.async_ssh.start_mqtt_bridge_async()
            else:
                success, msg = False, f"未知服务: {service_name}"
            
            if success:
                self.status_message.emit(f"{service_name} 启动成功")
            else:
                self.status_message.emit(f"{service_name} 启动失败")
            
            self.workflow_finished.emit(service_name, success, msg)
        except Exception as e:
            err_str = f"启动服务 {service_name} 异常: {e}"
            logging.error(err_str)
            self.workflow_finished.emit(service_name, False, err_str)

    async def stop_service_async(self, service_name: str):
        """通用入口：关闭指定服务"""
        try:
            self.status_message.emit(f"正在停止 {service_name}...")
            
            if service_name == "chassis":
                await self.async_ssh.stop_chassis_async()
            elif service_name == "navigation":
                await self.async_ssh.stop_navigation_async()
            elif service_name == "gmapping":
                await self.async_ssh.stop_gmapping_async()
            elif service_name == "mqtt":
                await self.async_ssh.stop_mqtt_bridge_async()
            else:
                logging.warning(f"未知服务无法停止: {service_name}")
                return
            
            self.status_message.emit(f"{service_name} 已发送停止指令")
            # 不一定要 emit workflow_finished，因为 UI 可能是即时响应的。如果有必要也可以发：
            # self.workflow_finished.emit(f"stop_{service_name}", True, "已停止")
        except Exception as e:
            err_str = f"停止服务 {service_name} 异常: {e}"
            logging.error(err_str)
            self.status_message.emit(err_str)

    # ---------- 针对 V2 UI 特化的执行包裹 ----------
    
    async def execute_mapping_workflow(self):
        """执行启动建图全家桶工作流"""
        await self.start_service_async("chassis")
        await asyncio.sleep(1) # 等待底盘响应
        await self.start_service_async("gmapping")
        
    async def execute_stop_mapping_workflow(self):
        """停止建图工作流"""
        await self.stop_service_async("gmapping")
        # 底盘可选停不停，一般建图完可能接着导航，所以不强杀底盘

    async def execute_navigation_workflow(self):
        """执行启动导航全家桶工作流"""
        await self.start_service_async("chassis")
        await asyncio.sleep(1)
        await self.start_service_async("navigation")
        
    async def execute_stop_navigation_workflow(self):
        """停止导航工作流"""
        await self.stop_service_async("navigation")

    async def execute_save_map_workflow(self):
        """执行保存并拉取最新地图工作流"""
        from src.core.constants import PATHS_CONFIG
        await self.save_and_sync_map_async("new_map", PATHS_CONFIG['maps_dir'])
