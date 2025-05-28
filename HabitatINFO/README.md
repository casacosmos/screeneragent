# HabitatINFO - Critical Habitat Analysis Module

## Overview

HabitatINFO is a comprehensive Python module for analyzing critical habitat areas designated under the U.S. Endangered Species Act (ESA). It provides tools to determine if geographic locations intersect with protected species habitats and offers detailed regulatory guidance for compliance and conservation planning.

## Features

### 🎯 Location-Based Analysis
- **Point Analysis**: Check if specific coordinates intersect with critical habitat
- **Buffer Analysis**: Analyze areas within specified distances of a location
- **Multi-Layer Queries**: Search both final and proposed habitat designations
- **Regulatory Assessment**: Provide ESA compliance guidance

### 🐾 Species-Based Search
- **Species Lookup**: Find all critical habitat areas for specific species
- **Common/Scientific Names**: Search by either common or scientific names
- **Habitat Mapping**: Identify geographic distribution of species protection
- **Conservation Status**: Assess protection levels and designation types

### 📊 Comprehensive Reporting
- **Detailed Analysis**: Species information, habitat units, and designation status
- **Regulatory Guidance**: ESA consultation requirements and recommendations
- **Summary Statistics**: Counts, areas, and protection levels
- **JSON Output**: Structured data for integration with other systems

## Installation

### Prerequisites
```bash
# Required Python packages
pip install requests langchain pydantic
```

### Setup
```bash
# Clone or copy the HabitatINFO directory to your project
# No additional installation required - uses public USFWS services
```

## Quick Start

### Basic Location Analysis
```python
from HabitatINFO.tools import analyze_critical_habitat

# Analyze a location for critical habitat
result = analyze_critical_habitat.invoke({
    "longitude": -122.4194,
    "latitude": 37.7749,
    "include_proposed": True,
    "buffer_meters": 0
})

print(result)
```

### Species Habitat Search
```python
from HabitatINFO.tools import search_species_habitat

# Search for salmon critical habitat
result = search_species_habitat.invoke({
    "species_name": "salmon",
    "search_type": "common"
})

print(result)
```

### Direct Client Usage
```python
from HabitatINFO.habitat_client import CriticalHabitatClient

client = CriticalHabitatClient()

# Analyze location
result = client.analyze_location(-80.9326, 25.4663)
summary = client.get_habitat_summary(result)

print(f"Critical habitat found: {result.has_critical_habitat}")
print(f"Species count: {len(set(h.species_common_name for h in result.critical_habitats))}")
```

## API Reference

### Tools

#### `analyze_critical_habitat`
Analyzes a geographic location for critical habitat intersections.

**Parameters:**
- `longitude` (float): Longitude coordinate in decimal degrees
- `latitude` (float): Latitude coordinate in decimal degrees  
- `include_proposed` (bool, optional): Include proposed designations (default: True)
- `buffer_meters` (float, optional): Buffer distance in meters (default: 0)

**Returns:** JSON string with analysis results

#### `search_species_habitat`
Searches for critical habitat areas by species name.

**Parameters:**
- `species_name` (str): Name of species to search for
- `search_type` (str, optional): "common" or "scientific" (default: "common")

**Returns:** JSON string with habitat locations and details

### Client Classes

#### `CriticalHabitatClient`
Main client for accessing USFWS critical habitat services.

**Key Methods:**
- `analyze_location(longitude, latitude, include_proposed, buffer_meters)`: Analyze location
- `get_species_habitats(species_name, search_type)`: Search by species
- `get_habitat_summary(result)`: Generate summary from analysis result

#### Data Classes

#### `CriticalHabitatInfo`
Information about a critical habitat area.

**Attributes:**
- `species_common_name`: Common name of the species
- `species_scientific_name`: Scientific name of the species
- `unit_name`: Name of the habitat unit
- `status`: Protection status
- `habitat_type`: "Final" or "Proposed"
- `geometry_type`: "Polygon" or "Linear"

#### `HabitatAnalysisResult`
Result of habitat analysis for a location.

**Attributes:**
- `location`: Coordinates analyzed
- `has_critical_habitat`: Boolean indicating presence
- `habitat_count`: Number of habitat areas found
- `critical_habitats`: List of CriticalHabitatInfo objects
- `query_success`: Boolean indicating successful query

## Usage Examples

### Example 1: Development Site Assessment
```python
from HabitatINFO.tools import analyze_critical_habitat
import json

# Assess a potential development site
site_coords = {"longitude": -81.3792, "latitude": 28.5383}

result = analyze_critical_habitat.invoke({
    **site_coords,
    "include_proposed": True,
    "buffer_meters": 100  # 100m buffer for safety
})

analysis = json.loads(result)
if analysis["critical_habitat_analysis"]["status"] == "critical_habitat_found":
    print("⚠️ ESA consultation required!")
    species = analysis["critical_habitat_analysis"]["affected_species"]
    print(f"Affected species: {[s['common_name'] for s in species]}")
else:
    print("✅ No critical habitat restrictions")
```

### Example 2: Species Conservation Planning
```python
from HabitatINFO.tools import search_species_habitat
import json

# Find all sea turtle critical habitat
result = search_species_habitat.invoke({
    "species_name": "sea turtle",
    "search_type": "common"
})

search_data = json.loads(result)
if search_data["species_habitat_search"]["status"] == "habitat_found":
    summary = search_data["species_habitat_search"]["summary"]
    print(f"Sea turtle habitat areas: {summary['total_habitat_areas']}")
    print(f"Habitat units: {summary['unique_habitat_units']}")
    
    # List species found
    for species in search_data["species_habitat_search"]["species_details"]:
        print(f"- {species['common_name']}: {species['unit_count']} units")
```

