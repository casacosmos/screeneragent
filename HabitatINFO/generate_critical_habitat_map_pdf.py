#!/usr/bin/env python3
"""
Generate Critical Habitat Map PDF

This module generates professional critical habitat map PDFs using USFWS Critical Habitat services.
Includes proper layer configuration, symbology, and layout options for professional PDF output.
Based on the successful WetlandsINFO implementation patterns.
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


class CriticalHabitatMapGenerator:
    """Generate professional critical habitat map PDFs with proper configuration"""
    
    def __init__(self):
        # Service URLs - using the same pattern as successful wetlands implementation
        self.printing_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map/execute"
        self.habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
        
        # Base map options
        self.base_map_urls = {
            "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
            "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
            "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer"
        }
        
        # Critical habitat layers
        self.habitat_layers = {
            'final_polygon': {
                'id': 0,
                'name': 'Critical Habitat - Polygon Features - Final',
                'geometry_type': 'Polygon',
                'habitat_type': 'Final'
            },
            'final_linear': {
                'id': 1,
                'name': 'Critical Habitat - Linear Features - Final',
                'geometry_type': 'Linear',
                'habitat_type': 'Final'
            },
            'proposed_polygon': {
                'id': 2,
                'name': 'Critical Habitat - Polygon Features - Proposed',
                'geometry_type': 'Polygon',
                'habitat_type': 'Proposed'
            },
            'proposed_linear': {
                'id': 3,
                'name': 'Critical Habitat - Linear Features - Proposed',
                'geometry_type': 'Linear',
                'habitat_type': 'Proposed'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CriticalHabitatMapGenerator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_critical_habitat_map_pdf(self, 
                                         longitude: float, 
                                         latitude: float,
                                         location_name: str = None,
                                         buffer_miles: float = 0.5,
                                         base_map: str = "World_Imagery",
                                         dpi: int = 300,
                                         output_size: tuple = (1224, 792),
                                         include_legend: bool = True,
                                         layout_template: str = None,
                                         include_proposed: bool = True,
                                         habitat_transparency: float = 0.8,
                                         output_filename: str = None) -> str:
        """
        Generate a critical habitat map PDF for a specific location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name for the map title
            buffer_miles: Buffer radius in miles (default 0.5)
            base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
            dpi: Resolution (96, 150, 300)
            output_size: Output size as (width, height) tuple
            include_legend: Whether to include legend
            layout_template: Optional layout template for the map
            include_proposed: Whether to include proposed critical habitat
            habitat_transparency: Critical habitat layer transparency (0.0-1.0, default 0.8)
            output_filename: Optional output filename
            
        Returns:
            Path to the generated PDF file
        """
        
        if location_name is None:
            location_name = f"Critical Habitat Map at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating critical habitat map PDF for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"📏 Buffer: {buffer_miles} miles")
        print(f"🎨 Base map: {base_map}")
        print(f"📐 Output: {output_size[0]}x{output_size[1]} at {dpi} DPI")
        print(f"🦎 Include proposed habitat: {include_proposed}")
        print(f"🌿 Habitat transparency: {habitat_transparency:.1f}")
        
        # First, check if there are critical habitats in the area
        print(f"\n🔍 Checking for critical habitat in the area...")
        habitats_found = self._check_critical_habitat_in_area(longitude, latitude, buffer_miles, include_proposed)
        if habitats_found:
            print(f"✅ Found {habitats_found} critical habitat feature(s) in the area")
        else:
            print(f"⚠️  No critical habitat found in the area - map will show base layers only")
        
        # Create the Web Map JSON specification
        web_map_json = self._create_web_map_json(
            longitude, latitude, location_name, buffer_miles,
            base_map, dpi, output_size, include_legend, include_proposed, habitat_transparency
        )
        
        # Select appropriate layout template
        if layout_template is None:
            if include_legend:
                layout_template = "Letter ANSI A Portrait"  # Default when legend is included
            else:
                layout_template = "MAP_ONLY"
        
        # Create export parameters with chosen layout
        export_params = {
            "f": "json",
            "Web_Map_as_JSON": json.dumps(web_map_json),
            "Format": "PDF",
            "Layout_Template": layout_template
        }
        
        print(f"📋 Using layout: {layout_template}")
        print(f"🎨 Legend included: {include_legend}")
        
        # Debug: Save Web Map JSON for inspection
        debug_filename = f"debug_habitat_webmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_filename, 'w') as f:
            json.dump(web_map_json, f, indent=2)
        print(f"🔍 Debug: Web Map JSON saved to {debug_filename}")
        
        # Submit the export request
        print("\n📤 Submitting map export request...")
        
        try:
            response = self.session.post(
                self.printing_service_url, 
                data=export_params, 
                timeout=60
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
                print(f"\n✅ Critical habitat map PDF saved to: {pdf_path}")
            
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
                            include_legend: bool, include_proposed: bool, 
                            habitat_transparency: float) -> Dict[str, Any]:
        """Create the Web Map JSON specification for critical habitat"""
        
        # Calculate extent based on buffer
        # Rough conversion: 1 degree ≈ 69 miles
        buffer_degrees = buffer_miles / 69.0
        
        extent = {
            "xmin": longitude - buffer_degrees,
            "ymin": latitude - buffer_degrees,
            "xmax": longitude + buffer_degrees,
            "ymax": latitude + buffer_degrees,
            "spatialReference": {"wkid": 4326}
        }
        
        # Calculate appropriate scale to ensure habitat visibility (following wetlands pattern)
        map_width_degrees = buffer_degrees * 2
        # Approximate scale calculation: degrees to feet conversion
        map_width_feet = map_width_degrees * 364000  # rough conversion
        map_scale = int(map_width_feet / (output_size[0] / dpi))
        
        # Ensure reasonable scale for habitat visibility
        # Critical habitat has no scale restrictions, but use reasonable limit for detail
        max_scale = 250000  # Use same limit as wetlands for consistency
        
        if map_scale > max_scale:
            # Adjust extent to get better scale
            scale_factor = map_scale / max_scale
            buffer_degrees = buffer_degrees / scale_factor
            extent = {
                "xmin": longitude - buffer_degrees,
                "ymin": latitude - buffer_degrees,
                "xmax": longitude + buffer_degrees,
                "ymax": latitude + buffer_degrees,
                "spatialReference": {"wkid": 4326}
            }
            map_scale = max_scale
        
        print(f"🎯 Calculated map scale: 1:{map_scale:,} (habitat visible at all scales)")
        
        # Get base map URL
        base_map_url = self.base_map_urls.get(base_map, self.base_map_urls["World_Imagery"])
        
        # Determine which habitat layers to show - using wetlands pattern
        visible_layers = [0, 1]  # Always include final polygon and linear features
        
        # Include proposed habitat if requested
        if include_proposed:
            visible_layers.extend([2, 3])  # Add proposed polygon and linear features
        
        print(f"🗂️  Using critical habitat layers: {visible_layers}")
        if include_proposed:
            print(f"   • Final and proposed designations")
        else:
            print(f"   • Final designations only")
        
        # Create single critical habitat operational layer with proper configuration (following wetlands pattern)
        habitat_layer = {
            "id": "critical_habitat_layer",
            "url": self.habitat_service_url,
            "title": "USFWS Critical Habitat",
            "opacity": habitat_transparency,
            "visibility": True,
            "layerType": "ArcGISMapServiceLayer",
            "visibleLayers": visible_layers,
            "minScale": 0,  # No scale restrictions like wetlands
            "maxScale": 0
        }
        
        # Create web map structure
        web_map = {
            "mapOptions": {
                "extent": extent,
                "spatialReference": {"wkid": 4326},
                "showAttribution": True,
                "scale": map_scale
            },
            "operationalLayers": [habitat_layer],
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
                "authorText": "HabitatINFO System",
                "copyrightText": f"USFWS Critical Habitat Data | Generated {datetime.now().strftime('%Y-%m-%d')}",
                "scaleBarOptions": {
                    "metricUnit": "esriKilometers",
                    "metricLabel": "km",
                    "nonMetricUnit": "esriMiles",
                    "nonMetricLabel": "mi"
                },
                "legendOptions": {
                    "operationalLayers": [
                        {
                            "id": "critical_habitat_layer",
                            "subLayerIds": visible_layers
                        }
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
                                        "size": 10,
                                        "outline": {
                                            "color": [255, 255, 255, 255],  # White outline
                                            "width": 2
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
        
        return web_map
    
    def _check_critical_habitat_in_area(self, longitude: float, latitude: float, 
                                       buffer_miles: float, include_proposed: bool = True) -> int:
        """Check if there are critical habitats in the specified area"""
        
        try:
            # Calculate extent
            buffer_degrees = buffer_miles / 69.0
            
            # Create envelope geometry for query
            envelope = {
                "xmin": longitude - buffer_degrees,
                "ymin": latitude - buffer_degrees,
                "xmax": longitude + buffer_degrees,
                "ymax": latitude + buffer_degrees,
                "spatialReference": {"wkid": 4326}
            }
            
            total_count = 0
            
            # Query final polygon features (layer 0)
            layers_to_check = [0]  # Final polygon
            if include_proposed:
                layers_to_check.append(2)  # Proposed polygon
            
            for layer_id in layers_to_check:
                params = {
                    "geometry": json.dumps(envelope),
                    "geometryType": "esriGeometryEnvelope",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "OBJECTID",
                    "returnGeometry": "false",
                    "returnCountOnly": "true",
                    "f": "json"
                }
                
                response = self.session.get(
                    f"{self.habitat_service_url}/{layer_id}/query", 
                    params=params, 
                    timeout=15
                )
                response.raise_for_status()
                
                data = response.json()
                count = data.get('count', 0)
                total_count += count
                
                layer_type = "Final" if layer_id == 0 else "Proposed"
                if count > 0:
                    print(f"   • {layer_type} habitat: {count} features")
            
            return total_count
            
        except Exception as e:
            print(f"⚠️  Error checking critical habitat: {e}")
            return 0
    
    def _download_pdf(self, result_url: str, output_filename: str = None) -> Optional[str]:
        """Download the PDF from the result URL"""
        
        try:
            response = self.session.get(result_url, timeout=60)
            response.raise_for_status()
            
            # Generate filename if not provided
            if output_filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"critical_habitat_map_{timestamp}.pdf"
            
            # Import output directory manager
            import sys
            import os
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
            
            # Save the PDF
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            return None
    
    def generate_detailed_critical_habitat_map(self, longitude: float, latitude: float,
                                              location_name: str = None, 
                                              habitat_transparency: float = 0.75) -> str:
        """Generate a detailed critical habitat map with all features"""
        
        return self.generate_critical_habitat_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.3,
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),  # Tabloid size
            include_legend=True,
            include_proposed=True,
            habitat_transparency=habitat_transparency
        )
    
    def generate_overview_critical_habitat_map(self, longitude: float, latitude: float,
                                              location_name: str = None,
                                              habitat_transparency: float = 0.8,
                                              layout_template: str = None) -> str:
        """Generate an overview critical habitat map"""
        
        return self.generate_critical_habitat_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=2.0,  # Show wider area for context
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),  # Larger size for better detail
            include_legend=True,
            layout_template=layout_template,
            include_proposed=True,
            habitat_transparency=habitat_transparency
        )
    
    def generate_species_habitat_map(self, species_name: str, 
                                    center_longitude: float = None, 
                                    center_latitude: float = None,
                                    buffer_miles: float = 2.0) -> str:
        """Generate a map focused on a specific species' critical habitat"""
        
        if center_longitude is None or center_latitude is None:
            # Default to continental US center
            center_longitude = -98.5795
            center_latitude = 39.8283
        
        location_name = f"Critical Habitat for {species_name}"
        
        return self.generate_critical_habitat_map_pdf(
            longitude=center_longitude,
            latitude=center_latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map="World_Topo_Map",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            include_proposed=True,
            habitat_transparency=0.7
        )


