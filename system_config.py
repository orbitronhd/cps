# config.py
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TICK_RATE = 1.0  # Server update interval in seconds

# MQTT Topics
TOPIC_TRAFFIC_UPDATE = "sensors/traffic/+"
TOPIC_AMB_REQUEST = "ambulance/requests"
TOPIC_AMB_LOCATION = "ambulance/location"
TOPIC_LIGHT_CONTROL = "traffic/control/"

# Initial City Topology (Node_A to Node_B, etc.)
CITY_EDGES = [
    ("N1", "N2", {"weight": 1.0}),
    ("N2", "N3", {"weight": 1.0}),
    ("N3", "N4", {"weight": 1.0}),
    ("N1", "N5", {"weight": 1.0}),
    ("N5", "N3", {"weight": 2.0}),
]

HOSPITALS = {
    "H1": {"node": "N4", "capacity": 2}
}