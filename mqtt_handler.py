import json
import paho.mqtt.client as mqtt
import system_config

class MQTTHandler:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "CentralServer")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("[MQTT] Server Connected to Broker.")
        client.subscribe(system_config.TOPIC_AMB_REQUEST)
        client.subscribe(system_config.TOPIC_AMB_LOCATION)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == system_config.TOPIC_AMB_REQUEST:
                self.state_manager.register_ambulance(payload["id"], payload["priority"], payload["dest"])
            elif msg.topic == system_config.TOPIC_AMB_LOCATION:
                self.state_manager.update_ambulance_location(payload["id"], payload["node"])
        except Exception as e:
            print(f"[MQTT Error] {e}")

    def send_light_command(self, node, state, target_amb):
        payload = json.dumps({"state": state, "target_amb": target_amb})
        self.client.publish(f"{system_config.TOPIC_LIGHT_CONTROL}{node}", payload)

    def start(self):
        self.client.connect(system_config.MQTT_BROKER, system_config.MQTT_PORT, 60)
        self.client.loop_start()