def main():
    """Main function for command line usage"""
    
    print("🦎 Critical Habitat Map PDF Generator")
    print("="*50)
    
    # Parse command line arguments
    if len(sys.argv) >= 3:
        try:
            longitude = float(sys.argv[1])
            latitude = float(sys.argv[2])
            location_name = sys.argv[3] if len(sys.argv) > 3 else None
            buffer_miles = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        except ValueError:
            print("❌ Invalid arguments")
            print("Usage: python generate_critical_habitat_map_pdf.py <longitude> <latitude> [location_name] [buffer_miles]")
            return
    else:
        # Interactive mode
        try:
            print("\nEnter coordinates for the critical habitat map:")
            longitude = float(input("Longitude: ") or "-122.4194")
            latitude = float(input("Latitude: ") or "37.7749")
            location_name = input("Location name (optional): ").strip() or None
            buffer_miles = float(input("Buffer radius in miles (default 0.5): ") or "0.5")
            
            print("\nMap options:")
            print("1. Detailed map (0.3 mile buffer, satellite imagery)")
            print("2. Standard map (0.5 mile buffer, satellite imagery)")
            print("3. Overview map (1.0 mile buffer, topographic)")
            print("4. Custom settings")
            
            choice = input("\nSelect option (1-4, default 2): ").strip() or "2"
            
        except ValueError:
            print("❌ Invalid input")
            return
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled")
            return
    
    # Create generator
    generator = CriticalHabitatMapGenerator()
    
    # Generate map based on choice
    if 'choice' in locals():
        if choice == "1":
            pdf_path = generator.generate_detailed_critical_habitat_map(longitude, latitude, location_name)
        elif choice == "3":
            pdf_path = generator.generate_overview_critical_habitat_map(longitude, latitude, location_name)
        elif choice == "4":
            # Custom settings
            base_map = input("Base map (World_Imagery/World_Topo_Map/World_Street_Map): ") or "World_Imagery"
            dpi = int(input("DPI (96/150/300): ") or "300")
            transparency = float(input("Habitat transparency (0.1-1.0, default 0.8): ") or "0.8")
            include_proposed = input("Include proposed habitat? (y/n, default y): ").lower() != 'n'
            
            pdf_path = generator.generate_critical_habitat_map_pdf(
                longitude, latitude, location_name, buffer_miles,
                base_map=base_map, dpi=dpi, habitat_transparency=transparency,
                include_proposed=include_proposed
            )
        else:
            # Standard map
            pdf_path = generator.generate_critical_habitat_map_pdf(
                longitude, latitude, location_name, buffer_miles
            )
    else:
        # Command line mode - standard map
        pdf_path = generator.generate_critical_habitat_map_pdf(
            longitude, latitude, location_name, buffer_miles
        )
    
    if pdf_path:
        print(f"\n✅ Success! Map features:")
        print(f"   • Critical habitat areas from USFWS data")
        print(f"   • Legend showing habitat classifications")
        print(f"   • Scale bar and north arrow")
        print(f"   • Location marker at specified coordinates")
        print(f"   • Professional layout with title and attribution")
        print(f"   • Final and proposed habitat designations")
    else:
        print("\n❌ Failed to generate map")


if __name__ == "__main__":
    main() 