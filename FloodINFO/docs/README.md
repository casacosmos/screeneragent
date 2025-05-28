# FloodINFO - FEMA Flood Data Query and FIRMette Generation Tool

A standalone Python tool for querying FEMA flood data and generating official FIRMette (Flood Insurance Rate Map) reports for any coordinate location, with special support for Puerto Rico.

## Features

- 🌊 **Comprehensive Flood Data Query** - Query FEMA's National Flood Hazard Layer (NFHL) for any coordinates
- 🗺️ **Official FIRMette Generation** - Generate official FEMA flood insurance rate maps (PDF)
- 📊 **Preliminary Comparison Reports** - Compare current vs preliminary flood data changes
- 🌊 **ABFE Data & Maps** - Query Advisory Base Flood Elevation data with visual maps
- 🏝️ **Puerto Rico Support** - Full support for Puerto Rico flood data and mapping
- 📄 **Data Export** - Save query results to JSON files for further analysis
- 📋 **Detailed Reporting** - Clear, organized flood hazard information display

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Installation**:
   ```bash
   python query_coordinates_data.py --help
   ```

## Usage

### Interactive Mode
```bash
python query_coordinates_data.py
```
Follow the prompts to enter coordinates and location name.

### Command Line Mode
```bash
python query_coordinates_data.py <longitude> <latitude> [location_name] [save]
```

### Examples

**Query Cataño, Puerto Rico (default coordinates):**
```bash
python query_coordinates_data.py
```

**Query specific coordinates:**
```bash
python query_coordinates_data.py -66.1689712 18.4282314 "Cataño, Puerto Rico"
```

**Query and auto-save results:**
```bash
python query_coordinates_data.py -66.1689712 18.4282314 "Cataño, Puerto Rico" save
```

**Query Miami, Florida:**
```bash
python query_coordinates_data.py -80.1918 25.7617 "Miami, Florida"
```

## What You Get

### Flood Data Query Results
- **NFHL (Current Effective)** - Current flood hazard zones, FIRM panels, political jurisdictions
- **Preliminary FIRM** - Upcoming flood map changes and updates
- **MapSearch Reports** - Community flood studies and reports

### FIRMette Generation
- **Official FEMA PDF** - Legally valid flood insurance rate map
- **High Resolution** - 300 DPI professional quality
- **Coordinate Specific** - Centered on your exact location
- **Downloadable** - Saved locally for immediate use

### Preliminary Comparison Reports
- **Current vs Preliminary** - Compare existing flood maps with upcoming changes
- **Change Detection** - Identify areas where flood zones will change
- **Official FEMA Analysis** - Generated using FEMA's comparison tool
- **Planning Support** - Essential for development and insurance planning

### ABFE Data & Maps
- **Advisory Elevations** - Non-regulatory flood elevation guidance
- **Visual Maps** - Interactive maps showing ABFE data layers
- **Post-Disaster Support** - Primarily available for recovery areas
- **Planning Guidance** - Advisory information for development planning

### Data Fields Explained
- **DFIRM_ID**: Digital FIRM identifier (72000C = Puerto Rico)
- **FIRM_PAN**: FIRM panel identifier
- **FLD_ZONE**: Flood zone designation (A, AE, X, VE, etc.)
- **STATIC_BFE**: Base Flood Elevation in feet
- **POL_AR_ID**: Political area identifier
- **ST_FIPS**: State FIPS code (72 = Puerto Rico)
- **EFF_DATE**: Effective date of the data
- **CID**: Community identifier

## Flood Zone Designations

| Zone | Description |
|------|-------------|
| **X** | Minimal flood hazard (outside 0.2% annual chance floodplain) |
| **AE** | 1% annual chance flood zone with base flood elevations |
| **A** | 1% annual chance flood zone without base flood elevations |
| **VE** | 1% annual chance coastal flood zone with wave action |

## Output Files

### JSON Data Export
Results are saved to `logs/coordinate_query_[coordinates]_[timestamp].json` containing:
- Complete query results
- All feature data from FEMA services
- Metadata and timestamps
- Puerto Rico data identifiers

