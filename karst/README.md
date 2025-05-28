# MIPR Karst Module

This module provides functionality to check if coordinates, cadastral numbers, or groups of cadastrals fall within the **PRAPEC** (Plan y Reglamento del Área de Planificación Especial del Carso) karst areas in Puerto Rico.

## Overview

The PRAPEC karst area is a special planning and regulation zone that covers approximately **87,375 hectares** of karst terrain in Puerto Rico. This area is governed by **Regulation 259** and includes important geological formations that require special environmental and development considerations.

## Features

- ✅ **Coordinate Checking**: Check if specific coordinates fall within karst areas
- 🏠 **Cadastral Checking**: Check if cadastral numbers intersect with karst areas  
- 📊 **Batch Processing**: Check multiple cadastrals at once
- 🔍 **Buffer Search**: Find karst areas within a specified radius (default: 0.5 miles)
- 📋 **Detailed Results**: Get comprehensive information about karst areas found

## Quick Start

### Simple Usage

```python
from mipr.karst import check_coordinates_for_karst, check_cadastral_for_karst

# Check coordinates
result = check_coordinates_for_karst(-66.7, 18.4)
if result['in_karst']:
    print("✅ Coordinates are in PRAPEC karst area!")
    print(f"Karst area: {result['karst_info']['nombre']}")

# Check cadastral number
result = check_cadastral_for_karst("227-052-007-20")
if result['in_karst']:
    print("✅ Cadastral intersects with PRAPEC karst area!")
```

### Advanced Usage

```python
from mipr.karst import PrapecKarstChecker

checker = PrapecKarstChecker()

# Check with custom buffer distance
result = checker.check_coordinates(
    longitude=-66.6, 
    latitude=18.4, 
    buffer_miles=1.0,  # 1 mile radius
    include_buffer_search=True
)

checker.print_result(result)
```

## API Reference

### Main Class

#### `PrapecKarstChecker`

The main class for checking karst areas.

**Methods:**
- `check_coordinates(longitude, latitude, buffer_miles=0.5, include_buffer_search=True)`
- `check_cadastral(cadastral_number, buffer_miles=0.5, include_buffer_search=True)`
- `check_multiple_cadastrals(cadastral_numbers, buffer_miles=0.5, include_buffer_search=True)`
- `print_result(result)` - Pretty print results

### Convenience Functions

#### `check_coordinates_for_karst(longitude, latitude, buffer_miles=0.5, include_buffer_search=True)`

Check if coordinates fall within PRAPEC karst areas.

**Parameters:**
- `longitude` (float): Longitude in WGS84 (EPSG:4326)
- `latitude` (float): Latitude in WGS84 (EPSG:4326)  
- `buffer_miles` (float): Buffer distance in miles for proximity search
- `include_buffer_search` (bool): Whether to search within buffer if not directly in karst

**Returns:** Dictionary with karst check results

#### `check_cadastral_for_karst(cadastral_number, buffer_miles=0.5, include_buffer_search=True)`

Check if a cadastral number falls within PRAPEC karst areas.

**Parameters:**
- `cadastral_number` (str): The cadastral number to check
- `buffer_miles` (float): Buffer distance in miles for proximity search
- `include_buffer_search` (bool): Whether to search within buffer if not directly in karst

**Returns:** Dictionary with karst check results

#### `check_multiple_cadastrals_for_karst(cadastral_numbers, buffer_miles=0.5, include_buffer_search=True)`

Check multiple cadastral numbers for PRAPEC karst areas.

**Parameters:**
- `cadastral_numbers` (List[str]): List of cadastral numbers to check
- `buffer_miles` (float): Buffer distance in miles for proximity search  
- `include_buffer_search` (bool): Whether to search within buffer if not directly in karst

**Returns:** Dictionary with results for all cadastrals

## Result Structure

All functions return a dictionary with the following structure:

```python
{
    'success': bool,                    # Whether the operation succeeded
    'coordinates': {                    # For coordinate checks
        'longitude': float,
        'latitude': float
    },
    'cadastral_number': str,           # For cadastral checks
    'cadastral_info': {                # Cadastral details (if applicable)
        'cadastral_number': str,
        'municipality': str,
        'classification': str,
        'area_m2': float
    },
    'in_karst': bool,                  # True if directly in karst area
    'karst_proximity': str,            # 'direct', 'nearby', 'none', or 'error'
    'distance_miles': str/float,       # Distance to karst (0 if direct)
    'karst_info': {                    # Karst area details (if found)
        'nombre': str,                 # Official name
        'regla': int,                  # Regulation number (259)
        'area_sq_meters': float,       # Total karst area in sq meters
        'area_hectares': float,        # Total karst area in hectares
        'perimeter_meters': float,     # Perimeter length
        'description': str             # Full description
    },
    'buffer_miles': float,             # Buffer distance used
    'message': str,                    # Human-readable result message
    'error': str                       # Error message (if success=False)
}
```

## Examples

### Example 1: Check Coordinates in Karst Area

