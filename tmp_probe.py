import paramiko

def main():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect('10.42.0.1', 22, 'pi', 'yahboom', timeout=5)
        print('SSH Connected.')
        
        # 获取容器 ID
        stdin, stdout, stderr = client.exec_command("docker ps --format '{{.ID}} {{.Image}}' | grep -i ros | head -n1 | awk '{print $1}'")
        cid = stdout.read().decode().strip()
        if not cid:
            print("No ROS container running.")
            return

        print(f"Container: {cid}")
        
        # 1. 查询日志
        stdin, stdout, stderr = client.exec_command(f"docker exec {cid} tail -n 50 /root/mqtt_bridge_ros2.log")
        print("\n--- MQTT Bridge Log ---")
        print(stdout.read().decode())
        
        # 2. 查询 ROS 话题
        stdin, stdout, stderr = client.exec_command(f"docker exec {cid} bash -c 'source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=20 && ros2 topic list -t'")
        print("\n--- ROS Topics ---")
        print(stdout.read().decode())
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
