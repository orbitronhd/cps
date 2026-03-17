# hardware_simulator.py
import time
import json
import paho.mqtt.client as mqtt
import config

def on_connect(client, userdata, flags, reason_code, properties):
    print("[SIMULATOR] Connected to Broker.")
    # Act as the traffic lights listening for commands
    client.subscribe("traffic/control/#")

def on_message(client, userdata, msg):
    print(f"[SIMULATOR - ESP8266 Light] {msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "HardwareSimulator")
client.on_connect = on_connect
client.on_message = on_message
client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
client.loop_start()

time.sleep(1)

# 1. Simulate Ambulance pressing the "High Priority" button
print("\n--- Simulating Ambulance Request ---")
req_payload = json.dumps({"id": "AMB_01", "priority": 1, "dest": "H1"})
client.publish(config.TOPIC_AMB_REQUEST, req_payload)
time.sleep(2)

# 2. Simulate Ambulance driving through the physical board nodes
route_simulation = ["N1", "N2", "N3", "N4"]

for node in route_simulation:
    print(f"\n--- Simulating Ambulance Arriving at {node} ---")
    loc_payload = json.dumps({"id": "AMB_01", "node": node})
    client.publish(config.TOPIC_AMB_LOCATION, loc_payload)
    
    # Wait to observe the server processing the route and sending light commands
    time.sleep(3)

print("\n[SIMULATOR] Simulation complete. Press Ctrl+C to exit.")
while True:
    time.sleep(1)