# ArcGIS MapServer Adaptation Guide

## Overview
This guide outlines how to adapt the FEMA flood data modules to work with other ArcGIS MapServer implementations. The modular structure allows for easy adaptation to different data sources while maintaining the same interface.

## Project Structure

```
YourProject/
├── main.py                    # Simplified interface for queries and reports
├── tools.py                   # LangGraph tools with @tool decorators
├── mcp_server.py             # MCP server for tool exposure
├── DataClient/               # Core data querying modules
│   ├── __init__.py
│   ├── arcgis_client.py      # Base ArcGIS client
│   ├── query_data.py         # Main data query module
│   ├── map_generator.py      # Map snapshot generator
│   ├── report_generator.py   # PDF report generator
│   └── requirements.txt
├── output/                   # Generated reports and maps
└── logs/                     # Query results and logs

```

## 1. Main.py - Simplified Interface

```python
#!/usr/bin/env python3
"""
ArcGIS Data Query Tool - Simplified Interface

Query ArcGIS MapServer data and generate reports for any coordinate.
"""

import sys
import os
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), 'DataClient'))

from query_data import query_coordinate_data, save_results_to_file
from map_generator import MapGenerator
from report_generator import ReportGenerator

class ArcGISDataQuery:
    """Simplified interface for ArcGIS data queries and report generation"""
    
    def __init__(self, service_config: Dict[str, str]):
        """
        Initialize with service configuration
        
        Args:
            service_config: Dictionary with service URLs and layer mappings
        """
        self.service_config = service_config
        self.map_generator = MapGenerator(service_config)
        self.report_generator = ReportGenerator()
        
        os.makedirs('output', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
    
    def query(self, longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
        """Query all data for given coordinates"""
        print(f"🗺️ Querying ArcGIS data for ({longitude}, {latitude})")
        
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        # Query data from all configured services
        results = query_coordinate_data(
            longitude, latitude, 
            location_name, 
            self.service_config
        )
        
        # Auto-save results
        save_results_to_file(results)
        
        return results
    
    def generate_map_snapshot(self, longitude: float, latitude: float, 
                            location_name: Optional[str] = None,
                            map_type: str = "default") -> Tuple[bool, str]:
        """
        Generate a map snapshot for coordinates
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            map_type: Type of map to generate
            
        Returns:
            (success: bool, message/filename: str)
        """
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        print(f"📸 Generating map snapshot for {location_name}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = f"output/map_{map_type}_{safe_name}_{timestamp}.pdf"
        
        try:
            success = self.map_generator.generate_map(
                longitude=longitude,
                latitude=latitude,
                output_file=filename,
                map_type=map_type,
                buffer_miles=0.5,
                dpi=300
            )
            
            if success:
                return True, f"Map saved as: {filename}"
            else:
                return False, "Map generation failed"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def generate_data_report(self, longitude: float, latitude: float,
                           location_name: Optional[str] = None,
                           report_type: str = "comprehensive") -> Tuple[bool, str]:
        """Generate a formatted PDF report with query results"""
        # Implementation similar to FIRMette generation
        pass

def main():
    """Command line interface"""
    # Similar structure to FEMA main.py
    pass

if __name__ == "__main__":
    main()
```

## 2. Core Modules

### 2.1 arcgis_client.py - Base ArcGIS Client

```python
"""
Base ArcGIS MapServer Client

Handles authentication, requests, and common operations for ArcGIS services.
"""

import requests
from typing import Dict, Any, List, Optional
import json

class ArcGISClient:
    """Base client for interacting with ArcGIS MapServer services"""
    
    def __init__(self, service_urls: Dict[str, str], timeout: int = 30):
        """
        Initialize with service URLs
        
        Args:
            service_urls: Dictionary mapping service names to URLs
            timeout: Request timeout in seconds
        """
        self.services = service_urls
        self.session = requests.Session()
        self.timeout = timeout
    
    def query_point(self, service_name: str, layer_id: int, 
                   longitude: float, latitude: float,
                   out_fields: str = "*") -> Dict[str, Any]:
        """
        Query a specific layer at a point
        
        Args:
            service_name: Name of the service
            layer_id: Layer ID to query
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            out_fields: Fields to return
            
        Returns:
            Query results with features
        """
        service_url = self.services.get(service_name)
        if not service_url:
            raise ValueError(f"Service {service_name} not configured")
        
        # Create point geometry
        geometry = {
            'x': longitude,
            'y': latitude,
            'spatialReference': {'wkid': 4326}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': out_fields,
            'f': 'json',
            'returnGeometry': 'true'
        }
        
        url = f"{service_url}/{layer_id}/query"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
    
    def get_map_export_url(self, service_name: str, bbox: List[float],
                          size: Tuple[int, int], dpi: int = 96,
                          layers: Optional[str] = None) -> str:
        """
        Get URL for map export
        
        Args:
            service_name: Name of the service
            bbox: Bounding box [xmin, ymin, xmax, ymax]
            size: Image size (width, height)
            dpi: DPI for export
            layers: Specific layers to show
            
        Returns:
            URL for map image
        """
        service_url = self.services.get(service_name)
        if not service_url:
            raise ValueError(f"Service {service_name} not configured")
        
        params = {
            'bbox': ','.join(map(str, bbox)),
            'size': f'{size[0]},{size[1]}',
            'dpi': dpi,
            'format': 'png',
            'transparent': 'false',
            'f': 'image'
        }
        
        if layers:
            params['layers'] = layers
        
        # Build URL with parameters
        param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{service_url}/export?{param_str}"
```

