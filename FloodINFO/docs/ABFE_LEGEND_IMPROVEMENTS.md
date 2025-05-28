# ABFE Map Legend Improvements

## Overview
This document outlines the improvements made to ensure ABFE (Advisory Base Flood Elevation) maps always display the full legend and map elements.

## Changes Made

### 1. Layout Template Selection
- **Before**: Used "A4 Portrait" layout template
- **After**: Changed to "Letter ANSI A Portrait" layout template
- **Benefit**: Better legend space allocation and US standard paper size

### 2. Legend Parameter Enforcement
- **Enhancement**: Added explicit `include_legend=True` parameter to all ABFE map generation calls
- **Fallback**: Updated `generate_and_download_abfe_map()` to always pass `include_legend=True`
- **Validation**: Added debug output to confirm legend inclusion

### 3. Layout Options Configuration
- **Added**: `layoutOptions` section to web map specification
- **Includes**:
  - `titleText`: Dynamic title with location name
  - `authorText`: "FEMA ABFE Data"
  - `copyrightText`: Source attribution
  - `scalebarUnit`: "Miles"
  - `legendLayers`: Explicit legend layer specification

### 4. Debug Information
- **Added**: Console output showing:
  - Legend inclusion status
  - Layout template being used
  - Output format and dimensions
  - DPI settings

## Current ABFE Map Configuration

```python
# Optimal settings for full legend display
abfe_client.generate_abfe_map(
    longitude=longitude,
    latitude=latitude,
    location_name=location_name,
    buffer_miles=0.3,
    base_map="World_Imagery",      # Satellite background
    show_point_marker=False,
    map_format="PDF",              # PDF format for proper layout
    dpi=250,                       # Web resolution
    output_size=(1224, 792),       # Larger format
    show_attribution=True,         # Show attribution
    include_legend=True            # ALWAYS include full legend and map elements
)
```

## Available Layout Templates

The ArcGIS PrintingTools service supports these layout templates:

1. **"Letter ANSI A Portrait"** ✅ (Current - Best for legend)
2. "Letter ANSI A Landscape"
3. "A4 Portrait"
4. "A4 Landscape"
5. "Tabloid ANSI B Portrait"
6. "Tabloid ANSI B Landscape"
7. "MAP_ONLY" (No legend or decorations)

## Map Elements Included

When `include_legend=True` and using "Letter ANSI A Portrait" layout:

- ✅ **Legend**: Shows ABFE layer symbology and descriptions
- ✅ **Scale Bar**: Distance measurement in miles
- ✅ **North Arrow**: Directional indicator
- ✅ **Title**: Dynamic title with location name
- ✅ **Attribution**: Data source credits
- ✅ **Copyright**: FEMA data attribution
- ✅ **Coordinate Grid**: Optional coordinate reference

## Verification

To verify the legend is included:

1. Check console output for "Legend included: True"
2. Confirm layout shows "Letter ANSI A Portrait"
3. Verify PDF file size (should be >1MB with full layout)
4. Open PDF and confirm legend appears on the map

## File Output

Maps are saved to the `output/` directory with naming pattern:
```
output/abfe_map_{location_name}_{timestamp}.pdf
```

Example: `output/abfe_map_Cataño_Puerto_Rico_20250526_233940.pdf` 