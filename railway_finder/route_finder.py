"""
Route finding algorithms for railway network navigation.
"""

import networkx as nx
from typing import List, Dict, Optional, Tuple
from fuzzywuzzy import fuzz
from dataclasses import dataclass


@dataclass
class RouteResult:
    """Represents a route between two stations."""
    from_station: str
    to_station: str
    path: List[str]
    total_distance: float
    intermediate_stations: List[Dict[str, any]]


class RouteFinder:
    """Finds routes between railway stations."""
    
    def __init__(self, network: nx.Graph):
        self.network = network
        self.stations = self._build_station_index()
    
    def _build_station_index(self) -> Dict[str, Dict]:
        """Build an index of all stations for fast lookup."""
        stations = {}
        for node_id, data in self.network.nodes(data=True):
            if data.get('is_station', False):
                station_name = data['name'].lower()
                stations[station_name] = {
                    'id': node_id,
                    'name': data['name'],
                    'type': data['type'],
                    'lat': data['lat'],
                    'lon': data['lon']
                }
        return stations
    
    def find_stations(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Find stations matching a query using fuzzy string matching.
        
        Args:
            query: Station name query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching stations with similarity scores
        """
        query_lower = query.lower()
        matches = []
        
        for station_name, station_data in self.stations.items():
            # Calculate similarity score
            ratio = fuzz.ratio(query_lower, station_name)
            partial_ratio = fuzz.partial_ratio(query_lower, station_name)
            token_ratio = fuzz.token_set_ratio(query_lower, station_name)
            
            # Use the best score
            best_score = max(ratio, partial_ratio, token_ratio)
            
            if best_score > 50:  # Minimum similarity threshold
                matches.append({
                    'station': station_data,
                    'score': best_score,
                    'match_type': 'fuzzy'
                })
        
        # Sort by score and return top results
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:max_results]
    
    def find_exact_station(self, query: str) -> Optional[Dict]:
        """Find an exact station match."""
        query_lower = query.lower()
        
        # Try exact match first
        if query_lower in self.stations:
            return self.stations[query_lower]
        
        # Try fuzzy matches and return the best one if score is very high
        matches = self.find_stations(query, max_results=1)
        if matches and matches[0]['score'] >= 90:
            return matches[0]['station']
        
        return None
    
    def find_route(self, from_station: str, to_station: str) -> Optional[RouteResult]:
        """
        Find the shortest route between two stations.
        
        Args:
            from_station: Starting station name
            to_station: Destination station name
            
        Returns:
            RouteResult object or None if no route found
        """
        # Find exact stations
        start_station = self.find_exact_station(from_station)
        end_station = self.find_exact_station(to_station)
        
        if not start_station:
            raise ValueError(f"Starting station '{from_station}' not found")
        
        if not end_station:
            raise ValueError(f"Destination station '{to_station}' not found")
        
        start_node_id = start_station['id']
        end_node_id = end_station['id']
        
        try:
            # Find shortest path using Dijkstra's algorithm
            path = nx.shortest_path(
                self.network, 
                start_node_id, 
                end_node_id, 
                weight='distance'
            )
            
            # Calculate total distance
            total_distance = nx.shortest_path_length(
                self.network,
                start_node_id,
                end_node_id,
                weight='distance'
            )
            
            # Build intermediate stations list
            intermediate_stations = self._build_route_details(path)
            
            return RouteResult(
                from_station=start_station['name'],
                to_station=end_station['name'],
                path=path,
                total_distance=total_distance,
                intermediate_stations=intermediate_stations
            )
            
        except nx.NetworkXNoPath:
            return None
    
    def _build_route_details(self, path: List[str]) -> List[Dict]:
        """Build detailed route information with distances."""
        route_details = []
        cumulative_distance = 0.0
        
        for i, node_id in enumerate(path):
            node_data = self.network.nodes[node_id]
            
            # Only include stations and important points
            if node_data.get('is_station', False) or i == 0 or i == len(path) - 1:
                route_details.append({
                    'name': node_data['name'],
                    'type': node_data['type'],
                    'distance_from_start': cumulative_distance,
                    'lat': node_data['lat'],
                    'lon': node_data['lon']
                })
            
            # Calculate distance to next node
            if i < len(path) - 1:
                next_node_id = path[i + 1]
                if self.network.has_edge(node_id, next_node_id):
                    edge_distance = self.network[node_id][next_node_id]['distance']
                    cumulative_distance += edge_distance
        
        return route_details
    
    def find_alternative_routes(self, from_station: str, to_station: str, num_routes: int = 3) -> List[RouteResult]:
        """
        Find multiple alternative routes between two stations.
        
        Args:
            from_station: Starting station name
            to_station: Destination station name
            num_routes: Number of alternative routes to find
            
        Returns:
            List of RouteResult objects
        """
        start_station = self.find_exact_station(from_station)
        end_station = self.find_exact_station(to_station)
        
        if not start_station or not end_station:
            return []
        
        start_node_id = start_station['id']
        end_node_id = end_station['id']
        
        routes = []
        
        try:
            # Find multiple shortest paths
            for i, path in enumerate(nx.shortest_simple_paths(
                self.network, 
                start_node_id, 
                end_node_id, 
                weight='distance'
            )):
                if i >= num_routes:
                    break
                
                # Calculate path length
                path_length = sum(
                    self.network[path[j]][path[j+1]]['distance']
                    for j in range(len(path) - 1)
                )
                
                # Build route details
                intermediate_stations = self._build_route_details(path)
                
                routes.append(RouteResult(
                    from_station=start_station['name'],
                    to_station=end_station['name'],
                    path=path,
                    total_distance=path_length,
                    intermediate_stations=intermediate_stations
                ))
                
        except nx.NetworkXNoPath:
            pass
        
        return routes
    
    def get_nearby_stations(self, lat: float, lon: float, radius_km: float = 10) -> List[Dict]:
        """
        Find stations within a certain radius of given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of nearby stations
        """
        from geopy.distance import geodesic
        
        nearby_stations = []
        
        for station_data in self.stations.values():
            station_coords = (station_data['lat'], station_data['lon'])
            query_coords = (lat, lon)
            
            distance = geodesic(query_coords, station_coords).kilometers
            
            if distance <= radius_km:
                nearby_stations.append({
                    'station': station_data,
                    'distance_km': round(distance, 2)
                })
        
        # Sort by distance
        nearby_stations.sort(key=lambda x: x['distance_km'])
        return nearby_stations