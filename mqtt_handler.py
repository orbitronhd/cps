# mqtt_handler.py
import json
import paho.mqtt.client as mqtt
import config

class MQTTHandler:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "CentralServer")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[MQTT] Connected. Code: {reason_code}")
        client.subscribe(config.TOPIC_TRAFFIC_UPDATE)
        client.subscribe(config.TOPIC_AMB_REQUEST)
        client.subscribe(config.TOPIC_AMB_LOCATION)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            if topic.startswith("sensors/traffic/"):
                edge = topic.split("/")[-1].split("-")
                if len(edge) == 2:
                    self.state_manager.update_traffic(edge[0], edge[1], payload.get("density", 1.0))
                    
            elif topic == config.TOPIC_AMB_REQUEST:
                self.state_manager.register_ambulance(
                    payload["id"], payload["priority"], payload["dest"]
                )
                
            elif topic == config.TOPIC_AMB_LOCATION:
                self.state_manager.update_ambulance_location(
                    payload["id"], payload["node"]
                )
        except Exception as e:
            print(f"[MQTT] Payload error on {msg.topic}: {e}")

    def send_light_command(self, node, state, target_amb):
        payload = json.dumps({"state": state, "target_amb": target_amb})
        self.client.publish(f"{config.TOPIC_LIGHT_CONTROL}{node}", payload)

    def start(self):
        self.client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60)
        self.client.loop_start()