#!/usr/bin/env python3
"""
Demo script for the Railway Route Finder.
Shows key functionality with sample data.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from osm_processor import OSMProcessor
from network_builder import NetworkBuilder
from route_finder import RouteFinder
from utils import save_network, load_network, format_distance


def main():
    """Run the demo."""
    print("🚂 Railway Route Finder - Demo")
    print("=" * 50)
    
    # Step 1: Process OSM data (using sample data)
    print("\n📋 Step 1: Processing sample railway data...")
    processor = OSMProcessor()
    railway_nodes, railway_ways, all_nodes = processor.process_file("sample.osm.pbf")
    
    # Show statistics
    stats = processor.get_railway_statistics()
    print(f"   ✅ Extracted {stats['total_nodes']} railway nodes")
    print(f"   ✅ Extracted {stats['total_ways']} railway ways")
    
    # Step 2: Build network
    print("\n🔗 Step 2: Building railway network...")
    builder = NetworkBuilder()
    network = builder.build_network(railway_nodes, railway_ways, all_nodes)
    
    net_stats = builder.get_network_statistics()
    print(f"   ✅ Built network with {net_stats['total_nodes']} nodes")
    print(f"   ✅ Total network length: {format_distance(net_stats['total_length_km'])}")
    
    # Step 3: Demonstrate route finding
    print("\n🗺️  Step 3: Finding routes...")
    finder = RouteFinder(network)
    
    # Example routes
    test_routes = [
        ("New York Penn Station", "Jamaica Station"),
        ("Herald Square", "Atlantic Terminal"),
        ("Penn", "World Trade Center")  # Test fuzzy matching
    ]
    
    for from_station, to_station in test_routes:
        print(f"\n   🔍 Route: {from_station} → {to_station}")
        
        try:
            route = finder.find_route(from_station, to_station)
            if route:
                print(f"      📏 Distance: {format_distance(route.total_distance)}")
                stations = [s for s in route.intermediate_stations if 'station' in s['type'].lower()]
                if len(stations) > 2:
                    print(f"      🚉 Via: {stations[1]['name']}")
                else:
                    print("      🚉 Direct route")
            else:
                print("      ❌ No route found")
        except ValueError as e:
            print(f"      ❌ {e}")
    
    # Step 4: Demonstrate station search
    print("\n🔍 Step 4: Station search demo...")
    
    search_terms = ["Penn", "Central", "Terminal"]
    for term in search_terms:
        matches = finder.find_stations(term, max_results=3)
        print(f"\n   🔎 Searching for '{term}':")
        if matches:
            for match in matches:
                station = match['station']
                print(f"      • {station['name']} ({station['type']}) - {match['score']}% match")
        else:
            print("      No matches found")
    
    # Step 5: Show network overview
    print("\n📊 Step 5: Network overview...")
    stations = finder.stations
    by_type = {}
    for station_data in stations.values():
        station_type = station_data['type']
        by_type[station_type] = by_type.get(station_type, 0) + 1
    
    for station_type, count in by_type.items():
        print(f"   • {station_type.replace('_', ' ').title()}: {count}")
    
    print("\n✅ Demo completed!")
    print("\n💡 To use with real OSM data:")
    print("   1. Download an OSM PBF file from Geofabrik or OSM")
    print("   2. Install pyosmium: pip install pyosmium")
    print("   3. Run: python railway_finder.py build --input your_file.osm.pbf --output network.pkl")
    print("   4. Find routes: python railway_finder.py route --network network.pkl --from 'Station A' --to 'Station B'")


if __name__ == "__main__":
    main()