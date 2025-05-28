# Wetland Map PDF Configuration Guide

## Overview

This guide explains the proper configuration for generating wetland map PDFs using ArcGIS REST services, based on successful patterns from the ABFE implementation.

## Key Configuration Elements

### 1. Service URLs

```python
# Printing service for PDF generation
printing_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map/execute"

# Wetlands data service
wetlands_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer"

# Base map services
base_map_urls = {
    "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
    "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
    "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer"
}
```

### 2. Web Map JSON Structure

The Web Map JSON must follow the ArcGIS Web Map specification:

```python
web_map = {
    "mapOptions": {
        "extent": {
            "xmin": -66.203,
            "ymin": 18.445,
            "xmax": -66.189,
            "ymax": 18.459,
            "spatialReference": {"wkid": 4326}  # WGS84
        },
        "showAttribution": True
    },
    "operationalLayers": [...],
    "baseMap": {...},
    "exportOptions": {...},
    "layoutOptions": {...},
    "version": "1.6.0"
}
```

### 3. Operational Layers Configuration

#### Wetlands Layer
```python
wetlands_layer = {
    "url": wetlands_service_url,
    "title": "National Wetlands Inventory",
    "opacity": 0.75,
    "visibility": True,
    "layerType": "ArcGISMapServiceLayer",
    "visibleLayers": [0]  # Layer 0 contains wetland features
}
```

#### Location Marker
```python
point_marker = {
    "featureCollection": {
        "layers": [{
            "featureSet": {
                "features": [{
                    "geometry": {
                        "x": longitude,
                        "y": latitude,
                        "spatialReference": {"wkid": 4326}
                    },
                    "attributes": {"name": location_name},
                    "symbol": {
                        "type": "esriSMS",
                        "style": "esriSMSCircle",
                        "color": [255, 0, 0, 255],
                        "size": 10,
                        "outline": {
                            "color": [255, 255, 255, 255],
                            "width": 2
                        }
                    }
                }],
                "geometryType": "esriGeometryPoint"
            },
            "layerDefinition": {
                "geometryType": "esriGeometryPoint",
                "fields": [
                    {
                        "name": "name",
                        "type": "esriFieldTypeString",
                        "alias": "Name"
                    }
                ]
            }
        }]
    },
    "title": "Query Location",
    "opacity": 1,
    "visibility": True
}
```

### 4. Export Options

```python
"exportOptions": {
    "outputSize": [1224, 792],  # Width x Height in pixels
    "dpi": 300                  # Print quality
}
```

**Common Output Sizes:**
- Letter: `[792, 612]` (8.5" x 11" at 72 DPI base)
- Tabloid: `[1224, 792]` (11" x 17")
- A4: `[842, 595]`
- Custom: Calculate as `inches * dpi`

### 5. Layout Options

```python
"layoutOptions": {
    "titleText": "Wetland Map - Location Name",
    "authorText": "WetlandsINFO System",
    "copyrightText": "USFWS National Wetlands Inventory | Generated 2024-01-15",
    "scaleBarOptions": {
        "metricUnit": "esriKilometers",
        "metricLabel": "km",
        "nonMetricUnit": "esriMiles",
        "nonMetricLabel": "mi"
    },
    "legendOptions": {
        "operationalLayers": [
            {
                "id": "wetlands_layer",
                "subLayerIds": visible_layers
            }
        ]
    }
}
```

**Important:** The operational layer must have an `id` field that matches the `id` in `legendOptions`.

### 6. Layout Templates

Available templates from the USFWS service:
- `"Letter ANSI A Portrait"` - Best for maps with legends
- `"Letter ANSI A Landscape"` - Wide format
- `"Tabloid ANSI B Portrait"` - Large format
- `"Tabloid ANSI B Landscape"` - Extra wide
- `"MAP_ONLY"` - No decorations, just the map

### 7. Export Parameters

```python
export_params = {
    "f": "json",
    "Web_Map_as_JSON": json.dumps(web_map),
    "Format": "PDF",
    "Layout_Template": "Letter ANSI A Portrait"
}
```

## Key Fixes for Wetland Display

The main issues preventing wetland polygons from displaying were:

1. **Scale Dependency**: The USFWS Wetlands service has a minimum scale of 1:250,000
2. **Layer Selection**: Different geographic regions use different layers
3. **Web Map Configuration**: Proper layer visibility and scale settings needed

### Scale Management
```python
# Calculate appropriate scale
map_scale = int(map_width_feet / (output_size[0] / dpi))

# Ensure scale allows wetlands visibility (< 1:250,000)
if map_scale > 200000:
    # Adjust extent for better scale
    scale_factor = map_scale / 200000
    buffer_degrees = buffer_degrees / scale_factor
    map_scale = 200000
```

### Geographic Layer Selection
```python
if -68 <= longitude <= -65 and 17 <= latitude <= 19:
    visible_layers = [5]  # Puerto Rico/Virgin Islands
elif longitude < -100:
    visible_layers = [0, 2]  # Western CONUS
else:
    visible_layers = [0, 1]  # Eastern CONUS
```

