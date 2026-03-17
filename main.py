# main.py
import time
import threading
import config
from routing_engine import RoutingEngine
from mqtt_handler import MQTTHandler

class StateManager:
    def __init__(self, routing_engine):
        self.routing = routing_engine
        self.ambulances = {}
        self.lock = threading.Lock()

    def update_traffic(self, node_a, node_b, weight):
        self.routing.update_edge_weight(node_a, node_b, weight)

    def register_ambulance(self, amb_id, priority, dest):
        with self.lock:
            if amb_id not in self.ambulances:
                self.ambulances[amb_id] = {"pos": None}
            self.ambulances[amb_id].update({"priority": priority, "dest": dest})

    def update_ambulance_location(self, amb_id, node):
        with self.lock:
            if amb_id in self.ambulances:
                self.ambulances[amb_id]["pos"] = node

    def get_ambulances(self):
        with self.lock:
            return dict(self.ambulances)

def server_loop(state_manager, routing_engine, mqtt_handler):
    print("[SERVER] Logic loop running...")
    while True:
        ambulances = state_manager.get_ambulances()
        routes = routing_engine.calculate_active_routes(ambulances)
        
        for amb_id, path in routes.items():
            print(f"[ROUTING] Amb {amb_id} Path: {path}")
            
            # Send Green Wave 2 signals ahead
            lookahead_nodes = path[1:3]
            for node in lookahead_nodes:
                mqtt_handler.send_light_command(node, "PREEMPT_GREEN", amb_id)
                
        time.sleep(config.TICK_RATE)

if __name__ == "__main__":
    routing = RoutingEngine(config.CITY_EDGES, config.HOSPITALS)
    state = StateManager(routing)
    mqtt = MQTTHandler(state)
    
    mqtt.start()
    server_loop(state, routing, mqtt)