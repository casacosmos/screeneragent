#!/usr/bin/env python3
"""
Karst Map Generator (using ArcGIS Export Web Map Task)

This module generates a map image (PDF or PNG) showing PRAPEC karst areas (Layer 15)
and specific zones (APE-ZC, ZA from Layer 0) around a given location, using an ArcGIS
Export Web Map Task service for direct static map generation.
"""

import requests
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KarstMapGenerator:
    """Generates maps for karst analysis using ArcGIS Export Web Map Task."""

    def __init__(self, output_directory: str = "maps"):
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)

        # Puerto Rico Planning Board (Junta de Planificación) service for Karst data
        self.karst_data_service_url = "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer"
        self.prapec_layer_id = 15 # PRAPEC (Carso) - overall area
        self.zones_layer_id = 0   # Zona de Amortiguamiento Reglamentada (contains APE-ZC, ZA)

        # Standard Esri public printing service
        self.printing_service_url = "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"
        
        # Base map options (publicly available)
        self.base_map_urls = {
            "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
            "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
            "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer",
            "USA_Topo_Maps": "https://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer"
        }

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'KarstMapGenerator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })

    def _calculate_extent(self, longitude: float, latitude: float, buffer_miles: float) -> Dict[str, Any]:
        """Calculate map extent based on buffer."""
        # Rough conversion: 1 degree latitude ≈ 69 miles
        # Longitude degree varies: 1 degree longitude ≈ 69 * cos(latitude_radians) miles
        import math
        lat_rad = math.radians(latitude)
        buffer_deg_lat = buffer_miles / 69.0
        buffer_deg_lon = buffer_miles / (69.0 * math.cos(lat_rad)) if math.cos(lat_rad) != 0 else buffer_miles / 69.0
        
        return {
            "xmin": longitude - buffer_deg_lon,
            "ymin": latitude - buffer_deg_lat,
            "xmax": longitude + buffer_deg_lon,
            "ymax": latitude + buffer_deg_lat,
            "spatialReference": {"wkid": 4326} # WGS84
        }

    def generate_map_export(
        self,
        longitude: float, 
        latitude: float,
        location_name: Optional[str] = None,
        buffer_miles: float = 1.0,
        base_map_name: str = "World_Topo_Map",
        output_format: str = "PDF", # PDF, PNG32, PNG8, JPG, GIF, EPS, SVG, SVGZ
        layout_template: str = "Letter ANSI A Landscape", # Common templates: MAP_ONLY, Letter ANSI A Landscape/Portrait
        dpi: int = 300,
        output_filename_prefix: str = "karst_map"
    ) -> Optional[str]:
        """Generates and saves the karst map using an Export Web Map Task."""

        if location_name is None:
            location_name = f"Karst Analysis at {latitude:.4f}, {longitude:.4f}"

        print(f"\n🗺️  Generating karst map ({output_format}) for: {location_name}")
        print(f"📍 Coordinates: ({longitude:.6f}, {latitude:.6f})")
        print(f"📏 Buffer: {buffer_miles} miles")

        extent = self._calculate_extent(longitude, latitude, buffer_miles)
        
        # Define operational layers for the Web Map JSON
        operational_layers = []

        # 1. PRAPEC Overall Area (Layer 15)
        operational_layers.append({
            "id": "prapec_overall",
            "title": "PRAPEC Karst Area (Overall)",
            "url": self.karst_data_service_url,
            "visibleLayers": [self.prapec_layer_id],
            "layerType": "ArcGISMapServiceLayer",
            "opacity": 0.4,
            "layerDefinition": { # Optional: define a simple renderer if default is not good
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "type": "esriSFS", "style": "esriSFSSolid",
                            "color": [255, 215, 0, 102], # Gold with alpha (40% opacity)
                            "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [204, 172, 0, 255], "width": 1}
                        }
                    }
                }
            }
        })

        # 2. APE-ZC Zones (from Layer 0)
        operational_layers.append({
            "id": "ape_zc_zones",
            "title": "APE-ZC (Special Karst Zone)",
            "url": self.karst_data_service_url,
            "visibleLayers": [self.zones_layer_id],
            "layerType": "ArcGISMapServiceLayer",
            "opacity": 0.6,
            "layerDefinition": {
                "definitionExpression": "UPPER(CALI_SOBRE) LIKE '%APE-ZC%'",
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "type": "esriSFS", "style": "esriSFSSolid",
                            "color": [255, 0, 0, 153], # Red with alpha (60% opacity)
                            "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [200, 0, 0, 255], "width": 1.5}
                        }
                    }
                }
            }
        })

        # 3. ZA - Buffer Zones (from Layer 0)
        operational_layers.append({
            "id": "za_buffer_zones",
            "title": "ZA (50m Buffer Zone)",
            "url": self.karst_data_service_url,
            "visibleLayers": [self.zones_layer_id],
            "layerType": "ArcGISMapServiceLayer",
            "opacity": 0.5,
            "layerDefinition": {
                "definitionExpression": "UPPER(CALI_SOBRE) LIKE '%ZA%'",
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "type": "esriSFS", "style": "esriSFSSolid",
                            "color": [0, 0, 255, 128], # Blue with alpha (50% opacity)
                            "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [0, 0, 200, 255], "width": 1}
                        }
                    }
                }
            }
        })

        # 4. Location Marker (using Feature Collection)
        operational_layers.append({
            "id": "location_marker",
            "title": "Query Location",
            "featureCollection": {
                "layers": [{
                    "layerDefinition": {
                        "name": "MarkerLayer",
                        "geometryType": "esriGeometryPoint",
                        "drawingInfo": {
                            "renderer": {
                                "type": "simple",
                                "symbol": {
                                    "type": "esriSMS", "style": "esriSMSCircle",
                                    "color": [0, 255, 0, 255], # Bright Green
                                    "size": 12,
                                    "outline": {"type": "esriSLS", "style": "esriSLSSolid", "color": [0,0,0,255], "width": 2}
                                }
                            }
                        }
                    },
                    "featureSet": {
                        "geometryType": "esriGeometryPoint",
                        "features": [{
                            "geometry": {"x": longitude, "y": latitude, "spatialReference": {"wkid": 4326}},
                            "attributes": {"id": 1, "name": "Query Location"}
                        }]
                    }
                }]
            }
        })

        web_map_json_payload = {
            "mapOptions": {
                "extent": extent,
                "spatialReference": {"wkid": 4326},
                "showAttribution": True
            },
            "operationalLayers": operational_layers,
            "baseMap": {
                "baseMapLayers": [
                    {"url": self.base_map_urls.get(base_map_name, self.base_map_urls["World_Topo_Map"])}
                ],
                "title": base_map_name.replace('_', ' ')
            },
            "exportOptions": {
                "outputSize": [1100, 850], # Standard Letter Landscape dimensions in pixels (approx for 96 DPI)
                "dpi": dpi
            },
            "layoutOptions": {
                "titleText": location_name,
                "authorText": "Karst Analysis Map",
                "copyrightText": "Data: PR Junta de Planificación (Reglamentario va2), Basemap: Esri",
                "legendOptions": {"operationalLayers": True}, # Auto-generate legend for all operational layers
                "scaleBarOptions": {"metricUnit": "esriKilometers", "nonMetricUnit": "esriMiles"}
            }
        }
        
        if layout_template == "MAP_ONLY":
            web_map_json_payload["exportOptions"]["outputSize"] = [1024, 768] # Adjust for map_only if needed
            web_map_json_payload.pop("layoutOptions", None)

        export_params = {
            "f": "json",
            "Web_Map_as_JSON": json.dumps(web_map_json_payload),
            "Format": output_format.upper(),
            "Layout_Template": layout_template
        }
        
        # For debugging the Web_Map_as_JSON:
        # print(json.dumps(web_map_json_payload, indent=2))

        try:
            print(f"📤 Submitting map export request to: {self.printing_service_url}")
            response = self.session.post(self.printing_service_url, data=export_params, timeout=120) # Increased timeout
            response.raise_for_status()
            result = response.json()

            if result.get('error'):
                print(f"❌ Service error: {result['error']}")
                return None
            
            result_url = result.get('results', [{}])[0].get('value', {}).get('url')
            if not result_url:
                print(f"❌ No output URL in result: {result}")
                return None

            print(f"✅ Map generated by service. URL: {result_url}")
            map_content_response = self.session.get(result_url, timeout=60)
            map_content_response.raise_for_status()

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_filename_prefix}_{timestamp}.{output_format.lower()}"
            filepath = os.path.join(self.output_directory, filename)

            with open(filepath, 'wb') as f:
                f.write(map_content_response.content)
            print(f"🗺️ Karst map ({output_format}) saved to: {filepath}")
            return filepath

        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"   Response content: {e.response.json()}") # Try to print JSON error from service
                except json.JSONDecodeError:
                    print(f"   Response content (not JSON): {e.response.text[:500]}...")
            return None
        except Exception as e:
            print(f"❌ Error generating map: {e}")
            return None

