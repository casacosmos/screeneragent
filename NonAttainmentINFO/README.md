# NonAttainmentINFO Module

## Overview

The NonAttainmentINFO module provides comprehensive access to EPA nonattainment areas data and generates professional PDF maps showing air quality violations. It uses the EPA Office of Air and Radiation (OAR) Office of Air Quality Planning and Standards (OAQPS) services to determine if a location intersects with nonattainment areas and provides detailed information about air quality standards violations.

## Features

- 🔍 **Location Analysis**: Check if any location is within EPA-designated nonattainment areas
- 📊 **Comprehensive Data**: Access all 12 EPA pollutant layers including active and revoked standards
- 🗺️ **Professional Maps**: Generate high-quality PDF maps showing nonattainment areas
- 🌫️ **Multi-Pollutant Support**: Analyze areas for Ozone, PM2.5, PM10, Lead, SO2, CO, and NO2
- 📈 **Status Classification**: Identify areas as Nonattainment, Maintenance, or meeting standards
- 🎯 **Adaptive Mapping**: Automatically adjust map settings based on analysis results
- 📋 **Smart Recommendations**: Get actionable guidance for development and compliance

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd NonAttainmentINFO

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- requests
- python >= 3.7
- Standard library modules: json, logging, datetime, math, os

## Quick Start

### Basic Usage

```python
from nonattainment_client import NonAttainmentAreasClient
from generate_nonattainment_map_pdf import NonAttainmentMapGenerator

# Initialize client and map generator
client = NonAttainmentAreasClient()
map_generator = NonAttainmentMapGenerator()

# Check a location
longitude = -118.2437  # Los Angeles
latitude = 34.0522
result = client.analyze_location(longitude, latitude)

# Display results
if result.has_nonattainment_areas:
    print(f"Found {result.area_count} nonattainment areas")
    for area in result.nonattainment_areas:
        print(f"- {area.pollutant_name}: {area.current_status}")

# Generate a map
pdf_path = map_generator.generate_nonattainment_map_pdf(
    longitude=longitude,
    latitude=latitude,
    location_name="Los Angeles, CA",
    buffer_miles=25.0
)
```

### Run Example Script

```bash
python example_usage.py
```

## API Reference

### NonAttainmentAreasClient

Main client for accessing EPA nonattainment data.

#### Methods

##### `analyze_location(longitude, latitude, include_revoked=False, buffer_meters=0, pollutants=None)`

Analyze a location for nonattainment area intersections.

**Parameters:**
- `longitude` (float): Longitude coordinate
- `latitude` (float): Latitude coordinate
- `include_revoked` (bool): Whether to include revoked standards (default: False)
- `buffer_meters` (float): Buffer distance around point in meters (default: 0)
- `pollutants` (List[str]): List of specific pollutants to check (default: None for all)

**Returns:** `NonAttainmentAnalysisResult` object

##### `get_pollutant_areas(pollutant, include_revoked=False)`

Get all nonattainment areas for a specific pollutant.

**Parameters:**
- `pollutant` (str): Name of the pollutant (e.g., "Ozone", "PM2.5", "Lead")
- `include_revoked` (bool): Whether to include revoked standards

**Returns:** List of `NonAttainmentAreaInfo` objects

##### `get_area_summary(result)`

Generate a summary of nonattainment analysis results with recommendations.

**Parameters:**
- `result` (NonAttainmentAnalysisResult): Analysis result to summarize

**Returns:** Dictionary with status, summary statistics, and recommendations

### NonAttainmentMapGenerator

Generate professional PDF maps of nonattainment areas.

#### Methods

##### `generate_nonattainment_map_pdf(...)`

Generate a customizable nonattainment areas map PDF.

**Key Parameters:**
- `longitude`, `latitude`: Location coordinates
- `location_name`: Name for the map title
- `buffer_miles`: Radius to show (default: 25.0)
- `base_map`: Base map style ("World_Topo_Map", "World_Street_Map", etc.)
- `dpi`: Resolution (96, 150, 300)
- `include_legend`: Whether to include legend
- `pollutants`: List of specific pollutants to show
- `include_revoked`: Whether to show revoked standards
- `nonattainment_transparency`: Layer transparency (0.0-1.0)

**Returns:** Path to generated PDF file

##### Specialized Map Methods

