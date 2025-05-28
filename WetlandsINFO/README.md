# WetlandsINFO - Wetland Data Query Tool

A comprehensive tool for querying wetland data and generating professional wetland maps for any coordinate. This tool provides a simplified interface similar to the FloodINFO system but focused on wetland analysis and mapping.

## Features

### 🌿 Wetland Data Analysis
- **Comprehensive wetland detection** at exact coordinates
- **Progressive search** within 0.5 and 1.0 mile radius if no wetlands at exact location
- **Multiple data sources**: USFWS National Wetlands Inventory (NWI), EPA RIBITS, riparian areas, watersheds
- **Detailed wetland classification** with NWI codes and descriptions
- **Regulatory implications** and recommendations

### 🗺️ Professional Map Generation
- **Adaptive mapping** with intelligent buffer sizing based on wetland analysis
- **Multiple map types**: Detailed, Overview, Adaptive, and Custom
- **High-resolution PDFs** with legends, scale bars, and professional layouts
- **Multiple base maps**: Satellite imagery, topographic, and street maps
- **Configurable transparency** and buffer distances

### 📊 Comprehensive Reporting
- **Detailed analysis reports** with wetland classifications
- **JSON output** for programmatic use
- **Summary reports** with regulatory implications
- **Auto-save functionality** for all results

## Installation

The tool requires Python 3.7+ and the following dependencies (already installed in the virtual environment):

```bash
# Activate the virtual environment
source ../.venv/bin/activate

# All dependencies are already installed
```

## Usage

### Command Line Interface

#### Basic Usage
```bash
# Interactive mode (recommended for first-time users)
python main.py

# Command line with coordinates
python main.py <longitude> <latitude> [location_name] [operation_type]
```

### MCP Server (AI Agents and Tools)

WetlandsINFO includes a Model Context Protocol (MCP) server for integration with AI agents and tools:

```bash
# Start MCP server with stdio transport (default)
python mcp_server.py

# Start with HTTP transport for web-based access
python mcp_server.py --transport streamable-http --port 8001
```

The MCP server exposes 5 tools:
- `query_wetland_data` - Comprehensive wetland analysis
- `generate_detailed_wetland_map` - High-resolution detailed maps
- `generate_overview_wetland_map` - Regional overview maps  
- `generate_adaptive_wetland_map` - Intelligent adaptive maps
- `generate_custom_wetland_map` - Custom maps with specified parameters

See `MCP_README.md` for detailed integration examples and API documentation.

#### Operation Types
- `comprehensive` - Complete analysis with adaptive map (default)
- `query` - Wetland data analysis only
- `detailed` - Detailed map (0.3 mile buffer, satellite imagery)
- `overview` - Overview map (1.0 mile buffer, topographic)
- `adaptive` - Intelligent map with optimal buffer sizing
- `custom` - Custom map with user-specified parameters
- `all_maps` - Generate all map types

### Examples

#### 1. Comprehensive Analysis (Default)
```bash
python main.py -66.199399 18.408303 "Bayamón, Puerto Rico"
```
This performs complete wetland analysis and generates an adaptive map with optimal settings.

#### 2. Query Only
```bash
python main.py -66.199399 18.408303 "Test Location" query
```
Analyzes wetland data without generating maps.

#### 3. Detailed Map
```bash
python main.py -66.199399 18.408303 "Detailed View" detailed
```
Generates a high-resolution detailed map with 0.3 mile buffer.

#### 4. Overview Map
```bash
python main.py -66.199399 18.408303 "Regional View" overview
```
Generates a topographic overview map with 1.0 mile buffer.

#### 5. All Maps
```bash
python main.py -66.199399 18.408303 "Complete Set" all_maps
```
Generates detailed, overview, and adaptive maps.

### Interactive Mode

Run without arguments for guided input:

```bash
python main.py
```

The interactive mode provides:
- Default coordinates (Puerto Rico example)
- Operation type selection menu
- Custom parameter input for custom maps
- Error handling and validation

## Output Files

### Analysis Results
- **JSON files**: Complete analysis data in `logs/` directory
- **Summary files**: Human-readable summaries with detailed classifications
- **Auto-generated filenames** with timestamps and coordinates

### Map Files
- **PDF maps**: High-resolution maps in `output/` directory
- **Professional layouts** with legends, scale bars, and attribution
- **Multiple formats**: Letter and Tabloid sizes available
- **Debug files**: Web Map JSON specifications for troubleshooting

## Map Types and Features

### 1. Detailed Maps
- **Buffer**: 0.3 miles
- **Base map**: Satellite imagery
- **Resolution**: 300 DPI
- **Best for**: Site-specific analysis