### 2.2 map_generator.py - Map Snapshot Generator

```python
"""
Map Generator Module

Generates map snapshots from ArcGIS MapServer services.
Similar to ABFE map generation but more generic.
"""

import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from typing import Dict, Tuple, Optional
import numpy as np

class MapGenerator:
    """Generate map snapshots from ArcGIS services"""
    
    def __init__(self, service_config: Dict[str, str]):
        self.service_config = service_config
        self.session = requests.Session()
    
    def generate_map(self, longitude: float, latitude: float,
                    output_file: str, map_type: str = "default",
                    buffer_miles: float = 0.5, dpi: int = 300,
                    include_legend: bool = True) -> bool:
        """
        Generate a map snapshot centered on coordinates
        
        Args:
            longitude: Center longitude
            latitude: Center latitude
            output_file: Output PDF filename
            map_type: Type of map to generate
            buffer_miles: Buffer around point in miles
            dpi: Output DPI
            include_legend: Whether to include legend
            
        Returns:
            Success boolean
        """
        try:
            # Calculate bounding box
            bbox = self._calculate_bbox(longitude, latitude, buffer_miles)
            
            # Get map configuration for the type
            map_config = self._get_map_config(map_type)
            
            # Fetch map image from ArcGIS
            map_image = self._fetch_map_image(
                bbox, 
                map_config['service'],
                map_config.get('layers'),
                (1200, 800),  # Image size
                dpi
            )
            
            # Create PDF with map and annotations
            self._create_pdf(
                map_image,
                output_file,
                longitude,
                latitude,
                map_config,
                include_legend
            )
            
            return True
            
        except Exception as e:
            print(f"Error generating map: {e}")
            return False
    
    def _calculate_bbox(self, lon: float, lat: float, buffer_miles: float) -> List[float]:
        """Calculate bounding box from center point and buffer"""
        # Approximate degrees per mile
        lat_miles = 69.0
        lon_miles = 69.0 * np.cos(np.radians(lat))
        
        lat_buffer = buffer_miles / lat_miles
        lon_buffer = buffer_miles / lon_miles
        
        return [
            lon - lon_buffer,  # xmin
            lat - lat_buffer,  # ymin
            lon + lon_buffer,  # xmax
            lat + lat_buffer   # ymax
        ]
    
    def _fetch_map_image(self, bbox: List[float], service_name: str,
                        layers: Optional[str], size: Tuple[int, int],
                        dpi: int) -> Image:
        """Fetch map image from ArcGIS service"""
        service_url = self.service_config.get(service_name)
        if not service_url:
            raise ValueError(f"Service {service_name} not configured")
        
        params = {
            'bbox': ','.join(map(str, bbox)),
            'size': f'{size[0]},{size[1]}',
            'dpi': dpi,
            'format': 'png',
            'transparent': 'false',
            'f': 'image'
        }
        
        if layers:
            params['layers'] = f'show:{layers}'
        
        response = self.session.get(
            f"{service_url}/export",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        return Image.open(BytesIO(response.content))
    
    def _create_pdf(self, map_image: Image, output_file: str,
                   lon: float, lat: float, map_config: Dict,
                   include_legend: bool):
        """Create PDF with map image and annotations"""
        
        with PdfPages(output_file) as pdf:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Display map image
            ax.imshow(map_image)
            ax.axis('off')
            
            # Add title
            title = map_config.get('title', 'Map View')
            plt.title(f'{title}\nLocation: ({lon:.6f}, {lat:.6f})', 
                     fontsize=14, pad=20)
            
            # Add center marker
            center_x, center_y = map_image.size[0] / 2, map_image.size[1] / 2
            ax.plot(center_x, center_y, 'r*', markersize=15, 
                   markeredgecolor='white', markeredgewidth=2)
            
            # Add legend if requested
            if include_legend and 'legend_items' in map_config:
                self._add_legend(ax, map_config['legend_items'])
            
            # Add metadata
            metadata_text = (
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Data Source: {map_config.get('source', 'ArcGIS MapServer')}\n"
                f"Scale: 1:{int(buffer_miles * 2 * 63360 / (map_image.size[0] / dpi))}"
            )
            plt.figtext(0.02, 0.02, metadata_text, fontsize=8, 
                       bbox=dict(boxstyle="round,pad=0.3", facecolor="white"))
            
            plt.tight_layout()
            pdf.savefig(fig, dpi=dpi)
            plt.close()
    
    def _get_map_config(self, map_type: str) -> Dict:
        """Get configuration for different map types"""
        configs = {
            'default': {
                'service': 'main_service',
                'title': 'General Map View',
                'source': 'ArcGIS MapServer'
            },
            'imagery': {
                'service': 'imagery_service',
                'title': 'Aerial Imagery',
                'source': 'Satellite Imagery'
            },
            'data_overlay': {
                'service': 'main_service',
                'layers': '0,1,2',  # Specific layers to show
                'title': 'Data Overlay Map',
                'legend_items': [
                    {'color': 'blue', 'label': 'Water Features'},
                    {'color': 'green', 'label': 'Land Areas'},
                    {'color': 'red', 'label': 'Critical Infrastructure'}
                ]
            }
        }
        return configs.get(map_type, configs['default'])
```