### Example 3: Regional Analysis
```python
from HabitatINFO.habitat_client import CriticalHabitatClient

client = CriticalHabitatClient()

# Analyze multiple points in a region
region_points = [
    (-122.4194, 37.7749),  # San Francisco
    (-122.2711, 37.8044),  # Berkeley
    (-122.0838, 37.4220),  # Palo Alto
]

regional_species = set()
for lon, lat in region_points:
    result = client.analyze_location(lon, lat)
    if result.has_critical_habitat:
        for habitat in result.critical_habitats:
            regional_species.add(habitat.species_common_name)

print(f"Regional species with critical habitat: {len(regional_species)}")
for species in sorted(regional_species):
    print(f"- {species}")
```

## Data Sources

### Primary Service
- **USFWS Critical Habitat Service**: Official U.S. Fish and Wildlife Service critical habitat data
- **URL**: `https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer`
- **Layers**:
  - Layer 0: Final Polygon Features
  - Layer 1: Final Linear Features  
  - Layer 2: Proposed Polygon Features
  - Layer 3: Proposed Linear Features

### Data Coverage
- **Geographic Scope**: United States and territories
- **Species Coverage**: All ESA-listed species with designated critical habitat
- **Update Frequency**: Updated as new designations are finalized
- **Data Quality**: Official federal regulatory data

## Regulatory Context

### Endangered Species Act (ESA)
Critical habitat designations under the ESA have significant regulatory implications:

- **Section 7 Consultation**: Federal agencies must consult with USFWS/NOAA for actions that may affect critical habitat
- **Jeopardy Analysis**: Actions cannot destroy or adversely modify critical habitat
- **Private Land Impacts**: Applies when federal permits, funding, or actions are involved
- **Planning Importance**: Early identification helps avoid conflicts and delays

### Designation Types
- **Final Critical Habitat**: Legally designated with full regulatory protection
- **Proposed Critical Habitat**: Under consideration, may become final
- **Linear Features**: Rivers, streams, migration corridors
- **Polygon Features**: Terrestrial and marine habitat areas

## Error Handling

The module includes comprehensive error handling:

```python
# Example error handling
try:
    result = analyze_critical_habitat.invoke({
        "longitude": -200,  # Invalid coordinate
        "latitude": 45
    })
    analysis = json.loads(result)
    if analysis["critical_habitat_analysis"]["status"] == "error":
        print(f"Analysis failed: {analysis['critical_habitat_analysis']['error']}")
except Exception as e:
    print(f"Tool execution failed: {e}")
```

## Performance Considerations

### Query Optimization
- **Point Queries**: Fastest for exact location analysis
- **Buffer Queries**: Slower but more comprehensive for area analysis
- **Species Searches**: May return large datasets for common species
- **Timeout Handling**: 30-second timeout for service requests

### Rate Limiting
- **Service Limits**: USFWS services have usage limits
- **Batch Processing**: Implement delays for multiple queries
- **Caching**: Consider caching results for repeated analyses

## Integration Examples

### LangChain Agent Integration
```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from HabitatINFO.tools import habitat_tools

# Create agent with habitat tools
llm = OpenAI(temperature=0)
agent = initialize_agent(
    habitat_tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Use agent for habitat analysis
response = agent.run(
    "Is there critical habitat at coordinates -122.4194, 37.7749? "
    "What species are protected there?"
)
```

### Web API Integration
```python
from flask import Flask, request, jsonify
from HabitatINFO.tools import analyze_critical_habitat

app = Flask(__name__)

@app.route('/api/habitat/analyze', methods=['POST'])
def analyze_habitat():
    data = request.json
    
    result = analyze_critical_habitat.invoke({
        "longitude": data["longitude"],
        "latitude": data["latitude"],
        "include_proposed": data.get("include_proposed", True)
    })
    
    return jsonify(json.loads(result))

if __name__ == '__main__':
    app.run(debug=True)
```

## Testing

### Run Example Script
```bash
cd HabitatINFO
python example_habitat_analysis.py
```

### Unit Testing
```python
# Basic functionality test
from HabitatINFO.habitat_client import CriticalHabitatClient

client = CriticalHabitatClient()
result = client.analyze_location(-122.4194, 37.7749)
assert isinstance(result.has_critical_habitat, bool)
assert result.query_success == True
```

## Troubleshooting

### Common Issues

#### No Results Found
- **Check Coordinates**: Ensure longitude/latitude are correct
- **Verify Coverage**: Not all areas have critical habitat
- **Try Buffer**: Use buffer_meters > 0 for nearby habitat

#### Service Timeouts
- **Network Issues**: Check internet connectivity
- **Service Availability**: USFWS services may have maintenance windows
- **Retry Logic**: Implement exponential backoff for retries

#### Import Errors
- **Path Issues**: Ensure HabitatINFO is in Python path
- **Dependencies**: Install required packages (requests, langchain, pydantic)

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging for troubleshooting
from HabitatINFO.habitat_client import CriticalHabitatClient
client = CriticalHabitatClient()
```

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Include docstrings
- Add logging for debugging

## License

This module uses public USFWS data services and is provided for educational and research purposes. Users are responsible for compliance with applicable regulations and proper attribution of data sources.

## Support

For issues and questions:
- Check the troubleshooting section
- Review example scripts
- Verify service availability
- Contact USFWS for data-specific questions

## Changelog

### Version 1.0.0
- Initial release
- USFWS Critical Habitat service integration
- Location and species analysis tools
- LangChain tool compatibility
- Comprehensive documentation and examples 