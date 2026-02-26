import paho.mqtt.client as mqtt
import time
import json
import logging

logging.basicConfig(level=logging.INFO)

scan_count = 0

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("robot/scan")
    client.subscribe("robot/status")

def on_message(client, userdata, msg):
    global scan_count
    if msg.topic == "robot/scan":
        scan_count += 1
        print(f"[{scan_count}] Received robot/scan. Payload size: {len(msg.payload)} bytes")
        try:
            # try parsing
            data = json.loads(msg.payload.decode('utf-8'))
            print("Successfully parsed JSON. Ranges length:", len(data.get('ranges', [])))
            
            # Print first 5 to see if they contain inf/nan
            ranges = data.get('ranges', [])
            print("First 5 points:", ranges[:5])
            
            client.disconnect()
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            client.disconnect()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    print("Connecting to local broker...")
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()
except KeyboardInterrupt:
    pass