### Structured Panel Information Export
Additional structured data is saved to `logs/panel_info_[coordinates]_[timestamp].json` containing:

**🎯 Current Effective Data** (legally binding):
- **Panel Information**: FIRM panels, numbers, suffixes, types
- **Flood Zones**: Current designations and base flood elevations
- **Political Jurisdictions**: Current jurisdiction names and floodplain numbers

**🔄 Preliminary Data** (upcoming changes):
- **Panel Information**: Upcoming FIRM panel changes
- **Flood Zones**: Future flood zone modifications
- **Political Jurisdictions**: Planned jurisdiction updates

**📊 Enhanced Features**:
- **Duplicate Removal**: Eliminates repeated data from multiple FEMA services
- **Clear Separation**: Distinguishes current effective vs preliminary data
- **Effective Dates**: Formatted in MM/DD/YYYY format
- **Regional Data**: State identification and FIPS codes
- **Summary Statistics**: Separate counts for current vs preliminary data
- **Source Tracking**: Shows which FEMA service provided each data point
- **Data Guide**: Complete explanations and flood zone meanings

### FIRMette PDF
FIRMette maps are saved as `firmette_[location]_[timestamp].pdf` containing:
- Official FEMA flood map
- Coordinate marker
- Flood zone boundaries
- Base flood elevations
- Legal map elements

### Preliminary Comparison PDF
Comparison reports are saved as `preliminary_comparison_[location]_[timestamp].pdf` containing:
- Side-by-side comparison of current and preliminary flood data
- Change analysis and impact assessment
- Flood zone modifications
- Base flood elevation changes
- Effective dates for changes

### ABFE Map PDF
ABFE maps are saved as `abfe_map_[location]_[timestamp].pdf` containing:
- Visual representation of Advisory Base Flood Elevation data
- Topographic base map with ABFE layers overlay
- Query location marker
- Advisory flood elevation information
- Non-regulatory guidance for planning purposes

## Technical Details

### FEMA Services Accessed
- **NFHL Service**: `https://hazards.fema.gov/arcgis/rest/services/FIRMette/NFHLREST_FIRMette/MapServer`
- **Preliminary FIRM**: `https://hazards.fema.gov/arcgis/rest/services/PrelimPending/Prelim_NFHL/MapServer`
- **MapSearch**: `https://hazards.fema.gov/arcgis/rest/services/MapSearch/MapSearch_v5/MapServer`
- **FIRMette Print**: `https://msc.fema.gov/arcgis/rest/services/NFHL_Print/AGOLPrintB/GPServer`
- **Preliminary Comparison**: `https://msc.fema.gov/arcgis/rest/services/PreliminaryComparisonTool/PreliminaryComparisonToolB/GPServer`
- **ABFE Data**: `https://hazards.geoplatform.gov/server/rest/services/Region2/Advisory_Base_Flood_Elevation__ABFE__Data/MapServer`
- **Map Export**: `https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer`

### Coordinate Systems
- **Input**: WGS84 (EPSG:4326) - Standard latitude/longitude
- **Processing**: Web Mercator (EPSG:3857) - For FEMA service compatibility
- **Output**: WGS84 coordinates in reports

## Troubleshooting

### Common Issues

**No flood data found:**
- Location may be outside FEMA-mapped areas
- Try nearby coordinates
- Check if location is in a participating NFIP community

**FIRMette generation fails:**
- FEMA service may be temporarily unavailable
- Try again after a few minutes
- Manual generation available at: https://msc.fema.gov/portal/advanceSearch

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.7+ required)

### Puerto Rico Specific Notes
- Puerto Rico uses DFIRM_ID: 72000C
- State FIPS code: 72
- Full coverage available for all municipalities
- Both English and Spanish location names supported

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your coordinates are correct (longitude, latitude format)
3. Ensure internet connectivity for FEMA service access

## Legal Notice

This tool accesses official FEMA flood data and generates official flood insurance rate maps. The generated FIRMettes are legally valid for flood insurance and floodplain management purposes when used in accordance with FEMA guidelines.

**Disclaimer**: This tool is not affiliated with FEMA. It provides access to publicly available FEMA flood data and services. 