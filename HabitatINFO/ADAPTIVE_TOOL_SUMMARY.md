# Adaptive Critical Habitat Map Tool

## Overview

The new `generate_adaptive_critical_habitat_map` tool provides intelligent, location-aware critical habitat mapping with comprehensive analysis capabilities. This tool automatically determines the optimal map buffer based on habitat proximity and provides detailed regulatory analysis.

## Key Features

### 🎯 Adaptive Buffer Sizing
- **Within Habitat**: Uses 0.5-mile buffer for detailed view
- **Near Habitat**: Uses distance to nearest habitat + 1 mile buffer
- **No Nearby Habitat**: Uses 2-mile regional overview buffer

### 🔍 Comprehensive Analysis
- Point-in-polygon habitat detection
- Distance calculation to nearest critical habitat
- Detailed species identification and analysis
- Regulatory implications assessment
- Professional recommendations

### 📊 Detailed Output
- High-quality PDF maps with appropriate scale
- Complete habitat analysis results
- Species-specific information
- Regulatory compliance guidance
- Next steps recommendations

## Tool Functionality

### Input Parameters
```python
@tool
def generate_adaptive_critical_habitat_map(
    longitude: float,           # Longitude coordinate (decimal degrees)
    latitude: float,            # Latitude coordinate (decimal degrees)
    location_name: Optional[str] = None,        # Optional location name
    base_map: str = "World_Imagery",            # Base map style
    include_proposed: bool = True,              # Include proposed habitat
    include_legend: bool = True,                # Include legend
    habitat_transparency: float = 0.8           # Habitat layer transparency
) -> str:
```

### Analysis Process

1. **Habitat Detection**
   - Performs point-in-polygon analysis using CriticalHabitatClient
   - Queries both final and proposed habitat layers
   - Identifies all species with habitat at the location

2. **Distance Calculation** (if not within habitat)
   - Searches within 50-mile radius for nearest habitat
   - Calculates precise distance to habitat boundary
   - Identifies nearest habitat species and details

3. **Buffer Determination**
   - Within habitat: 0.5 miles (detailed view)
   - Near habitat: distance + 1 mile (ensures habitat visibility)
   - No nearby habitat: 2 miles (regional context)

4. **Map Generation**
   - Uses optimized print service configuration
   - Applies calculated buffer for appropriate scale
   - Includes professional legend and attribution

5. **Comprehensive Analysis**
   - Species identification and grouping
   - Final vs proposed designation analysis
   - Regulatory implications assessment
   - Tailored recommendations

### Output Structure

```json
{
  "status": "success",
  "message": "Adaptive critical habitat map generated successfully",
  "pdf_path": "output/critical_habitat_map_20250127_143022.pdf",
  "location": {
    "longitude": -96.7970,
    "latitude": 28.1595,
    "location_name": "Texas_Coast_Test"
  },
  "habitat_analysis": {
    "habitat_status": "within_critical_habitat",
    "distance_to_nearest_habitat_miles": 0.0,
    "adaptive_buffer_miles": 0.5,
    "has_critical_habitat": true,
    "habitat_count": 3,
    "analysis_timestamp": "2025-01-27T14:30:22",
    "query_success": true,
    "affected_species": [
      {
        "common_name": "Whooping crane",
        "scientific_name": "Grus americana",
        "habitat_units": ["TX-8", "TX-9"],
        "designation_types": ["Final"],
        "geometry_types": ["Polygon"],
        "unit_count": 2
      }
    ],
    "regulatory_implications": {
      "esa_consultation_required": true,
      "final_designations": 3,
      "proposed_designations": 0,
      "total_species_affected": 1
    }
  },
  "map_details": {
    "base_map": "World_Imagery",
    "include_proposed": true,
    "include_legend": true,
    "habitat_transparency": 0.8
  },
  "recommendations": [
    "⚠️  Location is within designated critical habitat",
    "📋 ESA Section 7 consultation required for federal actions",
    "🔍 Review map for specific habitat boundaries and species",
    "📞 Contact USFWS for detailed project consultation",
    "🦎 Critical habitat for Whooping crane identified at this location",
    "✅ Habitat analysis completed successfully"
  ]
}
```

## Use Cases

### 1. Project Planning
- Automatically determines if ESA consultation is required
- Provides species-specific information for impact assessment
- Generates appropriate maps for regulatory submissions

### 2. Environmental Compliance
- Documents habitat presence/absence with precise analysis
- Provides regulatory guidance and next steps
- Creates professional maps for compliance documentation

### 3. Site Assessment
- Intelligent buffer sizing ensures relevant habitat is visible
- Comprehensive species analysis for impact evaluation
- Distance calculations for alternative site consideration

### 4. Regulatory Consultation
- Detailed species and unit information for USFWS coordination
- Professional maps suitable for consultation packages
- Clear regulatory implications and requirements

## Technical Implementation

### Integration with Existing Tools
- Uses proven `CriticalHabitatMapGenerator` for map creation
- Leverages `CriticalHabitatClient` for detailed analysis
- Applies successful wetlands implementation patterns

### Distance Calculation Algorithm
- Haversine formula for accurate distance measurement
- Polygon boundary analysis for precise habitat edges
- 50-mile search radius with expandable capability

### Error Handling
- Graceful degradation if analysis services fail
- Comprehensive error reporting and logging
- Fallback buffer strategies for service issues

## Testing

Run the test script to validate functionality:

```bash
python HabitatINFO/test_adaptive_tool.py
```

Test scenarios include:
- Locations within critical habitat
- Locations near but outside habitat
- Locations with no nearby habitat
- Multiple species scenarios

## Benefits

1. **Intelligent Automation**: Eliminates guesswork in buffer sizing
2. **Comprehensive Analysis**: Combines mapping with detailed habitat analysis
3. **Regulatory Compliance**: Provides all information needed for ESA compliance
4. **Professional Output**: High-quality maps suitable for official use
5. **Efficient Workflow**: Single tool provides mapping and analysis

## Future Enhancements

- Integration with additional species databases
- Automated report generation
- Batch processing capabilities
- Enhanced distance calculation algorithms
- Integration with project management systems 