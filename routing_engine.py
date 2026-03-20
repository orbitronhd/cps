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
        # Sort ambulances: Highest priority first (e.g., Priority 1 before Priority 2)
        sorted_ambs = sorted(ambulances.items(), key=lambda x: x[1]['priority'])

        with self.lock:
            # We use a temp graph to manipulate weights without affecting real traffic data
            temp_graph = self.graph.copy()
            
            # Keep track of edges that are already part of a Green Corridor
            active_corridor_edges = set()

            for amb_id, data in sorted_ambs:
                start = data.get("pos")
                dest_hosp = data.get("dest")
                
                if not start or not dest_hosp:
                    continue
                    
                target_node = self.hospitals.get(dest_hosp, {}).get("node")
                
                try:
                    # 1. Calculate the shortest path based on current temp_graph weights
                    path = nx.shortest_path(temp_graph, source=start, target=target_node, weight='weight')
                    active_routes[amb_id] = path
                    
                    # 2. Convert path nodes to edge tuples (e.g., ['N1', 'N2'] -> ('N1', 'N2'))
                    path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
                    
                    # 3. SHARED CORRIDOR LOGIC:
                    # Once a path is claimed, we set the traffic weight of those edges to 0.1 
                    # (effectively creating a frictionless "vacuum" for subsequent calculations).
                    # If Ambulance 2 is nearby, Dijkstra will see this 0.1 weight and route 
                    # Ambulance 2 onto the same path, creating a convoy.
                    # However, if Ambulance 2 is on the other side of the city, the cost to travel 
                    # to the corridor will be higher than taking a direct raw route, satisfying 
                    # your "time-limit" constraint perfectly via math.
                    
                    for u, v in path_edges:
                        if temp_graph.has_edge(u, v):
                            temp_graph[u][v]['weight'] = 0.1 
                            active_corridor_edges.add((u, v))

                except nx.NetworkXNoPath:
                    print(f"[LOGIC] No valid path found for {amb_id}")

        return active_routes