### Proper Layer Configuration
```python
wetlands_layer = {
    "url": wetlands_service_url,
    "title": "National Wetlands Inventory",
    "opacity": 0.8,
    "visibility": True,
    "layerType": "ArcGISMapServiceLayer",
    "visibleLayers": visible_layers,
    "minScale": 250000,  # Respect service constraints
    "maxScale": 0
}
```

## Common Issues and Solutions

### Issue 1: No Wetlands Visible
**Problem:** Wetlands don't appear on the map
**Solution:** 
- **Scale Issue**: Wetlands have a minimum scale of 1:250,000. Ensure map scale is more detailed (< 1:250,000)
- **Layer Selection**: Use correct layer for location:
  - Puerto Rico/Virgin Islands: Layer 5 (`Wetlands_PRVI`)
  - Western CONUS: Layers 0, 2 (`Wetlands`, `Wetlands_CONUS_West`)
  - Eastern CONUS: Layers 0, 1 (`Wetlands`, `Wetlands_CONUS_East`)
- **Buffer Size**: Use smaller buffer (0.3-0.5 miles) for better scale
- Verify the wetlands service is accessible

### Issue 2: Legend Not Appearing
**Problem:** Legend is missing from PDF
**Solution:**
- Use a layout template that supports legends (not `MAP_ONLY`)
- Use proper `legendOptions` structure in `layoutOptions`:
  ```python
  "legendOptions": {
      "operationalLayers": [
          {
              "id": "wetlands_layer",
              "subLayerIds": visible_layers
          }
      ]
  }
  ```
- Ensure operational layers have `id` fields
- Set `include_legend=True`

### Issue 3: Poor Quality Output
**Problem:** PDF appears pixelated or low quality
**Solution:**
- Increase DPI to 300 or higher
- Use larger output size
- Ensure base map supports the requested scale

### Issue 4: Timeout Errors
**Problem:** Request times out
**Solution:**
- Reduce the extent (smaller area)
- Lower the DPI
- Use simpler base maps

## Best Practices

1. **Coordinate Systems**
   - Use WGS84 (WKID 4326) for input coordinates
   - The service handles conversion to Web Mercator internally

2. **Scale Considerations**
   - Wetlands layer has scale dependencies
   - Best visibility at scales 1:24,000 or larger
   - Some features may not display at small scales

3. **Performance Optimization**
   - Limit extent to area of interest
   - Use appropriate DPI (300 for print, 96 for web)
   - Cache base map tiles when possible

4. **Error Handling**
   ```python
   try:
       response = session.post(url, data=params, timeout=60)
       response.raise_for_status()
       result = response.json()
       
       if 'error' in result:
           logger.error(f"Service error: {result['error']}")
           return None
           
   except requests.exceptions.RequestException as e:
       logger.error(f"Request failed: {e}")
       return None
   ```

## Example Configurations

### Detailed Site Map
```python
generator.generate_wetland_map_pdf(
    longitude=-66.196,
    latitude=18.452,
    location_name="Site Assessment",
    buffer_miles=0.3,
    base_map="World_Imagery",
    dpi=300,
    output_size=(1224, 792),
    include_legend=True
)
```

### Regional Overview
```python
generator.generate_wetland_map_pdf(
    longitude=-66.196,
    latitude=18.452,
    location_name="Regional Context",
    buffer_miles=2.0,
    base_map="World_Topo_Map",
    dpi=150,
    output_size=(792, 612),
    include_legend=True
)
```

### Quick Reference Map
```python
generator.generate_wetland_map_pdf(
    longitude=-66.196,
    latitude=18.452,
    location_name="Quick Reference",
    buffer_miles=0.5,
    base_map="World_Street_Map",
    dpi=96,
    output_size=(792, 612),
    include_legend=False
)
```

## Wetland Symbology

The National Wetlands Inventory uses standardized colors:
- **Estuarine/Marine**: Blues (deepwater to light blue)
- **Palustrine Emergent**: Greens (herbaceous wetlands)
- **Palustrine Forested**: Dark greens (woody wetlands)
- **Riverine**: Cyan/turquoise (flowing water)
- **Lacustrine**: Deep blue (lakes)

## Testing the Configuration

1. **Test with known wetland location:**
   ```bash
   python generate_wetland_map_pdf_v3.py -66.196 18.452 "Test Location"
   ```

2. **Verify output includes:**
   - Wetland polygons with proper symbology
   - Legend showing wetland types
   - Scale bar and north arrow
   - Location marker
   - Title and attribution

3. **Check PDF properties:**
   - File size (typically 1-5 MB)
   - Resolution matches requested DPI
   - All map elements are vector (not rasterized)

## Troubleshooting

Enable debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

Check service availability:
```bash
curl "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer?f=json"
```

Validate Web Map JSON:
```python
import json
try:
    json.dumps(web_map)
    print("✓ Valid JSON")
except:
    print("✗ Invalid JSON")
``` 