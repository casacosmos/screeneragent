#!/usr/bin/env python3
"""
FEMA ABFE (Advisory Base Flood Elevation) Client

Client for querying ABFE data and generating map snapshots showing
Advisory Base Flood Elevation information.
"""

import requests
import json
import time
import math
import os
import sys
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime



@dataclass
class ABFEData:
    """Data class for ABFE information"""
    location: str
    coordinates: tuple
    abfe_value: Optional[float] = None
    elevation_unit: str = "feet"
    source: str = "FEMA ABFE"
    effective_date: Optional[str] = None


@dataclass
class ABFEMapRequest:
    """Data class for ABFE map generation request"""
    longitude: float
    latitude: float
    location_name: Optional[str] = None
    map_format: str = "PDF"  # PDF, PNG, JPEG
    map_size: tuple = (792, 612)  # Letter size
    dpi: int = 300


class FEMAABFEClient:
    """
    Client for querying FEMA ABFE data and generating map snapshots
    """
    
    def __init__(self):
        self.abfe_service_url = "https://hazards.geoplatform.gov/server/rest/services/Region2/Advisory_Base_Flood_Elevation__ABFE__Data/MapServer"
        self.printing_service_url = "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ABFE-Client/1.0'
        })
        
        # Cache for service metadata
        self._service_info = None
        self._layers_info = None
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get ABFE service information and layer details"""
        
        if self._service_info is None:
            try:
                response = self.session.get(f"{self.abfe_service_url}?f=json", timeout=30)
                response.raise_for_status()
                self._service_info = response.json()
                
                # Also get layers information
                self._layers_info = self._service_info.get('layers', [])
                
            except Exception as e:
                print(f"⚠️  Error getting ABFE service info: {e}")
                self._service_info = {}
                self._layers_info = []
        
        return self._service_info
    
    def get_layers_info(self) -> List[Dict[str, Any]]:
        """Get information about available ABFE layers"""
        
        if self._layers_info is None:
            self.get_service_info()
        
        return self._layers_info or []
    
    def query_abfe_at_point(self, longitude: float, latitude: float) -> Dict[str, Any]:
        """
        Query ABFE data at a specific point
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            
        Returns:
            Dictionary with ABFE data and layer information
        """
        
        print(f"🌊 Querying ABFE data for coordinates: {latitude}, {longitude}")
        
        # Get service and layer information
        service_info = self.get_service_info()
        layers_info = self.get_layers_info()
        
        results = {
            'coordinates': (longitude, latitude),
            'service_info': {
                'service_name': service_info.get('serviceDescription', 'ABFE Data'),
                'service_url': self.abfe_service_url,
                'layers_count': len(layers_info)
            },
            'layers': {},
            'abfe_data_found': False,
            'summary': {
                'total_layers_queried': 0,
                'layers_with_data': 0,
                'abfe_values': []
            }
        }
        
        print(f"📊 Found {len(layers_info)} layers in ABFE service")
        
        # Query each layer for data
        for layer in layers_info:
            layer_id = layer.get('id')
            layer_name = layer.get('name', f'Layer {layer_id}')
            
            print(f"\n  🔍 Querying Layer {layer_id}: {layer_name}")
            
            layer_data = self._query_layer_at_point(layer_id, longitude, latitude)
            results['layers'][layer_id] = {
                'layer_name': layer_name,
                'layer_id': layer_id,
                'geometry_type': layer.get('geometryType'),
                'data': layer_data
            }
            
            results['summary']['total_layers_queried'] += 1
            
            if layer_data.get('has_data'):
                results['summary']['layers_with_data'] += 1
                results['abfe_data_found'] = True
                
                # Extract ABFE values
                for feature in layer_data.get('features', []):
                    attributes = feature.get('attributes', {})
                    
                    # Look for ABFE-related fields
                    abfe_fields = ['ABFE', 'ADVISORY_BFE', 'ADV_BFE', 'ELEVATION', 'BFE']
                    for field in abfe_fields:
                        if field in attributes and attributes[field] is not None:
                            try:
                                abfe_value = float(attributes[field])
                                results['summary']['abfe_values'].append({
                                    'layer': layer_name,
                                    'field': field,
                                    'value': abfe_value,
                                    'attributes': attributes
                                })
                                print(f"    ✅ Found ABFE value: {abfe_value} feet ({field})")
                            except (ValueError, TypeError):
                                continue
                
                print(f"    ✅ {layer_data['feature_count']} feature(s) found")
            else:
                print(f"    ❌ No data found")
        
        return results
    
    def _query_layer_at_point(self, layer_id: int, longitude: float, latitude: float) -> Dict[str, Any]:
        """Query a specific ABFE layer at given coordinates"""
        
        try:
            # Create point geometry
            geometry = {
                'x': longitude,
                'y': latitude,
                'spatialReference': {'wkid': 4326}
            }
            
            query_params = {
                'geometry': json.dumps(geometry),
                'geometryType': 'esriGeometryPoint',
                'spatialRel': 'esriSpatialRelIntersects',
                'outFields': '*',
                'f': 'json',
                'returnGeometry': 'true'
            }
            
            response = self.session.get(f"{self.abfe_service_url}/{layer_id}/query", params=query_params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            return {
                'layer_id': layer_id,
                'has_data': len(features) > 0,
                'feature_count': len(features),
                'features': features,
                'query_successful': True
            }
            
        except Exception as e:
            return {
                'layer_id': layer_id,
                'has_data': False,
                'feature_count': 0,
                'features': [],
                'query_successful': False,
                'error': str(e)
            }
    
    def generate_abfe_map(self, longitude: float, latitude: float, 
                         location_name: str = None,
                         map_format: str = "PDF",
                         buffer_miles: float = 0.5,
                         map_scale: int = None,
                         visible_layers: List[int] = None,
                         layer_opacity: float = 0.8,
                         base_map: str = "World_Topo_Map",
                         dpi: int = 300,
                         output_size: tuple = (792, 612),
                         show_attribution: bool = True,
                         show_point_marker: bool = True,
                         include_legend: bool = True) -> Tuple[bool, str, str]:
        """
        Generate a map snapshot showing ABFE data for the given location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            map_format: Output format (PDF, PNG, JPEG)
            buffer_miles: Buffer around point in miles for map extent
            map_scale: Specific map scale (e.g., 12000, 24000). If None, uses buffer_miles
            visible_layers: List of layer IDs to show (None = all layers)
            layer_opacity: ABFE layer transparency (0.0-1.0)
            base_map: Base map style ('World_Topo_Map', 'World_Street_Map', 'World_Imagery', 'NatGeo_World_Map')
            dpi: Map resolution (96, 150, 300)
            output_size: Output size as (width, height) tuple
            show_attribution: Whether to show map attribution
            show_point_marker: Whether to show query location marker
            include_legend: Whether to include legend and other map elements
            
        Returns:
            Tuple of (success, map_url_or_error, job_info)
        """
        
        try:
            print(f"🗺️  Generating ABFE map for coordinates: {latitude}, {longitude}")
            print(f"📊 Map parameters: Scale={map_scale or 'auto'}, Buffer={buffer_miles}mi, DPI={dpi}")
            
            # Calculate map extent
            if map_scale:
                # Use specific scale - calculate extent based on output size and scale
                # Scale formula: 1 inch on map = scale feet on ground
                # For Web Mercator, 1 degree ≈ 364,000 feet at equator
                map_width_feet = (output_size[0] / dpi) * map_scale
                map_height_feet = (output_size[1] / dpi) * map_scale
                
                # Convert to degrees (approximate)
                width_degrees = map_width_feet / 364000
                height_degrees = map_height_feet / 364000
                
                extent = {
                    "xmin": longitude - width_degrees / 2,
                    "ymin": latitude - height_degrees / 2,
                    "xmax": longitude + width_degrees / 2,
                    "ymax": latitude + height_degrees / 2,
                    "spatialReference": {"wkid": 4326}
                }
            else:
                # Use buffer distance
                # Rough conversion: 1 degree ≈ 69 miles
                buffer_degrees = buffer_miles / 69.0
                
                extent = {
                    "xmin": longitude - buffer_degrees,
                    "ymin": latitude - buffer_degrees,
                    "xmax": longitude + buffer_degrees,
                    "ymax": latitude + buffer_degrees,
                    "spatialReference": {"wkid": 4326}
                }
            
            # Base map URLs
            base_map_urls = {
                "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
                "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer",
                "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
                "NatGeo_World_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer"
            }
            
            base_map_url = base_map_urls.get(base_map, base_map_urls["World_Topo_Map"])
            
            # Create ABFE operational layer
            abfe_layer = {
                "url": self.abfe_service_url,
                "title": "ABFE Data",
                "opacity": layer_opacity,
                "visibility": True,
                "layerType": "ArcGISMapServiceLayer"
            }
            
            # Add visible layers specification if provided
            if visible_layers is not None:
                abfe_layer["visibleLayers"] = visible_layers
                print(f"🎨 Showing layers: {visible_layers}")
            
            # Create web map specification
            web_map = {
                "mapOptions": {
                    "extent": extent,
                    "spatialReference": {"wkid": 4326},
                    "showAttribution": show_attribution
                },
                "operationalLayers": [abfe_layer],
                "baseMap": {
                    "baseMapLayers": [
                        {
                            "url": base_map_url,
                            "title": base_map.replace('_', ' '),
                            "opacity": 1,
                            "visibility": True,
                            "layerType": "ArcGISMapServiceLayer"
                        }
                    ],
                    "title": base_map.replace('_', ' ')
                },
                "exportOptions": {
                    "outputSize": list(output_size),
                    "dpi": dpi
                },
                "layoutOptions": {
                    "titleText": f"ABFE Map - {location_name or 'Location'}",
                    "authorText": "FEMA ABFE Data",
                    "copyrightText": "Source: FEMA Advisory Base Flood Elevation Data",
                    "scalebarUnit": "Miles",
                    "legendLayers": [abfe_layer] if include_legend else []
                },
                "version": "1.6.0"
            }
            
            # Add point marker for the query location
            if show_point_marker and location_name:
                point_marker = {
                    "featureCollection": {
                        "layers": [
                            {
                                "featureSet": {
                                    "features": [
                                        {
                                            "geometry": {
                                                "x": longitude,
                                                "y": latitude,
                                                "spatialReference": {"wkid": 4326}
                                            },
                                            "attributes": {
                                                "name": location_name
                                            },
                                            "symbol": {
                                                "type": "esriSMS",
                                                "style": "esriSMSCircle",
                                                "color": [255, 0, 0, 255],  # Red
                                                "size": 6,  # Smaller marker
                                                "outline": {
                                                    "color": [255, 255, 255, 255],  # White outline
                                                    "width": 1  # Thinner outline
                                                }
                                            }
                                        }
                                    ],
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
                            }
                        ]
                    },
                    "title": "Query Location",
                    "opacity": 1,
                    "visibility": True
                }
                web_map["operationalLayers"].append(point_marker)
                print(f"📍 Added location marker for: {location_name}")
            
            # Map format conversion for ArcGIS service
            format_mapping = {
                "PDF": "PDF",
                "PNG": "PNG32",
                "JPEG": "JPG",
                "JPG": "JPG"
            }
            
            arcgis_format = format_mapping.get(map_format.upper(), "PDF")
            
            # Always use layout template with legend and map elements
            # Available templates: "A4 Portrait", "A4 Landscape", "Letter ANSI A Portrait", 
            # "Letter ANSI A Landscape", "Tabloid ANSI B Portrait", "Tabloid ANSI B Landscape",
            # "Letter ANSI A Portrait", "Letter ANSI A Landscape", "MAP_ONLY"
            if include_legend:
                # Use Letter ANSI A Portrait for better legend space and US standard
                layout_template = "Letter ANSI A Portrait"  # Full layout with legend, scale bar, north arrow, title
            else:
                layout_template = "MAP_ONLY"     # Map only, no legend or decorations
            
            # Export parameters
            export_params = {
                "f": "json",
                "Web_Map_as_JSON": json.dumps(web_map),
                "Format": arcgis_format,
                "Layout_Template": layout_template
            }
            
            print(f"📋 Using layout: {layout_template}")
            print(f"🎨 Legend included: {include_legend}")
            print(f"📐 Output format: {arcgis_format}")
            print(f"📏 Output size: {output_size[0]}x{output_size[1]} at {dpi} DPI")
            
            print(f"📤 Submitting map export request...")
            
            # Submit the export request
            response = self.session.post(self.printing_service_url, data=export_params, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if 'results' in result and len(result['results']) > 0:
                output_result = result['results'][0]
                if 'value' in output_result:
                    map_url = output_result['value'].get('url')
                    if map_url:
                        print(f"✅ ABFE map generated successfully!")
                        print(f"📄 Map URL: {map_url}")
                        return True, map_url, json.dumps(result)
            
            return False, f"Map generation failed: {result}", json.dumps(result)
            
        except Exception as e:
            return False, f"Error generating ABFE map: {str(e)}", None
    
    def download_abfe_map(self, download_url: str, filename: str = None, use_output_manager: bool = True) -> bool:
        """
        Download the ABFE map from the provided URL
        
        Args:
            download_url: URL to download the map from
            filename: Local filename to save to (optional) - if not provided, will auto-generate
            use_output_manager: Whether to use the output directory manager (default: True)
            
        Returns:
            True if download successful, False otherwise
        """
        
        try:
            if use_output_manager:
                # Use output directory manager to get proper file path
                output_manager = get_output_manager()
                
                if not filename:
                    # Generate filename from timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"abfe_map_{timestamp}.pdf"
                
                # Get file path in the reports subdirectory
                file_path = output_manager.get_file_path(filename, "reports")
                print(f"📁 Saving ABFE map to project directory: {file_path}")
                
            else:
                # Legacy behavior - save to current directory or specified path
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"abfe_map_{timestamp}.pdf"
                file_path = filename
                print(f"💾 Saving ABFE map to: {file_path}")
            
            response = self.session.get(download_url, timeout=60)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ ABFE map downloaded successfully: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading ABFE map: {e}")
            return False
    
    def generate_and_download_abfe_map(self, longitude: float, latitude: float,
                                      location_name: str = None,
                                      filename: str = None,
                                      map_format: str = "PDF",
                                      use_output_manager: bool = True) -> Tuple[bool, str]:
        """
        Generate and download an ABFE map in one operation
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            filename: Local filename to save to (optional)
            map_format: Output format (PDF, PNG, JPEG)
            use_output_manager: Whether to use the output directory manager (default: True)
            
        Returns:
            Tuple of (success, message)
        """
        
        print(f"🗺️ Generating ABFE map for coordinates: {latitude}, {longitude}")
        
        # Generate the map with full legend
        success, result, job_info = self.generate_abfe_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            map_format=map_format,
            include_legend=True  # Always include legend for complete maps
        )
        
        if not success:
            return False, f"Failed to generate ABFE map: {result}"
        
        if not result:
            return False, "No download URL received"
        
        print(f"✅ ABFE map generated successfully.")
        print(f"🔗 Download URL: {result}")
        
        # Download the file using output directory manager
        if self.download_abfe_map(result, filename, use_output_manager):
            return True, f"ABFE map generated and downloaded successfully"
        else:
            return False, "Map generated but download failed"
    
    def get_abfe_summary(self, longitude: float, latitude: float, location_name: str = None) -> Dict[str, Any]:
        """
        Get a comprehensive ABFE summary for a location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional name for the location
            
        Returns:
            Dictionary with ABFE summary information
        """
        
        # Query ABFE data
        abfe_results = self.query_abfe_at_point(longitude, latitude)
        
        summary = {
            'location': location_name or f"({longitude}, {latitude})",
            'coordinates': (longitude, latitude),
            'query_time': datetime.now().isoformat(),
            'abfe_data_available': abfe_results['abfe_data_found'],
            'service_info': abfe_results['service_info'],
            'layers_summary': {
                'total_layers': abfe_results['summary']['total_layers_queried'],
                'layers_with_data': abfe_results['summary']['layers_with_data'],
                'abfe_values_found': len(abfe_results['summary']['abfe_values'])
            },
            'abfe_values': abfe_results['summary']['abfe_values'],
            'recommendations': []
        }
        
        # Add recommendations based on findings
        if summary['abfe_data_available']:
            summary['recommendations'].extend([
                "ABFE (Advisory Base Flood Elevation) data found for this location",
                "ABFE values are advisory and may differ from regulatory BFE",
                "Use ABFE data for planning and risk assessment purposes",
                "Verify with local authorities for regulatory requirements"
            ])
        else:
            summary['recommendations'].extend([
                "No ABFE data found for this specific location",
                "ABFE data may be available for nearby areas",
                "Check FEMA's current effective flood maps for regulatory BFE",
                "Consider consulting with local floodplain administrators"
            ])
        
        return summary


def main():
    """Example usage of the ABFE client with different parameters"""
    
    client = FEMAABFEClient()
    
    # Example coordinates (Cataño, Puerto Rico)
    longitude = -66.1689712
    latitude = 18.4282314
    location_name = "Cataño, Puerto Rico"
    
    print("=== FEMA ABFE Data Query and Map Generation Examples ===")
    print(f"Location: {location_name}")
    print(f"Coordinates: {latitude}, {longitude}")
    
    # Get ABFE summary
    summary = client.get_abfe_summary(longitude, latitude, location_name)
    
    print(f"\n📊 ABFE Summary:")
    print(f"   ABFE data available: {summary['abfe_data_available']}")
    print(f"   Total layers: {summary['layers_summary']['total_layers']}")
    print(f"   Layers with data: {summary['layers_summary']['layers_with_data']}")
    print(f"   ABFE values found: {summary['layers_summary']['abfe_values_found']}")
    
    if summary['abfe_values']:
        print(f"\n🌊 ABFE Values:")
        for abfe_info in summary['abfe_values']:
            print(f"   Layer: {abfe_info['layer']}")
            print(f"   Value: {abfe_info['value']} feet")
            print(f"   Field: {abfe_info['field']}")
    
    # Example 1: Default map
    print(f"\n🗺️  Example 1: Default ABFE map...")
    success, message = client.generate_and_download_abfe_map(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        filename="catano_abfe_default.pdf"
    )
    
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    # Example 2: High-detail map with specific scale
    print(f"\n🗺️  Example 2: High-detail map (1:12,000 scale)...")
    success, result, job_id = client.generate_abfe_map(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        map_scale=12000,  # 1:12,000 scale
        visible_layers=[5, 6],  # Only Zone/BFE Boundary and Flood Hazard Area
        layer_opacity=0.7,
        base_map="World_Imagery",
        dpi=300
    )
    
    if success:
        print(f"✅ High-detail map generated!")
        print(f"📄 URL: {result}")
        if client.download_abfe_map(result, "catano_abfe_detailed.pdf"):
            print(f"✅ Downloaded as: catano_abfe_detailed.pdf")
    else:
        print(f"❌ Failed: {result}")
    
    # Example 3: Wide-area overview
    print(f"\n🗺️  Example 3: Wide-area overview...")
    success, result, job_id = client.generate_abfe_map(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        buffer_miles=2.0,  # 2-mile radius
        base_map="World_Street_Map",
        show_attribution=True,
        show_point_marker=True
    )
    
    if success:
        print(f"✅ Wide-area map generated!")
        if client.download_abfe_map(result, "catano_abfe_overview.pdf"):
            print(f"✅ Downloaded as: catano_abfe_overview.pdf")
    else:
        print(f"❌ Failed: {result}")
    
    print(f"\n📋 Parameter Examples:")
    print(f"   • map_scale: 12000 (detailed), 24000 (moderate), 50000 (regional)")
    print(f"   • buffer_miles: 0.1 (tight), 0.5 (default), 2.0 (wide)")
    print(f"   • visible_layers: [5,6] (boundaries only), [1,5,6] (with elevations)")
    print(f"   • base_map: 'World_Topo_Map', 'World_Imagery', 'World_Street_Map'")
    print(f"   • layer_opacity: 0.5 (transparent), 0.8 (default), 1.0 (opaque)")
    print(f"   • dpi: 150 (web), 300 (print), 600 (high-res)")
    print(f"   • output_size: (792,612) letter, (1224,792) tabloid, (2448,1584) large")


if __name__ == "__main__":
    main() 