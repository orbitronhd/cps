import paho.mqtt.client as mqtt
import json

# Configuration
MQTT_BROKER = "localhost" 
MQTT_PORT = 1883
MQTT_TOPIC = "ambulance/routing"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Server Connected to Broker.")
        # Subscribe to the topic the exact moment we connect
        client.subscribe(MQTT_TOPIC)
        print(f"[SERVER] Listening for preemption requests on '{MQTT_TOPIC}'...\n")
    else:
        print(f"[MQTT] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    # Decode the raw byte payload into a string
    payload_str = msg.payload.decode('utf-8')
    
    try:
        # Parse the JSON data sent by the ESP32
        data = json.loads(payload_str)
        
        # Display the update in a clean, readable format
        print("🚨 INCOMING PREEMPTION REQUEST 🚨")
        print(f"   Ambulance ID : {data.get('ambulance_id', 'UNKNOWN')}")
        print(f"   Priority Lvl : {data.get('priority', 'UNKNOWN')}")
        print(f"   Action       : {data.get('action', 'NONE')}")
        print("-" * 35)
        
        # Future Step: This is where you will add the logic to send 
        # the "PREEMPT_GREEN" command to the traffic lights.
        
    except json.JSONDecodeError:
        print(f"[ERROR] Received malformed JSON from ESP32: {payload_str}")

# Setup the MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("[SERVER] Core Routing Loop Active...")

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Block and keep the server running forever to listen for messages
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[SERVER] Shutting down...")
    client.disconnect()