# Example Usage:
if __name__ == "__main__":
    import math # Required for _calculate_extent helper
    # Test coordinates (e.g., Arecibo area, known for karst)
    test_longitude = -66.7
    test_latitude = 18.4
    output_dir = "karst_maps_output_arcgis"
    
    print(f"Generating karst map for location: ({test_latitude}, {test_longitude}) using ArcGIS Export")
    generator = KarstMapGenerator(output_directory=output_dir)
    
    # Generate PDF
    pdf_map_file = generator.generate_map_export(
        longitude=test_longitude, 
        latitude=test_latitude, 
        location_name="Arecibo Karst Area (PDF)",
        buffer_miles=1.5,
        output_format="PDF",
        layout_template="Letter ANSI A Landscape"
    )
    if pdf_map_file:
        print(f"PDF Map successfully generated: {pdf_map_file}")
    else:
        print("PDF Map generation failed.")

    # Generate PNG
    png_map_file = generator.generate_map_export(
        longitude=test_longitude, 
        latitude=test_latitude, 
        location_name="Arecibo Karst Area (PNG)",
        buffer_miles=0.75,
        output_format="PNG32",
        layout_template="MAP_ONLY"
    )
    if png_map_file:
        print(f"PNG Map successfully generated: {png_map_file}")
    else:
        print("PNG Map generation failed.")

    # Test coordinates likely outside direct karst but near buffer zones
    test_longitude_2 = -66.15 # Near San Juan / Catano
    test_latitude_2 = 18.45
    print(f"\nGenerating karst map for location: ({test_latitude_2}, {test_longitude_2}) using ArcGIS Export")
    generator2 = KarstMapGenerator(output_directory=output_dir)
    pdf_map_file_2 = generator2.generate_map_export(
        longitude=test_longitude_2, 
        latitude=test_latitude_2, 
        location_name="San Juan Nearby Karst (PDF)",
        buffer_miles=2.0,
        output_format="PDF"
    )
    if pdf_map_file_2:
        print(f"PDF Map successfully generated: {pdf_map_file_2}")
    else:
        print("PDF Map generation failed.") 