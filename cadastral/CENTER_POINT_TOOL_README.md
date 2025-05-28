# Cadastral Center Point Calculator Tool

A specialized tool for calculating accurate center point coordinates from cadastral polygon geometry data in Puerto Rico.

## Overview

The `calculate_cadastral_center_point` tool retrieves polygon geometry for a specified cadastral number and calculates the geometric centroid (center point) using advanced mathematical methods. It supports multiple calculation approaches and coordinate systems for maximum accuracy.

## Features

### 🎯 **Multiple Calculation Methods**
- **Geographic**: Standard centroid calculation using geographic coordinates (WGS84)
- **Projected**: High-accuracy calculation using projected coordinates (NAD83 Puerto Rico)
- **Both**: Performs both calculations and compares results for validation

### 🗺️ **Coordinate System Support**
- **WGS84**: World Geodetic System 1984 (EPSG:4326) - Global standard
- **NAD83**: North American Datum 1983 (EPSG:4152) - Local Puerto Rico datum

### 📊 **Advanced Features**
- Geometric centroid calculation using the shoelace formula
- Projected coordinate transformation for higher accuracy
- Method comparison and validation
- Polygon metadata and statistics
- Optional polygon coordinate export
- Project directory organization
- Comprehensive error handling

## Installation

The tool is part of the `cadastral` package and requires the following dependencies:

```python
# Required
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Optional (for high-accuracy calculations)
from pyproj import Transformer, CRS
```

## Usage

### Basic Usage

```python
from cadastral.cadastral_center_point_tool import calculate_cadastral_center_point

# Calculate center point for a cadastral number
result = calculate_cadastral_center_point(
    cadastral_number="227-052-007-20"
)

if result['success']:
    center = result['center_point']
    print(f"Center: ({center['longitude']:.6f}, {center['latitude']:.6f})")
    print(f"Coordinate System: {center['coordinate_system']}")
```

### Advanced Usage

```python
# High-accuracy calculation with both methods
result = calculate_cadastral_center_point(
    cadastral_number="227-052-007-20",
    output_coordinate_system="NAD83",
    calculation_method="both",
    include_polygon_data=True,
    save_to_file=True
)

if result['success']:
    # Primary center point
    center = result['center_point']
    print(f"Primary Center: ({center['longitude']:.8f}, {center['latitude']:.8f})")
    
    # Method comparison
    if 'comparison' in result['calculation_details']:
        comparison = result['calculation_details']['comparison']
        print(f"Method Difference: {comparison['difference_meters']:.2f} meters")
        print(f"Assessment: {comparison['difference_assessment']}")
    
    # Polygon metadata
    metadata = result['polygon_metadata']
    print(f"Polygon Points: {metadata['coordinate_count']}")
    print(f"Area: {metadata['area_hectares']:.4f} hectares")
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cadastral_number` | str | Required | Cadastral number to analyze (e.g., '227-052-007-20') |
| `output_coordinate_system` | str | "WGS84" | Output coordinate system: 'WGS84' or 'NAD83' |
| `calculation_method` | str | "projected" | Calculation method: 'geographic', 'projected', or 'both' |
| `include_polygon_data` | bool | False | Whether to include full polygon coordinates |
| `save_to_file` | bool | True | Whether to save results to project data directory |

## Response Format

```python
{
    "success": True,
    "cadastral_number": "227-052-007-20",
    "query_time": "2024-01-15T10:30:00",
    
    "center_point": {
        "longitude": -65.92583397,
        "latitude": 18.22780444,
        "coordinate_system": "WGS84 (EPSG:4326)",
        "precision": "8 decimal places",
        "calculation_method": "projected"
    },
    
    "calculation_details": {
        "projected": {
            "method": "Projected Centroid (NAD83 Puerto Rico)",
            "center_point_wgs84": [-65.92583397, 18.22780444],
            "description": "High-accuracy centroid calculated using projected coordinates",
            "accuracy": "High accuracy using local projected coordinate system"
        }
    },
    
    "polygon_metadata": {
        "coordinate_count": 156,
        "geometry_type": "Polygon",
        "rings_count": 1,
        "has_holes": False,
        "area_m2": 12450.5,
        "area_hectares": 1.2451
    },
    
    "coordinate_system_info": {
        "input_system": "WGS84 (from MIPR service)",
        "output_system": "WGS84 (EPSG:4326)",
        "conversion_applied": False,
        "pyproj_available": True
    },
    
    "accuracy_assessment": {
        "method_used": "projected",
        "accuracy_level": "High",
        "notes": [
            "High-accuracy calculation using projected coordinates",
            "Optimal for surveying and engineering applications",
            "Accounts for local coordinate system distortions",
            "Coordinates calculated to 8 decimal places precision"
        ]
    },
    
    "cadastral_info": {
        "municipality": "Juncos",
        "neighborhood": "Pueblo",
        "region": "Este",
        "classification": "Terrenos Públicos",
        "area_m2": 12450.5,
        "area_hectares": 1.2451
    }
}
```

