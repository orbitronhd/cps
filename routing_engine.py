# routing_engine.py
import networkx as nx
import threading

class RoutingEngine:
    def __init__(self, edges, hospitals):
        self.graph = nx.Graph()
        self.graph.add_edges_from(edges)
        self.hospitals = hospitals
        self.lock = threading.Lock()

    def update_edge_weight(self, node_a, node_b, weight):
        with self.lock:
            if self.graph.has_edge(node_a, node_b):
                self.graph[node_a][node_b]['weight'] = weight

    def calculate_active_routes(self, ambulances):
        active_routes = {}
        sorted_ambs = sorted(ambulances.items(), key=lambda x: x[1]['priority'])

        with self.lock:
            temp_graph = self.graph.copy()

            for amb_id, data in sorted_ambs:
                start = data.get("pos")
                dest_hosp = data.get("dest")
                
                if not start or not dest_hosp:
                    continue
                    
                target_node = self.hospitals.get(dest_hosp, {}).get("node")
                
                try:
                    path = nx.shortest_path(temp_graph, source=start, target=target_node, weight='weight')
                    active_routes[amb_id] = path
                    
                    # Inflate weight for lower-priority collision avoidance
                    for i in range(len(path) - 1):
                        temp_graph[path[i]][path[i+1]]['weight'] += 100.0

                except nx.NetworkXNoPath:
                    pass

        return active_routes