### 2.3 query_data.py - Data Query Module

```python
"""
Coordinate Data Query Module

Query specific coordinates and retrieve all available data
from configured ArcGIS services.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
from arcgis_client import ArcGISClient

def query_coordinate_data(longitude: float, latitude: float, 
                         location_name: str,
                         service_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query all available data for specific coordinates
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Name for the location
        service_config: Service configuration with URLs and layers
        
    Returns:
        Dictionary with all available data organized by service and layer
    """
    
    print(f"=== QUERYING DATA FOR {location_name.upper()} ===")
    print(f"Coordinates: {longitude}, {latitude}")
    print(f"Query time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    client = ArcGISClient(service_config['services'])
    
    results = {
        'location': location_name,
        'coordinates': (longitude, latitude),
        'query_time': datetime.now().isoformat(),
        'services': {},
        'summary': {
            'total_services_queried': len(service_config['query_layers']),
            'services_with_data': 0,
            'total_features_found': 0
        }
    }
    
    # Query each configured service and layer
    for service_name, layers in service_config['query_layers'].items():
        print(f"\n{'-'*60}")
        print(f"QUERYING: {service_name}")
        print(f"{'-'*60}")
        
        service_results = {
            'service_name': service_name,
            'layers': {},
            'has_data': False,
            'total_features': 0
        }
        
        for layer_id, layer_name in layers.items():
            print(f"\n  Layer {layer_id}: {layer_name}")
            
            try:
                # Query the layer
                layer_data = client.query_point(
                    service_name, 
                    layer_id, 
                    longitude, 
                    latitude
                )
                
                features = layer_data.get('features', [])
                
                layer_results = {
                    'layer_id': layer_id,
                    'layer_name': layer_name,
                    'has_data': len(features) > 0,
                    'feature_count': len(features),
                    'features': features
                }
                
                if layer_results['has_data']:
                    service_results['has_data'] = True
                    service_results['total_features'] += len(features)
                    print(f"    ✅ {len(features)} feature(s) found")
                    
                    # Display key attributes
                    for i, feature in enumerate(features[:2]):
                        attrs = feature.get('attributes', {})
                        print(f"    📋 Feature {i+1} data:")
                        
                        # Display first 5 non-null attributes
                        displayed = 0
                        for key, value in attrs.items():
                            if value is not None and displayed < 5:
                                print(f"      {key}: {value}")
                                displayed += 1
                else:
                    print(f"    ❌ No data found")
                
                service_results['layers'][layer_id] = layer_results
                
            except Exception as e:
                print(f"    ❌ Error querying layer: {e}")
                service_results['layers'][layer_id] = {
                    'layer_id': layer_id,
                    'layer_name': layer_name,
                    'has_data': False,
                    'error': str(e)
                }
        
        # Service summary
        if service_results['has_data']:
            results['summary']['services_with_data'] += 1
            results['summary']['total_features_found'] += service_results['total_features']
            
            print(f"\n  📊 {service_name} Summary:")
            print(f"    Total features: {service_results['total_features']}")
            print(f"    Layers with data: {sum(1 for l in service_results['layers'].values() if l.get('has_data'))}")
        
        results['services'][service_name] = service_results
    
    return results

def save_results_to_file(results: Dict[str, Any], filename: str = None):
    """Save results to a JSON file"""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{results['coordinates'][0]}_{results['coordinates'][1]}".replace('-', 'neg').replace('.', 'p')
        filename = f"query_{coords}_{timestamp}.json"
    
    os.makedirs('logs', exist_ok=True)
    filepath = os.path.join('logs', filename)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filepath}")
    return filepath
```

