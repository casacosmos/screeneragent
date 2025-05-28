# Comprehensive Wetland Analysis Tool

A single, comprehensive tool that combines wetland data querying and adaptive map generation for coordinate-based wetland analysis.

## Overview

The `wetland_analysis_tool.py` module provides a unified tool that performs complete wetland assessment in a single function call. This tool is designed to answer the key question: **"Is this coordinate point in a wetland, and if not, what wetlands are within 0.5 miles?"**

## Features

### 🔍 **Comprehensive Analysis**
- **Point Analysis**: Determines if coordinate is within a wetland
- **Radius Search**: Identifies wetlands within 0.5-mile radius
- **Detailed Information**: NWI codes, classifications, areas, distances
- **Regulatory Assessment**: Environmental and permit implications

### 🗺️ **Adaptive Map Generation**
- **Intelligent Buffer Sizing**: Automatically determines optimal map extent
- **Smart Base Map Selection**: Chooses appropriate imagery/topographic base
- **Optimal Transparency**: Adjusts wetland layer visibility
- **Professional Output**: High-resolution PDF with legend and scale

### ⚖️ **Regulatory Intelligence**
- **Risk Assessment**: Evaluates immediate impact potential
- **Permit Requirements**: Identifies likely regulatory needs
- **Buffer Considerations**: Analyzes proximity implications
- **Actionable Recommendations**: Provides next steps

## Tool Function

### `analyze_wetland_location_with_map`

**Single comprehensive function that combines all wetland analysis capabilities.**

```python
from wetland_analysis_tool import analyze_wetland_location_with_map

result = analyze_wetland_location_with_map(
    longitude=-66.199399,
    latitude=18.408303,
    location_name="Puerto Rico Test Site"
)
```

#### Parameters
- `longitude` (float): Longitude coordinate (negative for western hemisphere)
- `latitude` (float): Latitude coordinate (positive for northern hemisphere)  
- `location_name` (str, optional): Descriptive name for the location

#### Returns
Comprehensive dictionary containing:

```python
{
    "location_analysis": {
        "location": "Site name",
        "coordinates": (longitude, latitude),
        "is_in_wetland": bool,
        "total_wetlands_found": int,
        "search_radius_used": float,
        "data_sources": [list of data sources]
    },
    "wetlands_in_radius": {
        "radius_miles": 0.5,
        "radius_area_sq_miles": 0.79,
        "wetlands_count": int,
        "wetlands": [
            {
                "wetland_type": "Emergent Wetland",
                "nwi_code": "PEM1A",
                "area_acres": 2.5,
                "distance_miles": 0.2,
                "bearing": "Northeast",
                "regulatory_significance": "High - Emergent wetland, typically jurisdictional"
            }
        ]
    },
    "map_generation": {
        "success": bool,
        "filename": "path/to/generated/map.pdf",
        "adaptive_settings": {
            "buffer_miles": float,
            "base_map": "World_Imagery",
            "reasoning": "Explanation of settings chosen"
        }
    },
    "regulatory_assessment": {
        "immediate_impact_risk": "Low/Medium/High",
        "permit_requirements": [list],
        "regulatory_agencies": [list],
        "buffer_considerations": [list]
    },
    "recommendations": [
        "🚨 IMMEDIATE ACTION: ...",
        "📋 Conduct professional wetland delineation...",
        "⚖️ Consult with environmental attorney..."
    ],
    "analysis_summary": {
        "environmental_significance": "Description",
        "key_wetland_types": [list],
        "regulatory_complexity": "Low/Medium/High"
    }
}
```

## Data Sources

The tool queries multiple authoritative wetland databases:

- **USFWS National Wetlands Inventory (NWI)**: Primary wetland mapping
- **EPA RIBITS**: Regulatory tracking system
- **EPA National Hydrography Dataset (NHD)**: Water features
- **USFWS Riparian Mapping**: Riparian corridors

## Adaptive Map Logic

The tool intelligently determines map settings based on analysis results:

### Buffer Sizing
- **Wetlands at location**: 0.5-mile buffer for detailed view
- **Wetlands within 0.5 miles**: 1.0-mile buffer for context
- **Wetlands beyond 0.5 miles**: Distance + 1.0 mile buffer
- **No wetlands found**: 2.0-mile regional view

