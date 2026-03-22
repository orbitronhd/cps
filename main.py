import paho.mqtt.client as mqtt
import json
import time

# --- CONFIGURATION ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
HOSPITAL_TOPIC = "hospital/alerts/HOSP_01"

# --- THE CITY GRID ---
# Maps Nodes (Intersections) to their neighbors. 
# Includes the "Road Name" and the "Direction" needed to cross the intersection.
CITY_GRAPH = {
    "Base_Station": {
        "INT_01": {"road": "Road_1", "direction": "NS"}
    },
    "INT_01": {
        "INT_02": {"road": "Road_2", "direction": "EW"},
        "Hospital_Node": {"road": "Road_3", "direction": "NS"}
    },
    "INT_02": {
        "Hospital_Node": {"road": "Road_4", "direction": "EW"}
    },
    "Hospital_Node": {} # End of the line
}

# --- STATE TRACKING ---
active_ambulances = {} # Tracks current location, route, and priority
road_registry = {}     # Tracks which ambulances are on which roads for collision avoidance

# --- ROUTING ALGORITHM (Breadth-First Search) ---
def calculate_route(start_node, target_node="Hospital_Node"):
    queue = [[start_node]]
    visited = set()
    
    while queue:
        path = queue.pop(0)
        current_node = path[-1]
        
        if current_node == target_node:
            # Convert Node path (Base -> INT_01 -> Hosp) to Road path (Road_1 -> Road_3)
            road_sequence = []
            for i in range(len(path)-1):
                road_name = CITY_GRAPH[path[i]][path[i+1]]["road"]
                road_sequence.append(road_name)
            return path, road_sequence
            
        if current_node not in visited:
            neighbors = CITY_GRAPH.get(current_node, {}).keys()
            for neighbor in neighbors:
                new_path = list(path)
                new_path.append(neighbor)
                queue.append(new_path)
            visited.add(current_node)
    return None, []

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("\n[SYSTEM] Core Routing Engine Online.")
        client.subscribe("ambulance/routing")
        client.subscribe("ambulance/location")
        print("[SYSTEM] Idle. Monitoring city grid for emergency broadcasts...\n")
    else:
        print(f"[ERROR] Connection failed: {rc}")

def handle_collision_avoidance(amb_id, target_road, priority):
    # Check if another ambulance is currently on this road
    occupants = road_registry.get(target_road, [])
    
    for occupant in occupants:
        if occupant != amb_id:
            occupant_priority = active_ambulances[occupant]["priority"]
            if priority < occupant_priority: # Lower number = higher priority
                print(f"[WARNING] COLLISION AVOIDANCE ACTIVE: {occupant} (P{occupant_priority}) has right-of-way on {target_road}.")
                print(f"[ACTION] {amb_id} instructed to HOLD position.")
                return False # Do not proceed
            else:
                print(f"[TRAFFIC] {amb_id} and {occupant} sharing {target_road}. Spacing protocols active.")
    
    # Register this ambulance to the road
    if target_road not in road_registry:
        road_registry[target_road] = []
    if amb_id not in road_registry[target_road]:
        road_registry[target_road].append(amb_id)
    return True

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        action = data.get("action")
        amb_id = data.get("ambulance_id")
        
        # 1. INITIAL PREEMPTION REQUEST
        if action == "REQUEST_PREEMPTION":
            priority = data.get("priority", 2)
            start_location = data.get("location", "Base_Station")
            
            print(f"\n🚨 DISPATCH: {amb_id} CONNECTED 🚨")
            print(f"   Priority : Level {priority}")
            print(f"   Location : {start_location}")
            
            # Calculate initial route
            node_path, road_path = calculate_route(start_location)
            
            active_ambulances[amb_id] = {
                "priority": priority,
                "current_node": start_location,
                "planned_route": node_path,
                "road_sequence": road_path
            }
            
            print(f"   Route    : {' -> '.join(road_path)}")
            print("-" * 40)
            
            # Alert the Hospital
            client.publish(HOSPITAL_TOPIC, json.dumps({"action": "INCOMING_PATIENT", "priority": priority}))

        # 2. LIVE LOCATION UPDATES
        elif action == "LOCATION_UPDATE":
            current_node = data.get("location")
            priority = active_ambulances[amb_id]["priority"]
            planned_route = active_ambulances[amb_id]["planned_route"]
            
            # Check for Deviation
            if current_node not in planned_route:
                print(f"\n⚠️ DEVIATION DETECTED: {amb_id} is off-route at {current_node}.")
                node_path, road_path = calculate_route(current_node)
                active_ambulances[amb_id]["planned_route"] = node_path
                active_ambulances[amb_id]["road_sequence"] = road_path
                print(f"🔄 RECALCULATED ROUTE: {' -> '.join(road_path)}")
            else:
                print(f"\n📍 {amb_id} arrived at {current_node}.")

            # Update state
            active_ambulances[amb_id]["current_node"] = current_node
            
            # Look ahead to the next intersection to preempt traffic lights
            current_index = active_ambulances[amb_id]["planned_route"].index(current_node)
            if current_index + 1 < len(active_ambulances[amb_id]["planned_route"]):
                next_node = active_ambulances[amb_id]["planned_route"][current_index + 1]
                target_road = CITY_GRAPH[current_node][next_node]["road"]
                direction = CITY_GRAPH[current_node][next_node]["direction"]
                
                # Check for collisions before granting the green light
                if handle_collision_avoidance(amb_id, target_road, priority):
                    print(f"🚦 Preempting {next_node} for {direction} traffic...")
                    client.publish(f"traffic/lights/{next_node}", json.dumps({
                        "action": "PREEMPT_ROUTE",
                        "direction": direction
                    }))
            else:
                print(f"🏁 {amb_id} has arrived at the destination.")
                # Clear traffic lights and hospital state here

    except Exception as e:
        print(f"[ERROR] Engine Fault: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[SYSTEM] Engine Shutting Down...")
    client.disconnect()