## Calculation Methods

### Geographic Centroid
- Uses the shoelace formula for polygon centroid calculation
- Calculated directly in WGS84 geographic coordinates
- Standard accuracy suitable for most mapping applications
- Fast calculation with minimal dependencies

### Projected Centroid
- Projects polygon to NAD83 Puerto Rico coordinate system (EPSG:2866)
- Calculates centroid in projected coordinates for higher accuracy
- Transforms result back to geographic coordinates
- Optimal for surveying and engineering applications
- Requires `pyproj` library for coordinate transformations

### Both Methods
- Performs both geographic and projected calculations
- Compares results and provides difference assessment
- Uses projected result as primary if available
- Provides validation and accuracy assessment

## Accuracy Assessment

The tool provides automatic accuracy assessment based on:

- **Calculation method used**
- **Availability of pyproj library**
- **Polygon complexity and size**
- **Coordinate system conversions**

### Difference Assessment (Both Methods)
- **< 1 meter**: Excellent agreement
- **< 5 meters**: Good agreement  
- **< 10 meters**: Acceptable agreement
- **< 50 meters**: Moderate difference
- **≥ 50 meters**: Significant difference - recommend projected method

## Applications

### 🏗️ **Property Development**
- Site planning and design
- Building placement optimization
- Infrastructure planning
- Zoning compliance verification

### 📊 **Geographic Analysis**
- Spatial analysis and modeling
- Distance calculations
- Buffer zone analysis
- Geographic information systems (GIS)

### 📋 **Legal Documentation**
- Property surveys
- Legal descriptions
- Boundary documentation
- Official records

### 🗺️ **Mapping and Navigation**
- Map annotation
- GPS waypoint creation
- Navigation reference points
- Cartographic applications

## Error Handling

The tool provides comprehensive error handling for:

- **Invalid cadastral numbers**: Clear error messages with suggestions
- **Missing geometry data**: Detailed error information
- **Invalid parameters**: Parameter validation with helpful messages
- **Network issues**: Timeout and connection error handling
- **Coordinate transformation errors**: Fallback methods

## File Output

When `save_to_file=True`, the tool creates:

### Center Point Results File
```
data/center_point_{cadastral_number}_{timestamp}.json
```
Contains complete calculation results and metadata.

### Polygon Coordinates File (if requested)
```
data/polygon_coords_{cadastral_number}_{timestamp}.json
```
Contains full polygon coordinate array.

## Dependencies

### Required
- `langchain_core.tools`
- `pydantic`
- `requests`
- Standard Python libraries (math, datetime, typing)

### Optional
- `pyproj`: For high-accuracy projected coordinate calculations
- Without pyproj: Falls back to geographic calculations with warning

## Testing

Run the test suite to verify functionality:

```bash
python test_center_point_tool.py
```

The test suite includes:
- Basic functionality tests
- Multiple calculation methods
- Coordinate system conversions
- Error handling validation
- Performance verification

## Integration with LangGraph

The tool is designed for use with LangGraph agents:

```python
from cadastral.cadastral_center_point_tool import CADASTRAL_CENTER_POINT_TOOL

# Add to LangGraph ToolNode
tools = CADASTRAL_CENTER_POINT_TOOL

# Use in agent workflow
result = agent.invoke({
    "messages": [
        ("user", "Calculate the center point for cadastral 227-052-007-20")
    ]
})
```

## Performance

- **Typical response time**: 2-5 seconds
- **Geometry processing**: Handles polygons with 100-1000+ vertices
- **Memory usage**: Minimal (< 10MB for typical cadastrals)
- **Accuracy**: 8 decimal places (sub-meter precision)

## Limitations

- **Geographic scope**: Puerto Rico only (MIPR database)
- **Coordinate systems**: WGS84 and NAD83 only
- **Polygon types**: Simple polygons (holes supported but not optimized)
- **Network dependency**: Requires internet connection for MIPR service

## Support

For issues or questions:
1. Check error messages for specific guidance
2. Verify cadastral number format (XXX-XXX-XXX-XX)
3. Ensure network connectivity to MIPR services
4. Review coordinate system requirements

## Version History

- **v1.0.0**: Initial release with geographic and projected calculations
- Support for WGS84 and NAD83 coordinate systems
- Comprehensive accuracy assessment and validation
- Integration with project directory management 