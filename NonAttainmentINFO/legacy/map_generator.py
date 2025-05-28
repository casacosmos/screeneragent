#!/usr/bin/env python3
"""
Generate Nonattainment Areas Map PDF

This module provides comprehensive map generation for EPA nonattainment areas
using ArcGIS REST services. It creates professional PDF maps showing air quality
violations and regulatory boundaries.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
import math
from io import BytesIO
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NonAttainmentMapGenerator:
    """Generate professional nonattainment areas map PDFs"""
    
    def __init__(self):
        # EPA ArcGIS services
        self.printing_service_url = "https://gispub.epa.gov/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"
        self.nonattainment_service_url = "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer"
        
        # Base map options
        self.base_map_urls = {
            "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
            "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
            "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer",
            "USA_Topo_Maps": "https://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer"
        }
        
        # Layer definitions for different pollutants
        self.pollutant_layers = {
            'ozone_2015': {'id': 2, 'name': 'Ozone 8-hr (2015)', 'color': [255, 0, 0, 180]},
            'ozone_2008': {'id': 1, 'name': 'Ozone 8-hr (2008)', 'color': [255, 100, 0, 180]},
            'pm25_2012': {'id': 7, 'name': 'PM2.5 Annual (2012)', 'color': [128, 0, 128, 180]},
            'pm25_2006': {'id': 5, 'name': 'PM2.5 24hr (2006)', 'color': [255, 0, 255, 180]},
            'pm10_1987': {'id': 8, 'name': 'PM10 (1987)', 'color': [139, 69, 19, 180]},
            'lead_2008': {'id': 3, 'name': 'Lead (2008)', 'color': [0, 0, 255, 180]},
            'so2_2010': {'id': 4, 'name': 'SO2 1-hr (2010)', 'color': [255, 255, 0, 180]},
            'co_1971': {'id': 9, 'name': 'CO (1971)', 'color': [0, 255, 0, 180]},
            'no2_1971': {'id': 11, 'name': 'NO2 (1971)', 'color': [0, 255, 255, 180]}
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NonAttainmentMapGenerator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_nonattainment_map_pdf(self, 
                                      longitude: float, 
                                      latitude: float,
                                      location_name: str = None,
                                      buffer_miles: float = 25.0,
                                      base_map: str = "World_Topo_Map",
                                      dpi: int = 300,
                                      output_size: tuple = (1224, 792),
                                      include_legend: bool = True,
                                      pollutants: Optional[List[str]] = None,
                                      include_revoked: bool = False,
                                      nonattainment_transparency: float = 0.7,
                                      output_filename: str = None) -> str:
        """
        Generate a nonattainment areas map PDF for a specific location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name for the map title
            buffer_miles: Buffer radius in miles (default 25.0 for regional view)
            base_map: Base map style
            dpi: Resolution (96, 150, 300)
            output_size: Output size as (width, height) tuple
            include_legend: Whether to include legend
            pollutants: List of specific pollutants to show (None for all active)
            include_revoked: Whether to include revoked standards
            nonattainment_transparency: Nonattainment layer transparency (0.0-1.0)
            output_filename: Optional output filename
            
        Returns:
            Path to the generated PDF file
        """
        
        if location_name is None:
            location_name = f"Air Quality Analysis at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating nonattainment areas map PDF for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"📏 Buffer: {buffer_miles} miles")
        print(f"🎨 Base map: {base_map}")
        print(f"📐 Output: {output_size[0]}x{output_size[1]} at {dpi} DPI")
        print(f"🌫️ Nonattainment transparency: {nonattainment_transparency:.1f}")
        
        # Check for nonattainment areas in the region
        print(f"\n🔍 Checking for nonattainment areas in the region...")
        areas_found = self._check_nonattainment_in_area(longitude, latitude, buffer_miles, pollutants, include_revoked)
        if areas_found:
            print(f"✅ Found {areas_found} nonattainment area(s) in the region")
        else:
            print(f"✅ No nonattainment areas found in the region - map will show clean air status")
        
        # Create the Web Map JSON specification
        web_map_json = self._create_web_map_json(
            longitude, latitude, location_name, buffer_miles,
            base_map, dpi, output_size, include_legend, 
            pollutants, include_revoked, nonattainment_transparency
        )
        
        # Select appropriate layout template
        layout_template = "Letter ANSI A Portrait" if include_legend else "MAP_ONLY"
        
        # Create export parameters
        export_params = {
            "f": "json",
            "Web_Map_as_JSON": json.dumps(web_map_json),
            "Format": "PDF",
            "Layout_Template": layout_template
        }
        
        print(f"📋 Using layout: {layout_template}")
        print(f"🎨 Legend included: {include_legend}")
        
        # Debug: Save Web Map JSON for inspection
        debug_filename = f"debug_nonattainment_webmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_filename, 'w') as f:
            json.dump(web_map_json, f, indent=2)
        print(f"🔍 Debug: Web Map JSON saved to {debug_filename}")
        
        # Submit the export request
        print("\n📤 Submitting map export request...")
        
        try:
            response = self.session.post(
                self.printing_service_url, 
                data=export_params, 
                timeout=120  # Longer timeout for complex maps
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Check for errors
            if 'error' in result:
                logger.error(f"Service error: {result['error']}")
                print(f"🔍 Full error response: {json.dumps(result, indent=2)}")
                return None
            
            # Extract result URL
            result_url = None
            if 'results' in result and len(result['results']) > 0:
                output_result = result['results'][0]
                if 'value' in output_result:
                    result_url = output_result['value'].get('url')
            
            if not result_url:
                logger.error("No output URL in result")
                return None
            
            print("✅ Map generated successfully!")
            print(f"📄 Map URL: {result_url}")
            
            # Download the PDF
            print("\n📥 Downloading PDF...")
            pdf_path = self._download_pdf(result_url, output_filename)
            
            if pdf_path:
                print(f"\n✅ Map PDF saved to: {pdf_path}")
            
            return pdf_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error generating map: {e}")
            return None
    
    def _create_web_map_json(self, longitude: float, latitude: float, 
                            location_name: str, buffer_miles: float,
                            base_map: str, dpi: int, output_size: tuple,
                            include_legend: bool, pollutants: Optional[List[str]],
                            include_revoked: bool, nonattainment_transparency: float) -> Dict[str, Any]:
        """Create the Web Map JSON specification for nonattainment areas"""
        
        # Calculate extent based on buffer
        buffer_degrees = buffer_miles / 69.0  # Rough conversion: 1 degree ≈ 69 miles
        
        extent = {
            "xmin": longitude - buffer_degrees,
            "ymin": latitude - buffer_degrees,
            "xmax": longitude + buffer_degrees,
            "ymax": latitude + buffer_degrees,
            "spatialReference": {"wkid": 4326}
        }
        
        # Calculate appropriate scale for regional view
        map_width_degrees = buffer_degrees * 2
        map_width_feet = map_width_degrees * 364000  # rough conversion
        map_scale = int(map_width_feet / (output_size[0] / dpi))
        
        print(f"🎯 Calculated map scale: 1:{map_scale:,}")
        
        # Get base map URL
        base_map_url = self.base_map_urls.get(base_map, self.base_map_urls["World_Topo_Map"])
        
        # Determine which layers to show
        visible_layers = self._determine_visible_layers(pollutants, include_revoked)
        
        # Create nonattainment operational layers
        operational_layers = []
        
        # Add each pollutant as a separate layer for better control
        for layer_key, layer_info in self.pollutant_layers.items():
            if layer_info['id'] in visible_layers:
                layer = {
                    "id": f"nonattainment_{layer_key}",
                    "url": self.nonattainment_service_url,
                    "title": f"Nonattainment: {layer_info['name']}",
                    "opacity": nonattainment_transparency,
                    "visibility": True,
                    "layerType": "ArcGISMapServiceLayer",
                    "visibleLayers": [layer_info['id']],
                    "minScale": 0,
                    "maxScale": 0,
                    "layerDefinition": {
                        "drawingInfo": {
                            "renderer": {
                                "type": "simple",
                                "symbol": {
                                    "type": "esriSFS",
                                    "style": "esriSFSSolid",
                                    "color": layer_info['color'],
                                    "outline": {
                                        "type": "esriSLS",
                                        "style": "esriSLSSolid",
                                        "color": [0, 0, 0, 255],
                                        "width": 1
                                    }
                                }
                            }
                        }
                    }
                }
                operational_layers.append(layer)
        
        # Create web map structure
        web_map = {
            "mapOptions": {
                "extent": extent,
                "spatialReference": {"wkid": 4326},
                "showAttribution": True,
                "scale": map_scale
            },
            "operationalLayers": operational_layers,
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
                "dpi": dpi,
                "format": "PDF"
            },
            "layoutOptions": {
                "titleText": location_name,
                "authorText": "NonAttainmentINFO System",
                "copyrightText": f"EPA Nonattainment Areas | Generated {datetime.now().strftime('%Y-%m-%d')}",
                "scaleBarOptions": {
                    "metricUnit": "esriKilometers",
                    "metricLabel": "km",
                    "nonMetricUnit": "esriMiles",
                    "nonMetricLabel": "mi"
                },
                "legendOptions": {
                    "operationalLayers": [
                        {
                            "id": layer["id"],
                            "subLayerIds": layer["visibleLayers"]
                        } for layer in operational_layers
                    ]
                } if include_legend else {}
            },
            "version": "1.6.0"
        }
        
        # Add location marker
        point_marker = {
            "id": "location_marker",
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
                                        "size": 12,
                                        "outline": {
                                            "color": [255, 255, 255, 255],  # White outline
                                            "width": 3
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
            "title": "Analysis Location",
            "opacity": 1,
            "visibility": True
        }
        
        web_map["operationalLayers"].append(point_marker)
        
        return web_map
    
    def _determine_visible_layers(self, pollutants: Optional[List[str]], include_revoked: bool) -> List[int]:
        """Determine which layers should be visible based on pollutants and revoked status"""
        
        visible_layers = []
        
        # Map pollutant names to layer keys
        pollutant_mapping = {
            'Ozone': ['ozone_2015', 'ozone_2008'],
            'PM2.5': ['pm25_2012', 'pm25_2006'],
            'PM10': ['pm10_1987'],
            'Lead': ['lead_2008'],
            'Sulfur Dioxide': ['so2_2010'],
            'Carbon Monoxide': ['co_1971'],
            'Nitrogen Dioxide': ['no2_1971']
        }
        
        if pollutants:
            # Show only specified pollutants
            for pollutant in pollutants:
                if pollutant in pollutant_mapping:
                    for layer_key in pollutant_mapping[pollutant]:
                        if layer_key in self.pollutant_layers:
                            visible_layers.append(self.pollutant_layers[layer_key]['id'])
        else:
            # Show all active standards (non-revoked)
            active_layers = ['ozone_2015', 'ozone_2008', 'pm25_2012', 'pm25_2006', 
                           'pm10_1987', 'lead_2008', 'so2_2010', 'co_1971', 'no2_1971']
            
            for layer_key in active_layers:
                if layer_key in self.pollutant_layers:
                    visible_layers.append(self.pollutant_layers[layer_key]['id'])
        
        return visible_layers
    
    def _check_nonattainment_in_area(self, longitude: float, latitude: float, 
                                    buffer_miles: float, pollutants: Optional[List[str]],
                                    include_revoked: bool) -> int:
        """Check if there are nonattainment areas in the specified region"""
        
        try:
            # Create buffer geometry for query
            buffer_degrees = buffer_miles / 69.0
            
            geometry = {
                "xmin": longitude - buffer_degrees,
                "ymin": latitude - buffer_degrees,
                "xmax": longitude + buffer_degrees,
                "ymax": latitude + buffer_degrees,
                "spatialReference": {"wkid": 4326}
            }
            
            # Query a representative layer to check for areas
            query_params = {
                "geometry": json.dumps(geometry),
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OBJECTID",
                "returnGeometry": "false",
                "returnCountOnly": "true",
                "f": "json"
            }
            
            # Check ozone layer as representative
            response = self.session.get(
                f"{self.nonattainment_service_url}/2/query",  # Ozone 2015 layer
                params=query_params,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            return result.get('count', 0)
            
        except Exception as e:
            logger.warning(f"Could not check for nonattainment areas: {e}")
            return 0
    
    def _download_pdf(self, result_url: str, output_filename: str = None) -> Optional[str]:
        """Download the generated PDF from the result URL"""
        
        try:
            # Generate filename if not provided
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"nonattainment_map_{timestamp}.pdf"
            
            # Ensure .pdf extension
            if not output_filename.endswith('.pdf'):
                output_filename += '.pdf'
            
            # Download the PDF
            response = self.session.get(result_url, timeout=60)
            response.raise_for_status()
            
            # Save to file
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            
            # Verify file was created and has content
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                return output_filename
            else:
                logger.error("Downloaded file is empty or was not created")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
    
    def generate_adaptive_nonattainment_map(self, longitude: float, latitude: float,
                                          location_name: str = None,
                                          analysis_result = None) -> str:
        """
        Generate an adaptive nonattainment map based on analysis results
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            analysis_result: NonAttainmentAnalysisResult object
            
        Returns:
            Path to generated PDF file
        """
        
        if location_name is None:
            location_name = f"Air Quality Analysis at {latitude:.4f}, {longitude:.4f}"
        
        # Determine adaptive settings based on analysis
        if analysis_result and analysis_result.has_nonattainment_areas:
            # Areas found - use detailed view
            buffer_miles = 15.0
            base_map = "World_Topo_Map"
            transparency = 0.7
            reasoning = f"Found {analysis_result.area_count} nonattainment areas - using detailed 15-mile view"
            
            # Extract pollutants from results
            pollutants = list(set(area.pollutant_name for area in analysis_result.nonattainment_areas))
        else:
            # No areas found - use regional view
            buffer_miles = 50.0
            base_map = "World_Street_Map"
            transparency = 0.8
            reasoning = "No nonattainment areas found - using 50-mile regional view"
            pollutants = None
        
        print(f"🎯 Adaptive map settings: {reasoning}")
        
        return self.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=f"{location_name} - Adaptive Analysis Map",
            buffer_miles=buffer_miles,
            base_map=base_map,
            pollutants=pollutants,
            nonattainment_transparency=transparency,
            include_legend=True
        )


def main():
    """Example usage of the NonAttainmentMapGenerator"""
    
    print("🗺️  NonAttainment Areas Map Generator")
    print("=" * 50)
    
    generator = NonAttainmentMapGenerator()
    
    # Example locations
    test_locations = [
        (-118.2437, 34.0522, "Los Angeles, CA"),  # Known nonattainment area
        (-95.3698, 29.7604, "Houston, TX"),       # Known nonattainment area
        (-106.6504, 35.0844, "Santa Fe, NM"),     # Clean air area
    ]
    
    for longitude, latitude, name in test_locations:
        print(f"\n🌍 Generating map for {name}...")
        
        pdf_path = generator.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=name,
            buffer_miles=25.0,
            include_legend=True
        )
        
        if pdf_path:
            print(f"✅ Map saved: {pdf_path}")
        else:
            print(f"❌ Failed to generate map for {name}")


if __name__ == "__main__":
    main() 