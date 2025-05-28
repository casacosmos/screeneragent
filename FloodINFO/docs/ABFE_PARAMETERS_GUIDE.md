# ABFE Map Generation Parameters Guide

## Overview

The FEMA ABFE (Advisory Base Flood Elevation) client provides extensive customization options for generating flood elevation maps. This guide covers all available parameters for controlling scale, zoom, layer visibility, and display elements.

## Service Information

- **Service URL**: `https://hazards.geoplatform.gov/server/rest/services/Region2/Advisory_Base_Flood_Elevation__ABFE__Data/MapServer`
- **Coverage**: Puerto Rico only
- **Coordinate System**: Web Mercator (EPSG:3857), accepts WGS84 (EPSG:4326) input
- **Elevation Datum**: Puerto Rico Vertical Datum of 2002 (PRVD02)

## Available Layers

| Layer ID | Layer Name | Min Scale | Geometry Type | Description |
|----------|------------|-----------|---------------|-------------|
| 0 | Streamline | 1:9,028 | Polyline | Stream centerlines (zoom in to see) |
| 1 | Advisory Base Flood Elevation | 1:18,056 | Polyline | ABFE contour lines (zoom in to see) |
| 2 | Flood Hazard Boundary | No limit | Group | Container for boundary layers |
| 3 | Limit of Moderate Wave Action (LiMWA) | 1:288,895 | Polyline | Wave action boundaries |
| 4 | Flood Hazard Extent | 1:288,895 | Polyline | Flood zone boundaries |
| 5 | Zone/BFE Boundary | 1:288,895 | Polygon | Flood zone polygons |
| 6 | Flood Hazard Area | 1:288,895 | Polygon | Flood hazard areas (zoom in to see) |

## Scale and Zoom Parameters

### 1. Map Scale (`map_scale`)

Controls the map scale directly. When specified, overrides `buffer_miles`.

```python
# Examples
map_scale=1000    # 1:1,000 - Building level detail
map_scale=5000    # 1:5,000 - Neighborhood level
map_scale=12000   # 1:12,000 - Community level (recommended)
map_scale=24000   # 1:24,000 - City level
map_scale=50000   # 1:50,000 - Regional level
```

**Scale Guidelines:**
- **1:1,000 - 1:5,000**: Very detailed, good for individual properties
- **1:12,000**: Standard scale for flood insurance determinations
- **1:24,000**: Good for community planning
- **1:50,000+**: Regional overview

### 2. Buffer Distance (`buffer_miles`)

Controls area around the point when `map_scale` is not specified.

```python
# Examples
buffer_miles=0.1   # Very tight zoom (0.2 mile diameter)
buffer_miles=0.5   # Default zoom (1 mile diameter)
buffer_miles=1.0   # Wider area (2 mile diameter)
buffer_miles=2.0   # Regional view (4 mile diameter)
```

## Layer Visibility Parameters

### 3. Visible Layers (`visible_layers`)

Specify which layers to display. If `None`, all layers are shown.

```python
# Examples
visible_layers=None           # Show all layers (default)
visible_layers=[5, 6]         # Only flood zones and hazard areas
visible_layers=[1, 5, 6]      # ABFE lines + flood zones
visible_layers=[0, 1, 3, 4, 5, 6]  # All except group layer
```

**Common Combinations:**
- **[5, 6]**: Basic flood zones only
- **[1, 5, 6]**: ABFE elevations with flood zones
- **[3, 4, 5]**: All boundary types
- **[0, 1]**: Streams and elevation lines only

### 4. Layer Opacity (`layer_opacity`)

Controls transparency of ABFE layers (0.0 = transparent, 1.0 = opaque).

```python
# Examples
layer_opacity=0.5   # Semi-transparent
layer_opacity=0.8   # Default (slightly transparent)
layer_opacity=1.0   # Completely opaque
```

## Output Format Parameters

### 5. Map Format (`map_format`)

Output file format.

```python
# Options
map_format="PDF"    # Vector format, scalable (default)
map_format="PNG"    # Raster format, good for web
map_format="JPEG"   # Compressed raster format
```

### 6. Resolution (`dpi`)

Dots per inch for output quality.

