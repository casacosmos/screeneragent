# ABFE Parameters Quick Reference

## Complete Parameter List

The FEMA ABFE client supports the following parameters for controlling scale, zoom, and display elements:

### Scale & Zoom Control

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `map_scale` | int | None | Specific map scale (overrides buffer_miles) | 5000, 12000, 24000 |
| `buffer_miles` | float | 0.5 | Area around point in miles | 0.1, 0.5, 1.0, 2.0 |

### Layer Visibility

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `visible_layers` | List[int] | None | Layer IDs to display (None = all) | [5,6], [1,5,6], [3,4,5] |
| `layer_opacity` | float | 0.8 | ABFE layer transparency (0.0-1.0) | 0.5, 0.7, 1.0 |

### Output Format

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `map_format` | str | "PDF" | Output file format | "PDF", "PNG", "JPEG" |
| `dpi` | int | 300 | Resolution (dots per inch) | 96, 150, 300, 600 |
| `output_size` | tuple | (792, 612) | Map dimensions (width, height) | (800,600), (1224,792) |

### Base Map & Display

| Parameter | Type | Default | Description | Examples |
|-----------|------|---------|-------------|----------|
| `base_map` | str | "World_Topo_Map" | Background map style | "World_Imagery", "World_Street_Map" |
| `show_attribution` | bool | True | Show map credits | True, False |
| `show_point_marker` | bool | True | Show location marker | True, False |

## Layer Reference

| ID | Layer Name | Min Scale | Type | Best Use |
|----|------------|-----------|------|----------|
| 0 | Streamline | 1:9,028 | Line | Detailed drainage |
| 1 | Advisory Base Flood Elevation | 1:18,056 | Line | ABFE contours |
| 3 | Limit of Moderate Wave Action | 1:288,895 | Line | Coastal zones |
| 4 | Flood Hazard Extent | 1:288,895 | Line | Zone boundaries |
| 5 | Zone/BFE Boundary | 1:288,895 | Polygon | Flood zones |
| 6 | Flood Hazard Area | 1:288,895 | Polygon | Hazard areas |

## Common Parameter Combinations

### Property Analysis (Detailed)
```python
map_scale=5000
visible_layers=[1, 5, 6]  # ABFE lines + zones
base_map="World_Imagery"
dpi=300
```

### Community Planning (Standard)
```python
map_scale=12000
visible_layers=[5, 6]     # Flood zones only
base_map="World_Topo_Map"
dpi=300
```

### Regional Overview (Wide)
```python
buffer_miles=2.0
visible_layers=[5, 6]     # Zones only
base_map="World_Street_Map"
dpi=150
```

### Web Display (Optimized)
```python
map_format="PNG"
dpi=150
output_size=(800, 600)
show_attribution=False
```

## Scale Guidelines

- **1:1,000 - 1:5,000**: Building/parcel level detail
- **1:12,000**: Standard for flood determinations
- **1:24,000**: Community planning scale
- **1:50,000+**: Regional overview

## Usage Example

```python
from abfe_client import FEMAABFEClient

client = FEMAABFEClient()

# Generate custom ABFE map
success, url, job_id = client.generate_abfe_map(
    longitude=-66.1689712,
    latitude=18.4282314,
    location_name="Site Analysis",
    map_scale=12000,              # 1:12,000 scale
    visible_layers=[1, 5, 6],     # ABFE + flood zones
    layer_opacity=0.7,            # Semi-transparent
    base_map="World_Imagery",     # Satellite background
    dpi=300,                      # Print quality
    output_size=(1224, 792),      # Tabloid size
    show_point_marker=True,       # Show location
    show_attribution=True         # Include credits
)

if success:
    client.download_abfe_map(url, "custom_abfe_map.pdf")
```

## Notes

- Only works for Puerto Rico coordinates
- Layers 0 and 1 require zoomed-in scales to be visible
- PNG format uses PNG32 internally
- All elevations in Puerto Rico Vertical Datum of 2002 (PRVD02) 