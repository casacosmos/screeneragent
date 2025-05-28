# WetlandsINFO - Wetland Location Analysis System

## Overview

WetlandsINFO provides comprehensive wetland analysis capabilities for any geographic coordinate. The system determines whether a location is within a wetland territory and, if not, identifies the nearest wetlands with distance and bearing information.

## Features

### 🌿 **Wetland Detection**
- **Point-in-Wetland Analysis**: Determines if coordinates fall within mapped wetland boundaries
- **Wetland Classification**: Provides detailed wetland types (Forested, Emergent, Scrub-Shrub, etc.)
- **Area Calculation**: Reports wetland sizes in acres
- **Multiple Data Sources**: Queries both USFWS NWI and EPA RIBITS databases

### 🔍 **Nearest Wetland Search**
- **Progressive Search**: Expands search radius from 0.1 to 5 miles
- **Distance Calculation**: Precise distance measurements using Haversine formula
- **Directional Bearing**: Compass directions (N, NE, E, SE, etc.) to nearest wetlands
- **Top 5 Results**: Returns the 5 nearest wetlands when location is not in a wetland

### 🗺️ **Professional Map Generation**
- **PDF Map Output**: High-quality wetland maps with legends and scale bars
- **Multiple Base Maps**: Satellite imagery, topographic, and street maps
- **Configurable Output**: Custom DPI, sizes, and buffer distances
- **Professional Layout**: Title, attribution, north arrow, and scale bar
- **Location Markers**: Clear indication of query coordinates

### 💧 **Additional Environmental Data**
- **Riparian Areas**: Identifies stream corridors and riparian zones
- **Watershed Information**: HUC codes and watershed boundaries (HUC8, HUC10, HUC12)
- **Environmental Significance**: Assesses ecological importance
- **Regulatory Implications**: Provides guidance on permits and regulations

## Installation

1. Ensure Python 3.7+ is installed
2. Install required dependencies:
```bash
pip install requests
```

3. The system uses the following services (no API keys required):
   - USFWS National Wetlands Inventory (NWI)
   - EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)
   - EPA National Hydrography Dataset (NHD)
   - USFWS Riparian Mapping Service

## Usage

### Command Line Interface

```bash
# Basic usage - interactive mode
python query_wetland_location.py

# With coordinates
python query_wetland_location.py -66.150906 18.434059

# With coordinates and location name
python query_wetland_location.py -66.150906 18.434059 "Cataño, Puerto Rico"

# With auto-save option
python query_wetland_location.py -66.150906 18.434059 "Cataño, Puerto Rico" save

# Generate map PDF directly
python generate_wetland_map_pdf_v3.py -66.150906 18.434059 "Cataño, Puerto Rico"
```

### Map Generation

```bash
# Test PDF generation
python test_pdf_generation.py

# Test wetland polygon display specifically
python test_wetland_display.py

# Generate different map types
python generate_wetland_map_pdf_v3.py -66.196 18.452 "Test Location" 0.5

# Interactive map generation with options
python generate_wetland_map_pdf_v3.py
```

### Example Output

#### Location Within Wetland:
```
🌿 WETLAND STATUS:
   Status: Location is within a wetland area
   Wetlands at Location: 2
   Total Wetland Area: 15.3 acres
   Environmental Significance: High - Forested wetlands provide critical habitat
   
   Wetland Types Found:
     • Palustrine Forested Wetland
     • Palustrine Emergent Wetland
```

#### Location Not in Wetland:
```
🌿 WETLAND STATUS:
   Status: Location is not within a mapped wetland, nearest wetland is 0.3 miles NE
   
   Nearest Wetlands (within 0.5 miles):
     1. Palustrine Emergent Wetland
        Distance: 0.3 miles NE
        Code: PEM1C
        Area: 2.5 acres
```

## Data Interpretation

### Wetland Codes (NWI Classification)
- **P** = Palustrine (freshwater wetlands)
- **E** = Estuarine (saltwater influenced)
- **R** = Riverine (river systems)
- **L** = Lacustrine (lakes)
- **M** = Marine (ocean)

### Wetland Types
- **EM** = Emergent (herbaceous plants)
- **FO** = Forested (woody plants >6m tall)
- **SS** = Scrub-Shrub (woody plants <6m tall)
- **UB** = Unconsolidated Bottom (mud/sand)
- **AB** = Aquatic Bed (floating/submerged plants)

### HUC Levels
- **HUC8**: Subbasins
- **HUC10**: Watersheds  
- **HUC12**: Subwatersheds

## Output Files

### Data Files
Results are saved to the `logs/` directory with the naming pattern:
```
wetland_analysis_{longitude}_{latitude}_{timestamp}.json
wetland_analysis_{longitude}_{latitude}_{timestamp}_summary.json
```

### Map Files
PDF maps are saved to the `output/` directory:
```
wetland_map_{timestamp}.pdf
wetland_map_detailed_{location}_{timestamp}.pdf
wetland_map_overview_{location}_{timestamp}.pdf
```

## Regulatory Information

The tool provides guidance on:
- Clean Water Act Section 404 permits
- State wetland regulations
- Environmental impact assessments
- Wetland mitigation requirements
- Buffer zone requirements

## Recommendations

Based on the analysis, the tool provides specific recommendations:
- **If in wetland**: Consult specialists, obtain permits, conduct delineation
- **If not in wetland**: Verify with field survey, maintain buffers, implement BMPs

## Data Sources

- **USFWS National Wetlands Inventory (NWI)**: Primary wetland mapping data
- **EPA RIBITS**: Wetland banking and mitigation sites
- **EPA Waters**: Watershed boundaries and hydrography
- **USFWS Riparian Data**: Stream corridors and riparian zones

## Limitations

- Based on mapped wetland data; field verification recommended
- Wetland boundaries may change over time
- Small or seasonal wetlands may not be mapped
- Accuracy depends on source data quality

## Additional Resources

- [USFWS Wetlands Mapper](https://www.fws.gov/wetlands/data/mapper.html)
- [EPA Wetlands Information](https://www.epa.gov/wetlands)
- [Clean Water Act Section 404](https://www.epa.gov/cwa-404)
- [Wetland Delineation Manual](https://www.usace.army.mil/Missions/Civil-Works/Regulatory-Program-and-Permits/reg_supp/)

## Support

For issues or questions about wetland data:
- USFWS Wetlands Help: wetlands_team@fws.gov
- EPA Wetlands Hotline: 1-800-832-7828

## License

This tool is provided as-is for informational purposes. Always consult with qualified professionals for regulatory compliance and environmental assessments. 