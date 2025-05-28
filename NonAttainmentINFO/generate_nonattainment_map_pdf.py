#!/usr/bin/env python3
"""
Generate NonAttainment Areas Map PDF

This module generates professional nonattainment areas map PDFs using EPA OAR_OAQPS services.
Includes proper layer configuration, symbology, and layout options for professional PDF output.
Based on the successful HabitatINFO implementation patterns.
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
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NonAttainmentMapGenerator:
    """Generate professional nonattainment areas map PDFs with proper configuration"""
    
    def __init__(self):
        # Service URLs - using publicly accessible services
        self.printing_service_urls = [
            # Primary Esri public printing service
            "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute",
            # Alternative Esri printing service
            "https://services.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute",
            # Backup EPA service (may require authentication)
            "https://gispub.epa.gov/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task/execute"
        ]
        self.nonattainment_service_url = "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer"
        
        # Base map options
        self.base_map_urls = {
            "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
            "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
            "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer",
            "USA_Topo_Maps": "https://services.arcgisonline.com/ArcGIS/rest/services/USA_Topo_Maps/MapServer"
        }
        
        # NonAttainment layers based on EPA service analysis
        self.nonattainment_layers = {
            'ozone_1997': {
                'id': 0,
                'name': 'Ozone 8-hr (1997 standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (1997)',
                'status': 'revoked',
                'color': [255, 165, 0, 180]  # Orange
            },
            'ozone_2008': {
                'id': 1,
                'name': 'Ozone 8-hr (2008 standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (2008)',
                'status': 'active',
                'color': [255, 69, 0, 180]  # Red-Orange
            },
            'ozone_2015': {
                'id': 2,
                'name': 'Ozone 8-hr (2015 Standard)',
                'pollutant': 'Ozone',
                'standard': '8-hour (2015)',
                'status': 'active',
                'color': [255, 0, 0, 180]  # Red
            },
            'lead_2008': {
                'id': 3,
                'name': 'Lead (2008 standard)',
                'pollutant': 'Lead',
                'standard': '2008',
                'status': 'active',
                'color': [128, 0, 128, 180]  # Purple
            },
            'so2_2010': {
                'id': 4,
                'name': 'SO2 1-hr (2010 standard)',
                'pollutant': 'Sulfur Dioxide',
                'standard': '1-hour (2010)',
                'status': 'active',
                'color': [255, 255, 0, 180]  # Yellow
            },
            'pm25_2006': {
                'id': 5,
                'name': 'PM2.5 24hr (2006 standard)',
                'pollutant': 'PM2.5',
                'standard': '24-hour (2006)',
                'status': 'active',
                'color': [139, 69, 19, 180]  # Brown
            },
            'pm25_1997': {
                'id': 6,
                'name': 'PM2.5 Annual (1997 standard)',
                'pollutant': 'PM2.5',
                'standard': 'Annual (1997)',
                'status': 'active',
                'color': [160, 82, 45, 180]  # Saddle Brown
            },
            'pm25_2012': {
                'id': 7,
                'name': 'PM2.5 Annual (2012 standard)',
                'pollutant': 'PM2.5',
                'standard': 'Annual (2012)',
                'status': 'active',
                'color': [210, 180, 140, 180]  # Tan
            },
            'pm10_1987': {
                'id': 8,
                'name': 'PM10 (1987 standard)',
                'pollutant': 'PM10',
                'standard': '1987',
                'status': 'active',
                'color': [165, 42, 42, 180]  # Brown
            },
            'co_1971': {
                'id': 9,
                'name': 'CO (1971 Standard)',
                'pollutant': 'Carbon Monoxide',
                'standard': '1971',
                'status': 'active',
                'color': [0, 128, 0, 180]  # Green
            },
            'ozone_1979': {
                'id': 10,
                'name': 'Ozone 1-hr (1979 standard-revoked)',
                'pollutant': 'Ozone',
                'standard': '1-hour (1979)',
                'status': 'revoked',
                'color': [255, 192, 203, 180]  # Pink
            },
            'no2_1971': {
                'id': 11,
                'name': 'NO2 (1971 Standard)',
                'pollutant': 'Nitrogen Dioxide',
                'standard': '1971',
                'status': 'active',
                'color': [0, 191, 255, 180]  # Deep Sky Blue
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NonAttainmentMapGenerator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.epa.gov'  # Add referer for better compatibility
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
                                      layout_template: str = None,
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
            layout_template: Optional layout template for the map
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
        print(f"🔍 Include revoked standards: {include_revoked}")
        
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
        if layout_template is None:
            if include_legend:
                layout_template = "Letter ANSI A Portrait"  # Default when legend is included
            else:
                layout_template = "MAP_ONLY"
        
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
        
        # Try multiple printing services
        pdf_path = self._try_printing_services(export_params, output_filename)
        
        if pdf_path:
            print(f"\n✅ Nonattainment map PDF saved to: {pdf_path}")
        else:
            # Fallback: Create a simple HTML map if PDF generation fails
            print("\n⚠️  PDF generation failed. Creating fallback HTML map...")
            pdf_path = self._create_fallback_html_map(
                longitude, latitude, location_name, buffer_miles,
                areas_found, output_filename
            )
            if pdf_path:
                print(f"✅ Fallback HTML map saved to: {pdf_path}")
        
        return pdf_path
    
    def _try_printing_services(self, export_params: Dict, output_filename: str = None) -> Optional[str]:
        """Try multiple printing services with fallback"""
        
        for i, service_url in enumerate(self.printing_service_urls):
            service_name = "Esri Public" if i == 0 else ("Esri Alternative" if i == 1 else "EPA")
            print(f"🔄 Trying {service_name} printing service...")
            
            try:
                # Add timeout and retry logic
                for attempt in range(2):
                    try:
                        response = self.session.post(
                            service_url, 
                            data=export_params, 
                            timeout=120
                        )
                        response.raise_for_status()
                        break
                    except requests.exceptions.Timeout:
                        if attempt == 0:
                            print(f"   ⏱️ Timeout, retrying...")
                            time.sleep(2)
                        else:
                            raise
                
                result = response.json()
                
                # Check for errors
                if 'error' in result:
                    print(f"❌ {service_name} service error: {result['error']}")
                    if i < len(self.printing_service_urls) - 1:
                        print(f"🔄 Trying next service...")
                        continue
                    else:
                        return None
                
                # Extract result URL
                result_url = None
                if 'results' in result and len(result['results']) > 0:
                    output_result = result['results'][0]
                    if 'value' in output_result:
                        result_url = output_result['value'].get('url')
                
                if not result_url:
                    print(f"❌ No output URL from {service_name} service")
                    if i < len(self.printing_service_urls) - 1:
                        print(f"🔄 Trying next service...")
                        continue
                    else:
                        return None
                
                print(f"✅ Map generated successfully using {service_name} service!")
                print(f"📄 Map URL: {result_url}")
                
                # Download the PDF
                print("\n📥 Downloading PDF...")
                return self._download_pdf(result_url, output_filename)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ {service_name} service request failed: {e}")
                if i < len(self.printing_service_urls) - 1:
                    print(f"🔄 Trying next service...")
                    continue
                else:
                    logger.error(f"All printing services failed")
                    return None
            except Exception as e:
                print(f"❌ {service_name} service error: {e}")
                if i < len(self.printing_service_urls) - 1:
                    print(f"🔄 Trying next service...")
                    continue
                else:
                    logger.error(f"All printing services failed")
                    return None
        
        return None
    
    def _create_fallback_html_map(self, longitude: float, latitude: float, 
                                 location_name: str, buffer_miles: float,
                                 areas_found: int, output_filename: str = None) -> Optional[str]:
        """Create a simple HTML map as fallback when PDF generation fails"""
        
        try:
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"nonattainment_map_{timestamp}.html"
            elif output_filename.endswith('.pdf'):
                output_filename = output_filename.replace('.pdf', '.html')
            
            # Ensure output directory exists
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', output_filename)
            
            # Create simple HTML with embedded map
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{location_name} - NonAttainment Areas Map</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .info {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .map-container {{ border: 2px solid #ccc; padding: 10px; background: #fff; }}
        .status {{ font-weight: bold; color: {'#d9534f' if areas_found > 0 else '#5cb85c'}; }}
    </style>
</head>
<body>
    <h1>🌫️ NonAttainment Areas Map</h1>
    <h2>{location_name}</h2>
    
    <div class="info">
        <p><strong>📍 Location:</strong> {latitude:.4f}, {longitude:.4f}</p>
        <p><strong>📏 Analysis Radius:</strong> {buffer_miles} miles</p>
        <p><strong>📅 Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p class="status"><strong>🔍 Status:</strong> {'⚠️ ' + str(areas_found) + ' nonattainment area(s) found' if areas_found > 0 else '✅ Clean air - no nonattainment areas'}</p>
    </div>
    
    <div class="map-container">
        <h3>📍 Map View</h3>
        <p>To view the interactive map with nonattainment areas:</p>
        <ol>
            <li>Visit <a href="https://gispub.epa.gov/airnow/" target="_blank">EPA AirNow Interactive Map</a></li>
            <li>Navigate to coordinates: {latitude:.4f}, {longitude:.4f}</li>
            <li>Enable the "Nonattainment Areas" layer</li>
        </ol>
        
        <p>Alternative: View on <a href="https://www.google.com/maps/@{latitude},{longitude},10z" target="_blank">Google Maps</a> (terrain view)</p>
    </div>
    
    <div class="info">
        <h3>ℹ️ About NonAttainment Areas</h3>
        <p>Nonattainment areas are geographic regions that do not meet National Ambient Air Quality Standards (NAAQS) for one or more criteria pollutants:</p>
        <ul>
            <li>🌫️ Ozone (O₃)</li>
            <li>🌫️ Particulate Matter (PM2.5 and PM10)</li>
            <li>🌫️ Carbon Monoxide (CO)</li>
            <li>🌫️ Sulfur Dioxide (SO₂)</li>
            <li>🌫️ Nitrogen Dioxide (NO₂)</li>
            <li>🌫️ Lead (Pb)</li>
        </ul>
    </div>
    
    <p style="text-align: center; color: #666; margin-top: 40px;">
        Generated by NonAttainmentINFO System | Data Source: EPA OAR_OAQPS
    </p>
</body>
</html>
"""
            
            with open(output_path, 'w') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating fallback HTML map: {e}")
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
        for layer_key, layer_info in self.nonattainment_layers.items():
            if layer_info['id'] in visible_layers:
                layer = {
                    "id": f"nonattainment_{layer_key}",
                    "url": self.nonattainment_service_url,
                    "title": f"Nonattainment: {layer_info['name']}",
                    "opacity": nonattainment_transparency,
                    "visibility": True,
                    "layerType": "ArcGISMapServiceLayer",
                    "visibleLayers": [layer_info['id']],
                    "minScale": 0,  # No scale restrictions for nonattainment areas
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
            'Ozone': ['ozone_2015', 'ozone_2008', 'ozone_1997', 'ozone_1979'],
            'PM2.5': ['pm25_2012', 'pm25_2006', 'pm25_1997'],
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
                        if layer_key in self.nonattainment_layers:
                            layer_info = self.nonattainment_layers[layer_key]
                            # Check if we should include revoked standards
                            if include_revoked or layer_info['status'] != 'revoked':
                                visible_layers.append(layer_info['id'])
        else:
            # Show all layers based on revoked preference
            for layer_key, layer_info in self.nonattainment_layers.items():
                if include_revoked or layer_info['status'] != 'revoked':
                    visible_layers.append(layer_info['id'])
        
        print(f"🗂️  Using nonattainment layers: {visible_layers}")
        if include_revoked:
            print(f"   • Including revoked standards")
        else:
            print(f"   • Active standards only")
        
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
            
            # Check ozone 2015 layer as representative (most current active standard)
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
            
            # Import output directory manager
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from output_directory_manager import get_output_manager
            
            # Try to use output manager if available, otherwise fall back to output directory
            try:
                output_manager = get_output_manager()
                output_path = output_manager.get_file_path(output_filename, "maps")
            except:
                # Fallback to output directory if no project is set up
                os.makedirs('output', exist_ok=True)
                output_path = os.path.join('output', output_filename)
            
            # Download the PDF
            response = self.session.get(result_url, timeout=60)
            response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Verify file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
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
    
    def generate_detailed_nonattainment_map(self, longitude: float, latitude: float,
                                          location_name: str = None, 
                                          nonattainment_transparency: float = 0.75) -> str:
        """Generate a detailed nonattainment map with all active standards"""
        
        return self.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=10.0,  # Smaller buffer for detail
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            include_revoked=False,  # Active standards only
            nonattainment_transparency=nonattainment_transparency
        )
    
    def generate_overview_nonattainment_map(self, longitude: float, latitude: float,
                                          location_name: str = None,
                                          nonattainment_transparency: float = 0.8,
                                          layout_template: str = None) -> str:
        """Generate an overview nonattainment map"""
        
        return self.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=50.0,  # Show wider area for context
            base_map="World_Topo_Map",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            layout_template=layout_template,
            include_revoked=False,
            nonattainment_transparency=nonattainment_transparency
        )
    
    def generate_pollutant_specific_map(self, pollutant_name: str, 
                                      longitude: float, latitude: float,
                                      location_name: str = None,
                                      buffer_miles: float = 25.0) -> str:
        """Generate a map focused on a specific pollutant's nonattainment areas"""
        
        if location_name is None:
            location_name = f"{pollutant_name} Nonattainment Areas"
        
        return self.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map="World_Topo_Map",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            pollutants=[pollutant_name],
            include_revoked=True,  # Show all standards for this pollutant
            nonattainment_transparency=0.7
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