#!/usr/bin/env python3
"""
Wetland Location Analysis Library

This module provides comprehensive wetland analysis capabilities:
- WetlandLocationAnalyzer: Core analysis class for wetland data queries
- Checks if coordinates lie within wetland territories
- Finds nearest wetlands with progressive search radii
- Provides detailed wetland classification and characteristics
- Includes riparian areas and watershed information
- Generates formatted reports and saves results to JSON files

For command-line usage, use main.py instead of running this module directly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wetlands_client import WetlandsClient, WetlandInfo
import json
import math
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime


class WetlandLocationAnalyzer:
    """Analyzes wetland locations and finds nearest wetlands"""
    
    def __init__(self):
        self.client = WetlandsClient()
        self.search_radius_miles = [0.1, 0.5, 1.0, 2.0, 5.0]  # Progressive search radii
    
    def analyze_location(self, longitude: float, latitude: float, 
                        location_name: str = None) -> Dict[str, Any]:
        """
        Comprehensive wetland analysis for a location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            
        Returns:
            Dictionary with wetland analysis results
        """
        
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        print(f"\n{'='*80}")
        print(f"WETLAND LOCATION ANALYSIS")
        print(f"{'='*80}")
        print(f"📍 Location: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"🕒 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Query wetland data at the exact point
        print(f"\n🔍 Checking for wetlands at exact coordinates...")
        point_data = self.client.query_point_wetland_info(
            longitude, latitude, 
            include_riparian=True, 
            include_watershed=True
        )
    
    def analyze_polygon(self, polygon_coords: List[Tuple[float, float]], 
                       location_name: str = None) -> Dict[str, Any]:
        """
        Comprehensive wetland analysis for a polygon area
        
        Args:
            polygon_coords: List of (longitude, latitude) tuples defining the polygon
            location_name: Optional location name
            
        Returns:
            Dictionary with wetland analysis results
        """
        
        # Calculate centroid
        lon_sum = sum(coord[0] for coord in polygon_coords)
        lat_sum = sum(coord[1] for coord in polygon_coords)
        centroid = (lon_sum / len(polygon_coords), lat_sum / len(polygon_coords))
        
        if location_name is None:
            location_name = f"Polygon area (centroid: {centroid[0]:.6f}, {centroid[1]:.6f})"
        
        print(f"\n{'='*80}")
        print(f"WETLAND POLYGON ANALYSIS")
        print(f"{'='*80}")
        print(f"📍 Location: {location_name}")
        print(f"📐 Polygon vertices: {len(polygon_coords)}")
        print(f"📍 Centroid: {centroid[0]:.6f}, {centroid[1]:.6f}")
        print(f"🕒 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Query wetland data within the polygon
        print(f"\n🔍 Checking for wetlands within polygon area...")
        polygon_data = self.client.query_polygon_wetland_info(
            polygon_coords, 
            include_riparian=True, 
            include_watershed=True
        )
        
        results = {
            'location': location_name,
            'coordinates': centroid,
            'polygon_coords': polygon_coords,
            'query_time': datetime.now().isoformat(),
            'is_in_wetland': polygon_data.has_wetland_data,
            'wetlands_at_location': [],
            'nearest_wetlands': [],
            'riparian_areas': [],
            'watersheds': [],
            'search_summary': {
                'wetlands_found_in_polygon': 0,
                'total_wetland_area': 0,
                'polygon_area_acres': self._calculate_polygon_area(polygon_coords),
                'wetland_coverage_percent': 0
            }
        }
        
        # Process wetlands within polygon
        if polygon_data.has_wetland_data:
            print(f"✅ Found {len(polygon_data.wetlands)} wetland(s) within polygon!")
            results['wetlands_at_location'] = self._process_wetlands(polygon_data.wetlands)
            results['search_summary']['wetlands_found_in_polygon'] = len(polygon_data.wetlands)
            
            # Calculate total wetland area
            total_area = sum(w['area_acres'] for w in results['wetlands_at_location'] if w['area_acres'])
            results['search_summary']['total_wetland_area'] = round(total_area, 2)
            
            # Calculate coverage percentage
            if results['search_summary']['polygon_area_acres'] > 0:
                coverage = (total_area / results['search_summary']['polygon_area_acres']) * 100
                results['search_summary']['wetland_coverage_percent'] = round(coverage, 1)
        else:
            print(f"❌ No wetlands found within polygon area")
        
        # Process riparian areas
        if polygon_data.has_riparian_data:
            print(f"\n🌊 Found {len(polygon_data.riparian_areas)} riparian area(s)")
            results['riparian_areas'] = self._process_riparian_areas(polygon_data.riparian_areas)
        
        # Process watersheds
        if polygon_data.has_watershed_data:
            print(f"\n💧 Found {len(polygon_data.watersheds)} watershed(s)")
            results['watersheds'] = self._process_watersheds(polygon_data.watersheds)
        
        # Add analysis and recommendations
        results['analysis'] = self._generate_polygon_analysis(results)
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def analyze_location(self, longitude: float, latitude: float, 
                        location_name: str = None) -> Dict[str, Any]:
        """
        Comprehensive wetland analysis for a location
        
        Args:
            longitude: Longitude coordinate
            latitude: Latitude coordinate
            location_name: Optional location name
            
        Returns:
            Dictionary with wetland analysis results
        """
        
        if location_name is None:
            location_name = f"({longitude}, {latitude})"
        
        print(f"\n{'='*80}")
        print(f"WETLAND LOCATION ANALYSIS")
        print(f"{'='*80}")
        print(f"📍 Location: {location_name}")
        print(f"📍 Coordinates: {longitude}, {latitude}")
        print(f"🕒 Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Query wetland data at the exact point
        print(f"\n🔍 Checking for wetlands at exact coordinates...")
        point_data = self.client.query_point_wetland_info(
            longitude, latitude, 
            include_riparian=True, 
            include_watershed=True
        )
        
        results = {
            'location': location_name,
            'coordinates': (longitude, latitude),
            'query_time': datetime.now().isoformat(),
            'is_in_wetland': point_data.has_wetland_data,
            'wetlands_at_location': [],
            'nearest_wetlands': [],
            'riparian_areas': [],
            'watersheds': [],
            'search_summary': {
                'wetlands_found_at_location': 0,
                'nearest_wetlands_found': 0,
                'search_radius_used': 0,
                'total_wetlands_analyzed': 0
            }
        }
        
        # Process wetlands at exact location
        if point_data.has_wetland_data:
            print(f"✅ Found {len(point_data.wetlands)} wetland(s) at this location!")
            results['wetlands_at_location'] = self._process_wetlands(point_data.wetlands)
            results['search_summary']['wetlands_found_at_location'] = len(point_data.wetlands)
        else:
            print(f"❌ No wetlands found at exact coordinates")
        
        # Progressive search for nearby wetlands if not at exact location
        if not point_data.has_wetland_data:
            print(f"\n🔍 Searching for wetlands within 0.5 mile radius...")
            
            # First search within 0.5 miles
            nearby_wetlands = self._find_wetlands_in_radius(longitude, latitude, radius_miles=0.5)
            
            if nearby_wetlands:
                results['nearest_wetlands'] = nearby_wetlands[:10]  # Limit to 10 nearest
                results['search_summary']['nearest_wetlands_found'] = len(nearby_wetlands)
                results['search_summary']['search_radius_used'] = 0.5
                print(f"✅ Found {len(nearby_wetlands)} wetland(s) within 0.5 miles")
            else:
                print(f"❌ No wetlands found within 0.5 miles")
                print(f"\n🔍 Expanding search to 1.0 mile radius...")
                
                # Expand search to 1.0 miles
                nearby_wetlands = self._find_wetlands_in_radius(longitude, latitude, radius_miles=1.0)
                
                if nearby_wetlands:
                    results['nearest_wetlands'] = nearby_wetlands[:10]  # Limit to 10 nearest
                    results['search_summary']['nearest_wetlands_found'] = len(nearby_wetlands)
                    results['search_summary']['search_radius_used'] = 1.0
                    print(f"✅ Found {len(nearby_wetlands)} wetland(s) within 1.0 mile")
                else:
                    print(f"❌ No wetlands found within 1.0 mile")
                    results['search_summary']['search_radius_used'] = 1.0
        else:
            # If wetlands found at exact location, still search nearby for context
            print(f"\n🔍 Searching for additional wetlands within 0.5 mile radius...")
            
            nearby_wetlands = self._find_wetlands_in_radius(longitude, latitude, radius_miles=0.5)
            if nearby_wetlands:
                # Filter out wetlands already found at exact location
                exact_wetland_ids = {w.wetland_id for w in point_data.wetlands}
                nearby_wetlands = [w for w in nearby_wetlands 
                                 if w['wetland'].wetland_id not in exact_wetland_ids]
                
                if nearby_wetlands:
                    results['nearest_wetlands'] = nearby_wetlands[:10]  # Limit to 10 nearest
                    results['search_summary']['nearest_wetlands_found'] = len(nearby_wetlands)
                    results['search_summary']['search_radius_used'] = 0.5
                    print(f"✅ Found {len(nearby_wetlands)} additional wetland(s) within 0.5 miles")
        
        # Process riparian areas
        if point_data.has_riparian_data:
            print(f"\n🌊 Found {len(point_data.riparian_areas)} riparian area(s)")
            results['riparian_areas'] = self._process_riparian_areas(point_data.riparian_areas)
        
        # Process watersheds
        if point_data.has_watershed_data:
            print(f"\n💧 Found {len(point_data.watersheds)} watershed(s)")
            results['watersheds'] = self._process_watersheds(point_data.watersheds)
        
        # Calculate total wetlands analyzed
        results['search_summary']['total_wetlands_analyzed'] = (
            results['search_summary']['wetlands_found_at_location'] + 
            results['search_summary']['nearest_wetlands_found']
        )
        
        # Add analysis and recommendations
        results['analysis'] = self._generate_analysis(results)
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _find_wetlands_in_radius(self, longitude: float, latitude: float, 
                                radius_miles: float = 0.5) -> List[Dict[str, Any]]:
        """Find wetlands within a specific radius with improved efficiency"""
        
        # Validate input parameters
        self._validate_coordinates_and_radius(longitude, latitude, radius_miles)
        
        # Calculate search bounding box
        bbox = self._calculate_search_bbox(longitude, latitude, radius_miles)
        print(f"  📍 Search area: {bbox['min_lat']:.4f}°N to {bbox['max_lat']:.4f}°N, "
              f"{bbox['min_lon']:.4f}°W to {bbox['max_lon']:.4f}°W")
        
        # Query and process wetlands
        try:
            wetlands = self.client.query_wetlands_by_bbox(
                bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat'], source='both'
            )
            
            if not wetlands:
                print(f"  ❌ No wetlands found in bounding box")
                return []
            
            print(f"  🔍 Found {len(wetlands)} potential wetland(s) in bounding box")
            return self._process_wetlands_with_distance(wetlands, longitude, latitude, radius_miles)
            
        except Exception as e:
            print(f"  ⚠️  Error searching within {radius_miles} miles: {e}")
            import traceback
            print(f"  🔍 Error details: {traceback.format_exc()}")
            return []
    
    def _validate_coordinates_and_radius(self, longitude: float, latitude: float, radius_miles: float):
        """Validate input coordinates and radius"""
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90) or radius_miles <= 0:
            raise ValueError(f"Invalid coordinates ({longitude}, {latitude}) or radius ({radius_miles})")
    
    def _calculate_search_bbox(self, longitude: float, latitude: float, radius_miles: float) -> Dict[str, float]:
        """Calculate bounding box for wetland search"""
        lat_delta = radius_miles / 69.0  # 1 degree latitude ≈ 69 miles
        lon_delta = radius_miles / (69.0 * math.cos(math.radians(latitude)))  # Cosine correction
        
        return {
            'min_lon': max(longitude - lon_delta, -180.0),
            'max_lon': min(longitude + lon_delta, 180.0),
            'min_lat': max(latitude - lat_delta, -90.0),
            'max_lat': min(latitude + lat_delta, 90.0)
        }
    
    def _process_wetlands_with_distance(self, wetlands: List, longitude: float, 
                                       latitude: float, radius_miles: float) -> List[Dict[str, Any]]:
        """Process wetlands and calculate distances"""
        wetlands_with_distance = []
        precise_count = 0
        estimated_count = 0
        
        for wetland in wetlands:
            wetland_info = self._create_wetland_distance_info(
                wetland, longitude, latitude, radius_miles
            )
            
            if wetland_info:
                wetlands_with_distance.append(wetland_info)
                if wetland_info['coordinate_precision'] == 'precise':
                    precise_count += 1
                else:
                    estimated_count += 1
        
        # Sort by precision first, then by distance
        wetlands_with_distance.sort(key=lambda x: (
            x['coordinate_precision'] == 'estimated',
            x['distance_miles']
        ))
        
        # Report results
        if precise_count > 0:
            print(f"  ✅ {precise_count} wetland(s) with precise coordinates within {radius_miles} miles")
        if estimated_count > 0:
            print(f"  📍 {estimated_count} wetland(s) with estimated coordinates included")
        
        return wetlands_with_distance
    
    def _create_wetland_distance_info(self, wetland, longitude: float, latitude: float, 
                                     radius_miles: float) -> Optional[Dict[str, Any]]:
        """Create wetland info with distance calculation"""
        wetland_lon, wetland_lat = self._get_wetland_centroid(wetland)
        
        # Handle wetlands with precise coordinates
        if wetland_lon and wetland_lat and wetland_lon != "NEEDS_GEOMETRY":
            try:
                distance = self._calculate_distance(longitude, latitude, wetland_lon, wetland_lat)
                
                # Only include if within radius
                if distance <= radius_miles:
                    return {
                        'wetland': self._create_enhanced_wetland_info(wetland),
                        'distance_miles': round(distance, 2),
                        'bearing': self._calculate_bearing(longitude, latitude, wetland_lon, wetland_lat),
                        'search_radius': radius_miles,
                        'centroid': (wetland_lon, wetland_lat),
                        'coordinate_precision': 'precise'
                    }
            except Exception as e:
                print(f"    ⚠️  Error calculating distance for wetland: {e}")
                return None
        
        # Handle wetlands without precise coordinates
        elif wetland_lon == "NEEDS_GEOMETRY":
            return {
                'wetland': self._create_enhanced_wetland_info(wetland),
                'distance_miles': round(radius_miles * 0.8, 2),  # Conservative estimate
                'bearing': 'Unknown',
                'search_radius': radius_miles,
                'centroid': None,
                'coordinate_precision': 'estimated'
            }
        
        return None
    
    def _find_nearest_wetlands(self, longitude: float, latitude: float) -> List[Dict[str, Any]]:
        """Find nearest wetlands using expanding search radius"""
        
        nearest_wetlands = []
        
        for radius in self.search_radius_miles:
            print(f"\n  🔍 Searching within {radius} mile(s)...")
            
            # Calculate bounding box
            lat_delta = radius / 69.0  # Rough conversion
            lon_delta = radius / (69.0 * math.cos(math.radians(latitude)))
            
            min_lon = longitude - lon_delta
            max_lon = longitude + lon_delta
            min_lat = latitude - lat_delta
            max_lat = latitude + lat_delta
            
            # Query wetlands in bounding box
            try:
                wetlands = self.client.query_wetlands_by_bbox(
                    min_lon, min_lat, max_lon, max_lat, source='both'
                )
                
                if wetlands:
                    print(f"  ✅ Found {len(wetlands)} wetland(s) within {radius} mile(s)")
                    
                    # Calculate distances and sort
                    wetlands_with_distance = []
                    for wetland in wetlands:
                        # Extract centroid from attributes or estimate
                        wetland_lon, wetland_lat = self._get_wetland_centroid(wetland)
                        if wetland_lon and wetland_lat and wetland_lon != "NEEDS_GEOMETRY":
                            distance = self._calculate_distance(
                                longitude, latitude, wetland_lon, wetland_lat
                            )
                            
                            wetland_info = {
                                'wetland': self._create_enhanced_wetland_info(wetland),
                                'distance_miles': round(distance, 2),
                                'bearing': self._calculate_bearing(
                                    longitude, latitude, wetland_lon, wetland_lat
                                ),
                                'search_radius': radius,
                                'centroid': (wetland_lon, wetland_lat),
                                'coordinate_precision': 'precise'
                            }
                            wetlands_with_distance.append(wetland_info)
                        elif wetland_lon == "NEEDS_GEOMETRY":
                            # Handle wetlands without precise coordinates
                            estimated_distance = radius * 0.8
                            wetland_info = {
                                'wetland': self._create_enhanced_wetland_info(wetland),
                                'distance_miles': round(estimated_distance, 2),
                                'bearing': 'Unknown',
                                'search_radius': radius,
                                'centroid': None,
                                'coordinate_precision': 'estimated'
                            }
                            wetlands_with_distance.append(wetland_info)
                    
                    # Sort by distance
                    wetlands_with_distance.sort(key=lambda x: x['distance_miles'])
                    
                    # Take up to 5 nearest
                    nearest_wetlands = wetlands_with_distance[:5]
                    break
                else:
                    print(f"  ❌ No wetlands found within {radius} mile(s)")
                    
            except Exception as e:
                print(f"  ⚠️  Error searching at {radius} miles: {e}")
        
        return nearest_wetlands
    
    def _get_wetland_centroid(self, wetland: WetlandInfo) -> Tuple[Optional[float], Optional[float]]:
        """Extract or estimate wetland centroid coordinates with improved validation"""
        
        def validate_coords(lon: float, lat: float) -> bool:
            """Validate coordinate ranges"""
            return -180 <= lon <= 180 and -90 <= lat <= 90
        
        # Try location attribute first
        if wetland.location:
            lon, lat = wetland.location
            if validate_coords(lon, lat):
                return wetland.location
        
        # Try attributes with prioritized field names
        attrs = wetland.attributes or {}
        coord_fields = [
            ('CENTROID_X', 'CENTROID_Y'),
            ('CENTER_X', 'CENTER_Y'), 
            ('LONGITUDE', 'LATITUDE'),
            ('LON', 'LAT'),
            ('X_COORD', 'Y_COORD'),
            ('X', 'Y')
        ]
        
        for x_field, y_field in coord_fields:
            if x_field in attrs and y_field in attrs:
                try:
                    lon, lat = float(attrs[x_field]), float(attrs[y_field])
                    if validate_coords(lon, lat):
                        return lon, lat
                except (ValueError, TypeError, AttributeError):
                    continue
        
        # Try geometry extraction
        if 'geometry' in attrs:
            try:
                geom = attrs['geometry']
                if isinstance(geom, dict):
                    # Handle GeoJSON-style coordinates
                    if 'coordinates' in geom and isinstance(geom['coordinates'], list):
                        coords = geom['coordinates']
                        if len(coords) >= 2:
                            lon, lat = float(coords[0]), float(coords[1])
                            if validate_coords(lon, lat):
                                return lon, lat
                    # Handle x,y format
                    elif 'x' in geom and 'y' in geom:
                        lon, lat = float(geom['x']), float(geom['y'])
                        if validate_coords(lon, lat):
                            return lon, lat
            except (ValueError, TypeError, KeyError, AttributeError):
                pass
        
        # Return flag for wetlands needing geometry processing
        return "NEEDS_GEOMETRY", "NEEDS_GEOMETRY"
    
    def _calculate_distance(self, lon1: float, lat1: float, 
                          lon2: float, lat2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula"""
        
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_bearing(self, lon1: float, lat1: float, 
                         lon2: float, lat2: float) -> str:
        """Calculate compass bearing from point 1 to point 2"""
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing = math.degrees(math.atan2(x, y))
        bearing = (bearing + 360) % 360
        
        # Convert to compass direction
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(bearing / 22.5) % 16
        
        return directions[index]
    
    def _calculate_polygon_area(self, polygon_coords: List[Tuple[float, float]]) -> float:
        """Calculate polygon area in acres using shoelace formula"""
        # Convert to projected coordinates for area calculation
        # This is a simplified calculation - for accurate results use proper projection
        
        # Close polygon if not closed
        coords = list(polygon_coords)
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        
        # Shoelace formula
        area = 0.0
        for i in range(len(coords) - 1):
            area += coords[i][0] * coords[i + 1][1]
            area -= coords[i + 1][0] * coords[i][1]
        area = abs(area) / 2.0
        
        # Convert from square degrees to acres (rough approximation)
        # At equator: 1 degree ≈ 69 miles, 1 sq degree ≈ 4761 sq miles ≈ 3,047,040 acres
        # Adjust for latitude
        avg_lat = sum(coord[1] for coord in polygon_coords) / len(polygon_coords)
        lat_adjustment = math.cos(math.radians(avg_lat))
        acres_per_sq_degree = 3047040 * lat_adjustment
        
        return round(area * acres_per_sq_degree, 2)
    
    def _create_enhanced_wetland_info(self, wetland: WetlandInfo) -> Dict[str, Any]:
        """Create enhanced wetland info with proper data extraction from attributes"""
        
        attrs = wetland.attributes or {}
        
        # Helper function to get attribute with fallback
        def get_attr(primary_key: str, fallback_key: str, default: Any = '') -> Any:
            return attrs.get(primary_key, attrs.get(fallback_key, default))
        
        return {
            'id': str(get_attr('Wetlands.OBJECTID', 'OBJECTID')),
            'type': get_attr('Wetlands.WETLAND_TYPE', 'WETLAND_TYPE', 'Unknown'),
            'code': get_attr('Wetlands.ATTRIBUTE', 'ATTRIBUTE'),
            'description': self._create_wetland_description(attrs),
            'area_acres': get_attr('Wetlands.ACRES', 'ACRES'),
            'nwi_classification': self._extract_nwi_classification(attrs),
            'attributes': attrs
        }
    
    def _create_wetland_description(self, attrs: Dict[str, Any]) -> str:
        """Create a comprehensive wetland description from NWI attributes"""
        
        # Get basic wetland type
        wetland_type = attrs.get('Wetlands.WETLAND_TYPE', attrs.get('WETLAND_TYPE', 'Unknown'))
        
        # Get NWI classification details
        system_name = attrs.get('NWI_Wetland_Codes.SYSTEM_NAME', '')
        class_name = attrs.get('NWI_Wetland_Codes.CLASS_NAME', '')
        subclass_name = attrs.get('NWI_Wetland_Codes.SUBCLASS_NAME', '')
        water_regime_name = attrs.get('NWI_Wetland_Codes.WATER_REGIME_NAME', '')
        
        # Build comprehensive description
        if system_name and class_name:
            description_parts = [system_name]
            
            if class_name:
                description_parts.append(class_name)
            
            if subclass_name:
                description_parts.append(f"({subclass_name})")
            
            if water_regime_name:
                description_parts.append(f"- {water_regime_name}")
            
            return " ".join(description_parts)
        else:
            return wetland_type
    
    def _extract_nwi_classification(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed NWI classification information"""
        
        def extract_nwi_component(component: str) -> Dict[str, str]:
            """Extract NWI component (system, subsystem, class, etc.)"""
            prefix = f'NWI_Wetland_Codes.{component.upper()}'
            return {
                'code': attrs.get(prefix, ''),
                'name': attrs.get(f'{prefix}_NAME', ''),
                'definition': attrs.get(f'{prefix}_DEFINITION', '')
            }
        
        classification = {}
        for component in ['system', 'subsystem', 'class', 'subclass']:
            classification[component] = extract_nwi_component(component)
        
        # Water regime has additional subgroup field
        classification['water_regime'] = extract_nwi_component('water_regime')
        classification['water_regime']['subgroup'] = attrs.get('NWI_Wetland_Codes.WATER_REGIME_SUBGROUP', '')
        
        return classification
    
    def _process_wetlands(self, wetlands: List[WetlandInfo]) -> List[Dict[str, Any]]:
        """Process wetland information for output"""
        
        processed = []
        for wetland in wetlands:
            # Use enhanced wetland info extraction
            enhanced_info = self._create_enhanced_wetland_info(wetland)
            processed.append(enhanced_info)
        return processed
    
    def _process_riparian_areas(self, riparian_areas: List[Any]) -> List[Dict[str, Any]]:
        """Process riparian area information"""
        
        processed = []
        for area in riparian_areas:
            processed.append({
                'id': area.feature_id,
                'type': area.feature_type,
                'description': area.description,
                'attributes': area.attributes
            })
        return processed
    
    def _process_watersheds(self, watersheds: List[Any]) -> List[Dict[str, Any]]:
        """Process watershed information"""
        
        processed = []
        for watershed in watersheds:
            processed.append({
                'huc_code': watershed.huc_code,
                'huc_level': watershed.huc_level,
                'name': watershed.name,
                'area_sqkm': watershed.area_sqkm,
                'attributes': watershed.attributes
            })
        return processed
    
    def _generate_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis of wetland findings"""
        
        analysis = {
            'wetland_status': '',
            'wetland_types': [],
            'total_wetland_area': 0,
            'environmental_significance': '',
            'regulatory_implications': []
        }
        
        if results['is_in_wetland']:
            analysis['wetland_status'] = 'Location is within a wetland area'
            
            # Analyze wetland types
            wetland_types = set()
            total_area = 0
            
            for wetland in results['wetlands_at_location']:
                wetland_types.add(wetland['description'])
                if wetland['area_acres']:
                    total_area += wetland['area_acres']
            
            analysis['wetland_types'] = list(wetland_types)
            analysis['total_wetland_area'] = round(total_area, 2)
            
            # Environmental significance
            if 'Forested' in str(wetland_types):
                analysis['environmental_significance'] = 'High - Forested wetlands provide critical habitat'
            elif 'Emergent' in str(wetland_types):
                analysis['environmental_significance'] = 'Moderate to High - Emergent wetlands support diverse species'
            else:
                analysis['environmental_significance'] = 'Moderate - All wetlands provide ecosystem services'
            
            # Regulatory implications
            analysis['regulatory_implications'] = [
                'Activities may require permits under Clean Water Act Section 404',
                'State wetland regulations may apply',
                'Environmental impact assessment likely required',
                'Mitigation may be necessary for any impacts'
            ]
            
        else:
            analysis['wetland_status'] = 'Location is not within a mapped wetland'
            
            if results['nearest_wetlands']:
                nearest = results['nearest_wetlands'][0]
                search_radius = results['search_summary']['search_radius_used']
                
                # Format bearing properly
                bearing_text = f" to the {nearest['bearing']}" if nearest['bearing'] != 'Unknown' else ""
                analysis['wetland_status'] += f", nearest wetland is {nearest['distance_miles']} miles away{bearing_text}"
                
                # Add information about wetlands within search radius
                wetlands_in_radius = len(results['nearest_wetlands'])
                analysis['wetland_status'] += f" ({wetlands_in_radius} wetland(s) found within {search_radius} mile radius)"
            else:
                # No wetlands found even after expanded search
                search_radius = results['search_summary']['search_radius_used']
                analysis['wetland_status'] += f", no wetlands found within {search_radius} mile radius"
            
            search_radius = results['search_summary']['search_radius_used']
            wetlands_count = len(results.get("nearest_wetlands", []))
            
            analysis['regulatory_implications'] = [
                'No direct wetland impacts expected at exact location',
                'Verify with field delineation for regulatory certainty',
                'Consider indirect impacts to nearby wetlands',
                'Buffer requirements may still apply',
                f'{wetlands_count} wetland(s) within {search_radius} mile radius may require consideration'
            ]
        
        return analysis
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on findings"""
        
        recommendations = []
        
        if results['is_in_wetland']:
            recommendations.extend([
                '🚨 Consult with wetland specialists before any development',
                '📋 Obtain jurisdictional determination from Army Corps of Engineers',
                '🔍 Conduct detailed wetland delineation',
                '📑 Review local and state wetland regulations',
                '🌱 Consider wetland enhancement opportunities'
            ])
        else:
            recommendations.extend([
                '✅ No wetlands identified at exact location',
                '🔍 Consider professional wetland delineation for confirmation',
                '📏 Maintain appropriate buffers from nearby wetlands',
                '💧 Implement stormwater best management practices',
                '🌿 Consider creating wetland habitat if appropriate'
            ])
        
        # Add watershed-specific recommendations
        if results['watersheds']:
            recommendations.append('💧 Follow watershed management guidelines')
        
        # Add riparian-specific recommendations
        if results['riparian_areas']:
            recommendations.append('🌊 Protect riparian buffers and stream corridors')
        
        return recommendations
    
    def _generate_polygon_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis specific to polygon queries"""
        
        analysis = {
            'wetland_status': '',
            'wetland_types': [],
            'total_wetland_area': results['search_summary']['total_wetland_area'],
            'polygon_area': results['search_summary']['polygon_area_acres'],
            'wetland_coverage': results['search_summary']['wetland_coverage_percent'],
            'environmental_significance': '',
            'regulatory_implications': []
        }
        
        if results['is_in_wetland']:
            analysis['wetland_status'] = f"Polygon contains {results['search_summary']['wetlands_found_in_polygon']} wetland(s)"
            
            # Analyze wetland types
            wetland_types = set()
            for wetland in results['wetlands_at_location']:
                wetland_types.add(wetland['description'])
            
            analysis['wetland_types'] = list(wetland_types)
            
            # Environmental significance based on coverage
            if analysis['wetland_coverage'] > 50:
                analysis['environmental_significance'] = 'Very High - Majority of area is wetland'
            elif analysis['wetland_coverage'] > 25:
                analysis['environmental_significance'] = 'High - Significant wetland presence'
            elif analysis['wetland_coverage'] > 10:
                analysis['environmental_significance'] = 'Moderate - Notable wetland areas'
            else:
                analysis['environmental_significance'] = 'Low to Moderate - Limited wetland coverage'
            
            # Regulatory implications
            analysis['regulatory_implications'] = [
                f'Wetlands cover {analysis["wetland_coverage"]}% of the polygon area',
                'Activities affecting wetlands require Clean Water Act Section 404 permits',
                'Wetland delineation required for precise boundaries',
                'Mitigation likely required for wetland impacts',
                'Consider avoiding/minimizing wetland impacts in project design'
            ]
            
        else:
            analysis['wetland_status'] = 'No mapped wetlands found within polygon area'
            
            analysis['regulatory_implications'] = [
                'No mapped wetlands in polygon area',
                'Field verification still recommended',
                'Small or seasonal wetlands may not be mapped',
                'Consider buffer zones if wetlands exist nearby'
            ]
        
        return analysis


def generate_summary_report(results: Dict[str, Any]):
    """Generate a formatted summary report"""
    
    print(f"\n{'='*80}")
    print(f"WETLAND ANALYSIS SUMMARY REPORT")
    print(f"{'='*80}")
    
    print(f"\n📍 LOCATION INFORMATION:")
    print(f"   Location: {results['location']}")
    print(f"   Coordinates: {results['coordinates'][0]}, {results['coordinates'][1]}")
    print(f"   Query Time: {results['query_time']}")
    
    print(f"\n🌿 WETLAND STATUS:")
    analysis = results['analysis']
    print(f"   Status: {analysis['wetland_status']}")
    
    if results['is_in_wetland']:
        # Check if it's a polygon or point analysis
        if 'polygon_coords' in results:
            print(f"   Wetlands in Polygon: {results['search_summary']['wetlands_found_in_polygon']}")
            print(f"   Polygon Area: {results['search_summary']['polygon_area_acres']} acres")
            print(f"   Total Wetland Area: {analysis['total_wetland_area']} acres")
            print(f"   Wetland Coverage: {results['search_summary']['wetland_coverage_percent']}%")
        else:
            print(f"   Wetlands at Location: {results['search_summary']['wetlands_found_at_location']}")
            print(f"   Total Wetland Area: {analysis['total_wetland_area']} acres")
        print(f"   Environmental Significance: {analysis['environmental_significance']}")
        
        print(f"\n   Wetland Types Found:")
        for wetland_type in analysis['wetland_types']:
            print(f"     • {wetland_type}")
        
        print(f"\n   Detailed Wetlands:")
        for i, wetland in enumerate(results['wetlands_at_location'], 1):
            print(f"     {i}. {wetland['description']}")
            print(f"        Code: {wetland['code']}")
            if wetland['area_acres']:
                print(f"        Area: {wetland['area_acres']} acres")
    
    else:
        print(f"   ❌ No wetlands at exact coordinates")
    
    # Always show nearby wetlands for point queries
    if 'polygon_coords' not in results and results['nearest_wetlands']:
        print(f"\n   Wetlands within {results['search_summary']['search_radius_used']} mile radius:")
        for i, nearest in enumerate(results['nearest_wetlands'], 1):
            wetland = nearest['wetland']
            # Handle both enhanced dict format and WetlandInfo objects
            if isinstance(wetland, dict):
                description = wetland.get('description', 'Unknown')
                code = wetland.get('code', '')
                area_acres = wetland.get('area_acres')
                wetland_id = wetland.get('id', '')
            else:
                description = wetland.description
                code = wetland.wetland_code
                area_acres = wetland.area_acres
                wetland_id = wetland.wetland_id
            
            print(f"     {i}. {description}")
            print(f"        ID: {wetland_id}")
            
            # Format distance and bearing properly
            bearing_text = f" to the {nearest['bearing']}" if nearest['bearing'] != 'Unknown' else ""
            print(f"        Distance: {nearest['distance_miles']} miles{bearing_text}")
            print(f"        Code: {code}")
            if area_acres:
                print(f"        Area: {area_acres} acres")
    
    # Watersheds
    if results['watersheds']:
        print(f"\n💧 WATERSHED INFORMATION:")
        for watershed in results['watersheds']:
            print(f"   • {watershed['name']} (HUC{watershed['huc_level']}: {watershed['huc_code']})")
            if watershed['area_sqkm']:
                print(f"     Area: {watershed['area_sqkm']} sq km")
    
    # Riparian areas
    if results['riparian_areas']:
        print(f"\n🌊 RIPARIAN AREAS:")
        for area in results['riparian_areas']:
            print(f"   • {area['description']} ({area['type']})")
    
    # Regulatory implications
    print(f"\n⚖️  REGULATORY IMPLICATIONS:")
    for implication in analysis['regulatory_implications']:
        print(f"   • {implication}")
    
    # Recommendations
    print(f"\n📋 RECOMMENDATIONS:")
    for recommendation in results['recommendations']:
        print(f"   {recommendation}")
    
    # Data sources
    print(f"\n📊 DATA SOURCES:")
    print(f"   • USFWS National Wetlands Inventory (NWI)")
    print(f"   • EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)")
    print(f"   • EPA National Hydrography Dataset (NHD)")
    print(f"   • USFWS Riparian Mapping")


def save_results_to_file(results: Dict[str, Any], filename: str = None):
    """Save results to a JSON file"""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{results['coordinates'][0]}_{results['coordinates'][1]}".replace('-', 'neg').replace('.', 'p')
        filename = f"wetland_analysis_{coords}_{timestamp}.json"
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    filepath = os.path.join('logs', filename)
    
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filepath}")
    
    # Also save a summary file
    summary_filepath = save_summary_to_file(results, filename)
    
    return filepath

