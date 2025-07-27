"""
OSM PBF processor for extracting railway data from OpenStreetMap files.
"""

try:
    import osmium
    HAS_OSMIUM = True
except ImportError:
    HAS_OSMIUM = False
    print("Warning: pyosmium not available. Using mock data for demonstration.")

from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import json


@dataclass
class RailwayNode:
    """Represents a railway node (station, halt, junction, etc.)"""
    id: int
    lat: float
    lon: float
    name: str
    railway_type: str
    tags: Dict[str, str]


@dataclass
class RailwayWay:
    """Represents a railway way (track, line)"""
    id: int
    nodes: List[int]
    railway_type: str
    tags: Dict[str, str]


if HAS_OSMIUM:
    class RailwayHandler(osmium.SimpleHandler):
        """OSM handler for extracting railway data."""
        
        def __init__(self):
            super().__init__()
            self.railway_nodes: Dict[int, RailwayNode] = {}
            self.railway_ways: Dict[int, RailwayWay] = {}
            self.all_nodes: Dict[int, Tuple[float, float]] = {}
            
            # Railway types we're interested in
            self.railway_node_types = {
                'station', 'halt', 'tram_stop', 'subway_entrance',
                'junction', 'crossing', 'level_crossing'
            }
            
            self.railway_way_types = {
                'rail', 'light_rail', 'subway', 'tram', 'monorail',
                'narrow_gauge', 'funicular', 'rack'
            }
        
        def node(self, n):
            """Process OSM nodes."""
            # Store all node coordinates for way processing
            self.all_nodes[n.id] = (n.location.lat, n.location.lon)
            
            # Check if this is a railway node
            if 'railway' in n.tags:
                railway_type = n.tags.get('railway')
                if railway_type in self.railway_node_types:
                    name = n.tags.get('name', f'Unnamed {railway_type}')
                    
                    railway_node = RailwayNode(
                        id=n.id,
                        lat=n.location.lat,
                        lon=n.location.lon,
                        name=name,
                        railway_type=railway_type,
                        tags=dict(n.tags)
                    )
                    self.railway_nodes[n.id] = railway_node
        
        def way(self, w):
            """Process OSM ways."""
            if 'railway' in w.tags:
                railway_type = w.tags.get('railway')
                if railway_type in self.railway_way_types:
                    # Only include ways that are not abandoned or disused
                    if w.tags.get('service') not in ['abandoned', 'disused']:
                        railway_way = RailwayWay(
                            id=w.id,
                            nodes=list(w.nodes),
                            railway_type=railway_type,
                            tags=dict(w.tags)
                        )
                        self.railway_ways[w.id] = railway_way