```python
from mipr.karst import check_coordinates_for_karst

# Coordinates in Arecibo area (known karst region)
result = check_coordinates_for_karst(-66.7, 18.4)

if result['success']:
    if result['in_karst']:
        print("✅ DIRECTLY in PRAPEC karst area!")
        print(f"Area: {result['karst_info']['area_hectares']:,.0f} hectares")
        print(f"Regulation: {result['karst_info']['regla']}")
    elif result['karst_proximity'] == 'nearby':
        print(f"🔍 Karst found within {result['distance_miles']} miles")
    else:
        print("❌ No karst found")
```

### Example 2: Check Multiple Cadastrals

```python
from mipr.karst import check_multiple_cadastrals_for_karst

cadastrals = [
    "227-062-084-05",
    "227-052-007-20", 
    "227-062-084-04"
]

result = check_multiple_cadastrals_for_karst(cadastrals, buffer_miles=1.0)

print(f"Checked {result['total_cadastrals']} cadastrals:")
print(f"✅ In karst: {result['summary']['in_karst']}")
print(f"🔍 Nearby karst: {result['summary']['nearby_karst']}")
print(f"❌ No karst: {result['summary']['no_karst']}")
```

### Example 3: Using the Class for Advanced Control

```python
from mipr.karst import PrapecKarstChecker

checker = PrapecKarstChecker()

# Check without buffer search (exact intersection only)
result = checker.check_coordinates(
    longitude=-66.5, 
    latitude=18.3,
    buffer_miles=0,
    include_buffer_search=False
)

# Pretty print the results
checker.print_result(result)
```

## Files in this Module

- **`prapec_karst_checker.py`** - Main karst checking functionality
- **`karst_tools.py`** - LangGraph tools for agent integration
- **`example_karst_usage.py`** - Usage examples and demonstrations
- **`example_karst_tools.py`** - LangGraph tools usage examples
- **`test_karst_points.py`** - Test script with multiple coordinate points
- **`explore_reglamentario.py`** - MapServer exploration utility
- **`test_prapec_query.py`** - Basic PRAPEC layer testing

## Data Source

This module queries the **MIPR Reglamentario_va2 MapServer** service:
- **Service URL**: `https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer`
- **Layer ID**: 15 (PRAPEC Carso layer)
- **Coordinate System**: Web Mercator (EPSG:3857) for queries, WGS84 (EPSG:4326) for input

## Important Notes

- **Coordinates**: Must be provided in WGS84 format (longitude, latitude)
- **Buffer Distance**: Default is 0.5 miles, can be customized
- **Karst Area**: There is only 1 PRAPEC feature covering the entire karst region
- **Regulation**: The karst area is governed by Regulation 259
- **Area Coverage**: Approximately 87,375 hectares (873,746,596 square meters)

## Usage Tips

1. **Use appropriate buffer distances**: 0.5 miles is good for most cases, but you can increase for broader searches
2. **Disable buffer search** if you only want exact intersections: `include_buffer_search=False`
3. **Batch processing** is more efficient for multiple cadastrals than individual checks
4. **Error handling**: Always check the `success` field in results before using data
5. **Coordinate format**: Ensure coordinates are in WGS84 (longitude, latitude) format

## Running Examples

```bash
# Run the main examples
python mipr/karst/prapec_karst_checker.py

# Run usage examples  
python mipr/karst/example_karst_usage.py

# Test multiple points
python mipr/karst/test_karst_points.py
```

## LangGraph Tools

This module also provides specialized LangGraph tools for agent integration:

### Karst Tools for Agents

#### `check_cadastral_karst(cadastral_number, buffer_miles=0.5, include_buffer_search=True)`

LangGraph tool to check if a single cadastral falls within PRAPEC karst areas.

**Features:**
- Comprehensive regulatory analysis
- Environmental impact assessment
- Development implications
- Detailed property information

**Example:**
```python
from mipr.karst import KARST_TOOLS

# Use in LangGraph agent
result = check_cadastral_karst.invoke({
    "cadastral_number": "227-052-007-20",
    "buffer_miles": 1.0
})
```

#### `check_multiple_cadastrals_karst(cadastral_numbers, buffer_miles=0.5, include_buffer_search=True)`

LangGraph tool for batch checking multiple cadastrals with comprehensive analysis.

**Features:**
- Batch processing efficiency
- Summary statistics
- Risk categorization
- Development recommendations

#### `find_nearest_karst(cadastral_number, max_search_miles=5.0)`

LangGraph tool to find the nearest PRAPEC karst area to a cadastral.

**Features:**
- Progressive distance search
- Proximity risk assessment
- Regulatory impact analysis
- Development planning guidance

#### `analyze_cadastral_karst_proximity(cadastral_numbers, analysis_radius_miles=2.0)`

LangGraph tool for comprehensive karst proximity analysis.

**Features:**
- Spatial clustering analysis
- Risk assessment matrix
- Development planning recommendations
- Mitigation strategies
- Regulatory framework guidance

### Tool Integration

```python
from mipr.karst import KARST_TOOLS
from langgraph.prebuilt import ToolNode

# Add to your LangGraph agent
tool_node = ToolNode(KARST_TOOLS)

# Or use individual tools
from mipr.karst import (
    check_cadastral_karst,
    check_multiple_cadastrals_karst,
    find_nearest_karst,
    analyze_cadastral_karst_proximity
)
``` 