#!/usr/bin/env python3
"""
Point to Map Generator

Single function to go from a point coordinate or cadastral number to a complete map.
Integrates point lookup, polygon coordinate retrieval, and map generation.
"""

import sys
import os
import math
from typing import List, Tuple, Optional, Dict, Any, Union

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cadastral.point_lookup import MIPRPointLookup
from cadastral.cadastral_search import MIPRCadastralSearch
from map_generator import MIPRMapGenerator

class PointToMapGenerator:
    """
    Generate maps from point coordinates or cadastral numbers.
    
    This class provides a unified interface to:
    1. Look up cadastral data from point coordinates
    2. Get polygon coordinates from cadastral numbers
    3. Generate maps with polygon overlays
    """
    
    def __init__(self):
        """Initialize the point to map generator."""
        self.point_lookup = MIPRPointLookup()
        self.cadastral_search = MIPRCadastralSearch()
        self.map_generator = MIPRMapGenerator()
    
    def create_map_from_point(
        self,
        longitude: float,
        latitude: float,
        save_path: str = 'point_map.png',
        buffer_meters: float = 0,
        service: str = 'foto_pr_2017',
        show_circle: bool = True,
        circle_radius: float = 0.1,
        style: str = 'default',
        show_on_screen: bool = False,
        template: str = 'JP_print',
        return_cadastral_data: bool = True
    ) -> Dict[str, Any]:
        """
        Create a map from a point coordinate by finding the cadastral parcel and its polygon.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            save_path: Where to save the map
            buffer_meters: Buffer around point for cadastral lookup (0 = exact)
            service: Map service ('topografico' or 'foto_pr_2017')
            show_circle: Whether to show buffer circle
            circle_radius: Radius of buffer circle in miles
            style: Map style ('default', 'yellow_filled', 'blue_classic')
            show_on_screen: Whether to display map on screen
            template: Print template ('JP_print' or 'MAP_ONLY')
            return_cadastral_data: Whether to include cadastral data in response
            
        Returns:
            Dictionary with success status, cadastral data, and map info
        """
        
        print(f"🗺️  Creating map from point ({longitude:.6f}, {latitude:.6f})")
        print("=" * 60)
        
        try:
            # Step 1: Get cadastral data at point
            print("1️⃣  Looking up cadastral data at point...")
            
            if buffer_meters == 0:
                cadastral_result = self.point_lookup.get_single_cadastral(longitude, latitude, include_geometry=False)
                if not cadastral_result:
                    return {
                        'success': False,
                        'error': 'No cadastral parcel found at exact point location',
                        'coordinates': {'longitude': longitude, 'latitude': latitude},
                        'cadastral_data': None,
                        'map_created': False
                    }
                cadastral_data = cadastral_result
            else:
                lookup_result = self.point_lookup.lookup_point(longitude, latitude, buffer_meters)
                if not lookup_result['success'] or not lookup_result['cadastral_data']:
                    return {
                        'success': False,
                        'error': lookup_result.get('error', 'No cadastral data found'),
                        'coordinates': {'longitude': longitude, 'latitude': latitude},
                        'cadastral_data': None,
                        'map_created': False
                    }
                cadastral_data = lookup_result['cadastral_data']
            
            cadastral_number = cadastral_data['cadastral_number']
            print(f"   ✅ Found cadastral: {cadastral_number}")
            print(f"   📍 Municipality: {cadastral_data['municipality']}")
            print(f"   🏷️  Classification: {cadastral_data['classification_code']} - {cadastral_data['classification_description']}")
            
            # Step 2: Get polygon coordinates for the cadastral
            print(f"\n2️⃣  Getting polygon coordinates for cadastral {cadastral_number}...")
            polygon_coords = self._get_cadastral_polygon_coords(cadastral_number)
            
            if not polygon_coords:
                return {
                    'success': False,
                    'error': f'Could not retrieve polygon coordinates for cadastral {cadastral_number}',
                    'coordinates': {'longitude': longitude, 'latitude': latitude},
                    'cadastral_data': cadastral_data if return_cadastral_data else None,
                    'map_created': False
                }
            
            print(f"   ✅ Retrieved {len(polygon_coords)} polygon coordinates")
            
            # Step 3: Create map with polygon overlay
            print(f"\n3️⃣  Creating map with polygon overlay...")
            # Switch to the requested service
            if service == 'topografico':
                self.map_generator.switch_base_map('topografico')
            elif service == 'foto_pr_2017':
                self.map_generator.switch_base_map('foto_pr_2017')
            
            # Create the map using the basic MIPR map method
            map_success = self.map_generator.create_basic_mipr_map(
                polygon_coords=polygon_coords,
                title=f"Property Map - {cadastral_number}",
                save_path=save_path
            )
            
            if map_success:
                print(f"   ✅ Map saved to: {save_path}")
            else:
                print(f"   ❌ Failed to create map")
            
            return {
                'success': True,
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'cadastral_data': cadastral_data if return_cadastral_data else None,
                'cadastral_number': cadastral_number,
                'polygon_coords': polygon_coords,
                'map_created': map_success,
                'map_path': save_path if map_success else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'cadastral_data': None,
                'map_created': False
            }
    
    def create_map_from_cadastral(
        self,
        cadastral_number: str,
        save_path: str = 'cadastral_map.png',
        service: str = 'foto_pr_2017',
        show_circle: bool = True,
        circle_radius: float = 0.1,
        style: str = 'default',
        show_on_screen: bool = False,
        template: str = 'JP_print',
        return_cadastral_data: bool = True
    ) -> Dict[str, Any]:
        """
        Create a map from a cadastral number by getting its polygon coordinates.
        
        Args:
            cadastral_number: The cadastral number to map
            save_path: Where to save the map
            service: Map service ('topografico' or 'foto_pr_2017')
            show_circle: Whether to show buffer circle
            circle_radius: Radius of buffer circle in miles
            style: Map style ('default', 'yellow_filled', 'blue_classic')
            show_on_screen: Whether to display map on screen
            template: Print template ('JP_print' or 'MAP_ONLY')
            return_cadastral_data: Whether to include cadastral data in response
            
        Returns:
            Dictionary with success status, cadastral data, and map info
        """
        
        print(f"🗺️  Creating map from cadastral: {cadastral_number}")
        print("=" * 60)
        
        try:
            # Step 1: Get cadastral data
            print("1️⃣  Looking up cadastral data...")
            search_result = self.cadastral_search.search_by_cadastral(
                cadastral_number, exact_match=True, include_geometry=False
            )
            
            if not search_result['success'] or search_result['feature_count'] == 0:
                return {
                    'success': False,
                    'error': f'Cadastral {cadastral_number} not found',
                    'cadastral_number': cadastral_number,
                    'cadastral_data': None,
                    'map_created': False
                }
            
            cadastral_data = search_result['results'][0]
            print(f"   ✅ Found cadastral: {cadastral_data['cadastral_number']}")
            print(f"   📍 Municipality: {cadastral_data['municipality']}")
            print(f"   🏷️  Classification: {cadastral_data['classification_code']} - {cadastral_data['classification_description']}")
            print(f"   📏 Area: {cadastral_data['area_m2']:,.2f} m²")
            
            # Step 2: Get polygon coordinates
            print(f"\n2️⃣  Getting polygon coordinates...")
            polygon_coords = self._get_cadastral_polygon_coords(cadastral_number)
            
            if not polygon_coords:
                return {
                    'success': False,
                    'error': f'Could not retrieve polygon coordinates for cadastral {cadastral_number}',
                    'cadastral_number': cadastral_number,
                    'cadastral_data': cadastral_data if return_cadastral_data else None,
                    'map_created': False
                }
            
            print(f"   ✅ Retrieved {len(polygon_coords)} polygon coordinates")
            
            # Step 3: Create map with polygon overlay
            print(f"\n3️⃣  Creating map with polygon overlay...")
            # Switch to the requested service
            if service == 'topografico':
                self.map_generator.switch_base_map('topografico')
            elif service == 'foto_pr_2017':
                self.map_generator.switch_base_map('foto_pr_2017')
            
            # Create the map using the basic MIPR map method
            map_success = self.map_generator.create_basic_mipr_map(
                polygon_coords=polygon_coords,
                title=f"Cadastral Map - {cadastral_number}",
                save_path=save_path
            )
            
            if map_success:
                print(f"   ✅ Map saved to: {save_path}")
            else:
                print(f"   ❌ Failed to create map")
            
            return {
                'success': True,
                'cadastral_number': cadastral_number,
                'cadastral_data': cadastral_data if return_cadastral_data else None,
                'polygon_coords': polygon_coords,
                'map_created': map_success,
                'map_path': save_path if map_success else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'cadastral_number': cadastral_number,
                'cadastral_data': None,
                'map_created': False
            }
    
    def _get_cadastral_polygon_coords(self, cadastral_number: str) -> Optional[List[Tuple[float, float]]]:
        """
        Get polygon coordinates for a cadastral number.
        
        Args:
            cadastral_number: The cadastral number to search for
            
        Returns:
            List of (longitude, latitude) coordinate pairs, or None if not found
        """
        
        try:
            # Search for cadastral with geometry
            result = self.cadastral_search.search_by_cadastral(
                cadastral_number, exact_match=True, include_geometry=True
            )
            
            if not result['success'] or result['feature_count'] == 0:
                print(f"   ❌ Cadastral {cadastral_number} not found")
                return None
            
            feature = result['results'][0]
            
            # Extract geometry
            geometry = feature.get('geometry')
            if not geometry or 'rings' not in geometry:
                print(f"   ❌ No polygon geometry found for cadastral {cadastral_number}")
                return None
            
            rings = geometry['rings']
            if not rings:
                print(f"   ❌ No coordinate rings found for cadastral {cadastral_number}")
                return None
            
            # Use the outer ring (first ring)
            outer_ring = rings[0]
            
            # Convert from Web Mercator to WGS84
            wgs84_coords = []
            for point in outer_ring:
                if len(point) >= 2:
                    x, y = point[0], point[1]
                    
                    # Convert from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)
                    lon = x / 20037508.34 * 180
                    lat = y / 20037508.34 * 180
                    lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
                    
                    wgs84_coords.append((lon, lat))
            
            return wgs84_coords
            
        except Exception as e:
            print(f"   ❌ Error getting polygon coordinates: {str(e)}")
            return None
    
    def print_result_summary(self, result: Dict[str, Any]):
        """Print a formatted summary of the result."""
        
        print(f"\n📋 RESULT SUMMARY")
        print("=" * 40)
        
        if not result['success']:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
            return
        
        print(f"✅ Success!")
        
        if 'coordinates' in result:
            coords = result['coordinates']
            print(f"📍 Point: ({coords['longitude']:.6f}, {coords['latitude']:.6f})")
        
        if 'cadastral_number' in result:
            print(f"🏠 Cadastral: {result['cadastral_number']}")
        
        if result.get('cadastral_data'):
            data = result['cadastral_data']
            print(f"🏷️  Classification: {data['classification_code']} - {data['classification_description']}")
            print(f"📍 Municipality: {data['municipality']}")
            if data.get('area_m2'):
                print(f"📏 Area: {data['area_m2']:,.2f} m²")
        
        if result.get('polygon_coords'):
            print(f"🔗 Polygon: {len(result['polygon_coords'])} coordinates")
        
        if result.get('map_created'):
            print(f"🗺️  Map: {result['map_path']}")
        else:
            print(f"🗺️  Map: Not created")


