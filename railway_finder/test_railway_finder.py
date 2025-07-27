#!/usr/bin/env python3
"""
Simple tests for the railway finder components.
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add the railway_finder directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from osm_processor import OSMProcessor, RailwayNode, RailwayWay
from network_builder import NetworkBuilder
from route_finder import RouteFinder
from utils import save_network, load_network


class TestRailwayFinder(unittest.TestCase):
    """Test cases for railway finder components."""
    
    def setUp(self):
        """Set up test data."""
        self.processor = OSMProcessor()
        
        # Create some sample data using the mock processor
        self.processor.handler.apply_file("dummy.pbf")
        
        self.railway_nodes = self.processor.handler.railway_nodes
        self.railway_ways = self.processor.handler.railway_ways
        self.all_nodes = self.processor.handler.all_nodes
    
    def test_osm_processor(self):
        """Test OSM processor functionality."""
        self.assertGreater(len(self.railway_nodes), 0, "Should have railway nodes")
        self.assertGreater(len(self.railway_ways), 0, "Should have railway ways")
        
        # Check that we have the expected sample stations
        station_names = [node.name for node in self.railway_nodes.values()]
        self.assertIn("New York Penn Station", station_names)
        self.assertIn("Jamaica Station", station_names)
    
    def test_network_builder(self):
        """Test network building functionality."""
        builder = NetworkBuilder()
        network = builder.build_network(self.railway_nodes, self.railway_ways, self.all_nodes)
        
        self.assertGreater(network.number_of_nodes(), 0, "Network should have nodes")
        self.assertGreater(network.number_of_edges(), 0, "Network should have edges")
        
        # Check that stations are in the network
        stations = builder.get_stations()
        self.assertGreater(len(stations), 0, "Should have stations")
        
        station_names = [s['name'] for s in stations]
        self.assertIn("New York Penn Station", station_names)
    
    def test_route_finder(self):
        """Test route finding functionality."""
        # Build network
        builder = NetworkBuilder()
        network = builder.build_network(self.railway_nodes, self.railway_ways, self.all_nodes)
        
        # Initialize route finder
        finder = RouteFinder(network)
        
        # Test station search
        matches = finder.find_stations("Penn")
        self.assertGreater(len(matches), 0, "Should find Penn Station")
        
        # Test exact station finding
        station = finder.find_exact_station("New York Penn Station")
        self.assertIsNotNone(station, "Should find exact station")
        self.assertEqual(station['name'], "New York Penn Station")
        
        # Test route finding
        route = finder.find_route("New York Penn Station", "Jamaica Station")
        self.assertIsNotNone(route, "Should find route between stations")
        self.assertEqual(route.from_station, "New York Penn Station")
        self.assertEqual(route.to_station, "Jamaica Station")
        self.assertGreater(route.total_distance, 0, "Route should have distance")
    
    def test_network_persistence(self):
        """Test saving and loading networks."""
        # Build network
        builder = NetworkBuilder()
        network = builder.build_network(self.railway_nodes, self.railway_ways, self.all_nodes)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        try:
            save_network(network, temp_path)
            
            # Load network back
            loaded_network = load_network(temp_path)
            
            self.assertIsNotNone(loaded_network, "Should load network")
            self.assertEqual(network.number_of_nodes(), loaded_network.number_of_nodes())
            self.assertEqual(network.number_of_edges(), loaded_network.number_of_edges())
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_statistics(self):
        """Test statistics generation."""
        stats = self.processor.get_railway_statistics()
        
        self.assertIn('total_nodes', stats)
        self.assertIn('total_ways', stats)
        self.assertIn('node_types', stats)
        self.assertIn('way_types', stats)
        
        self.assertGreater(stats['total_nodes'], 0)
        self.assertGreater(stats['total_ways'], 0)


if __name__ == '__main__':
    print("🧪 Running Railway Finder Tests...")
    unittest.main(verbosity=2)