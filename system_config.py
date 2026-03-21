# Network Settings
MQTT_BROKER = "localhost" # Ensure Mosquitto is running
MQTT_PORT = 1883
TICK_RATE = 0.5 

# MQTT Topics
TOPIC_AMB_REQUEST = "ambulance/requests"
TOPIC_AMB_LOCATION = "ambulance/location"
TOPIC_LIGHT_CONTROL = "traffic/control/"
TOPIC_HOSPITAL_STATUS = "hospital/status/"

# City Graph Topology (Edges and Weights)
CITY_EDGES = [
    ("N1", "N2", {"weight": 1.0}),
    ("N2", "N3", {"weight": 1.0}),
    ("N3", "N4", {"weight": 1.0}),
    ("N1", "N5", {"weight": 1.0}),
    ("N5", "N3", {"weight": 2.0}),
]

# Hospitals (Matching your 3-hospital update)
HOSPITALS = {
    "H1": {"node": "N4"},
    "H2": {"node": "N5"},
    "H3": {"node": "N1"}
}