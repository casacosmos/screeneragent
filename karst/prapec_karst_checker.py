#!/usr/bin/env python3
"""
PRAPEC Karst Area Checker

Check if coordinates, cadastral numbers, or groups of cadastrals fall within 
the PRAPEC (Plan y Reglamento del Área de Planificación Especial del Carso) karst areas.
"""

import sys
import os
import json
import requests
import urllib3
from typing import Dict, List, Any, Optional, Tuple, Union

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mapmaker.common import MapServerClient
from cadastral.cadastral_search import MIPRCadastralSearch
from cadastral.point_lookup import MIPRPointLookup

class PrapecKarstChecker:
    """
    Check if locations fall within PRAPEC karst areas.
    
    This class provides functionality to check if coordinates, cadastral numbers,
    or groups of cadastrals fall within the PRAPEC karst regulation areas.
    """
    
    def __init__(self):
        """Initialize the PRAPEC karst checker."""
        self.service_url = "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer"
        self.prapec_layer_id = 15
        self.query_url = f"{self.service_url}/{self.prapec_layer_id}/query"
        
        # Initialize clients for cadastral and point lookups
        self.client = MapServerClient(self.service_url)
        self.cadastral_search = MIPRCadastralSearch()
        self.point_lookup = MIPRPointLookup()
        
        # Convert miles to meters for buffer calculations
        self.meters_per_mile = 1609.34
    
    def check_coordinates(
        self,
        longitude: float,
        latitude: float,
        buffer_miles: float = 0.5,
        include_buffer_search: bool = True
    ) -> Dict[str, Any]:
        """
        Check if coordinates fall within PRAPEC karst areas.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            buffer_miles: Buffer distance in miles for proximity search
            include_buffer_search: Whether to search within buffer if not directly in karst
            
        Returns:
            Dictionary with karst check results
        """
        
        print(f"🔍 Checking coordinates ({longitude:.6f}, {latitude:.6f}) for PRAPEC karst...")
        
        try:
            # Convert to Web Mercator
            x_merc, y_merc = self.client.lonlat_to_webmercator(longitude, latitude)
            
            geometry = {
                "x": x_merc,
                "y": y_merc,
                "spatialReference": {"wkid": 102100}
            }
            
            # First check: exact point intersection
            params = {
                'geometry': json.dumps(geometry),
                'geometryType': 'esriGeometryPoint',
                'spatialRel': 'esriSpatialRelIntersects',
                'inSR': 102100,
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json'
            }
            
            response = requests.get(self.query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if features:
                # Point is directly in karst area
                karst_info = self._extract_karst_info(features[0])
                return {
                    'success': True,
                    'coordinates': {'longitude': longitude, 'latitude': latitude},
                    'in_karst': True,
                    'karst_proximity': 'direct',
                    'distance_miles': 0,
                    'karst_info': karst_info,
                    'buffer_miles': buffer_miles,
                    'message': 'Coordinates are directly within PRAPEC karst area'
                }
            
            elif include_buffer_search and buffer_miles > 0:
                # Second check: buffer search
                print(f"   Not directly in karst, checking within {buffer_miles} mile radius...")
                
                buffer_distance_meters = buffer_miles * self.meters_per_mile
                
                buffer_params = {
                    'geometry': json.dumps(geometry),
                    'geometryType': 'esriGeometryPoint',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'distance': buffer_distance_meters,
                    'units': 'esriSRUnit_Meter',
                    'inSR': 102100,
                    'outFields': '*',
                    'returnGeometry': 'false',
                    'f': 'json'
                }
                
                buffer_response = requests.get(self.query_url, params=buffer_params, verify=False, timeout=15)
                buffer_response.raise_for_status()
                buffer_data = buffer_response.json()
                
                buffer_features = buffer_data.get('features', [])
                
                if buffer_features:
                    karst_info = self._extract_karst_info(buffer_features[0])
                    return {
                        'success': True,
                        'coordinates': {'longitude': longitude, 'latitude': latitude},
                        'in_karst': False,
                        'karst_proximity': 'nearby',
                        'distance_miles': f'within {buffer_miles}',
                        'karst_info': karst_info,
                        'buffer_miles': buffer_miles,
                        'message': f'PRAPEC karst area found within {buffer_miles} miles'
                    }
            
            # No karst found
            return {
                'success': True,
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'in_karst': False,
                'karst_proximity': 'none',
                'distance_miles': f'> {buffer_miles}' if include_buffer_search else 'not checked',
                'karst_info': None,
                'buffer_miles': buffer_miles,
                'message': f'No PRAPEC karst area found within {buffer_miles} miles' if include_buffer_search else 'Not in PRAPEC karst area'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'in_karst': False,
                'karst_proximity': 'error',
                'distance_miles': None,
                'karst_info': None,
                'buffer_miles': buffer_miles
            }
    
    def check_cadastral(
        self,
        cadastral_number: str,
        buffer_miles: float = 0.5,
        include_buffer_search: bool = True
    ) -> Dict[str, Any]:
        """
        Check if a cadastral number falls within PRAPEC karst areas.
        
        Args:
            cadastral_number: The cadastral number to check
            buffer_miles: Buffer distance in miles for proximity search
            include_buffer_search: Whether to search within buffer if not directly in karst
            
        Returns:
            Dictionary with karst check results
        """
        
        print(f"🔍 Checking cadastral {cadastral_number} for PRAPEC karst...")
        
        try:
            # Get cadastral polygon coordinates
            search_result = self.cadastral_search.search_by_cadastral(
                cadastral_number, exact_match=True, include_geometry=True
            )
            
            if not search_result['success'] or search_result['feature_count'] == 0:
                return {
                    'success': False,
                    'error': f'Cadastral {cadastral_number} not found',
                    'cadastral_number': cadastral_number,
                    'in_karst': False,
                    'karst_proximity': 'error',
                    'distance_miles': None,
                    'karst_info': None,
                    'buffer_miles': buffer_miles
                }
            
            feature = search_result['results'][0]
            cadastral_info = {
                'cadastral_number': feature['cadastral_number'],
                'municipality': feature['municipality'],
                'classification': f"{feature['classification_code']} - {feature['classification_description']}",
                'area_m2': feature['area_m2']
            }
            
            # Get geometry for spatial query
            geometry = feature.get('geometry')
            if not geometry or 'rings' not in geometry:
                return {
                    'success': False,
                    'error': f'No geometry found for cadastral {cadastral_number}',
                    'cadastral_number': cadastral_number,
                    'cadastral_info': cadastral_info,
                    'in_karst': False,
                    'karst_proximity': 'error',
                    'distance_miles': None,
                    'karst_info': None,
                    'buffer_miles': buffer_miles
                }
            
            # Use polygon geometry for intersection query
            polygon_geometry = {
                "rings": geometry['rings'],
                "spatialReference": {"wkid": 102100}  # Web Mercator
            }
            
            # Check polygon intersection with karst area
            params = {
                'geometry': json.dumps(polygon_geometry),
                'geometryType': 'esriGeometryPolygon',
                'spatialRel': 'esriSpatialRelIntersects',
                'inSR': 102100,
                'outFields': '*',
                'returnGeometry': 'false',
                'f': 'json'
            }
            
            response = requests.get(self.query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if features:
                # Cadastral intersects with karst area
                karst_info = self._extract_karst_info(features[0])
                return {
                    'success': True,
                    'cadastral_number': cadastral_number,
                    'cadastral_info': cadastral_info,
                    'in_karst': True,
                    'karst_proximity': 'intersects',
                    'distance_miles': 0,
                    'karst_info': karst_info,
                    'buffer_miles': buffer_miles,
                    'message': 'Cadastral polygon intersects with PRAPEC karst area'
                }
            
            elif include_buffer_search and buffer_miles > 0:
                # Check with buffer around cadastral polygon
                print(f"   No direct intersection, checking within {buffer_miles} mile buffer...")
                
                buffer_distance_meters = buffer_miles * self.meters_per_mile
                
                buffer_params = {
                    'geometry': json.dumps(polygon_geometry),
                    'geometryType': 'esriGeometryPolygon',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'distance': buffer_distance_meters,
                    'units': 'esriSRUnit_Meter',
                    'inSR': 102100,
                    'outFields': '*',
                    'returnGeometry': 'false',
                    'f': 'json'
                }
                
                buffer_response = requests.get(self.query_url, params=buffer_params, verify=False, timeout=15)
                buffer_response.raise_for_status()
                buffer_data = buffer_response.json()
                
                buffer_features = buffer_data.get('features', [])
                
                if buffer_features:
                    karst_info = self._extract_karst_info(buffer_features[0])
                    return {
                        'success': True,
                        'cadastral_number': cadastral_number,
                        'cadastral_info': cadastral_info,
                        'in_karst': False,
                        'karst_proximity': 'nearby',
                        'distance_miles': f'within {buffer_miles}',
                        'karst_info': karst_info,
                        'buffer_miles': buffer_miles,
                        'message': f'PRAPEC karst area found within {buffer_miles} miles of cadastral'
                    }
            
            # No karst found
            return {
                'success': True,
                'cadastral_number': cadastral_number,
                'cadastral_info': cadastral_info,
                'in_karst': False,
                'karst_proximity': 'none',
                'distance_miles': f'> {buffer_miles}' if include_buffer_search else 'not checked',
                'karst_info': None,
                'buffer_miles': buffer_miles,
                'message': f'No PRAPEC karst area found within {buffer_miles} miles' if include_buffer_search else 'Not in PRAPEC karst area'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'cadastral_number': cadastral_number,
                'in_karst': False,
                'karst_proximity': 'error',
                'distance_miles': None,
                'karst_info': None,
                'buffer_miles': buffer_miles
            }
    
    def check_multiple_cadastrals(
        self,
        cadastral_numbers: List[str],
        buffer_miles: float = 0.5,
        include_buffer_search: bool = True
    ) -> Dict[str, Any]:
        """
        Check multiple cadastral numbers for PRAPEC karst areas.
        
        Args:
            cadastral_numbers: List of cadastral numbers to check
            buffer_miles: Buffer distance in miles for proximity search
            include_buffer_search: Whether to search within buffer if not directly in karst
            
        Returns:
            Dictionary with results for all cadastrals
        """
        
        print(f"🔍 Checking {len(cadastral_numbers)} cadastrals for PRAPEC karst...")
        
        results = {
            'success': True,
            'total_cadastrals': len(cadastral_numbers),
            'buffer_miles': buffer_miles,
            'summary': {
                'in_karst': 0,
                'nearby_karst': 0,
                'no_karst': 0,
                'errors': 0
            },
            'cadastral_results': [],
            'karst_info': None
        }
        
        karst_found = False
        
        for cadastral_number in cadastral_numbers:
            result = self.check_cadastral(cadastral_number, buffer_miles, include_buffer_search)
            results['cadastral_results'].append(result)
            
            if result['success']:
                if result['in_karst']:
                    results['summary']['in_karst'] += 1
                    if not karst_found:
                        results['karst_info'] = result['karst_info']
                        karst_found = True
                elif result['karst_proximity'] == 'nearby':
                    results['summary']['nearby_karst'] += 1
                    if not karst_found:
                        results['karst_info'] = result['karst_info']
                        karst_found = True
                else:
                    results['summary']['no_karst'] += 1
            else:
                results['summary']['errors'] += 1
        
        # Generate summary message
        if results['summary']['in_karst'] > 0:
            results['message'] = f"{results['summary']['in_karst']} cadastral(s) directly in PRAPEC karst area"
        elif results['summary']['nearby_karst'] > 0:
            results['message'] = f"{results['summary']['nearby_karst']} cadastral(s) have PRAPEC karst within {buffer_miles} miles"
        else:
            results['message'] = f"No cadastrals have PRAPEC karst within {buffer_miles} miles"
        
        return results
    
    def _extract_karst_info(self, feature: Dict[str, Any]) -> Dict[str, Any]:
        """Extract karst information from a feature."""
        attrs = feature.get('attributes', {})
        return {
            'nombre': attrs.get('Nombre', 'N/A'),
            'regla': attrs.get('Regla', 'N/A'),
            'area_sq_meters': attrs.get('Shape.STArea()', 0),
            'area_hectares': attrs.get('Shape.STArea()', 0) / 10000,
            'perimeter_meters': attrs.get('Shape.STLength()', 0),
            'description': 'Plan y Reglamento del Área de Planificación Especial del Carso (PRAPEC)'
        }
    
    def print_result(self, result: Dict[str, Any]):
        """Print a formatted result."""
        
        if not result['success']:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            return
        
        # Handle multiple cadastrals result
        if 'total_cadastrals' in result:
            self._print_multiple_result(result)
            return
        
        # Handle single result
        print(f"\n📋 PRAPEC KARST CHECK RESULT")
        print("=" * 50)
        
        if 'coordinates' in result:
            coords = result['coordinates']
            print(f"📍 Coordinates: ({coords['longitude']:.6f}, {coords['latitude']:.6f})")
        
        if 'cadastral_number' in result:
            print(f"🏠 Cadastral: {result['cadastral_number']}")
            if result.get('cadastral_info'):
                info = result['cadastral_info']
                print(f"   Municipality: {info['municipality']}")
                print(f"   Classification: {info['classification']}")
                print(f"   Area: {info['area_m2']:,.0f} m²")
        
        if result['in_karst']:
            print(f"✅ IN KARST AREA: {result['karst_proximity']}")
        elif result['karst_proximity'] == 'nearby':
            print(f"🔍 KARST NEARBY: within {result['distance_miles']} miles")
        else:
            print(f"❌ NO KARST: {result['karst_proximity']}")
        
        if result.get('karst_info'):
            karst = result['karst_info']
            print(f"\n🏔️  KARST INFORMATION:")
            print(f"   Name: {karst['nombre']}")
            print(f"   Regulation: {karst['regla']}")
            print(f"   Area: {karst['area_hectares']:,.0f} hectares")
            print(f"   Description: {karst['description']}")
        
        print(f"\n💬 {result['message']}")
    
    def _print_multiple_result(self, result: Dict[str, Any]):
        """Print results for multiple cadastrals."""
        
        print(f"\n📋 MULTIPLE CADASTRALS PRAPEC KARST CHECK")
        print("=" * 60)
        print(f"Total cadastrals checked: {result['total_cadastrals']}")
        print(f"Buffer distance: {result['buffer_miles']} miles")
        
        summary = result['summary']
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Directly in karst: {summary['in_karst']}")
        print(f"   🔍 Karst nearby: {summary['nearby_karst']}")
        print(f"   ❌ No karst: {summary['no_karst']}")
        print(f"   ⚠️  Errors: {summary['errors']}")
        
        if result.get('karst_info'):
            karst = result['karst_info']
            print(f"\n🏔️  KARST INFORMATION:")
            print(f"   Name: {karst['nombre']}")
            print(f"   Regulation: {karst['regla']}")
            print(f"   Area: {karst['area_hectares']:,.0f} hectares")
            print(f"   Description: {karst['description']}")
        
        print(f"\n💬 {result['message']}")
        
        # Show individual results
        print(f"\n📋 INDIVIDUAL RESULTS:")
        for i, cad_result in enumerate(result['cadastral_results'], 1):
            status = "✅" if cad_result.get('in_karst') else "🔍" if cad_result.get('karst_proximity') == 'nearby' else "❌"
            cadastral = cad_result.get('cadastral_number', 'Unknown')
            proximity = cad_result.get('karst_proximity', 'unknown')
            print(f"   {i:2d}. {status} {cadastral} - {proximity}")


# Convenience functions for direct usage
def check_coordinates_for_karst(
    longitude: float,
    latitude: float,
    buffer_miles: float = 0.5,
    include_buffer_search: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to check coordinates for PRAPEC karst.
    
    Args:
        longitude: Longitude in WGS84
        latitude: Latitude in WGS84
        buffer_miles: Buffer distance in miles
        include_buffer_search: Whether to search within buffer
        
    Returns:
        Result dictionary
    """
    checker = PrapecKarstChecker()
    return checker.check_coordinates(longitude, latitude, buffer_miles, include_buffer_search)


def check_cadastral_for_karst(
    cadastral_number: str,
    buffer_miles: float = 0.5,
    include_buffer_search: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to check a cadastral for PRAPEC karst.
    
    Args:
        cadastral_number: The cadastral number
        buffer_miles: Buffer distance in miles
        include_buffer_search: Whether to search within buffer
        
    Returns:
        Result dictionary
    """
    checker = PrapecKarstChecker()
    return checker.check_cadastral(cadastral_number, buffer_miles, include_buffer_search)


def check_multiple_cadastrals_for_karst(
    cadastral_numbers: List[str],
    buffer_miles: float = 0.5,
    include_buffer_search: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to check multiple cadastrals for PRAPEC karst.
    
    Args:
        cadastral_numbers: List of cadastral numbers
        buffer_miles: Buffer distance in miles
        include_buffer_search: Whether to search within buffer
        
    Returns:
        Result dictionary
    """
    checker = PrapecKarstChecker()
    return checker.check_multiple_cadastrals(cadastral_numbers, buffer_miles, include_buffer_search)


# Example usage and testing
if __name__ == "__main__":
    print("🏔️  PRAPEC KARST CHECKER EXAMPLES")
    print("=" * 70)
    
    # Initialize checker
    checker = PrapecKarstChecker()
    
    # Example 1: Check coordinates
    print("\n1️⃣  Checking coordinates...")
    print("-" * 50)
    
    # Test point in known karst area
    result = checker.check_coordinates(-66.7, 18.4, buffer_miles=0.5)
    checker.print_result(result)
    
    # Example 2: Check cadastral number
    print("\n2️⃣  Checking cadastral number...")
    print("-" * 50)
    
    # Test with a known cadastral
    result = checker.check_cadastral("227-052-007-20", buffer_miles=0.5)
    checker.print_result(result)
    
    # Example 3: Check multiple cadastrals
    print("\n3️⃣  Checking multiple cadastrals...")
    print("-" * 50)
    
    test_cadastrals = [
        "227-062-084-05",
        "227-052-007-20",
        "227-062-084-04"
    ]
    
    result = checker.check_multiple_cadastrals(test_cadastrals, buffer_miles=0.5)
    checker.print_result(result)
    
    print(f"\n✅ PRAPEC Karst Checker examples completed!") 