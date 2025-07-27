"""
Network builder for constructing railway graphs from OSM data.
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional
from geopy.distance import geodesic
import math

from osm_processor import RailwayNode, RailwayWay


class NetworkBuilder:
    """Builds a NetworkX graph from railway OSM data."""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.node_lookup = {}  # node_id -> graph_node_id mapping
        
    def build_network(self, 
                     railway_nodes: Dict[int, RailwayNode], 
                     railway_ways: Dict[int, RailwayWay],
                     all_nodes: Dict[int, Tuple[float, float]]) -> nx.Graph:
        """
        Build a NetworkX graph from railway data.
        
        Args:
            railway_nodes: Dictionary of railway nodes
            railway_ways: Dictionary of railway ways
            all_nodes: Dictionary of all node coordinates
            
        Returns:
            NetworkX graph representing the railway network
        """
        print("Building railway network graph...")
        
        # Add railway nodes to the graph
        self._add_railway_nodes(railway_nodes)
        
        # Add edges based on railway ways
        self._add_railway_connections(railway_ways, all_nodes)
        
        # Add intermediate nodes for long segments
        self._add_intermediate_nodes(railway_ways, all_nodes)
        
        print(f"Built network with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def _add_railway_nodes(self, railway_nodes: Dict[int, RailwayNode]) -> None:
        """Add railway stations and important nodes to the graph."""
        for node_id, node in railway_nodes.items():
            graph_node_id = f"station_{node_id}"
            self.node_lookup[node_id] = graph_node_id
            
            self.graph.add_node(
                graph_node_id,
                name=node.name,
                type=node.railway_type,
                lat=node.lat,
                lon=node.lon,
                osm_id=node_id,
                is_station=True
            )
    
    def _add_railway_connections(self, 
                               railway_ways: Dict[int, RailwayWay],
                               all_nodes: Dict[int, Tuple[float, float]]) -> None:
        """Add edges between connected nodes."""
        for way_id, way in railway_ways.items():
            way_nodes = []
            
            # Get coordinates for all nodes in this way
            for node_id in way.nodes:
                if node_id in all_nodes:
                    lat, lon = all_nodes[node_id]
                    
                    # Check if this is a railway station/important node
                    if node_id in self.node_lookup:
                        graph_node_id = self.node_lookup[node_id]
                    else:
                        # Create a regular track node
                        graph_node_id = f"track_{node_id}"
                        if graph_node_id not in self.graph:
                            self.graph.add_node(
                                graph_node_id,
                                name=f"Track point {node_id}",
                                type="track_point",
                                lat=lat,
                                lon=lon,
                                osm_id=node_id,
                                is_station=False
                            )
                        self.node_lookup[node_id] = graph_node_id
                    
                    way_nodes.append(graph_node_id)
            
            # Add edges between consecutive nodes in the way
            for i in range(len(way_nodes) - 1):
                node1_id = way_nodes[i]
                node2_id = way_nodes[i + 1]
                
                if node1_id in self.graph and node2_id in self.graph:
                    node1_data = self.graph.nodes[node1_id]
                    node2_data = self.graph.nodes[node2_id]
                    
                    # Calculate distance
                    distance = self._calculate_distance(
                        (node1_data['lat'], node1_data['lon']),
                        (node2_data['lat'], node2_data['lon'])
                    )
                    
                    self.graph.add_edge(
                        node1_id,
                        node2_id,
                        distance=distance,
                        way_id=way_id,
                        railway_type=way.railway_type
                    )
    
    def _add_intermediate_nodes(self, 
                              railway_ways: Dict[int, RailwayWay],
                              all_nodes: Dict[int, Tuple[float, float]]) -> None:
        """Add intermediate nodes for very long segments to improve routing."""
        edges_to_split = []
        
        # Find edges longer than 50km that might need intermediate nodes
        for edge in self.graph.edges(data=True):
            if edge[2]['distance'] > 50:  # 50km threshold
                edges_to_split.append(edge)
        
        for edge in edges_to_split:
            node1, node2, data = edge
            distance = data['distance']
            
            # Only split if distance is very long (>100km)
            if distance > 100:
                node1_data = self.graph.nodes[node1]
                node2_data = self.graph.nodes[node2]
                
                # Calculate midpoint
                mid_lat = (node1_data['lat'] + node2_data['lat']) / 2
                mid_lon = (node1_data['lon'] + node2_data['lon']) / 2
                
                # Create intermediate node
                mid_node_id = f"intermediate_{node1}_{node2}"
                self.graph.add_node(
                    mid_node_id,
                    name=f"Intermediate point",
                    type="intermediate",
                    lat=mid_lat,
                    lon=mid_lon,
                    osm_id=0,
                    is_station=False
                )
                
                # Remove original edge
                self.graph.remove_edge(node1, node2)
                
                # Add two new edges
                dist1 = self._calculate_distance(
                    (node1_data['lat'], node1_data['lon']),
                    (mid_lat, mid_lon)
                )
                dist2 = self._calculate_distance(
                    (mid_lat, mid_lon),
                    (node2_data['lat'], node2_data['lon'])
                )
                
                self.graph.add_edge(node1, mid_node_id, distance=dist1, **data)
                self.graph.add_edge(mid_node_id, node2, distance=dist2, **data)
    
    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers."""
        return geodesic(coord1, coord2).kilometers
    
    def get_stations(self) -> List[Dict]:
        """Get all railway stations from the network."""
        stations = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get('is_station', False):
                stations.append({
                    'id': node_id,
                    'name': data['name'],
                    'type': data['type'],
                    'lat': data['lat'],
                    'lon': data['lon']
                })
        return stations
    
    def get_network_statistics(self) -> Dict:
        """Get network statistics."""
        stations = [n for n, d in self.graph.nodes(data=True) if d.get('is_station', False)]
        track_points = [n for n, d in self.graph.nodes(data=True) if not d.get('is_station', False)]
        
        # Calculate total network length
        total_length = sum(data['distance'] for _, _, data in self.graph.edges(data=True))
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'stations': len(stations),
            'track_points': len(track_points),
            'total_length_km': round(total_length, 2),
            'connected_components': nx.number_connected_components(self.graph)
        }