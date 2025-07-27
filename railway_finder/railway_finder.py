#!/usr/bin/env python3
"""
Railway Route Finder - Main CLI Application

A Python-based tool for finding railway routes using OpenStreetMap data.
"""

import click
import sys
from pathlib import Path
from tqdm import tqdm

from osm_processor import OSMProcessor
from network_builder import NetworkBuilder
from route_finder import RouteFinder
from utils import save_network, load_network, format_distance, validate_file_exists, ensure_directory_exists


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🚂 Railway Route Finder - Find routes between railway stations using OSM data."""
    pass


@cli.command()
@click.option('--input', '-i', required=True, type=click.Path(exists=True), 
              help='Input OSM PBF file path')
@click.option('--output', '-o', required=True, type=click.Path(), 
              help='Output network file path (.pkl)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def build(input, output, verbose):
    """
    🔧 Build railway network from OSM PBF file.
    
    Process an OpenStreetMap PBF file to extract railway infrastructure
    and build a network graph for route finding.
    """
    click.echo("🚂 Railway Route Finder - Network Builder")
    click.echo("=" * 50)
    
    if verbose:
        click.echo(f"📂 Input file: {input}")
        click.echo(f"💾 Output file: {output}")
    
    try:
        # Ensure output directory exists
        ensure_directory_exists(output)
        
        # Step 1: Process OSM PBF file
        click.echo("\n📋 Step 1: Processing OSM PBF file...")
        processor = OSMProcessor()
        
        with tqdm(desc="Processing OSM data", unit="MB") as pbar:
            railway_nodes, railway_ways, all_nodes = processor.process_file(input)
            pbar.update(1)
        
        if not railway_nodes:
            click.echo("❌ No railway nodes found in the OSM file!")
            sys.exit(1)
        
        # Show statistics
        stats = processor.get_railway_statistics()
        click.echo(f"   ✅ Found {stats['total_nodes']} railway nodes")
        click.echo(f"   ✅ Found {stats['total_ways']} railway ways")
        
        if verbose:
            click.echo("   📊 Node types:")
            for node_type, count in stats['node_types'].items():
                click.echo(f"      • {node_type}: {count}")
            
            click.echo("   📊 Way types:")
            for way_type, count in stats['way_types'].items():
                click.echo(f"      • {way_type}: {count}")
        
        # Step 2: Build network graph
        click.echo("\n🔗 Step 2: Building network graph...")
        builder = NetworkBuilder()
        
        with tqdm(desc="Building network", unit="connections") as pbar:
            network = builder.build_network(railway_nodes, railway_ways, all_nodes)
            pbar.update(1)
        
        # Show network statistics
        net_stats = builder.get_network_statistics()
        click.echo(f"   ✅ Built network with {net_stats['total_nodes']} nodes")
        click.echo(f"   ✅ Created {net_stats['total_edges']} connections")
        click.echo(f"   ✅ Total network length: {format_distance(net_stats['total_length_km'])}")
        click.echo(f"   ✅ Railway stations: {net_stats['stations']}")
        
        if net_stats['connected_components'] > 1:
            click.echo(f"   ⚠️  Network has {net_stats['connected_components']} disconnected components")
        
        # Step 3: Save network
        click.echo("\n💾 Step 3: Saving network...")
        with tqdm(desc="Saving network", unit="MB") as pbar:
            save_network(network, output)
            pbar.update(1)
        
        click.echo(f"   ✅ Network saved to: {output}")
        click.echo("\n🎉 Network building completed successfully!")
        click.echo(f"🚀 You can now find routes using: python railway_finder.py route --network {output}")
        
    except Exception as e:
        click.echo(f"❌ Error during network building: {e}")
        sys.exit(1)


@cli.command()
@click.option('--network', '-n', required=True, type=click.Path(exists=True),
              help='Network file path (.pkl)')
@click.option('--from', 'from_station', required=True, help='Starting station name')
@click.option('--to', 'to_station', required=True, help='Destination station name')
@click.option('--alternatives', '-a', is_flag=True, help='Show alternative routes')
@click.option('--max-alternatives', default=3, help='Maximum number of alternative routes')
def route(network, from_station, to_station, alternatives, max_alternatives):
    """
    🗺️  Find route between two railway stations.
    
    Calculate the optimal route between two stations using the pre-built
    railway network graph.
    """
    click.echo("🚂 Railway Route Finder - Route Planner")
    click.echo("=" * 50)
    
    try:
        # Load network
        click.echo("📡 Loading railway network...")
        graph = load_network(network)
        
        if graph is None:
            click.echo(f"❌ Could not load network from: {network}")
            sys.exit(1)
        
        click.echo(f"   ✅ Loaded network with {graph.number_of_nodes()} nodes")
        
        # Initialize route finder
        finder = RouteFinder(graph)
        
        # Handle ambiguous station names
        from_matches = finder.find_stations(from_station, max_results=5)
        to_matches = finder.find_stations(to_station, max_results=5)
        
        # Check for exact matches first
        from_exact = finder.find_exact_station(from_station)
        to_exact = finder.find_exact_station(to_station)
        
        # Handle starting station ambiguity
        if not from_exact and len(from_matches) > 1:
            click.echo(f"\n🤔 Multiple matches found for '{from_station}':")
            for i, match in enumerate(from_matches[:5]):
                station = match['station']
                click.echo(f"   {i+1}. {station['name']} ({station['type']}) - {match['score']}% match")
            
            choice = click.prompt("Please select starting station", type=int, default=1)
            from_station = from_matches[choice-1]['station']['name']
        elif from_exact:
            from_station = from_exact['name']
        elif from_matches:
            from_station = from_matches[0]['station']['name']
        else:
            click.echo(f"❌ Starting station '{from_station}' not found!")
            sys.exit(1)
        
        # Handle destination station ambiguity
        if not to_exact and len(to_matches) > 1:
            click.echo(f"\n🤔 Multiple matches found for '{to_station}':")
            for i, match in enumerate(to_matches[:5]):
                station = match['station']
                click.echo(f"   {i+1}. {station['name']} ({station['type']}) - {match['score']}% match")
            
            choice = click.prompt("Please select destination station", type=int, default=1)
            to_station = to_matches[choice-1]['station']['name']
        elif to_exact:
            to_station = to_exact['name']
        elif to_matches:
            to_station = to_matches[0]['station']['name']
        else:
            click.echo(f"❌ Destination station '{to_station}' not found!")
            sys.exit(1)
        
        # Find route(s)
        click.echo(f"\n🔍 Finding route from '{from_station}' to '{to_station}'...")
        
        if alternatives:
            routes = finder.find_alternative_routes(from_station, to_station, max_alternatives)
        else:
            main_route = finder.find_route(from_station, to_station)
            routes = [main_route] if main_route else []
        
        if not routes:
            click.echo("❌ No route found between the specified stations.")
            click.echo("   💡 Tip: The stations might be on disconnected parts of the network.")
            sys.exit(1)
        
        # Display route(s)
        for i, route in enumerate(routes):
            if len(routes) > 1:
                click.echo(f"\n🛤️  Route {i+1}:")
            else:
                click.echo(f"\n🚂 Route found: {route.from_station} → {route.to_station}")
            
            click.echo(f"📏 Total Distance: {format_distance(route.total_distance)}")
            
            # Show intermediate stations
            stations_only = [station for station in route.intermediate_stations 
                           if any(station_type in station['type'] for station_type in ['station', 'halt', 'junction'])]
            
            if len(stations_only) > 2:  # More than just start and end
                click.echo(f"🚉 Intermediate stations ({len(stations_only) - 2}):")
                for j, station in enumerate(stations_only):
                    distance_info = format_distance(station['distance_from_start'])
                    station_type = station['type'].replace('_', ' ').title()
                    click.echo(f"  {j+1}. {station['name']} ({station_type}) - {distance_info}")
            else:
                click.echo("🚉 Direct route (no intermediate stations)")
            
            if alternatives and i < len(routes) - 1:
                click.echo("-" * 30)
        
        if alternatives and len(routes) > 1:
            click.echo(f"\n💡 Found {len(routes)} alternative routes")
        
        click.echo("\n✅ Route planning completed!")
        
    except Exception as e:
        click.echo(f"❌ Error during route finding: {e}")
        sys.exit(1)


@cli.command()
@click.option('--network', '-n', required=True, type=click.Path(exists=True),
              help='Network file path (.pkl)')
@click.option('--station', '-s', help='Search for specific station')
@click.option('--lat', type=float, help='Latitude for nearby station search')
@click.option('--lon', type=float, help='Longitude for nearby station search')
@click.option('--radius', default=10, help='Search radius in kilometers')
def stations(network, station, lat, lon, radius):
    """
    🚉 Search and list railway stations.
    
    Search for specific stations or find stations near given coordinates.
    """
    click.echo("🚂 Railway Route Finder - Station Search")
    click.echo("=" * 50)
    
    try:
        # Load network
        click.echo("📡 Loading railway network...")
        graph = load_network(network)
        
        if graph is None:
            click.echo(f"❌ Could not load network from: {network}")
            sys.exit(1)
        
        finder = RouteFinder(graph)
        
        if station:
            # Search for specific station
            click.echo(f"\n🔍 Searching for stations matching '{station}'...")
            matches = finder.find_stations(station, max_results=10)
            
            if not matches:
                click.echo("❌ No stations found matching your query.")
            else:
                click.echo(f"📍 Found {len(matches)} matching stations:")
                for i, match in enumerate(matches):
                    st = match['station']
                    click.echo(f"  {i+1}. {st['name']} ({st['type']}) - {match['score']}% match")
                    click.echo(f"      📍 {st['lat']:.6f}, {st['lon']:.6f}")
        
        elif lat is not None and lon is not None:
            # Find nearby stations
            click.echo(f"\n🔍 Finding stations within {radius}km of ({lat:.6f}, {lon:.6f})...")
            nearby = finder.get_nearby_stations(lat, lon, radius)
            
            if not nearby:
                click.echo(f"❌ No stations found within {radius}km of the specified location.")
            else:
                click.echo(f"📍 Found {len(nearby)} nearby stations:")
                for i, item in enumerate(nearby):
                    st = item['station']
                    dist = item['distance_km']
                    click.echo(f"  {i+1}. {st['name']} ({st['type']}) - {dist}km away")
                    click.echo(f"      📍 {st['lat']:.6f}, {st['lon']:.6f}")
        
        else:
            # List all stations
            all_stations = finder.stations
            click.echo(f"\n📋 Network contains {len(all_stations)} stations:")
            
            # Group by type
            by_type = {}
            for station_data in all_stations.values():
                station_type = station_data['type']
                if station_type not in by_type:
                    by_type[station_type] = []
                by_type[station_type].append(station_data)
            
            for station_type, stations_list in by_type.items():
                click.echo(f"\n🏷️  {station_type.replace('_', ' ').title()} ({len(stations_list)}):")
                for station in sorted(stations_list, key=lambda x: x['name'])[:10]:
                    click.echo(f"   • {station['name']}")
                
                if len(stations_list) > 10:
                    click.echo(f"   ... and {len(stations_list) - 10} more")
        
    except Exception as e:
        click.echo(f"❌ Error during station search: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()