- `generate_adaptive_nonattainment_map()`: Automatically adjusts settings based on analysis
- `generate_detailed_nonattainment_map()`: 10-mile detailed view
- `generate_overview_nonattainment_map()`: 50-mile regional view
- `generate_pollutant_specific_map()`: Focus on single pollutant

## Data Structure

### NonAttainmentAreaInfo

Information about a specific nonattainment area:

```python
@dataclass
class NonAttainmentAreaInfo:
    pollutant_name: str          # e.g., "8-Hour Ozone (2015 Standard)"
    area_name: str               # e.g., "Los Angeles-South Coast Air Basin"
    state_name: str              # e.g., "California"
    state_abbreviation: str      # e.g., "CA"
    epa_region: int              # EPA region number (1-10)
    current_status: str          # "Nonattainment" or "Maintenance"
    classification: str          # e.g., "Extreme", "Serious", "Moderate"
    design_value: float          # Air quality measurement
    design_value_units: str      # e.g., "ppm", "µg/m³"
    meets_naaqs: str            # "Yes", "No", or "Incomplete"
    population_2020: float       # 2020 population in area
```

### EPA Pollutant Layers

The module accesses 12 EPA layers covering all criteria pollutants:

| Layer | Pollutant | Standard | Status |
|-------|-----------|----------|---------|
| 0 | Ozone 8-hr | 1997 standard | Revoked |
| 1 | Ozone 8-hr | 2008 standard | Active |
| 2 | Ozone 8-hr | 2015 standard | Active |
| 3 | Lead | 2008 standard | Active |
| 4 | SO2 1-hr | 2010 standard | Active |
| 5 | PM2.5 24hr | 2006 standard | Active |
| 6 | PM2.5 Annual | 1997 standard | Active |
| 7 | PM2.5 Annual | 2012 standard | Active |
| 8 | PM10 | 1987 standard | Active |
| 9 | CO | 1971 standard | Active |
| 10 | Ozone 1-hr | 1979 standard | Revoked |
| 11 | NO2 | 1971 standard | Active |

## Advanced Usage

### Buffer Analysis

Check nonattainment areas within a buffer distance:

```python
# Check within 5km radius
result = client.analyze_location(
    longitude, latitude,
    buffer_meters=5000
)
```

### Pollutant-Specific Analysis

Focus on specific pollutants:

```python
# Check only for Ozone and PM2.5
result = client.analyze_location(
    longitude, latitude,
    pollutants=["Ozone", "PM2.5"]
)
```

### Historical Analysis

Include revoked standards for historical perspective:

```python
result = client.analyze_location(
    longitude, latitude,
    include_revoked=True
)
```

### Custom Map Generation

Create highly customized maps:

```python
pdf_path = map_generator.generate_nonattainment_map_pdf(
    longitude=longitude,
    latitude=latitude,
    location_name="Custom Analysis",
    buffer_miles=30.0,
    base_map="World_Imagery",
    dpi=300,
    output_size=(1500, 1000),
    include_legend=True,
    pollutants=["Ozone", "PM2.5"],
    include_revoked=False,
    nonattainment_transparency=0.6,
    output_filename="custom_nonattainment_map.pdf"
)
```

## Testing

Run the comprehensive test suite:

```bash
python test_nonattainment_complete.py
```

This will test:
- Multiple locations (urban, industrial, remote)
- All map generation options
- Buffer analysis
- Pollutant-specific queries
- Error handling

## Troubleshooting

### Common Issues

1. **Map Generation Fails**
   - The module will automatically fall back to HTML map generation if PDF services are unavailable
   - Check internet connectivity
   - Verify EPA services are accessible

2. **No Data Returned**
   - Verify coordinates are in decimal degrees
   - Check if location is within the United States
   - Some layers may have intermittent service issues

3. **Timeout Errors**
   - The module includes retry logic for timeouts
   - Increase timeout values if needed
   - Check network connectivity

### Debug Information

- Web Map JSON specifications are saved as `debug_nonattainment_webmap_*.json`
- Enable logging for detailed debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Data Sources

- **Primary Service**: EPA OAR_OAQPS NonattainmentAreas MapServer
- **URL**: https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer
- **Authority**: U.S. Environmental Protection Agency
- **Update Frequency**: Regular updates as designations change

## License

This module is provided as-is for environmental analysis purposes. Always verify results with official EPA sources for regulatory compliance.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test examples
3. Consult EPA's official documentation
4. Submit an issue on the repository

---

**Note**: This module is for informational purposes. For official regulatory determinations, always consult directly with EPA and relevant state agencies.