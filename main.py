import time
import threading
import system_config
from routing_engine import RoutingEngine
from mqtt_handler import MQTTHandler

class StateManager:
    def __init__(self, routing_engine):
        self.routing = routing_engine
        self.ambulances = {}
        self.lock = threading.Lock()

    def register_ambulance(self, amb_id, priority, dest):
        with self.lock:
            if amb_id not in self.ambulances: self.ambulances[amb_id] = {"pos": None}
            self.ambulances[amb_id].update({"priority": priority, "dest": dest})

    def update_ambulance_location(self, amb_id, node):
        with self.lock:
            if amb_id in self.ambulances: self.ambulances[amb_id]["pos"] = node

    def get_ambulances(self):
        with self.lock: return dict(self.ambulances)

def server_loop(state_manager, routing_engine, mqtt_handler):
    print("[SERVER] Core Routing Loop Active...")
    while True:
        ambulances = state_manager.get_ambulances()
        routes = routing_engine.calculate_active_routes(ambulances)
        
        for amb_id, path in routes.items():
            if len(path) > 1:
                next_node = path[1] # Look 1 node ahead for immediate preempt
                mqtt_handler.send_light_command(next_node, "PREEMPT_GREEN", amb_id)
        time.sleep(system_config.TICK_RATE)

if __name__ == "__main__":
    routing = RoutingEngine(system_config.CITY_EDGES, system_config.HOSPITALS)
    state = StateManager(routing)
    mqtt = MQTTHandler(state)
    mqtt.start()
    server_loop(state, routing, mqtt)