# Convenience functions for direct usage
def create_map_from_point(
    longitude: float,
    latitude: float,
    save_path: str = 'point_map.png',
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to create a map from a point coordinate.
    
    Args:
        longitude: Longitude in WGS84
        latitude: Latitude in WGS84
        save_path: Where to save the map
        **kwargs: Additional arguments for create_map_from_point
        
    Returns:
        Result dictionary
    """
    generator = PointToMapGenerator()
    return generator.create_map_from_point(longitude, latitude, save_path, **kwargs)


def create_map_from_cadastral(
    cadastral_number: str,
    save_path: str = 'cadastral_map.png',
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to create a map from a cadastral number.
    
    Args:
        cadastral_number: The cadastral number
        save_path: Where to save the map
        **kwargs: Additional arguments for create_map_from_cadastral
        
    Returns:
        Result dictionary
    """
    generator = PointToMapGenerator()
    return generator.create_map_from_cadastral(cadastral_number, save_path, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    print("🗺️  POINT TO MAP GENERATOR EXAMPLES")
    print("=" * 70)
    
    # Initialize generator
    generator = PointToMapGenerator()
    
    # Example 1: Create map from point coordinates
    print("\n1️⃣  Creating map from point coordinates...")
    print("-" * 50)
    
    # Test point in Juncos
    lon, lat = -65.925834, 18.227804
    
    result = generator.create_map_from_point(
        longitude=lon,
        latitude=lat,
        save_path='mipr/example_point_map.png',
        buffer_meters=0,  # Exact point lookup
        service='foto_pr_2017',
        show_circle=True,
        circle_radius=0.05,
        style='yellow_filled',
        template='JP_print'
    )
    
    generator.print_result_summary(result)
    
    # Example 2: Create map from cadastral number
    print("\n2️⃣  Creating map from cadastral number...")
    print("-" * 50)
    
    cadastral_number = "227-052-007-20"  # Known cadastral from examples
    
    result = generator.create_map_from_cadastral(
        cadastral_number=cadastral_number,
        save_path='mipr/example_cadastral_map.png',
        service='topografico',
        show_circle=True,
        circle_radius=0.1,
        style='blue_classic',
        template='JP_print'
    )
    
    generator.print_result_summary(result)
    
    # Example 3: Batch processing
    print("\n3️⃣  Batch processing multiple points...")
    print("-" * 50)
    
    test_points = [
        (-65.925834, 18.227804, "point_1_map.png"),
        (-65.925855, 18.227957, "point_2_map.png"),
        (-65.925770, 18.227978, "point_3_map.png")
    ]
    
    for i, (lon, lat, filename) in enumerate(test_points):
        print(f"\n   Processing point {i+1}: ({lon:.6f}, {lat:.6f})")
        result = generator.create_map_from_point(
            longitude=lon,
            latitude=lat,
            save_path=f'mipr/{filename}',
            buffer_meters=10,
            service='foto_pr_2017',
            show_circle=False,
            template='MAP_ONLY',
            return_cadastral_data=False
        )
        
        if result['success']:
            print(f"      ✅ {result['cadastral_number']} -> {filename}")
        else:
            print(f"      ❌ Failed: {result['error']}")
    
    print(f"\n✅ Point to Map Generator examples completed!") 