def save_summary_to_file(results: Dict[str, Any], original_filename: str = None):
    """Save a detailed summary to a separate JSON file"""
    
    if original_filename:
        summary_filename = original_filename.replace('.json', '_summary.json')
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{results['coordinates'][0]}_{results['coordinates'][1]}".replace('-', 'neg').replace('.', 'p')
        summary_filename = f"wetland_summary_{coords}_{timestamp}.json"
    
    summary_data = generate_detailed_summary(results)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    summary_filepath = os.path.join('logs', summary_filename)
    
    with open(summary_filepath, 'w') as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    print(f"📋 Summary saved to: {summary_filepath}")
    return summary_filepath

def generate_detailed_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a detailed, human-readable summary of wetland data"""
    
    summary = {
        "location_info": {
            "name": results['location'],
            "coordinates": {
                "longitude": results['coordinates'][0],
                "latitude": results['coordinates'][1]
            },
            "analysis_date": results['query_time']
        },
        "wetland_summary": {
            "has_wetlands": results['is_in_wetland'],
            "total_wetlands_found": len(results['wetlands_at_location']),
            "total_area_acres": results['analysis']['total_wetland_area'],
            "environmental_significance": results['analysis']['environmental_significance']
        },
        "detailed_wetlands": [],
        "nearby_wetlands": [],
        "regulatory_information": {
            "status": results['analysis']['wetland_status'],
            "implications": results['analysis']['regulatory_implications'],
            "recommendations": results['recommendations']
        },
        "data_sources": [
            "USFWS National Wetlands Inventory (NWI)",
            "EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)",
            "EPA National Hydrography Dataset (NHD)",
            "USFWS Riparian Mapping"
        ]
    }
    
    # Process detailed wetlands at location
    for wetland in results['wetlands_at_location']:
        wetland_detail = {
            "id": wetland['id'],
            "classification": {
                "code": wetland['code'],
                "type": wetland['type'],
                "description": wetland['description']
            },
            "area_acres": wetland['area_acres'],
            "detailed_attributes": {}
        }
        
        # Extract detailed NWI classification if available
        attrs = wetland.get('attributes', {})
        if 'NWI_Wetland_Codes.SYSTEM_NAME' in attrs:
            wetland_detail["nwi_classification"] = {
                "system": {
                    "code": attrs.get('NWI_Wetland_Codes.SYSTEM'),
                    "name": attrs.get('NWI_Wetland_Codes.SYSTEM_NAME'),
                    "definition": attrs.get('NWI_Wetland_Codes.SYSTEM_DEFINITION')
                },
                "subsystem": {
                    "code": attrs.get('NWI_Wetland_Codes.SUBSYSTEM'),
                    "name": attrs.get('NWI_Wetland_Codes.SUBSYSTEM_NAME'),
                    "definition": attrs.get('NWI_Wetland_Codes.SUBSYSTEM_DEFINITION')
                },
                "class": {
                    "code": attrs.get('NWI_Wetland_Codes.CLASS'),
                    "name": attrs.get('NWI_Wetland_Codes.CLASS_NAME'),
                    "definition": attrs.get('NWI_Wetland_Codes.CLASS_DEFINITION')
                },
                "subclass": {
                    "code": attrs.get('NWI_Wetland_Codes.SUBCLASS'),
                    "name": attrs.get('NWI_Wetland_Codes.SUBCLASS_NAME'),
                    "definition": attrs.get('NWI_Wetland_Codes.SUBCLASS_DEFINITION')
                },
                "water_regime": {
                    "code": attrs.get('NWI_Wetland_Codes.WATER_REGIME'),
                    "name": attrs.get('NWI_Wetland_Codes.WATER_REGIME_NAME'),
                    "subgroup": attrs.get('NWI_Wetland_Codes.WATER_REGIME_SUBGROUP'),
                    "definition": attrs.get('NWI_Wetland_Codes.WATER_REGIME_DEFINITION')
                }
            }
        
        # Add physical characteristics
        if 'Wetlands.Shape_Length' in attrs:
            wetland_detail["physical_characteristics"] = {
                "perimeter_meters": attrs.get('Wetlands.Shape_Length'),
                "area_square_meters": attrs.get('Wetlands.Shape_Area'),
                "area_acres": attrs.get('Wetlands.ACRES')
            }
        
        summary["detailed_wetlands"].append(wetland_detail)
    
    # Process nearby wetlands
    for nearby in results['nearest_wetlands']:
        wetland = nearby['wetland']
        # Handle both enhanced dict format and WetlandInfo objects
        if isinstance(wetland, dict):
            nearby_detail = {
                "id": wetland.get('id', ''),
                "classification": {
                    "code": wetland.get('code', ''),
                    "type": wetland.get('type', ''),
                    "description": wetland.get('description', '')
                },
                "distance_miles": nearby['distance_miles'],
                "bearing": nearby['bearing'],
                "area_acres": wetland.get('area_acres'),
                "centroid_coordinates": nearby['centroid'],
                "nwi_classification": wetland.get('nwi_classification', {})
            }
        else:
            # Legacy WetlandInfo object format
            nearby_detail = {
                "id": wetland.wetland_id,
                "classification": {
                    "code": wetland.wetland_code,
                    "type": wetland.wetland_type,
                    "description": wetland.description
                },
                "distance_miles": nearby['distance_miles'],
                "bearing": nearby['bearing'],
                "area_acres": wetland.area_acres,
                "centroid_coordinates": nearby['centroid']
            }
        summary["nearby_wetlands"].append(nearby_detail)
    
    # Add additional context for polygon analysis
    if 'polygon_coords' in results:
        summary["polygon_analysis"] = {
            "polygon_area_acres": results['search_summary']['polygon_area_acres'],
            "wetland_coverage_percent": results['search_summary']['wetland_coverage_percent'],
            "vertices_count": len(results['polygon_coords'])
        }
    
    # Add search information
    summary["search_info"] = {
        "search_radius_miles": results['search_summary'].get('search_radius_used', 0),
        "wetlands_at_exact_location": results['search_summary']['wetlands_found_at_location'],
        "nearby_wetlands_found": results['search_summary']['nearest_wetlands_found'],
        "total_wetlands_analyzed": results['search_summary']['total_wetlands_analyzed']
    }
    
    return summary


# This module is designed to be imported and used by main.py
# For command-line usage, run: python main.py 