## 3. Tools.py - LangGraph Tools

```python
#!/usr/bin/env python3
"""
ArcGIS Data Tools for LangGraph Agents

LangGraph tools for querying ArcGIS data and generating maps/reports.
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

# Import your modules
from main import ArcGISDataQuery

# Initialize with your service configuration
SERVICE_CONFIG = {
    'services': {
        'main_service': 'https://your-server.com/arcgis/rest/services/YourService/MapServer',
        'imagery_service': 'https://your-server.com/arcgis/rest/services/Imagery/MapServer'
    },
    'query_layers': {
        'main_service': {
            0: 'Boundaries',
            1: 'Infrastructure',
            2: 'Environmental Data'
        }
    }
}

# Create query instance
query_client = ArcGISDataQuery(SERVICE_CONFIG)

class CoordinateInput(BaseModel):
    """Input schema for coordinate-based queries"""
    longitude: float = Field(description="Longitude coordinate")
    latitude: float = Field(description="Latitude coordinate")
    location_name: Optional[str] = Field(default=None, description="Optional location name")

@tool("query_arcgis_data", args_schema=CoordinateInput)
def query_arcgis_data(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Query comprehensive data from ArcGIS services for specific coordinates.
    
    Returns structured data with all available information from configured layers.
    """
    return query_client.query(longitude, latitude, location_name)

@tool("generate_map_snapshot", args_schema=CoordinateInput)
def generate_map_snapshot(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a map snapshot PDF centered on the given coordinates.
    
    Creates a high-quality PDF map with annotations, legend, and metadata.
    """
    success, message = query_client.generate_map_snapshot(
        longitude, latitude, location_name, map_type="data_overlay"
    )
    
    return {
        "success": success,
        "message": message,
        "location": location_name or f"({longitude}, {latitude})",
        "coordinates": (longitude, latitude)
    }

# Export tools for LangGraph
ARCGIS_TOOLS = [
    query_arcgis_data,
    generate_map_snapshot
]
```

## 4. Key Implementation Details

### 4.1 Map Snapshot Generation Process

1. **Calculate Bounding Box**: Convert buffer distance to degrees based on latitude
2. **Request Map Image**: Use ArcGIS REST API export endpoint
3. **Process Image**: Add annotations, markers, and legend
4. **Generate PDF**: Use matplotlib to create professional PDF output

### 4.2 Service Configuration Structure

```python
SERVICE_CONFIG = {
    'services': {
        'service_name': 'https://server/arcgis/rest/services/ServiceName/MapServer'
    },
    'query_layers': {
        'service_name': {
            layer_id: 'Layer Name'
        }
    },
    'map_types': {
        'type_name': {
            'service': 'service_name',
            'layers': 'layer_ids',
            'title': 'Map Title'
        }
    }
}
```

### 4.3 Error Handling

- Graceful degradation when services are unavailable
- Timeout handling for slow services
- Clear error messages for debugging

### 4.4 Output Formats

- **JSON Logs**: Structured query results with all data
- **PDF Maps**: High-quality maps with annotations
- **PDF Reports**: Formatted reports with data summaries

## 5. Adaptation Checklist

1. **Identify Your Services**:
   - Map service URLs
   - Available layers and their IDs
   - Authentication requirements

2. **Configure Services**:
   - Update SERVICE_CONFIG with your URLs
   - Map layer IDs to meaningful names
   - Define map types for different use cases

3. **Customize Output**:
   - Modify map styling and annotations
   - Adjust report formatting
   - Add service-specific data processing

4. **Test Components**:
   - Test individual service queries
   - Verify map generation
   - Validate report output

5. **Integrate with LangGraph**:
   - Update tool descriptions
   - Add service-specific tools
   - Configure MCP server if needed

## 6. Example Usage

```python
# Initialize with your configuration
query_client = ArcGISDataQuery(SERVICE_CONFIG)

# Query data
results = query_client.query(-122.4194, 37.7749, "San Francisco, CA")

# Generate map
success, filename = query_client.generate_map_snapshot(
    -122.4194, 37.7749, 
    "San Francisco, CA",
    map_type="imagery"
)

# Use with LangGraph agent
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(
    model="google_genai:gemini-2.0-flash-exp",
    tools=ARCGIS_TOOLS
)
```

This modular approach allows you to:
- Easily adapt to different ArcGIS services
- Maintain consistent interfaces
- Generate professional map outputs
- Integrate with AI agents seamlessly 