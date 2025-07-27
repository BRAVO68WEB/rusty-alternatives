# Python Railway Route Finder PoC

A Python-based Proof of Concept (PoC) that processes OpenStreetMap PBF files to build a railway network and find routes between any two railway stations.

## Features

🚂 **Core Functionality**
- Parse and extract railway data from `.osm.pbf` files using `pyosmium`
- Build NetworkX graph from railway infrastructure 
- Calculate optimal routes between stations using Dijkstra's algorithm
- Command-line interface with `click`

🔍 **Smart Station Search**
- Fuzzy string matching for station names using `fuzzywuzzy`
- Handle station name variations and ambiguity
- Geographic search for nearby stations

🛤️ **Advanced Routing**
- Shortest path calculation with distance optimization
- Alternative route suggestions
- Intermediate station identification
- Handle disconnected network components

## Installation

1. **Install Python Dependencies**
   ```bash
   cd railway_finder
   pip install -r requirements.txt
   ```

2. **Download Sample OSM Data** (Optional)
   ```bash
   # Download a small region for testing (e.g., a city or state)
   wget https://download.geofabrik.de/europe/monaco-latest.osm.pbf
   ```

## Usage

### 1. Build Railway Network

Process an OSM PBF file to extract railway data and build the network:

```bash
python railway_finder.py build --input sample.osm.pbf --output network.pkl
```

**Options:**
- `--input, -i`: Input OSM PBF file path (required)
- `--output, -o`: Output network file path (.pkl) (required)  
- `--verbose, -v`: Enable verbose output

### 2. Find Routes

Find the shortest route between two stations:

```bash
python railway_finder.py route --network network.pkl --from "Mumbai Central" --to "New Delhi"
```

**Options:**
- `--network, -n`: Network file path (.pkl) (required)
- `--from`: Starting station name (required)
- `--to`: Destination station name (required)
- `--alternatives, -a`: Show alternative routes
- `--max-alternatives`: Maximum number of alternative routes (default: 3)

**Example Output:**
```
🚂 Route found: Mumbai Central → New Delhi
📏 Total Distance: 1,384.2 km
🚉 Intermediate stations (3):
  1. Mumbai Central (Station) - 0.0 km
  2. Vadodara Junction (Junction) - 391.4 km  
  3. Kota Junction (Junction) - 781.2 km
  4. New Delhi (Station) - 1,384.2 km
```

### 3. Search Stations

Search for stations by name or location:

```bash
# Search by name
python railway_finder.py stations --network network.pkl --station "Central"

# Find nearby stations
python railway_finder.py stations --network network.pkl --lat 19.0330 --lon 72.8570 --radius 5

# List all stations
python railway_finder.py stations --network network.pkl
```

**Options:**
- `--network, -n`: Network file path (.pkl) (required)
- `--station, -s`: Search for specific station by name
- `--lat`: Latitude for geographic search
- `--lon`: Longitude for geographic search  
- `--radius`: Search radius in kilometers (default: 10)

## Architecture

### File Structure
```
railway_finder/
├── railway_finder.py          # Main CLI application
├── osm_processor.py           # OSM PBF parsing and data extraction
├── network_builder.py         # Graph construction from railway data
├── route_finder.py            # Route finding algorithms
├── utils.py                   # Utility functions
├── requirements.txt           # Python dependencies
└── README.md                  # This documentation
```

### Core Components

**OSM Processor** (`osm_processor.py`)
- Extracts railway nodes (stations, junctions, halts, stops)
- Extracts railway ways (rail lines, tracks)  
- Filters active railway infrastructure
- Uses `pyosmium` for efficient PBF parsing

**Network Builder** (`network_builder.py`)
- Builds NetworkX graph from OSM data
- Creates nodes for stations with coordinates and metadata
- Creates weighted edges based on geographic distance
- Adds intermediate nodes for very long segments

**Route Finder** (`route_finder.py`)
- Implements Dijkstra's shortest path algorithm
- Fuzzy station name matching with `fuzzywuzzy`
- Alternative route calculation
- Geographic station search

**CLI Application** (`railway_finder.py`)
- Command-line interface using `click`
- Progress indicators with `tqdm`
- Interactive station disambiguation
- Formatted output with emojis and colors

## Technical Details

### Supported Railway Types

**Nodes:**
- `station` - Railway stations
- `halt` - Small stops/halts
- `junction` - Railway junctions
- `crossing` - Level crossings
- `tram_stop` - Tram/light rail stops

**Ways:**
- `rail` - Main railway lines
- `light_rail` - Light rail/metro
- `subway` - Underground rail
- `tram` - Tram lines
- `monorail` - Monorail systems

### Performance

- **Small datasets** (cities): Process in seconds
- **Regional datasets**: Process in minutes  
- **Memory efficient**: Handles 500MB+ PBF files
- **Network persistence**: Save/load processed networks

### Limitations

- Requires quality OSM railway data
- Route quality depends on OSM data completeness
- Large datasets may require significant memory
- No real-time scheduling information

## Sample Datasets

For testing, you can download OSM extracts from:
- [Geofabrik](https://download.geofabrik.de/) - Regional extracts
- [BBBike](https://extract.bbbike.org/) - City extracts
- [OpenStreetMap](https://planet.openstreetmap.org/) - Full planet (very large)

**Recommended for testing:**
```bash
# Small country (Monaco)
wget https://download.geofabrik.de/europe/monaco-latest.osm.pbf

# City extract (London)  
wget https://download.geofabrik.de/europe/great-britain/england/london-latest.osm.pbf

# State/region (California)
wget https://download.geofabrik.de/north-america/us/california-latest.osm.pbf
```

## Dependencies

- **pyosmium** ≥3.6.0 - OSM PBF file processing
- **networkx** ≥3.1 - Graph algorithms and data structures
- **click** ≥8.1.0 - Command-line interface framework
- **geopy** ≥2.3.0 - Geographic distance calculations
- **fuzzywuzzy** ≥0.18.0 - Fuzzy string matching
- **python-Levenshtein** ≥0.21.0 - Fast string similarity
- **tqdm** ≥4.66.0 - Progress bars

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the rusty-alternatives repository and follows the same MIT License.

## Future Enhancements

- 🌐 Web interface for route visualization
- 🚌 Multi-modal transport integration  
- ⏰ Real-time schedule data integration
- 📱 Mobile app development
- 🗺️ Interactive map visualization
- 🔄 Incremental OSM data updates