```python
# Examples
dpi=96     # Web quality
dpi=150    # Good quality
dpi=300    # Print quality (default)
dpi=600    # High resolution
```

### 7. Output Size (`output_size`)

Map dimensions in pixels as (width, height) tuple.

```python
# Standard sizes
output_size=(792, 612)    # Letter size (default)
output_size=(1224, 792)   # Tabloid size
output_size=(1584, 1224)  # A3 size
output_size=(2448, 1584)  # Large format
```

## Base Map Options

### 8. Base Map (`base_map`)

Background map style.

```python
# Available options
base_map="World_Topo_Map"     # Topographic (default)
base_map="World_Street_Map"   # Street map
base_map="World_Imagery"      # Satellite imagery
base_map="NatGeo_World_Map"   # National Geographic style
```

**Base Map Characteristics:**
- **World_Topo_Map**: Shows terrain, good for elevation context
- **World_Street_Map**: Shows roads and urban features
- **World_Imagery**: Satellite photos, good for land use context
- **NatGeo_World_Map**: Artistic style with terrain

## Display Element Parameters

### 9. Attribution (`show_attribution`)

Whether to show map credits and attribution.

```python
show_attribution=True   # Show credits (default)
show_attribution=False  # Hide credits
```

### 10. Point Marker (`show_point_marker`)

Whether to show a marker at the query location.

```python
show_point_marker=True   # Show red marker (default)
show_point_marker=False  # No marker
```

## Usage Examples

### Basic Usage

```python
from abfe_client import FEMAABFEClient

client = FEMAABFEClient()

# Simple map with defaults
success, url, job_id = client.generate_abfe_map(
    longitude=-66.1689712,
    latitude=18.4282314,
    location_name="Cataño, Puerto Rico"
)
```

### Detailed Property Map

```python
# High-detail map for property analysis
success, url, job_id = client.generate_abfe_map(
    longitude=-66.1689712,
    latitude=18.4282314,
    location_name="Property Site",
    map_scale=5000,              # 1:5,000 scale
    visible_layers=[1, 5, 6],    # ABFE lines + flood zones
    layer_opacity=0.7,           # Semi-transparent
    base_map="World_Imagery",    # Satellite background
    dpi=300,                     # Print quality
    show_point_marker=True
)
```

### Regional Overview Map

```python
# Wide-area overview for planning
success, url, job_id = client.generate_abfe_map(
    longitude=-66.1689712,
    latitude=18.4282314,
    location_name="Regional Study Area",
    buffer_miles=2.0,            # 2-mile radius
    visible_layers=[5, 6],       # Flood zones only
    base_map="World_Topo_Map",   # Topographic background
    output_size=(1224, 792),     # Larger format
    show_attribution=True
)
```

### Custom Styled Map

```python
# Custom styling for presentations
success, url, job_id = client.generate_abfe_map(
    longitude=-66.1689712,
    latitude=18.4282314,
    location_name="Study Location",
    map_scale=12000,             # Standard scale
    visible_layers=[3, 4, 5],    # All boundaries
    layer_opacity=0.6,           # More transparent
    base_map="NatGeo_World_Map", # Artistic style
    dpi=150,                     # Web quality
    show_point_marker=False,     # No marker
    show_attribution=False       # Clean appearance
)
```

## Scale Dependencies

Some layers have minimum scale requirements:

- **Layers 0, 1**: Only visible at scales larger than 1:18,000
- **Layers 3, 4, 5, 6**: Visible at all scales up to 1:288,895

When using `map_scale` parameter, ensure it's appropriate for the layers you want to display.

## Best Practices

1. **For Property Analysis**: Use scales 1:1,000 to 1:12,000 with layers [1, 5, 6]
2. **For Community Planning**: Use scales 1:12,000 to 1:24,000 with all layers
3. **For Regional Studies**: Use buffer_miles 1.0-2.0 with layers [5, 6] only
4. **For Print Output**: Use DPI 300+ and appropriate output_size
5. **For Web Display**: Use DPI 150 and PNG format

## Troubleshooting

- **Empty maps**: Check if coordinates are within Puerto Rico
- **Missing layers**: Verify scale is appropriate for layer visibility
- **Large file sizes**: Reduce DPI or output_size
- **Slow generation**: Use fewer visible_layers or lower DPI 