### 2. Overview Maps
- **Buffer**: 1.0 miles
- **Base map**: Topographic
- **Resolution**: 250 DPI
- **Best for**: Regional context

### 3. Adaptive Maps
- **Buffer**: Intelligent sizing based on wetland analysis
  - Wetlands at location: 0.5 miles
  - Wetlands within 0.5 miles: Nearest distance + 1.5 miles
  - Wetlands within 1.0 mile: Nearest distance + 1.5 miles
  - No wetlands found: 2.0 miles regional view
- **Base map**: Automatically selected
- **Resolution**: 300 DPI
- **Best for**: Optimal visualization

### 4. Custom Maps
- **User-configurable** buffer, base map, and transparency
- **Three base map options**: Imagery, Topographic, Street
- **Transparency control**: 0.0 (opaque) to 1.0 (transparent)
- **Flexible sizing**: Any buffer radius

## Data Sources

### Primary Sources
- **USFWS National Wetlands Inventory (NWI)**: Comprehensive wetland mapping
- **EPA RIBITS**: Regulatory wetland tracking system
- **EPA National Hydrography Dataset**: Watershed boundaries
- **USFWS Riparian Mapping**: Stream corridors and riparian areas

### Geographic Coverage
- **Puerto Rico and Virgin Islands**: Specialized layer (5)
- **Western CONUS**: Layers 0, 2
- **Eastern CONUS**: Layers 0, 1
- **Automatic layer selection** based on coordinates

## Programmatic Usage

### Python API

```python
from main import WetlandDataQuery

# Initialize the query tool
wetland_query = WetlandDataQuery()

# Query wetland data
results = wetland_query.query(-66.199399, 18.408303, "My Location")

# Generate adaptive map
success, message = wetland_query.generate_adaptive_map(
    -66.199399, 18.408303, "My Location"
)

# Comprehensive analysis
comprehensive = wetland_query.comprehensive_analysis(
    -66.199399, 18.408303, "My Location"
)
```

### Key Methods

#### `query(longitude, latitude, location_name)`
Returns comprehensive wetland analysis data.

#### `generate_detailed_map(longitude, latitude, location_name)`
Generates detailed map with 0.3 mile buffer.

#### `generate_overview_map(longitude, latitude, location_name)`
Generates overview map with 1.0 mile buffer.

#### `generate_adaptive_map(longitude, latitude, location_name)`
Generates map with intelligent buffer sizing.

#### `generate_custom_map(longitude, latitude, location_name, buffer_miles, base_map, transparency)`
Generates map with custom parameters.

#### `comprehensive_analysis(longitude, latitude, location_name)`
Performs complete analysis with adaptive map generation.

## Error Handling

The tool includes comprehensive error handling:
- **Service connectivity** validation
- **Invalid coordinate** detection
- **Missing data** graceful handling
- **Map generation** failure recovery
- **File I/O** error management

## Troubleshooting

### Common Issues

1. **No wetlands found**: Tool will expand search radius automatically
2. **Map generation fails**: Check internet connectivity and service availability
3. **Invalid coordinates**: Ensure longitude/latitude are in decimal degrees
4. **Permission errors**: Ensure write access to `output/` and `logs/` directories

### Debug Information

- **Web Map JSON files** saved for map generation debugging
- **Detailed error messages** with service responses
- **Verbose logging** for troubleshooting

## Regulatory Information

### Important Notes
- **Field verification required**: Maps are for preliminary assessment only
- **Professional delineation**: Consult wetland specialists for regulatory purposes
- **Permit requirements**: Activities in wetlands may require Clean Water Act permits
- **Buffer zones**: Local regulations may require setbacks from wetlands

### Recommended Next Steps
1. **Professional wetland delineation** for regulatory certainty
2. **Jurisdictional determination** from Army Corps of Engineers
3. **Local permit research** for additional requirements
4. **Environmental impact assessment** for development projects

## Additional Resources

- **USFWS Wetlands Mapper**: https://www.fws.gov/wetlands/data/mapper.html
- **EPA Wetlands Information**: https://www.epa.gov/wetlands
- **Clean Water Act Info**: https://www.epa.gov/cwa-404
- **Wetland Delineation Manual**: https://www.usace.army.mil/Missions/Civil-Works/Regulatory-Program-and-Permits/reg_supp/

## Support

For technical support or questions about wetland regulations:
- Review the generated analysis reports
- Consult the additional resources listed above
- Contact local environmental consultants for site-specific guidance

---

**Disclaimer**: This tool provides preliminary wetland information for planning purposes. Professional field verification and regulatory consultation are required for official determinations. 