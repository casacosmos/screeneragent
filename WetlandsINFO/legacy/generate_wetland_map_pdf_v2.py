#!/usr/bin/env python3
"""
Generate Wetland Map PDF - Version 2

This version queries wetlands in the area first and adds them as graphics layers
to ensure they are properly displayed on the map.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WetlandMapGeneratorV2:
    """Generate professional wetland map PDFs with explicit wetland features"""
    
    def __init__(self):
        # Service URLs
        self.export_webmap_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map"
        self.wetlands_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer"
        self.world_imagery_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WetlandMapGenerator/2.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_wetland_map_pdf(self, 
                                longitude: float, 
                                latitude: float,
                                location_name: str = None,
                                buffer_miles: float = 0.5,
                                output_filename: str = None) -> str:
        """
        Generate a wetland map PDF for a specific location
        """
        
        if location_name is None:
            location_name = f"Wetland Map at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating wetland map PDF for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"📏 Buffer: {buffer_miles} miles")
        
        # First, query wetlands in the area
        print("\n🔍 Querying wetlands in the area...")
        wetlands = self._query_wetlands_in_area(longitude, latitude, buffer_miles)
        print(f"✅ Found {len(wetlands)} wetland features")
        
        # Create the Web Map JSON with wetland features
        web_map_json = self._create_web_map_json_with_features(
            longitude, latitude, location_name, buffer_miles, wetlands
        )
        
        # Create the export parameters
        export_params = self._create_export_params(web_map_json)
        
        # Submit the export job
        print("\n📤 Submitting map export request...")
        result = self._submit_export_job(export_params)
        
        if not result:
            logger.error("Failed to submit export job")
            return None
        
        # Handle synchronous or asynchronous result
        if 'results' in result:
            print("✅ Map generated")
            result_url = self._extract_result_url(result)
        else:
            job_id = result.get('jobId')
            if not job_id:
                logger.error("No job ID returned")
                return None
                
            print(f"✅ Job submitted: {job_id}")
            print("\n⏳ Processing map...")
            result_url = self._monitor_job_status(job_id)
        
        if not result_url:
            logger.error("Failed to get result URL")
            return None
        
        # Download the PDF
        print("\n📥 Downloading PDF...")
        pdf_path = self._download_pdf(result_url, output_filename)
        
        if pdf_path:
            print(f"\n✅ Map PDF generated successfully: {pdf_path}")
        
        return pdf_path
    
    def _query_wetlands_in_area(self, longitude: float, latitude: float, 
                                buffer_miles: float) -> List[Dict[str, Any]]:
        """Query wetlands within the buffer area"""
        
        # Convert buffer to degrees (rough approximation)
        buffer_degrees = buffer_miles / 69.0
        
        # Create envelope geometry
        envelope = {
            "xmin": longitude - buffer_degrees,
            "ymin": latitude - buffer_degrees,
            "xmax": longitude + buffer_degrees,
            "ymax": latitude + buffer_degrees,
            "spatialReference": {"wkid": 4326}
        }
        
        # Query parameters
        params = {
            "geometry": json.dumps(envelope),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json"
        }
        
        try:
            # Query layer 0 (Wetlands)
            response = self.session.get(f"{self.wetlands_url}/0/query", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('features', [])
            
        except Exception as e:
            logger.error(f"Failed to query wetlands: {e}")
            return []
    
    def _create_web_map_json_with_features(self, longitude: float, latitude: float, 
                                          location_name: str, buffer_miles: float,
                                          wetland_features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create Web Map JSON with wetland features as graphics"""
        
        # Calculate extent
        buffer_meters = buffer_miles * 1609.34
        lat_buffer = buffer_meters / 111111
        lon_buffer = buffer_meters / (111111 * abs(math.cos(math.radians(latitude))))
        
        extent = {
            "xmin": longitude - lon_buffer,
            "ymin": latitude - lat_buffer,
            "xmax": longitude + lon_buffer,
            "ymax": latitude + lat_buffer,
            "spatialReference": {"wkid": 4326}
        }
        
        extent_mercator = self._convert_extent_to_web_mercator(extent)
        point_mercator = self._convert_point_to_web_mercator(longitude, latitude)
        
        # Process wetland features
        wetland_graphics = []
        wetland_types = {}
        
        for feature in wetland_features:
            geometry = feature.get('geometry', {})
            attributes = feature.get('attributes', {})
            
            # Get wetland type for symbology
            wetland_type = attributes.get('WETLAND_TYPE', 'Unknown')
            wetland_code = attributes.get('ATTRIBUTE', '')
            
            # Count wetland types for legend
            if wetland_type not in wetland_types:
                wetland_types[wetland_type] = 0
            wetland_types[wetland_type] += 1
            
            # Convert geometry to Web Mercator if needed
            if geometry.get('spatialReference', {}).get('wkid') == 4326:
                geometry = self._convert_geometry_to_web_mercator(geometry)
            
            # Create graphic with appropriate symbol
            graphic = {
                "geometry": geometry,
                "attributes": {
                    "OBJECTID": attributes.get('OBJECTID', 0),
                    "WETLAND_TYPE": wetland_type,
                    "ATTRIBUTE": wetland_code,
                    "ACRES": attributes.get('ACRES', 0)
                },
                "symbol": self._get_wetland_symbol(wetland_type)
            }
            
            wetland_graphics.append(graphic)
        
        # Create the web map
        web_map = {
            "mapOptions": {
                "showAttribution": True,
                "extent": extent_mercator,
                "spatialReference": {"wkid": 102100},
                "scale": 24000
            },
            "operationalLayers": [
                {
                    "id": "wetlandGraphics",
                    "title": "Wetlands",
                    "opacity": 0.75,
                    "minScale": 0,
                    "maxScale": 0,
                    "featureCollection": {
                        "layers": [
                            {
                                "layerDefinition": {
                                    "name": "Wetlands",
                                    "geometryType": "esriGeometryPolygon",
                                    "spatialReference": {"wkid": 102100},
                                    "fields": [
                                        {
                                            "name": "OBJECTID",
                                            "type": "esriFieldTypeOID",
                                            "alias": "OBJECTID"
                                        },
                                        {
                                            "name": "WETLAND_TYPE",
                                            "type": "esriFieldTypeString",
                                            "alias": "Wetland Type",
                                            "length": 50
                                        },
                                        {
                                            "name": "ATTRIBUTE",
                                            "type": "esriFieldTypeString",
                                            "alias": "NWI Code",
                                            "length": 15
                                        },
                                        {
                                            "name": "ACRES",
                                            "type": "esriFieldTypeDouble",
                                            "alias": "Acres"
                                        }
                                    ]
                                },
                                "featureSet": {
                                    "geometryType": "esriGeometryPolygon",
                                    "spatialReference": {"wkid": 102100},
                                    "features": wetland_graphics
                                }
                            }
                        ]
                    }
                },
                {
                    "id": "locationGraphics",
                    "title": "Location",
                    "opacity": 1,
                    "minScale": 0,
                    "maxScale": 0,
                    "featureCollection": {
                        "layers": [
                            {
                                "layerDefinition": {
                                    "name": "Location Point",
                                    "geometryType": "esriGeometryPoint",
                                    "spatialReference": {"wkid": 102100},
                                    "fields": [
                                        {
                                            "name": "OBJECTID",
                                            "type": "esriFieldTypeOID",
                                            "alias": "OBJECTID"
                                        },
                                        {
                                            "name": "Name",
                                            "type": "esriFieldTypeString",
                                            "alias": "Name",
                                            "length": 255
                                        }
                                    ]
                                },
                                "featureSet": {
                                    "geometryType": "esriGeometryPoint",
                                    "spatialReference": {"wkid": 102100},
                                    "features": [
                                        {
                                            "geometry": {
                                                "x": point_mercator["x"],
                                                "y": point_mercator["y"],
                                                "spatialReference": {"wkid": 102100}
                                            },
                                            "attributes": {
                                                "OBJECTID": 1,
                                                "Name": location_name
                                            },
                                            "symbol": {
                                                "type": "esriSMS",
                                                "style": "esriSMSCircle",
                                                "color": [255, 0, 0, 255],
                                                "size": 12,
                                                "outline": {
                                                    "color": [255, 255, 255, 255],
                                                    "width": 2
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ],
            "baseMap": {
                "baseMapLayers": [
                    {
                        "id": "World_Imagery",
                        "opacity": 1,
                        "visibility": True,
                        "url": self.world_imagery_url
                    }
                ],
                "title": "World Imagery"
            },
            "exportOptions": {
                "outputSize": [800, 1100],
                "dpi": 300
            },
            "layoutOptions": {
                "titleText": location_name,
                "authorText": "WetlandsINFO System",
                "copyrightText": f"USFWS NWI | Generated {datetime.now().strftime('%Y-%m-%d')}",
                "scaleBarOptions": {
                    "metricUnit": "esriKilometers",
                    "metricLabel": "km",
                    "nonMetricUnit": "esriMiles",
                    "nonMetricLabel": "mi"
                },
                "legendOptions": {
                    "operationalLayers": [
                        {
                            "id": "wetlandGraphics",
                            "subLayerIds": [0]
                        }
                    ]
                },
                "customTextElements": [
                    {
                        "text": f"Total Wetlands: {len(wetland_features)}"
                    }
                ]
            }
        }
        
        return web_map
    
    def _get_wetland_symbol(self, wetland_type: str) -> Dict[str, Any]:
        """Get appropriate symbol for wetland type"""
        
        # Define colors for different wetland types
        wetland_colors = {
            "Estuarine and Marine Deepwater": [0, 0, 139, 180],      # Dark blue
            "Estuarine and Marine Wetland": [0, 191, 255, 180],      # Deep sky blue
            "Freshwater Emergent Wetland": [127, 255, 0, 180],       # Chartreuse
            "Freshwater Forested/Shrub Wetland": [34, 139, 34, 180], # Forest green
            "Freshwater Pond": [30, 144, 255, 180],                  # Dodger blue
            "Lake": [0, 0, 255, 180],                                # Blue
            "Riverine": [64, 224, 208, 180],                         # Turquoise
            "Other": [128, 128, 128, 180]                            # Gray
        }
        
        # Get color for this wetland type
        color = wetland_colors.get(wetland_type, wetland_colors["Other"])
        
        return {
            "type": "esriSFS",
            "style": "esriSFSSolid",
            "color": color,
            "outline": {
                "type": "esriSLS",
                "style": "esriSLSSolid",
                "color": [0, 0, 0, 255],
                "width": 0.5
            }
        }
    
    def _convert_geometry_to_web_mercator(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Convert geometry from WGS84 to Web Mercator"""
        
        if 'rings' in geometry:
            # Polygon geometry
            mercator_rings = []
            for ring in geometry['rings']:
                mercator_ring = []
                for coord in ring:
                    x = coord[0] * 20037508.34 / 180
                    y = math.log(math.tan((90 + coord[1]) * math.pi / 360)) / (math.pi / 180)
                    y = y * 20037508.34 / 180
                    mercator_ring.append([x, y])
                mercator_rings.append(mercator_ring)
            
            return {
                "rings": mercator_rings,
                "spatialReference": {"wkid": 102100}
            }
        
        return geometry
    
    def _convert_extent_to_web_mercator(self, extent_wgs84: Dict[str, Any]) -> Dict[str, Any]:
        """Convert extent from WGS84 to Web Mercator"""
        
        def lon_to_x(lon):
            return lon * 20037508.34 / 180
        
        def lat_to_y(lat):
            y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
            return y * 20037508.34 / 180
        
        return {
            "xmin": lon_to_x(extent_wgs84["xmin"]),
            "ymin": lat_to_y(extent_wgs84["ymin"]),
            "xmax": lon_to_x(extent_wgs84["xmax"]),
            "ymax": lat_to_y(extent_wgs84["ymax"]),
            "spatialReference": {"wkid": 102100}
        }
    
    def _convert_point_to_web_mercator(self, longitude: float, latitude: float) -> Dict[str, float]:
        """Convert a point from WGS84 to Web Mercator"""
        
        x = longitude * 20037508.34 / 180
        y = math.log(math.tan((90 + latitude) * math.pi / 360)) / (math.pi / 180)
        y = y * 20037508.34 / 180
        
        return {"x": x, "y": y}
    
    def _create_export_params(self, web_map_json: Dict[str, Any]) -> Dict[str, Any]:
        """Create parameters for the ExportWebMap service"""
        
        layout_template = "Letter ANSI A Landscape"
        
        export_params = {
            "Web_Map_as_JSON": json.dumps(web_map_json),
            "Format": "PDF",
            "Layout_Template": layout_template,
            "f": "json"
        }
        
        return export_params
    
    def _submit_export_job(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Submit the export job to the service"""
        
        try:
            execute_url = f"{self.export_webmap_url}/execute"
            response = self.session.post(execute_url, data=params, timeout=60)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to submit export job: {e}")
            return None
    
    def _extract_result_url(self, result: Dict[str, Any]) -> Optional[str]:
        """Extract result URL from synchronous result"""
        
        results_list = result.get('results', [])
        
        for param in results_list:
            if param.get('paramName') == 'Output_File':
                return param.get('value', {}).get('url')
        
        return None
    
    def _monitor_job_status(self, job_id: str, timeout: int = 120) -> Optional[str]:
        """Monitor job status and return result URL when complete"""
        
        status_url = f"{self.export_webmap_url}/jobs/{job_id}"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(f"{status_url}?f=json", timeout=10)
                response.raise_for_status()
                
                job_info = response.json()
                status = job_info.get('jobStatus', '')
                
                if status == 'esriJobSucceeded':
                    results = job_info.get('results', {})
                    output_file = results.get('Output_File', {})
                    param_url = output_file.get('paramUrl')
                    
                    if param_url:
                        if param_url.startswith('http'):
                            return param_url
                        else:
                            base_url = self.export_webmap_url.rsplit('/', 1)[0]
                            return f"{base_url}/jobs/{job_id}/{param_url}"
                    
                elif status in ['esriJobFailed', 'esriJobCancelled']:
                    return None
                
                print(f"  Status: {status}")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(2)
        
        return None
    
    def _download_pdf(self, result_url: str, output_filename: str = None) -> Optional[str]:
        """Download the PDF from the result URL"""
        
        try:
            pdf_url = result_url if result_url.endswith('.pdf') else f"{result_url}?f=pdf"
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"wetland_map_v2_{timestamp}.pdf"
            
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            return None


def main():
    """Main function for command line usage"""
    
    print("🗺️  Wetland Map PDF Generator V2")
    print("="*50)
    
    if len(sys.argv) >= 3:
        try:
            longitude = float(sys.argv[1])
            latitude = float(sys.argv[2])
            location_name = sys.argv[3] if len(sys.argv) > 3 else None
            buffer_miles = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        except ValueError:
            print("❌ Invalid arguments")
            print("Usage: python generate_wetland_map_pdf_v2.py <longitude> <latitude> [location_name] [buffer_miles]")
            return
    else:
        try:
            print("\nEnter coordinates for the wetland map:")
            longitude = float(input("Longitude: ") or "-66.196")
            latitude = float(input("Latitude: ") or "18.452")
            location_name = input("Location name (optional): ").strip() or None
            buffer_miles = float(input("Buffer radius in miles (default 0.5): ") or "0.5")
        except ValueError:
            print("❌ Invalid input")
            return
    
    generator = WetlandMapGeneratorV2()
    pdf_path = generator.generate_wetland_map_pdf(
        longitude, latitude, location_name, buffer_miles
    )
    
    if pdf_path:
        print(f"\n✅ Success! Map saved to: {pdf_path}")
    else:
        print("\n❌ Failed to generate map")


if __name__ == "__main__":
    main() 