# hardware_simulator.py
import time
import json
import paho.mqtt.client as mqtt
import system_config

# --- SIMULATOR SETTINGS ---
SIM_AMBULANCE_ID = "AMB_01"
SIM_ROUTE = ["N1", "N2", "N3", "N4"]  # The path the "toy car" will follow

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"✅ [SIMULATOR] Connected to Broker at {system_config.MQTT_BROKER}")
    # Subscribe to the traffic control topic to act as the ESP8266 Traffic Lights
    client.subscribe(f"{system_config.TOPIC_LIGHT_CONTROL}#")

def on_message(client, userdata, msg):
    """Mimics the ESP8266 Traffic Light receiving a command."""
    try:
        payload = json.loads(msg.payload.decode())
        node_id = msg.topic.split("/")[-1]
        state = payload.get("state")
        target = payload.get("target_amb")
        
        print(f"🚥 [VIRTUAL LIGHT @ {node_id}] Command Received: {state} for {target}")
    except Exception as e:
        print(f"❌ [SIMULATOR] Error parsing light command: {e}")

# 1. Setup the Simulator Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Hardware_Simulator_Node")
client.on_connect = on_connect
client.on_message = on_message

print("🚀 [SIMULATOR] Starting Hardware Emulation...")
client.connect(system_config.MQTT_BROKER, system_config.MQTT_PORT, 60)
client.loop_start()

time.sleep(1)  # Wait for connection to stabilize

# 2. Step 1: Simulate the "Distress Button" press on the ESP32 Ambulance
print("\n--- 🚨 ACTION: Ambulance sends Emergency Request ---")
request_payload = {
    "id": SIM_AMBULANCE_ID,
    "priority": 1,
    "dest": "H1"
}
client.publish(system_config.TOPIC_AMB_REQUEST, json.dumps(request_payload))
print(f"Sent: {request_payload} to {system_config.TOPIC_AMB_REQUEST}")

# 3. Step 2: Simulate moving the toy car through the map
# Each step simulates the car being moved by hand and triggering a location update.
for current_node in SIM_ROUTE:
    print(f"\n--- 📍 ACTION: Ambulance enters {current_node} ---")
    
    location_payload = {
        "id": SIM_AMBULANCE_ID,
        "node": current_node
    }
    client.publish(system_config.TOPIC_AMB_LOCATION, json.dumps(location_payload))
    
    # Observe the server's output in the other terminal. 
    # It should calculate the path and send commands to the NEXT nodes in SIM_ROUTE.
    time.sleep(4) 

print("\n🏁 [SIMULATOR] Route Complete. Ambulance has arrived at Hospital.")
print("Press Ctrl+C to stop emulation.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping Simulator...")
    client.loop_stop()
    client.disconnect()