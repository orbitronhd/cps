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
    payload_str = msg.payload.decode('utf-8')
    
    try:
        data = json.loads(payload_str)
        action = data.get('action', 'NONE')
        
        if action == "REQUEST_PREEMPTION":
            amb_id = data.get('ambulance_id', 'UNKNOWN')
            priority = data.get('priority', 2)
            
            # 1. Print the update in the server terminal
            print("🚨 INCOMING PREEMPTION REQUEST 🚨")
            print(f"   Ambulance ID : {amb_id}")
            print(f"   Priority Lvl : {priority}")
            print("-" * 35)
            print(f"[SERVER] Routing {amb_id} to Hospital 01...")
            
            # 2. Forward the command to the Hospital ESP-12E
            hosp_payload = json.dumps({
                "action": "INCOMING_PATIENT",
                "priority": priority
            })
            client.publish("hospital/alerts/HOSP_01", hosp_payload)
            print("[SERVER] Dispatch sent to Hospital Node.\n")
            
    except json.JSONDecodeError:
        print(f"[ERROR] Malformed JSON: {payload_str}")
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