### Base Map Selection
- **World_Imagery**: High-resolution satellite (default for wetland areas)
- **World_Topo_Map**: Topographic (used when no wetlands found)
- **World_Street_Map**: Street view (alternative option)

### Transparency Optimization
- **0.75**: Detailed view when wetlands at location
- **0.8**: Standard view for nearby wetlands

## Usage Examples

### Basic Usage
```python
from wetland_analysis_tool import analyze_wetland_location_with_map

# Analyze a coastal location
result = analyze_wetland_location_with_map(-66.199399, 18.408303, "Puerto Rico Coast")

# Check if in wetland
if result['location_analysis']['is_in_wetland']:
    print("⚠️ Location is within a wetland!")
else:
    wetland_count = result['wetlands_in_radius']['wetlands_count']
    print(f"Found {wetland_count} wetlands within 0.5 miles")

# Access map file
if result['map_generation']['success']:
    map_file = result['map_generation']['filename']
    print(f"Map saved to: {map_file}")
```

### LangGraph Integration
```python
from langchain_core.tools import ToolNode
from wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL

# Create tool node
tool_node = ToolNode(COMPREHENSIVE_WETLAND_TOOL)

# Use in LangGraph workflow
# The tool will be available as "analyze_wetland_location_with_map"
```

### Regulatory Assessment
```python
result = analyze_wetland_location_with_map(-80.8, 25.5, "Everglades Area")

# Check regulatory risk
risk = result['regulatory_assessment']['immediate_impact_risk']
print(f"Impact Risk: {risk}")

# Get recommendations
for rec in result['recommendations']:
    print(f"• {rec}")

# Check permit requirements
permits = result['regulatory_assessment']['permit_requirements']
if permits:
    print("Permits likely required:")
    for permit in permits:
        print(f"  - {permit}")
```

## Output Files

### Automatic File Generation
- **Detailed JSON Results**: Saved to `logs/` directory with timestamp
- **High-Resolution Map**: Saved to `output/` directory as PDF
- **Analysis Metadata**: Included in return dictionary

### File Naming Convention
- **Data**: `wetland_analysis_YYYYMMDD_HHMMSS.json`
- **Maps**: `wetland_map_adaptive_YYYYMMDD_HHMMSS.pdf`

## Error Handling

The tool includes comprehensive error handling:

```python
result = analyze_wetland_location_with_map(invalid_coords...)

if 'error' in result['location_analysis']:
    print(f"Analysis failed: {result['location_analysis']['error']}")
    # Tool still returns structured error information
```

## Performance Considerations

- **Data Query**: 5-15 seconds depending on wetland density
- **Map Generation**: 10-30 seconds depending on complexity
- **Total Runtime**: Typically 15-45 seconds for complete analysis
- **File Sizes**: Maps typically 2-8 MB, JSON data < 1 MB

## Dependencies

Required modules (already included in existing project):
- `query_wetland_location.py`: Core wetland data analysis
- `generate_wetland_map_pdf_v3.py`: Map generation capabilities
- `langchain_core.tools`: LangGraph tool integration
- `pydantic`: Input validation

## Example Script

Run the included example to see the tool in action:

```bash
cd WetlandsINFO
python example_comprehensive_analysis.py
```

This will demonstrate the tool with multiple test locations and show the complete output structure.

## Integration Notes

### With Existing Tools
This comprehensive tool **complements** the existing individual tools in `tools.py`:
- Use this tool for **complete analysis** when you need both data and maps
- Use individual tools when you need **specific functionality** only

### With LangGraph Agents
The tool is designed for LangGraph integration:
- Single tool call provides complete wetland assessment
- Structured output enables agent decision-making
- Automatic file generation supports documentation needs

## Best Practices

1. **Always provide location_name** for better documentation
2. **Check map_generation.success** before using map files
3. **Review recommendations** for next steps
4. **Save result dictionary** for later reference
5. **Consider regulatory_assessment** for compliance planning

---

*This tool provides a complete wetland analysis solution in a single function call, combining the power of multiple data sources with intelligent map generation and regulatory assessment.* 