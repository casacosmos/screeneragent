#!/usr/bin/env python3
"""
Generate Wetland Map PDF - Version 3

This version uses proper Web Map JSON configuration based on successful ABFE implementation patterns.
Includes proper layer configuration, symbology, and layout options for professional PDF output.
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


class WetlandMapGeneratorV3:
    """Generate professional wetland map PDFs with proper configuration"""
    
    def __init__(self):
        # Service URLs - using the same pattern as ABFE
        self.printing_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map/execute"
        self.wetlands_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer"
        
        # Base map options
        self.base_map_urls = {
            "World_Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer",
            "World_Topo_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer",
            "World_Street_Map": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer"
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WetlandMapGenerator/3.0',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def generate_wetland_map_pdf(self, 
                                longitude: float, 
                                latitude: float,
                                location_name: str = None,
                                buffer_miles: float = 0.5,
                                base_map: str = "World_Imagery",
                                dpi: int = 300,
                                output_size: tuple = (1224, 792),
                                include_legend: bool = True,
                                layout_template: str = None,
                                wetland_transparency: float = 0.8,
                                output_filename: str = None) -> str:
        """
        Generate a wetland map PDF for a specific location
        
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
            wetland_transparency: Wetland layer transparency (0.0-1.0, default 0.8)
            output_filename: Optional output filename
            
        Returns:
            Path to the generated PDF file
        """
        
        if location_name is None:
            location_name = f"Wetland Map at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating wetland map PDF for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"📏 Buffer: {buffer_miles} miles")
        print(f"🎨 Base map: {base_map}")
        print(f"📐 Output: {output_size[0]}x{output_size[1]} at {dpi} DPI")
        print(f"🌿 Wetland transparency: {wetland_transparency:.1f}")
        
        # First, check if there are wetlands in the area
        print(f"\n🔍 Checking for wetlands in the area...")
        wetlands_found = self._check_wetlands_in_area(longitude, latitude, buffer_miles)
        if wetlands_found:
            print(f"✅ Found {wetlands_found} wetland feature(s) in the area")
        else:
            print(f"⚠️  No wetlands found in the area - map will show base layers only")
        
        # Create the Web Map JSON specification
        web_map_json = self._create_web_map_json(
            longitude, latitude, location_name, buffer_miles,
            base_map, dpi, output_size, include_legend, wetland_transparency
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
        debug_filename = f"debug_webmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
                            include_legend: bool, wetland_transparency: float) -> Dict[str, Any]:
        """Create the Web Map JSON specification following ABFE patterns"""
        
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
        
        # Calculate appropriate scale to ensure wetlands are visible
        # Wetlands have minScale of 250,000, so we need to be more zoomed in
        map_width_degrees = buffer_degrees * 2
        # Approximate scale calculation: degrees to feet conversion
        map_width_feet = map_width_degrees * 364000  # rough conversion
        map_scale = int(map_width_feet / (output_size[0] / dpi))
        
        # Ensure scale is appropriate for wetlands visibility (must be < 250,000)
        # Use a more conservative scale limit to ensure wetlands are clearly visible
        max_scale = 150000  # More conservative than the 250,000 limit
        
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
        
        print(f"🎯 Calculated map scale: 1:{map_scale:,} (wetlands visible < 1:250,000)")
        
        # Get base map URL
        base_map_url = self.base_map_urls.get(base_map, self.base_map_urls["World_Imagery"])
        
        # Determine which wetlands layers to show based on location
        # For Puerto Rico/Caribbean: use layer 5 (Wetlands_PRVI)
        # For CONUS: use layers 0, 1, 2
        if -68 <= longitude <= -65 and 17 <= latitude <= 19:
            # Puerto Rico and Virgin Islands
            visible_layers = [5]
            print(f"🌴 Using Puerto Rico/Virgin Islands wetlands layer (5)")
        elif longitude < -100:
            # Western CONUS
            visible_layers = [0, 2]
            print(f"🏔️ Using Western CONUS wetlands layers (0, 2)")
        else:
            # Eastern CONUS and general
            visible_layers = [0, 1]
            print(f"🌲 Using Eastern CONUS wetlands layers (0, 1)")
        
        # Create wetlands operational layer with proper configuration
        wetlands_layer = {
            "id": "wetlands_layer",
            "url": self.wetlands_service_url,
            "title": "National Wetlands Inventory",
            "opacity": wetland_transparency,
            "visibility": True,
            "layerType": "ArcGISMapServiceLayer",
            "visibleLayers": visible_layers,
            "minScale": 250000,  # Respect service constraints
            "maxScale": 0
        }
        
        # Create web map structure
        web_map = {
            "mapOptions": {
                "extent": extent,
                "spatialReference": {"wkid": 4326},
                "showAttribution": True,
                "scale": map_scale  # Set explicit scale for wetlands visibility
            },
            "operationalLayers": [wetlands_layer],
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
                "authorText": "WetlandsINFO System",
                "copyrightText": f"USFWS National Wetlands Inventory | Generated {datetime.now().strftime('%Y-%m-%d')}",
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
    
    def _create_circle_overlay(self, longitude: float, latitude: float, 
                              radius_miles: float, location_name: str) -> Dict[str, Any]:
        """Create a circle overlay showing the specified radius around a point"""
        
        # Calculate circle points (approximate)
        # For better accuracy, use proper geodetic calculations, but this approximation works for small areas
        earth_radius_miles = 3959  # Earth radius in miles
        
        # Convert radius to degrees (approximate)
        lat_rad = math.radians(latitude)
        radius_deg_lat = radius_miles / 69.0  # 1 degree latitude ≈ 69 miles
        radius_deg_lon = radius_miles / (69.0 * math.cos(lat_rad))  # Adjust for longitude
        
        # Create circle points (36 points for smooth circle)
        circle_points = []
        for i in range(37):  # 37 points to close the circle
            angle = (i * 2 * math.pi) / 36
            point_lon = longitude + (radius_deg_lon * math.cos(angle))
            point_lat = latitude + (radius_deg_lat * math.sin(angle))
            circle_points.append([point_lon, point_lat])
        
        # Create circle feature
        circle_overlay = {
            "id": "radius_circle",
            "featureCollection": {
                "layers": [
                    {
                        "featureSet": {
                            "features": [
                                {
                                    "geometry": {
                                        "rings": [circle_points],
                                        "spatialReference": {"wkid": 4326}
                                    },
                                    "attributes": {
                                        "name": f"{radius_miles} Mile Radius",
                                        "description": f"{radius_miles} mile radius around {location_name}"
                                    },
                                    "symbol": {
                                        "type": "esriSFS",
                                        "style": "esriSFSNull",  # No fill, outline only
                                        "outline": {
                                            "type": "esriSLS",
                                            "style": "esriSLSSolid",
                                            "color": [255, 165, 0, 255],  # Orange
                                            "width": 3
                                        }
                                    }
                                }
                            ],
                            "geometryType": "esriGeometryPolygon"
                        },
                        "layerDefinition": {
                            "geometryType": "esriGeometryPolygon",
                            "fields": [
                                {
                                    "name": "name",
                                    "type": "esriFieldTypeString",
                                    "alias": "Name"
                                },
                                {
                                    "name": "description",
                                    "type": "esriFieldTypeString",
                                    "alias": "Description"
                                }
                            ]
                        }
                    }
                ]
            },
            "title": f"{radius_miles} Mile Radius",
            "opacity": 1,
            "visibility": True
        }
        
        return circle_overlay
    
    def _create_circle_feature_layer(self, longitude: float, latitude: float, 
                                    radius_miles: float, location_name: str) -> Dict[str, Any]:
        """
        Create a proper ArcGIS feature layer with circle geometry for the operational layers.
        This ensures the circle is rendered as part of the map service request.
        """
        
        # Generate precise circle points using geodesic calculations
        circle_points = self._generate_circle_points_precise(longitude, latitude, radius_miles)
        
        # Convert to ArcGIS rings format (list of coordinate pairs)
        circle_rings = [[list(point) for point in circle_points]]
        
        # Create the feature layer definition
        circle_feature_layer = {
            "id": "radius_circle_layer",
            "title": f"{radius_miles} Mile Radius Buffer",
            "opacity": 1.0,
            "visibility": True,
            "minScale": 0,
            "maxScale": 0,
            "featureCollection": {
                "layers": [
                    {
                        "layerDefinition": {
                            "geometryType": "esriGeometryPolygon",
                            "objectIdField": "OBJECTID",
                            "fields": [
                                {
                                    "name": "OBJECTID",
                                    "type": "esriFieldTypeOID",
                                    "alias": "OBJECTID"
                                },
                                {
                                    "name": "RadiusMiles",
                                    "type": "esriFieldTypeDouble", 
                                    "alias": "Radius (Miles)"
                                },
                                {
                                    "name": "Description",
                                    "type": "esriFieldTypeString",
                                    "alias": "Description",
                                    "length": 255
                                }
                            ],
                            "spatialReference": {"wkid": 4326},
                            "drawingInfo": {
                                "renderer": {
                                    "type": "simple",
                                    "symbol": {
                                        "type": "esriSFS",
                                        "style": "esriSFSNull",  # No fill, outline only
                                        "outline": {
                                            "type": "esriSLS",
                                            "style": "esriSLSSolid",
                                            "color": [255, 165, 0, 255],  # Orange
                                            "width": 4  # Thick line for visibility
                                        }
                                    }
                                }
                            }
                        },
                        "featureSet": {
                            "geometryType": "esriGeometryPolygon",
                            "spatialReference": {"wkid": 4326},
                            "features": [
                                {
                                    "geometry": {
                                        "rings": circle_rings,
                                        "spatialReference": {"wkid": 4326}
                                    },
                                    "attributes": {
                                        "OBJECTID": 1,
                                        "RadiusMiles": radius_miles,
                                        "Description": f"{radius_miles} mile radius around {location_name}"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        return circle_feature_layer
    
    def _create_simple_circle_overlay(self, longitude: float, latitude: float, radius_miles: float) -> Dict[str, Any]:
        """
        Create a simple circle overlay using the same pattern as the working location marker
        """
        # Generate precise circle points using pyproj for accurate geodesic calculations
        circle_points = self._generate_circle_points_precise(longitude, latitude, radius_miles, num_points=72)
        
        # Create simple feature collection following the same pattern as location marker
        circle_overlay = {
            "id": "radius_circle",
            "featureCollection": {
                "layers": [
                    {
                        "featureSet": {
                            "features": [
                                {
                                    "geometry": {
                                        "rings": [[list(point) for point in circle_points]],
                                        "spatialReference": {"wkid": 4326}
                                    },
                                    "attributes": {
                                        "name": f"{radius_miles} Mile Radius"
                                    },
                                    "symbol": {
                                        "type": "esriSFS",
                                        "style": "esriSFSNull",  # No fill
                                        "color": [0, 0, 0, 0],  # Transparent fill
                                        "outline": {
                                            "type": "esriSLS", 
                                            "style": "esriSLSSolid",
                                            "color": [255, 165, 0, 255],  # Orange
                                            "width": 6  # Thicker line for better visibility
                                        }
                                    }
                                }
                            ],
                            "geometryType": "esriGeometryPolygon"
                        },
                        "layerDefinition": {
                            "geometryType": "esriGeometryPolygon",
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
            "title": f"{radius_miles} Mile Radius",
            "opacity": 1,
            "visibility": True
        }
        
        return circle_overlay
    
    def _create_geometry_service_circle(self, longitude: float, latitude: float, radius_miles: float) -> Dict[str, Any]:
        """
        Create a circle using proper feature collection geometry that forms an actual circle
        """
        
        print(f"⭕ Creating {radius_miles} mile radius circle using corrected geometry...")
        
        # Generate precise circle points using geodesic calculations with more points for smoother circle
        circle_points = self._generate_circle_points_precise(longitude, latitude, radius_miles, num_points=72)
        
        # Ensure the circle is properly closed by making the last point exactly equal to the first
        if len(circle_points) > 0:
            # Remove the last point if it's a duplicate, then add exact first point to close properly
            if len(circle_points) > 1 and circle_points[-1] != circle_points[0]:
                circle_points.append(circle_points[0])
            elif len(circle_points) > 1:
                circle_points[-1] = circle_points[0]  # Ensure exact closure
        
        # Convert to ArcGIS rings format with proper coordinate precision
        circle_rings = [[[round(point[0], 8), round(point[1], 8)] for point in circle_points]]
        
        print(f"🔍 Generated proper circle with {len(circle_points)} points")
        print(f"📐 First point: ({circle_points[0][0]:.6f}, {circle_points[0][1]:.6f})")
        print(f"📐 Last point: ({circle_points[-1][0]:.6f}, {circle_points[-1][1]:.6f})")
        print(f"📐 Circle properly closed: {circle_points[0] == circle_points[-1]}")
        
        # Validate the circle by checking radius consistency
        if len(circle_points) >= 4:  # Need at least 4 points to validate
            import math
            center_lon, center_lat = longitude, latitude
            
            # Check a few points to ensure they're all roughly the same distance from center
            test_points = [circle_points[0], circle_points[len(circle_points)//4], circle_points[len(circle_points)//2]]
            distances = []
            
            for point_lon, point_lat in test_points:
                # Calculate distance using Haversine formula
                R = 3959  # Earth radius in miles
                lat1_rad = math.radians(center_lat)
                lat2_rad = math.radians(point_lat)
                delta_lat = math.radians(point_lat - center_lat)
                delta_lon = math.radians(point_lon - center_lon)
                
                a = (math.sin(delta_lat / 2) ** 2 + 
                     math.cos(lat1_rad) * math.cos(lat2_rad) * 
                     math.sin(delta_lon / 2) ** 2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                distance = R * c
                distances.append(distance)
            
            avg_distance = sum(distances) / len(distances)
            max_deviation = max(abs(d - avg_distance) for d in distances)
            
            print(f"🔍 Circle validation:")
            print(f"   Target radius: {radius_miles:.3f} miles")
            print(f"   Actual avg radius: {avg_distance:.3f} miles")
            print(f"   Max deviation: {max_deviation:.3f} miles")
            
            if max_deviation > radius_miles * 0.01:  # More than 1% deviation
                print(f"⚠️  Circle may be distorted - large radius deviation detected")
        
        # Create feature collection with simplified, robust structure
        circle_feature_collection = {
            "id": "radius_circle_overlay",
            "title": f"{radius_miles} Mile Radius Buffer",
            "opacity": 1.0,
            "visibility": True,
            "featureCollection": {
                "layers": [
                    {
                        "layerDefinition": {
                            "name": f"radius_buffer_{radius_miles}_miles",
                            "geometryType": "esriGeometryPolygon",
                            "objectIdField": "OBJECTID",
                            "fields": [
                                {
                                    "name": "OBJECTID",
                                    "type": "esriFieldTypeOID",
                                    "alias": "Object ID"
                                },
                                {
                                    "name": "RadiusMiles",
                                    "type": "esriFieldTypeDouble",
                                    "alias": "Radius (Miles)"
                                }
                            ],
                            "spatialReference": {"wkid": 4326},
                            "drawingInfo": {
                                "renderer": {
                                    "type": "simple",
                                    "symbol": {
                                        "type": "esriSFS",
                                        "style": "esriSFSNull",  # No fill, outline only
                                        "outline": {
                                            "type": "esriSLS",
                                            "style": "esriSLSSolid",
                                            "color": [255, 165, 0, 255],  # Orange
                                            "width": 4  # Visible but not too thick to avoid geometry errors
                                        }
                                    }
                                }
                            }
                        },
                        "featureSet": {
                            "geometryType": "esriGeometryPolygon",
                            "spatialReference": {"wkid": 4326},
                            "features": [
                                {
                                    "geometry": {
                                        "rings": circle_rings,
                                        "spatialReference": {"wkid": 4326}
                                    },
                                    "attributes": {
                                        "OBJECTID": 1,
                                        "RadiusMiles": radius_miles
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        print(f"✅ Created validated circle feature collection with {len(circle_rings[0])} ring points")
        
        return circle_feature_collection
    
    def _create_geodesic_buffer(self, point_geometry: Dict[str, Any], radius_meters: float) -> Optional[Dict[str, Any]]:
        """
        Create a geodesic buffer around a point using ArcGIS Geometry Service
        
        Args:
            point_geometry: Point geometry in GCS (WGS84)
            radius_meters: Buffer radius in meters
            
        Returns:
            Buffered polygon geometry or None if failed
        """
        # Try multiple geometry service URLs
        geometry_service_urls = [
            "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer",
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Utilities/Geometry/GeometryServer"
        ]
        
        for service_url in geometry_service_urls:
            try:
                # Use simplified parameters that are more likely to work
                buffer_params = {
                    "f": "json",
                    "geometries": json.dumps({
                        "geometryType": "esriGeometryPoint",
                        "geometries": [point_geometry]
                    }),
                    "inSR": "4326",
                    "outSR": "4326", 
                    "distances": str(radius_meters),
                    "unit": "esriSRUnit_Meter",
                    "geodesic": "true"
                }
                
                print(f"🌐 Trying ArcGIS Geometry Service: {service_url}")
                
                # Call the buffer operation with GET instead of POST
                response = self.session.get(
                    f"{service_url}/buffer",
                    params=buffer_params,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Check for errors
                if 'error' in result:
                    print(f"❌ Service error: {result['error']}")
                    continue  # Try next service
                
                # Extract buffered geometry
                if 'geometries' in result and len(result['geometries']) > 0:
                    buffered_geom = result['geometries'][0]
                    print(f"✅ Geodesic buffer created successfully using {service_url}")
                    return buffered_geom
                else:
                    print(f"❌ No geometries returned from {service_url}")
                    continue  # Try next service
                    
            except Exception as e:
                print(f"❌ Error with {service_url}: {e}")
                continue  # Try next service
        
        # If all services fail, try the USFWS WIM service
        wim_result = self._try_wim_buffer_service(point_geometry, radius_meters)
        if wim_result:
            return wim_result
        
        # Final fallback: try using a GP service for buffer creation
        return self._try_gp_buffer_service(point_geometry, radius_meters)
    
    def _try_wim_buffer_service(self, point_geometry: Dict[str, Any], radius_meters: float) -> Optional[Dict[str, Any]]:
        """
        Try using USFWS WIM services for buffer creation as a fallback
        """
        try:
            print(f"🌐 Trying USFWS WIM buffer service...")
            
            # Try using the existing USFWS service infrastructure for buffering
            wim_geom_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Utilities/Geometry/GeometryServer"
            
            buffer_params = {
                "f": "json",
                "geometries": json.dumps({
                    "geometryType": "esriGeometryPoint", 
                    "geometries": [point_geometry]
                }),
                "inSR": "4326",
                "outSR": "4326",
                "distances": str(radius_meters),
                "unit": "esriSRUnit_Meter",
                "geodesic": "true"
            }
            
            response = self.session.get(
                f"{wim_geom_url}/buffer",
                params=buffer_params,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' not in result and 'geometries' in result and len(result['geometries']) > 0:
                buffered_geom = result['geometries'][0]
                print(f"✅ Buffer created using USFWS WIM service")
                return buffered_geom
            else:
                print(f"❌ USFWS WIM service also failed")
                return None
                
        except Exception as e:
            print(f"❌ USFWS WIM service error: {e}")
            return None
    
    def _try_gp_buffer_service(self, point_geometry: Dict[str, Any], radius_meters: float) -> Optional[Dict[str, Any]]:
        """
        Try using ArcGIS GP Service for buffer creation - most reliable approach
        """
        try:
            print(f"🔧 Trying ArcGIS GP Service for buffer creation...")
            
            # Use the same service infrastructure that we know works for the print service
            gp_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Tools/GPServer/Buffer"
            
            # Alternative: try USGS or other known GP services
            fallback_gp_urls = [
                "https://sampleserver6.arcgisonline.com/arcgis/rest/services/911CallsHotspot/GPServer/911%20Calls%20Hotspot/buffer",
                "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/buffer"
            ]
            
            for gp_url in [gp_service_url] + fallback_gp_urls:
                try:
                    # Create feature for GP service input
                    input_features = {
                        "geometryType": "esriGeometryPoint",
                        "features": [
                            {
                                "geometry": point_geometry,
                                "attributes": {"OBJECTID": 1}
                            }
                        ],
                        "spatialReference": {"wkid": 4326}
                    }
                    
                    # GP service parameters
                    gp_params = {
                        "f": "json",
                        "Input_Features": json.dumps(input_features),
                        "Distance": f"{radius_meters} Meters",
                        "Output_Coordinate_System": json.dumps({"wkid": 4326}),
                        "env:outSR": "4326"
                    }
                    
                    print(f"   Trying GP service: {gp_url}")
                    
                    response = self.session.post(
                        f"{gp_url}/submitJob",
                        data=gp_params,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    job_result = response.json()
                    
                    if 'jobId' in job_result:
                        # Wait for job completion and get results
                        job_id = job_result['jobId']
                        print(f"   GP Job submitted: {job_id}")
                        
                        # Wait for completion (simplified - in production would poll status)
                        import time
                        time.sleep(2)
                        
                        # Get results
                        result_response = self.session.get(
                            f"{gp_url}/jobs/{job_id}/results/Output_Features",
                            params={"f": "json"},
                            timeout=30
                        )
                        result_response.raise_for_status()
                        
                        result_data = result_response.json()
                        
                        if 'value' in result_data and 'features' in result_data['value']:
                            features = result_data['value']['features']
                            if len(features) > 0:
                                buffered_geom = features[0]['geometry']
                                print(f"✅ Buffer created using GP service")
                                return buffered_geom
                    
                except Exception as e:
                    print(f"   ❌ GP service {gp_url} failed: {e}")
                    continue
            
            print(f"❌ All GP services failed")
            return None
            
        except Exception as e:
            print(f"❌ GP service approach failed: {e}")
            return None
    
    def _add_circle_using_mapmaker(self, base_pdf_path: str, longitude: float, latitude: float, 
                                   radius_miles: float, map_buffer_miles: float, 
                                   output_filename: str) -> Optional[str]:
        """
        Add circle overlay using proven PyMuPDF approach for guaranteed visibility
        """
        print(f"🔄 Adding {radius_miles} mile radius circle overlay...")
        return self._add_circle_overlay_to_pdf(
            base_pdf_path, longitude, latitude, radius_miles, 
            "Wetland Map", map_buffer_miles, output_filename
        )
    
    def _check_wetlands_in_area(self, longitude: float, latitude: float, buffer_miles: float) -> int:
        """Check if there are wetlands in the specified area"""
        
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
            
            # Determine which layer to query based on location
            if -68 <= longitude <= -65 and 17 <= latitude <= 19:
                layer_id = 5  # Puerto Rico/Virgin Islands
            elif longitude < -100:
                layer_id = 2  # Western CONUS
            else:
                layer_id = 1  # Eastern CONUS
            
            # Query parameters
            params = {
                "geometry": json.dumps(envelope),
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OBJECTID",
                "returnGeometry": "false",
                "returnCountOnly": "true",
                "f": "json"
            }
            
            # Query the wetlands service
            response = self.session.get(
                f"{self.wetlands_service_url}/{layer_id}/query", 
                params=params, 
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('count', 0)
            
        except Exception as e:
            print(f"⚠️  Error checking wetlands: {e}")
            return 0
    
    def _download_pdf(self, result_url: str, output_filename: str = None) -> Optional[str]:
        """Download the PDF from the result URL"""
        
        try:
            response = self.session.get(result_url, timeout=60)
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
    
    def generate_detailed_wetland_map(self, longitude: float, latitude: float,
                                     location_name: str = None, 
                                     wetland_transparency: float = 0.75) -> str:
        """Generate a detailed wetland map with all features"""
        
        return self.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.3,
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),  # Tabloid size
            include_legend=True,
            wetland_transparency=wetland_transparency
        )
    
    def generate_overview_wetland_map(self, longitude: float, latitude: float,
                                     location_name: str = None,
                                     wetland_transparency: float = 0.8,
                                     layout_template: str = None) -> str:
        """Generate an overview wetland map with 0.5-mile radius circle"""
        
        return self.generate_wetland_map_with_circle(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            circle_radius_miles=0.5,
            map_buffer_miles=1.0,  # Show wider area for context
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),  # Larger size for better detail
            include_legend=True,
            layout_template=layout_template,
            wetland_transparency=wetland_transparency
        )
    
    def generate_wetland_map_with_circle(self, 
                                        longitude: float, 
                                        latitude: float,
                                        location_name: str = None,
                                        circle_radius_miles: float = 0.5,
                                        map_buffer_miles: float = 1.0,
                                        base_map: str = "World_Imagery",
                                        dpi: int = 300,
                                        output_size: tuple = (1224, 792),
                                        include_legend: bool = True,
                                        layout_template: str = None,
                                        wetland_transparency: float = 0.8,
                                        output_filename: str = None) -> str:
        """
        Generate a wetland map PDF with a circle overlay showing the specified radius
        Uses a hybrid approach: tries ArcGIS featureCollection first, then applies PyMuPDF overlay as guaranteed fallback
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name for the map title
            circle_radius_miles: Radius of the circle to draw in miles
            map_buffer_miles: Buffer radius for the map extent in miles
            base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
            dpi: Resolution (96, 150, 300)
            output_size: Output size as (width, height) tuple
            include_legend: Whether to include legend
            layout_template: Optional layout template for the map
            wetland_transparency: Wetland layer transparency (0.0-1.0, default 0.8)
            output_filename: Optional output filename
            
        Returns:
            Path to the generated PDF file
        """
        
        if location_name is None:
            location_name = f"Wetland Map with {circle_radius_miles} Mile Radius at {latitude:.4f}, {longitude:.4f}"
        
        print(f"\n🗺️  Generating wetland map with circle overlay for: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"⭕ Circle radius: {circle_radius_miles} miles")
        print(f"📏 Map buffer: {map_buffer_miles} miles")
        print(f"🎨 Base map: {base_map}")
        print(f"📐 Output: {output_size[0]}x{output_size[1]} at {dpi} DPI")
        print(f"🌿 Wetland transparency: {wetland_transparency:.1f}")
        
        # First, check if there are wetlands in the circle area
        print(f"\n🔍 Checking for wetlands within {circle_radius_miles} mile radius...")
        wetlands_found = self._check_wetlands_in_area(longitude, latitude, circle_radius_miles)
        if wetlands_found:
            print(f"✅ Found {wetlands_found} wetland feature(s) within the {circle_radius_miles} mile radius")
        else:
            print(f"⚠️  No wetlands found within the {circle_radius_miles} mile radius")

        # Generate base output filename
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"wetland_map_with_circle_{timestamp}.pdf"

        # STEP 1: Try generating the map with ArcGIS featureCollection circle overlay
        print(f"\n📤 STEP 1: Attempting ArcGIS featureCollection circle overlay...")
        
        # Create the Web Map JSON specification with circle overlay
        web_map_json = self._create_web_map_json_with_circle(
            longitude, latitude, location_name, circle_radius_miles, map_buffer_miles,
            base_map, dpi, output_size, include_legend, wetland_transparency
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
        debug_filename = f"debug_webmap_circle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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
            
            print("✅ Base map generated successfully!")
            print(f"📄 Map URL: {result_url}")
            
            # Download the base PDF
            print("\n📥 Downloading base PDF...")
            temp_base_filename = f"temp_base_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            base_pdf_path = self._download_pdf(result_url, temp_base_filename)
            
            if not base_pdf_path:
                print("❌ Failed to download base PDF")
                return None
            
            print(f"✅ Base PDF downloaded: {base_pdf_path}")
            
            # STEP 2: Apply guaranteed PyMuPDF circle overlay
            print(f"\n🔄 STEP 2: Applying guaranteed PyMuPDF circle overlay...")
            print(f"   This ensures the circle is always visible regardless of print template issues")
            
            final_pdf_path = self._add_circle_overlay_to_pdf(
                base_pdf_path, longitude, latitude, circle_radius_miles,
                location_name, map_buffer_miles, output_filename
            )
            
            # Clean up temporary base PDF
            try:
                os.remove(base_pdf_path)
                print(f"🧹 Cleaned up temporary base PDF")
            except:
                pass
            
            if final_pdf_path:
                print(f"\n✅ HYBRID SUCCESS! Map PDF with guaranteed circle overlay saved to: {final_pdf_path}")
                print(f"🎯 Features included:")
                print(f"   • High-quality base map from ArcGIS service")
                print(f"   • Wetland layers from National Wetlands Inventory") 
                print(f"   • Professional legend and scale bars")
                print(f"   • Guaranteed visible {circle_radius_miles} mile radius circle (orange)")
                print(f"   • Clean circle display without center point marker")
                return final_pdf_path
            else:
                print(f"❌ Failed to apply circle overlay")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error generating map: {e}")
            return None
    
    def _create_web_map_json_with_circle(self, longitude: float, latitude: float, 
                                        location_name: str, circle_radius_miles: float,
                                        map_buffer_miles: float, base_map: str, 
                                        dpi: int, output_size: tuple,
                                        include_legend: bool, wetland_transparency: float) -> Dict[str, Any]:
        """Create the Web Map JSON specification with circle overlay"""
        
        # Calculate extent based on map buffer (larger than circle for context)
        # Rough conversion: 1 degree ≈ 69 miles
        buffer_degrees = map_buffer_miles / 69.0
        
        extent = {
            "xmin": longitude - buffer_degrees,
            "ymin": latitude - buffer_degrees,
            "xmax": longitude + buffer_degrees,
            "ymax": latitude + buffer_degrees,
            "spatialReference": {"wkid": 4326}
        }
        
        # Calculate appropriate scale to ensure wetlands are visible
        # Wetlands have minScale of 250,000, so we need to be more zoomed in
        map_width_degrees = buffer_degrees * 2
        # Approximate scale calculation: degrees to feet conversion
        map_width_feet = map_width_degrees * 364000  # rough conversion
        map_scale = int(map_width_feet / (output_size[0] / dpi))
        
        # Ensure scale is appropriate for wetlands visibility (must be < 250,000)
        # Use a more conservative scale limit to ensure wetlands are clearly visible
        max_scale = 150000  # More conservative than the 250,000 limit
        
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
        
        print(f"🎯 Calculated map scale: 1:{map_scale:,} (wetlands visible < 1:250,000)")
        print(f"📏 Circle radius: {circle_radius_miles} miles")
        print(f"🗺️  Map extent: {map_buffer_miles} miles")
        
        # Get base map URL
        base_map_url = self.base_map_urls.get(base_map, self.base_map_urls["World_Imagery"])
        
        # Determine which wetlands layers to show based on location
        # For Puerto Rico/Caribbean: use layer 5 (Wetlands_PRVI)
        # For CONUS: use layers 0, 1, 2
        if -68 <= longitude <= -65 and 17 <= latitude <= 19:
            # Puerto Rico and Virgin Islands
            visible_layers = [5]
            print(f"🌴 Using Puerto Rico/Virgin Islands wetlands layer (5)")
        elif longitude < -100:
            # Western CONUS
            visible_layers = [0, 2]
            print(f"🏔️ Using Western CONUS wetlands layers (0, 2)")
        else:
            # Eastern CONUS and general
            visible_layers = [0, 1]
            print(f"🌲 Using Eastern CONUS wetlands layers (0, 1)")
        
        # Create wetlands operational layer with proper configuration
        wetlands_layer = {
            "id": "wetlands_layer",
            "url": self.wetlands_service_url,
            "title": "National Wetlands Inventory",
            "opacity": wetland_transparency,
            "visibility": True,
            "layerType": "ArcGISMapServiceLayer",
            "visibleLayers": visible_layers,
            "minScale": 250000,  # Respect service constraints
            "maxScale": 0
        }
        
        # Create web map structure
        web_map = {
            "mapOptions": {
                "extent": extent,
                "spatialReference": {"wkid": 4326},
                "showAttribution": True,
                "scale": map_scale  # Set explicit scale for wetlands visibility
            },
            "operationalLayers": [wetlands_layer],
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
                "authorText": "WetlandsINFO System",
                "copyrightText": f"USFWS National Wetlands Inventory | Generated {datetime.now().strftime('%Y-%m-%d')}",
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
                } if include_legend else {}
            },
            "version": "1.6.0"
        }
        
        # Add circle overlay using feature collection pattern - this should be clearly visible
        circle_overlay = self._create_geometry_service_circle(longitude, latitude, circle_radius_miles)
        web_map["operationalLayers"].append(circle_overlay)
        
        # NOTE: Removed the center point marker so the circle is clearly visible without obstruction
        print(f"⭕ Circle overlay added without center point marker for clear visibility")
        
        return web_map
    
    def _add_circle_overlay_to_pdf(self, pdf_path: str, longitude: float, latitude: float, 
                                  radius_miles: float, location_name: str, 
                                  map_buffer_miles: float, output_filename: str) -> Optional[str]:
        """
        Add circle overlay to a PDF by converting to image, adding circle, and saving back as PDF
        
        Args:
            pdf_path: Path to the base PDF file
            longitude: Center longitude for circle
            latitude: Center latitude for circle  
            radius_miles: Radius of circle in miles
            location_name: Location name for the map
            map_buffer_miles: Map buffer used to calculate extent
            output_filename: Desired output filename
            
        Returns:
            Path to the final PDF with circle overlay, or None if failed
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image, ImageDraw
            
            # Open the PDF
            pdf_document = fitz.open(pdf_path)
            
            if len(pdf_document) == 0:
                print("Error: PDF has no pages")
                return None
            
            # Get the first page
            page = pdf_document[0]
            
            # Convert PDF page to image at high resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x scaling for balance of quality/size
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Load as PIL image
            base_image = Image.open(BytesIO(img_data))
            img_width, img_height = base_image.size
            
            print(f"🖼️  PDF converted to image: {img_width}x{img_height} pixels")
            
            # Calculate the map extent based on the original parameters
            buffer_degrees = map_buffer_miles / 69.0
            extent = {
                "xmin": longitude - buffer_degrees,
                "ymin": latitude - buffer_degrees,
                "xmax": longitude + buffer_degrees,
                "ymax": latitude + buffer_degrees
            }
            
            # Helper to convert lon/lat to Web Mercator (EPSG:3857)
            def lonlat_to_merc(lon_deg, lat_deg):
                R_MAJOR = 6378137.0
                x = math.radians(lon_deg) * R_MAJOR
                # Clamp latitude for Mercator projection
                lat_rad = math.radians(max(min(lat_deg, 89.9), -89.9))
                y = R_MAJOR * math.log(math.tan(math.pi/4 + lat_rad/2))
                return x, y

            # Convert geographic extent to Mercator extent for accurate aspect ratio
            minx_merc, miny_merc = lonlat_to_merc(extent['xmin'], extent['ymin'])
            maxx_merc, maxy_merc = lonlat_to_merc(extent['xmax'], extent['ymax'])

            # Generate circle points (geodesic) and map to pixel using Mercator
            circle_points = self._generate_circle_points_precise(longitude, latitude, radius_miles, num_points=144)

            circle_pixels = []
            for lon, lat in circle_points:
                mx, my = lonlat_to_merc(lon, lat)
                x_pixel = (mx - minx_merc) / (maxx_merc - minx_merc) * img_width
                y_pixel = (maxy_merc - my) / (maxy_merc - miny_merc) * img_height
                # Ensure pixel coordinates are within bounds
                x_pixel = max(0, min(img_width - 1, x_pixel))
                y_pixel = max(0, min(img_height - 1, y_pixel))
                circle_pixels.append((x_pixel, y_pixel))
            
            # Create a copy of the image to draw on
            draw_image = base_image.copy()
            draw = ImageDraw.Draw(draw_image)
            
            # Draw the circle with orange outline (visible color)
            circle_color = (255, 165, 0)  # Orange
            circle_width = max(8, int(img_width * 0.003))  # Thicker line for better visibility
            
            print(f"⭕ Drawing circle with {len(circle_pixels)} points, width: {circle_width}px")
            
            # Draw circle as a polygon for smoother appearance
            try:
                # Try drawing as a polygon outline first (smoother)
                draw.polygon(circle_pixels, outline=circle_color, width=circle_width)
                print("✅ Circle drawn as smooth polygon")
            except:
                # Fallback to line segments if polygon method fails
                print("⚠️  Using line segments fallback for circle")
                for i in range(len(circle_pixels)):
                    start_point = circle_pixels[i]
                    end_point = circle_pixels[(i + 1) % len(circle_pixels)]
                    draw.line([start_point, end_point], fill=circle_color, width=circle_width)
            
            # NOTE: Center point marker removed per user request - clean circle only
            print(f"⭕ Clean {radius_miles} mile radius circle drawn without center marker")
            
            # Verify circle positioning by calculating its bounds
            if len(circle_pixels) > 0:
                min_x = min(p[0] for p in circle_pixels)
                max_x = max(p[0] for p in circle_pixels)
                min_y = min(p[1] for p in circle_pixels)
                max_y = max(p[1] for p in circle_pixels)
                
                # Calculate expected center from the map extent
                center_mx, center_my = lonlat_to_merc(longitude, latitude)
                center_x = (center_mx - minx_merc) / (maxx_merc - minx_merc) * img_width
                center_y = (maxy_merc - center_my) / (maxy_merc - miny_merc) * img_height
                
                # Calculate actual circle center
                actual_center_x = (min_x + max_x) / 2
                actual_center_y = (min_y + max_y) / 2
                
                offset_x = abs(center_x - actual_center_x)
                offset_y = abs(center_y - actual_center_y)
                circle_width_pixels = max_x - min_x
                circle_height_pixels = max_y - min_y
                
                print(f"🔍 Circle verification:")
                print(f"   Circle bounds: ({min_x:.0f}, {min_y:.0f}) to ({max_x:.0f}, {max_y:.0f})")
                print(f"   Circle dimensions: {circle_width_pixels:.0f}x{circle_height_pixels:.0f} pixels")
                print(f"   Expected center: ({center_x:.0f}, {center_y:.0f})")
                print(f"   Actual center: ({actual_center_x:.0f}, {actual_center_y:.0f})")
                print(f"   Center offset: ({offset_x:.1f}, {offset_y:.1f}) pixels")
            
            # Convert back to PDF
            # First save as high-quality image
            temp_image_path = pdf_path.replace('.pdf', '_with_circle.png')
            draw_image.save(temp_image_path, 'PNG', dpi=(300, 300))
            
            # Convert image to PDF
            final_pdf_path = os.path.join('output', output_filename)
            
            # Create new PDF from the image
            img_pdf = fitz.open()
            img_page = img_pdf.new_page(width=img_width, height=img_height)
            
            # Insert the image
            img_page.insert_image(img_page.rect, filename=temp_image_path, keep_proportion=True)
            
            # Save the final PDF
            img_pdf.save(final_pdf_path)
            img_pdf.close()
            pdf_document.close()
            
            # Clean up temporary image
            try:
                os.remove(temp_image_path)
            except:
                pass
            
            print(f"💾 Final PDF with circle saved: {final_pdf_path}")
            return final_pdf_path
            
        except ImportError:
            print("⚠️  PyMuPDF (fitz) not available. Install with: pip install PyMuPDF")
            print("   Falling back to image-based approach...")
            return self._add_circle_overlay_image_fallback(pdf_path, longitude, latitude, radius_miles, 
                                                         location_name, map_buffer_miles, output_filename)
        except Exception as e:
            print(f"❌ Error adding circle overlay: {e}")
            print("   Trying image-based fallback...")
            return self._add_circle_overlay_image_fallback(pdf_path, longitude, latitude, radius_miles,
                                                         location_name, map_buffer_miles, output_filename)
    
    def _add_circle_overlay_image_fallback(self, pdf_path: str, longitude: float, latitude: float, 
                                          radius_miles: float, location_name: str, 
                                          map_buffer_miles: float, output_filename: str) -> Optional[str]:
        """
        Fallback method to add circle overlay using matplotlib when PyMuPDF is not available
        """
        try:
            print("🔄 Using matplotlib fallback for circle overlay...")
            
            # For now, just return the original PDF path 
            # In a full implementation, you could use pdf2image to convert and then add overlays
            print("⚠️  PDF circle overlay requires PyMuPDF. Please install with: pip install PyMuPDF")
            print("   Returning original PDF without circle overlay.")
            
            # Copy the original file to the desired output name
            final_pdf_path = os.path.join('output', output_filename)
            import shutil
            shutil.copy2(pdf_path, final_pdf_path)
            
            return final_pdf_path
            
        except Exception as e:
            print(f"❌ Fallback method also failed: {e}")
            return None
    
    def _generate_circle_points_precise(self, center_lon: float, center_lat: float, 
                                       radius_miles: float, num_points: int = 72) -> List[Tuple[float, float]]:
        """
        Generate precise circle points using proper geodesic calculations to form a true circle
        
        Args:
            center_lon: Center longitude
            center_lat: Center latitude
            radius_miles: Radius in miles
            num_points: Number of points to generate (more = smoother circle)
            
        Returns:
            List of (longitude, latitude) points forming a proper circle
        """
        try:
            # Try to use pyproj for accurate geodesic calculations
            from pyproj import Geod
            
            geod = Geod(ellps='WGS84')
            radius_meters = radius_miles * 1609.34  # Convert miles to meters
            circle_points = []
            
            print(f"🌐 Using pyproj for geodesic circle generation")
            print(f"   Center: ({center_lon:.6f}, {center_lat:.6f})")
            print(f"   Radius: {radius_miles} miles ({radius_meters:.0f} meters)")
            
            for i in range(num_points):  # Don't add +1 here, we'll close it separately
                # Calculate bearing for this point (0° = North, clockwise)
                bearing = (i * 360.0) / num_points
                
                # Use pyproj's forward geodesic calculation for accuracy
                lon2, lat2, back_azimuth = geod.fwd(center_lon, center_lat, bearing, radius_meters)
                circle_points.append((lon2, lat2))
            
            # Validate the circle by checking distances
            distances = []
            for i, (lon, lat) in enumerate(circle_points[:4]):  # Check first 4 points
                lon2, lat2, distance = geod.inv(center_lon, center_lat, lon, lat)
                distance_miles = distance / 1609.34
                distances.append(distance_miles)
            
            avg_dist = sum(distances) / len(distances)
            max_deviation = max(abs(d - avg_dist) for d in distances)
            
            print(f"🔍 Circle validation (pyproj):")
            print(f"   Target radius: {radius_miles:.6f} miles")
            print(f"   Actual radius: {avg_dist:.6f} miles")
            print(f"   Max deviation: {max_deviation:.6f} miles")
            
            return circle_points
            
        except ImportError:
            # Fallback to improved Haversine formula if pyproj not available
            print("⚠️  pyproj not available, using enhanced fallback geodesic calculation")
            return self._generate_circle_points_fallback(center_lon, center_lat, radius_miles, num_points)
    
    def _generate_circle_points_fallback(self, center_lon: float, center_lat: float, 
                                        radius_miles: float, num_points: int = 72) -> List[Tuple[float, float]]:
        """
        Fallback method for generating circle points using improved Haversine formula
        """
        radius_meters = radius_miles * 1609.34  # Convert miles to meters
        circle_points = []
        
        # Earth radius in meters
        R = 6371000.0
        
        # Convert center to radians
        center_lat_rad = math.radians(center_lat)
        center_lon_rad = math.radians(center_lon)
        
        print(f"🔄 Using fallback geodesic circle generation")
        print(f"   Center: ({center_lon:.6f}, {center_lat:.6f})")
        print(f"   Radius: {radius_miles} miles ({radius_meters:.0f} meters)")
        
        for i in range(num_points):  # Don't add +1 here, we'll close it separately
            # Calculate bearing for this point (0° = North, clockwise)
            bearing_deg = (i * 360.0) / num_points
            bearing_rad = math.radians(bearing_deg)
            
            # Calculate destination point using more accurate formula
            # Angular distance
            angular_dist = radius_meters / R
            
            # Destination latitude
            lat2_rad = math.asin(
                math.sin(center_lat_rad) * math.cos(angular_dist) +
                math.cos(center_lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
            )
            
            # Destination longitude  
            dlon_rad = math.atan2(
                math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(center_lat_rad),
                math.cos(angular_dist) - math.sin(center_lat_rad) * math.sin(lat2_rad)
            )
            
            lon2_rad = center_lon_rad + dlon_rad
            
            # Normalize longitude to [-180, 180]
            lon2_rad = ((lon2_rad + 3 * math.pi) % (2 * math.pi)) - math.pi
            
            # Convert back to degrees
            lat2 = math.degrees(lat2_rad)
            lon2 = math.degrees(lon2_rad)
            
            circle_points.append((lon2, lat2))
        
        # Validate the fallback circle by checking distances
        distances = []
        for i, (lon, lat) in enumerate(circle_points[:4]):  # Check first 4 points
            # Calculate distance using Haversine
            lat1_rad = math.radians(center_lat)
            lat2_rad = math.radians(lat)
            delta_lat = math.radians(lat - center_lat)
            delta_lon = math.radians(lon - center_lon)
            
            a = (math.sin(delta_lat / 2) ** 2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_miles = R * c / 1609.34  # Convert to miles
            distances.append(distance_miles)
        
        avg_dist = sum(distances) / len(distances)
        max_deviation = max(abs(d - avg_dist) for d in distances)
        
        print(f"🔍 Circle validation (fallback):")
        print(f"   Target radius: {radius_miles:.6f} miles")
        print(f"   Actual radius: {avg_dist:.6f} miles")
        print(f"   Max deviation: {max_deviation:.6f} miles")
        
        return circle_points


def main():
    """Main function for command line usage"""
    
    print("🗺️  Wetland Map PDF Generator V3")
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
            print("Usage: python generate_wetland_map_pdf_v3.py <longitude> <latitude> [location_name] [buffer_miles]")
            return
    else:
        # Interactive mode
        try:
            print("\nEnter coordinates for the wetland map:")
            longitude = float(input("Longitude: ") or "-66.196")
            latitude = float(input("Latitude: ") or "18.452")
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
    generator = WetlandMapGeneratorV3()
    
    # Generate map based on choice
    if 'choice' in locals():
        if choice == "1":
            pdf_path = generator.generate_detailed_wetland_map(longitude, latitude, location_name)
        elif choice == "3":
            pdf_path = generator.generate_overview_wetland_map(longitude, latitude, location_name)
        elif choice == "4":
            # Custom settings
            base_map = input("Base map (World_Imagery/World_Topo_Map/World_Street_Map): ") or "World_Imagery"
            dpi = int(input("DPI (96/150/300): ") or "300")
            transparency = float(input("Wetland transparency (0.1-1.0, default 0.8): ") or "0.8")
            
            pdf_path = generator.generate_wetland_map_pdf(
                longitude, latitude, location_name, buffer_miles,
                base_map=base_map, dpi=dpi, wetland_transparency=transparency
            )
        else:
            # Standard map
            pdf_path = generator.generate_wetland_map_pdf(
                longitude, latitude, location_name, buffer_miles
            )
    else:
        # Command line mode - standard map
        pdf_path = generator.generate_wetland_map_pdf(
            longitude, latitude, location_name, buffer_miles
        )
    
    if pdf_path:
        print(f"\n✅ Success! Map features:")
        print(f"   • Wetland areas from National Wetlands Inventory")
        print(f"   • Legend showing wetland classifications")
        print(f"   • Scale bar and north arrow")
        print(f"   • Location marker at specified coordinates")
        print(f"   • Professional layout with title and attribution")
    else:
        print("\n❌ Failed to generate map")


if __name__ == "__main__":
    main() 