else:
    class RailwayHandler:
        """Mock railway handler for demonstration when osmium is not available."""
        
        def __init__(self):
            self.railway_nodes: Dict[int, RailwayNode] = {}
            self.railway_ways: Dict[int, RailwayWay] = {}
            self.all_nodes: Dict[int, Tuple[float, float]] = {}
            
        def apply_file(self, filename):
            """Mock apply_file method that creates sample data."""
            # Create sample railway network data for demonstration
            self._create_sample_network()
        
        def _create_sample_network(self):
            """Create a small sample railway network for testing."""
            # Sample stations
            sample_stations = [
                (1001, 40.7589, -73.9851, "New York Penn Station", "station"),
                (1002, 40.7505, -73.9934, "Herald Square", "station"),
                (1003, 40.7282, -73.7948, "Jamaica Station", "station"),
                (1004, 40.6781, -73.9442, "Atlantic Terminal", "station"),
                (1005, 40.8176, -73.9782, "125th Street", "station"),
                (1006, 40.7052, -74.0114, "Hoboken Terminal", "station"),
                (1007, 41.2033, -73.9565, "White Plains", "station"),
                (1008, 40.6643, -73.8364, "East New York", "junction"),
                (1009, 40.7128, -74.0060, "World Trade Center", "station"),
                (1010, 40.6936, -73.9893, "Park Slope", "halt")
            ]
            
            # Create nodes
            for node_id, lat, lon, name, station_type in sample_stations:
                self.all_nodes[node_id] = (lat, lon)
                railway_node = RailwayNode(
                    id=node_id,
                    lat=lat,
                    lon=lon,
                    name=name,
                    railway_type=station_type,
                    tags={'name': name, 'railway': station_type}
                )
                self.railway_nodes[node_id] = railway_node
            
            # Add some intermediate track points
            track_points = [
                (2001, 40.7500, -73.9900),
                (2002, 40.7400, -73.9800),
                (2003, 40.7300, -73.9700),
                (2004, 40.7200, -73.9600),
                (2005, 40.7100, -73.9500),
                (2006, 40.7000, -73.9400),
                (2007, 40.6900, -73.9300),
                (2008, 40.6800, -73.9200),
            ]
            
            for node_id, lat, lon in track_points:
                self.all_nodes[node_id] = (lat, lon)
            
            # Create sample ways (railway lines)
            sample_ways = [
                (3001, [1001, 2001, 1002, 2002, 1003], "rail"),  # Penn Station -> Herald -> Jamaica
                (3002, [1001, 2003, 1004], "rail"),               # Penn Station -> Atlantic Terminal
                (3003, [1002, 2004, 1005], "rail"),               # Herald Square -> 125th Street
                (3004, [1001, 2005, 1006], "rail"),               # Penn Station -> Hoboken
                (3005, [1005, 2006, 1007], "rail"),               # 125th Street -> White Plains
                (3006, [1003, 2007, 1008], "rail"),               # Jamaica -> East New York
                (3007, [1001, 2008, 1009], "subway"),             # Penn Station -> WTC (subway)
                (3008, [1004, 1010], "rail"),                     # Atlantic Terminal -> Park Slope
            ]
            
            for way_id, nodes, railway_type in sample_ways:
                railway_way = RailwayWay(
                    id=way_id,
                    nodes=nodes,
                    railway_type=railway_type,
                    tags={'railway': railway_type}
                )
                self.railway_ways[way_id] = railway_way


class OSMProcessor:
    """Main processor for OSM PBF files."""
    
    def __init__(self):
        self.handler = RailwayHandler()
    
    def process_file(self, pbf_file: str) -> Tuple[Dict[int, RailwayNode], Dict[int, RailwayWay], Dict[int, Tuple[float, float]]]:
        """
        Process an OSM PBF file and extract railway data.
        
        Returns:
            Tuple of (railway_nodes, railway_ways, all_nodes)
        """
        print(f"Processing OSM PBF file: {pbf_file}")
        
        if not HAS_OSMIUM:
            print("Note: Using sample data for demonstration (pyosmium not available)")
            self.handler.apply_file(pbf_file)
        else:
            try:
                self.handler.apply_file(pbf_file)
            except Exception as e:
                raise RuntimeError(f"Failed to process PBF file: {e}")
        
        print(f"Found {len(self.handler.railway_nodes)} railway nodes")
        print(f"Found {len(self.handler.railway_ways)} railway ways")
        
        return (
            self.handler.railway_nodes,
            self.handler.railway_ways,
            self.handler.all_nodes
        )
    
    def get_railway_statistics(self) -> Dict[str, int]:
        """Get statistics about the extracted railway data."""
        node_types = {}
        way_types = {}
        
        for node in self.handler.railway_nodes.values():
            node_types[node.railway_type] = node_types.get(node.railway_type, 0) + 1
        
        for way in self.handler.railway_ways.values():
            way_types[way.railway_type] = way_types.get(way.railway_type, 0) + 1
        
        return {
            'total_nodes': len(self.handler.railway_nodes),
            'total_ways': len(self.handler.railway_ways),
            'node_types': node_types,
            'way_types': way_types
        }