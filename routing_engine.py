import networkx as nx
import threading

class RoutingEngine:
    def __init__(self, edges, hospitals):
        self.graph = nx.Graph()
        self.graph.add_edges_from(edges)
        self.hospitals = hospitals
        self.lock = threading.Lock()

    def calculate_active_routes(self, ambulances):
        active_routes = {}
        sorted_ambs = sorted(ambulances.items(), key=lambda x: x[1]['priority'])

        with self.lock:
            temp_graph = self.graph.copy()
            for amb_id, data in sorted_ambs:
                start = data.get("pos")
                dest_hosp = data.get("dest")
                
                if not start or not dest_hosp: continue
                target_node = self.hospitals.get(dest_hosp, {}).get("node")
                
                try:
                    path = nx.shortest_path(temp_graph, source=start, target=target_node, weight='weight')
                    active_routes[amb_id] = path
                    
                    # Shared Corridor Logic: Drop weight for subsequent ambulances to encourage convoy
                    for i in range(len(path)-1):
                        temp_graph[path[i]][path[i+1]]['weight'] = 0.1 
                except nx.NetworkXNoPath:
                    pass
        return active_routes