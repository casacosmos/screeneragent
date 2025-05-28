#!/usr/bin/env python3
"""
Generate Wetland Map PDF

This script generates professional wetland maps in PDF format using the USFWS ExportWebMap service.
Maps include wetland layers, legend, scale bar, north arrow, and satellite imagery basemap.
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WetlandMapGenerator:
    """Generate professional wetland map PDFs using USFWS services"""
    
    def __init__(self):
        # Service URLs
        self.export_webmap_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map"
        self.wetlands_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer"
        self.world_imagery_url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WetlandMapGenerator/1.0',
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
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name for the map title
            buffer_miles: Buffer radius in miles (default 0.5)
            output_filename: Optional output filename
            
        Returns:
            Path to the generated PDF file
        """
        
        if location_name is None:
            location_name = f"Wetland Map at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating wetland map PDF for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"📏 Buffer: {buffer_miles} miles")
        
        # Create the Web Map JSON specification
        web_map_json = self._create_web_map_json(
            longitude, latitude, location_name, buffer_miles
        )
        
        # Create the export parameters
        export_params = self._create_export_params(web_map_json)
        
        # Submit the export job
        print("\n📤 Submitting map export request...")
        result = self._submit_export_job(export_params)
        
        if not result:
            logger.error("Failed to submit export job")
            return None
        
        # Check if it's a synchronous result or async job
        if 'results' in result:
            # Synchronous execution - get result directly
            print("✅ Map generated (synchronous)")
            
            # Results is a list of output parameters
            results_list = result.get('results', [])
            result_url = None
            
            # Find the Output_File parameter
            for param in results_list:
                if param.get('paramName') == 'Output_File':
                    result_url = param.get('value', {}).get('url')
                    break
            
            if not result_url:
                logger.error("No output URL in synchronous result")
                print(f"🔍 Debug - Results structure: {json.dumps(results_list, indent=2)}")
                return None
        else:
            # Asynchronous execution - monitor job
            job_id = result.get('jobId')
            if not job_id:
                logger.error("No job ID returned")
                return None
                
            print(f"✅ Job submitted: {job_id}")
            print("\n⏳ Processing map...")
            result_url = self._monitor_job_status(job_id)
            
            if not result_url:
                logger.error("Job failed or timed out")
                return None
        
        # Download the PDF
        print("\n📥 Downloading PDF...")
        pdf_path = self._download_pdf(result_url, output_filename)
        
        if pdf_path:
            print(f"\n✅ Map PDF generated successfully: {pdf_path}")
        
        return pdf_path
    
    def _create_web_map_json(self, longitude: float, latitude: float, 
                            location_name: str, buffer_miles: float) -> Dict[str, Any]:
        """Create the Web Map JSON specification"""
        
        # Convert buffer miles to meters
        buffer_meters = buffer_miles * 1609.34
        
        # Calculate extent based on buffer
        # Rough conversion: 1 degree latitude = 111,111 meters
        lat_buffer = buffer_meters / 111111
        # Longitude buffer varies by latitude
        lon_buffer = buffer_meters / (111111 * abs(math.cos(math.radians(latitude))))
        
        extent = {
            "xmin": longitude - lon_buffer,
            "ymin": latitude - lat_buffer,
            "xmax": longitude + lon_buffer,
            "ymax": latitude + lat_buffer,
            "spatialReference": {"wkid": 4326}
        }
        
        # Convert extent to Web Mercator for the map
        extent_mercator = self._convert_extent_to_web_mercator(extent)
        
        # Create a point graphic for the location
        point_mercator = self._convert_point_to_web_mercator(longitude, latitude)
        
        web_map = {
            "mapOptions": {
                "showAttribution": True,
                "extent": extent_mercator,
                "spatialReference": {"wkid": 102100},  # Web Mercator
                "scale": 24000  # 1:24,000 scale - well within the 1:250,000 minimum scale for wetlands
            },
            "operationalLayers": [
                {
                    "id": "wetlands_layer",
                    "title": "Wetlands",
                    "opacity": 0.75,
                    "url": self.wetlands_url,
                    "visibility": True,
                    "visibleLayers": [0],  # Make layer 0 (Wetlands) visible
                    "layerDefinition": {
                        "definitionExpression": "",  # No filter, show all wetlands
                        "layerTimeOptions": {
                            "useTime": False
                        }
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
                "outputSize": [800, 1100],  # Width x Height in pixels
                "dpi": 300
            },
            "layoutOptions": {
                "titleText": location_name,
                "authorText": "WetlandsINFO System",
                "copyrightText": "USFWS National Wetlands Inventory",
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
                            "subLayerIds": [0]
                        }
                    ]
                }
            }
        }
        
        return web_map
    
    def _convert_extent_to_web_mercator(self, extent_wgs84: Dict[str, Any]) -> Dict[str, Any]:
        """Convert extent from WGS84 to Web Mercator"""
        import math
        
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
        import math
        
        x = longitude * 20037508.34 / 180
        y = math.log(math.tan((90 + latitude) * math.pi / 360)) / (math.pi / 180)
        y = y * 20037508.34 / 180
        
        return {"x": x, "y": y}
    
    def _create_export_params(self, web_map_json: Dict[str, Any]) -> Dict[str, Any]:
        """Create parameters for the ExportWebMap service"""
        
        # Layout template options from USFWS service
        layout_template = "Letter ANSI A Landscape"  # 11x8.5 inches
        
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
            # Try synchronous execution first
            execute_url = f"{self.export_webmap_url}/execute"
            
            response = self.session.post(execute_url, data=params, timeout=60)
            
            if response.status_code != 200:
                print(f"⚠️  Response status: {response.status_code}")
                print(f"⚠️  Response text: {response.text}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Check for errors in result
            if 'error' in result:
                logger.error(f"Service error: {result['error']}")
                return None
            
            # Check if it's an async job
            if 'jobId' in result:
                return result
            elif 'results' in result:
                # Synchronous result
                return result
            else:
                # Try async submission
                submit_url = f"{self.export_webmap_url}/submitJob"
                response = self.session.post(submit_url, data=params, timeout=30)
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to submit export job: {e}")
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
                    # Get the output URL
                    results = job_info.get('results', {})
                    output_file = results.get('Output_File', {})
                    param_url = output_file.get('paramUrl')
                    
                    if param_url:
                        # Construct full URL
                        if param_url.startswith('http'):
                            return param_url
                        else:
                            base_url = self.export_webmap_url.rsplit('/', 1)[0]
                            return f"{base_url}/jobs/{job_id}/{param_url}"
                    
                elif status in ['esriJobFailed', 'esriJobCancelled']:
                    messages = job_info.get('messages', [])
                    for msg in messages:
                        logger.error(f"Job message: {msg}")
                    return None
                
                # Job still running
                print(f"  Status: {status}")
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(2)
        
        logger.error("Job timed out")
        return None
    
    def _download_pdf(self, result_url: str, output_filename: str = None) -> Optional[str]:
        """Download the PDF from the result URL"""
        
        try:
            # Get the PDF
            pdf_url = result_url if result_url.endswith('.pdf') else f"{result_url}?f=pdf"
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # Generate filename if not provided
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"wetland_map_{timestamp}.pdf"
            
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', output_filename)
            
            # Save the PDF
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            return None


def generate_simple_wetland_map(longitude: float, latitude: float, 
                               location_name: str = None,
                               buffer_miles: float = 0.5) -> str:
    """
    Simple function to generate a wetland map PDF
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Optional location name
        buffer_miles: Buffer radius in miles
        
    Returns:
        Path to generated PDF file
    """
    
    generator = WetlandMapGenerator()
    return generator.generate_wetland_map_pdf(
        longitude, latitude, location_name, buffer_miles
    )


def main():
    """Main function for command line usage"""
    
    print("🗺️  Wetland Map PDF Generator")
    print("="*50)
    
    # Check command line arguments
    if len(sys.argv) >= 3:
        try:
            longitude = float(sys.argv[1])
            latitude = float(sys.argv[2])
            location_name = sys.argv[3] if len(sys.argv) > 3 else None
            buffer_miles = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        except ValueError:
            print("❌ Invalid arguments")
            print("Usage: python generate_wetland_map_pdf.py <longitude> <latitude> [location_name] [buffer_miles]")
            return
    else:
        # Interactive mode
        try:
            print("\nEnter coordinates for the wetland map:")
            longitude = float(input("Longitude: ") or "-66.196")
            latitude = float(input("Latitude: ") or "18.452")
            location_name = input("Location name (optional): ").strip() or None
            buffer_miles = float(input("Buffer radius in miles (default 0.5): ") or "0.5")
        except ValueError:
            print("❌ Invalid input")
            return
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled")
            return
    
    # Generate the map
    pdf_path = generate_simple_wetland_map(
        longitude, latitude, location_name, buffer_miles
    )
    
    if pdf_path:
        print(f"\n✅ Success! Map saved to: {pdf_path}")
        print(f"\n📄 You can open the PDF to view:")
        print(f"   - Wetland areas overlaid on satellite imagery")
        print(f"   - Legend showing wetland types")
        print(f"   - Scale bar and north arrow")
        print(f"   - Location marker at specified coordinates")
    else:
        print("\n❌ Failed to generate map")


if __name__ == "__main__":
    import math
    main() 