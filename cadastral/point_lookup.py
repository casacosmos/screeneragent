#!/usr/bin/env python3
"""
MIPR Point Lookup
Retrieve MIPR land use classification and cadastral data for specific coordinates
"""

import sys
import os
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Add the parent directory to the path to access mapmaker
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mapmaker.common import MapServerClient
from .cadastral_utils import CadastralDataProcessor, CadastralQueryBuilder

class MIPRPointLookup:
    """
    Lookup MIPR land use classification and cadastral data for specific point coordinates.
    
    This class provides point-based lookup capabilities for getting MIPR data
    at specific coordinates with configurable buffer distances.
    """
    
    def __init__(self):
        """Initialize the MIPR Point Lookup service."""
        self.service_url = "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer"
        self.query_builder = CadastralQueryBuilder(self.service_url)
    
    def lookup_point_exact(
        self,
        longitude: float,
        latitude: float
    ) -> Dict[str, Any]:
        """
        Get MIPR data for the exact cadastral parcel containing a specific point.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            
        Returns:
            Dictionary with MIPR data for the single cadastral parcel containing the point
        """
        try:
            # Build query parameters using centralized utility
            params = self.query_builder.build_point_query_params(
                longitude, latitude, buffer_meters=0, include_geometry=False, max_results=1
            )
            
            # Query the service with exact point intersection (no buffer)
            query_url = f"{self.service_url}/0/query"
            
            response = requests.get(query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if not features:
                return {
                    'success': True,
                    'coordinates': {'longitude': longitude, 'latitude': latitude},
                    'feature_count': 0,
                    'cadastral_data': None,
                    'message': 'No MIPR data found at this exact location'
                }
            
            # Process the single feature using centralized utility
            processed_features = CadastralDataProcessor.process_feature_list(features, include_geometry=False)
            cadastral_data = processed_features[0]
            
            return {
                'success': True,
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'feature_count': len(features),
                'cadastral_data': cadastral_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'feature_count': 0,
                'cadastral_data': None
            }

    def lookup_point(
        self,
        longitude: float,
        latitude: float,
        buffer_meters: float = 10
    ) -> Dict[str, Any]:
        """
        Get MIPR data for the primary cadastral parcel at a point location.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            buffer_meters: Buffer distance around the point in meters (default: 10m)
            
        Returns:
            Dictionary with MIPR data for the primary cadastral parcel only
        """
        try:
            # Build query parameters using centralized utility
            params = self.query_builder.build_point_query_params(
                longitude, latitude, buffer_meters=buffer_meters, include_geometry=True, max_results=5
            )
            
            # Query the service
            query_url = f"{self.service_url}/0/query"
            
            response = requests.get(query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if not features:
                return {
                    'success': True,
                    'coordinates': {'longitude': longitude, 'latitude': latitude},
                    'buffer_meters': buffer_meters,
                    'feature_count': 0,
                    'cadastral_data': None,
                    'message': 'No MIPR data found at this location'
                }
            
            # Process features and get only the primary cadastral
            processed_features = CadastralDataProcessor.process_feature_list(features, include_geometry=True)
            primary_feature = CadastralDataProcessor.find_primary_cadastral(processed_features)
            
            if not primary_feature:
                return {
                    'success': True,
                    'coordinates': {'longitude': longitude, 'latitude': latitude},
                    'buffer_meters': buffer_meters,
                    'feature_count': 0,
                    'cadastral_data': None,
                    'message': 'No primary cadastral found at this location'
                }
            
            return {
                'success': True,
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'buffer_meters': buffer_meters,
                'feature_count': 1,
                'cadastral_data': primary_feature
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'coordinates': {'longitude': longitude, 'latitude': latitude},
                'buffer_meters': buffer_meters,
                'feature_count': 0,
                'cadastral_data': None
            }
    

    
    def get_cadastral_at_point(
        self,
        longitude: float,
        latitude: float,
        exact: bool = True
    ) -> Optional[str]:
        """
        Get the cadastral number at a specific point.
        
        Args:
            longitude: Longitude in WGS84
            latitude: Latitude in WGS84
            exact: If True, get exact parcel; if False, use small buffer
            
        Returns:
            Cadastral number or None if not found
        """
        if exact:
            result = self.lookup_point_exact(longitude, latitude)
            if result['success'] and result['cadastral_data']:
                return result['cadastral_data']['cadastral_number']
        else:
            result = self.lookup_point(longitude, latitude, buffer_meters=5)
            if result['success'] and result['cadastral_data']:
                return result['cadastral_data']['cadastral_number']
        return None
    
    def get_classification_at_point(
        self,
        longitude: float,
        latitude: float,
        exact: bool = True
    ) -> Optional[Dict[str, str]]:
        """
        Get the land use classification at a specific point.
        
        Args:
            longitude: Longitude in WGS84
            latitude: Latitude in WGS84
            exact: If True, get exact parcel; if False, use small buffer
            
        Returns:
            Dictionary with classification code and description, or None if not found
        """
        if exact:
            result = self.lookup_point_exact(longitude, latitude)
            if result['success'] and result['cadastral_data']:
                return {
                    'code': result['cadastral_data']['classification_code'],
                    'description': result['cadastral_data']['classification_description']
                }
        else:
            result = self.lookup_point(longitude, latitude, buffer_meters=5)
            if result['success'] and result['cadastral_data']:
                return {
                    'code': result['cadastral_data']['classification_code'],
                    'description': result['cadastral_data']['classification_description']
                }
        return None
    
    def get_municipality_at_point(
        self,
        longitude: float,
        latitude: float,
        exact: bool = True
    ) -> Optional[str]:
        """
        Get the municipality at a specific point.
        
        Args:
            longitude: Longitude in WGS84
            latitude: Latitude in WGS84
            exact: If True, get exact parcel; if False, use small buffer
            
        Returns:
            Municipality name or None if not found
        """
        if exact:
            result = self.lookup_point_exact(longitude, latitude)
            if result['success'] and result['cadastral_data']:
                return result['cadastral_data']['municipality']
        else:
            result = self.lookup_point(longitude, latitude, buffer_meters=5)
            if result['success'] and result['cadastral_data']:
                return result['cadastral_data']['municipality']
        return None
    
    def batch_lookup_points(
        self,
        coordinates: List[Tuple[float, float]],
        buffer_meters: float = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform batch lookup for multiple points.
        
        Args:
            coordinates: List of (longitude, latitude) tuples
            buffer_meters: Buffer distance in meters
            
        Returns:
            List of lookup results for each point
        """
        results = []
        
        for i, (lon, lat) in enumerate(coordinates):
            print(f"Processing point {i+1}/{len(coordinates)}: ({lon:.6f}, {lat:.6f})")
            result = self.lookup_point(lon, lat, buffer_meters)
            results.append(result)
        
        return results
    
    def export_point_data(
        self,
        lookup_result: Dict[str, Any],
        output_file: str,
        format: str = 'json'
    ) -> str:
        """
        Export point lookup results to a file.
        
        Args:
            lookup_result: Result from lookup_point()
            output_file: Path to output file
            format: Output format ('json', 'csv')
            
        Returns:
            Path to exported file
        """
        try:
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(lookup_result, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                import csv
                
                # Export cadastral data as CSV
                if lookup_result.get('cadastral_data'):
                    cadastral_data = lookup_result['cadastral_data']
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        # Remove geometry for CSV export
                        feature_copy = {k: v for k, v in cadastral_data.items() if k != 'geometry'}
                        writer = csv.DictWriter(f, fieldnames=feature_copy.keys())
                        writer.writeheader()
                        writer.writerow(feature_copy)
            
            print(f"✅ Point data exported to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error exporting point data: {e}")
            return ""
    
    def print_exact_point_summary(self, lookup_result: Dict[str, Any]):
        """Print a formatted summary of exact point lookup results."""
        
        if not lookup_result['success']:
            print(f"❌ Lookup failed: {lookup_result.get('error', 'Unknown error')}")
            return
        
        coords = lookup_result['coordinates']
        print(f"\n📍 MIPR EXACT POINT LOOKUP SUMMARY")
        print("=" * 50)
        print(f"Coordinates: ({coords['longitude']:.6f}, {coords['latitude']:.6f})")
        print(f"Features Found: {lookup_result['feature_count']}")
        
        if lookup_result['feature_count'] == 0:
            print(lookup_result.get('message', 'No data found.'))
            return
        
        # Cadastral data
        cadastral = lookup_result['cadastral_data']
        if cadastral:
            print(f"\n🏠 Cadastral Information:")
            print(f"   Cadastral: {cadastral['cadastral_number'] or 'Not available'}")
            print(f"   Land Use: {cadastral['classification_code']} - {cadastral['classification_description']}")
            print(f"   Municipality: {cadastral['municipality']}")
            if cadastral['neighborhood']:
                print(f"   Neighborhood: {cadastral['neighborhood']}")
            if cadastral['region']:
                print(f"   Region: {cadastral['region']}")
            print(f"   Area: {cadastral['area_m2']:,.0f} m²")
            if cadastral['status']:
                print(f"   Status: {cadastral['status']}")
            if cadastral['case_number']:
                print(f"   Case Number: {cadastral['case_number']}")

    def print_point_summary(self, lookup_result: Dict[str, Any]):
        """Print a formatted summary of point lookup results."""
        
        if not lookup_result['success']:
            print(f"❌ Lookup failed: {lookup_result.get('error', 'Unknown error')}")
            return
        
        coords = lookup_result['coordinates']
        print(f"\n📍 MIPR POINT LOOKUP SUMMARY")
        print("=" * 50)
        print(f"Coordinates: ({coords['longitude']:.6f}, {coords['latitude']:.6f})")
        print(f"Buffer: {lookup_result['buffer_meters']} meters")
        print(f"Features Found: {lookup_result['feature_count']}")
        
        if lookup_result['feature_count'] == 0:
            print(lookup_result.get('message', 'No data found.'))
            return
        
        # Cadastral data
        cadastral = lookup_result['cadastral_data']
        if cadastral:
            print(f"\n🏠 Cadastral Information:")
            print(f"   Cadastral: {cadastral['cadastral_number'] or 'Not available'}")
            print(f"   Land Use: {cadastral['classification_code']} - {cadastral['classification_description']}")
            print(f"   Municipality: {cadastral['municipality']}")
            if cadastral['neighborhood']:
                print(f"   Neighborhood: {cadastral['neighborhood']}")
            if cadastral['region']:
                print(f"   Region: {cadastral['region']}")
            print(f"   Area: {cadastral['area_m2']:,.0f} m²")
            if cadastral['status']:
                print(f"   Status: {cadastral['status']}")
            if cadastral.get('case_number'):
                print(f"   Case Number: {cadastral['case_number']}")

    def get_single_cadastral(
        self,
        longitude: float,
        latitude: float,
        include_geometry: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get the single cadastral parcel where a point lies.
        
        This method performs an exact point-in-polygon query to find the specific
        cadastral parcel that contains the given coordinates.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            include_geometry: Whether to include geometry in the result
            
        Returns:
            Dictionary with cadastral data or None if no parcel found
        """
        try:
            # Build query parameters for exact point intersection
            params = self.query_builder.build_point_query_params(
                longitude, latitude, 
                buffer_meters=0,  # No buffer for exact intersection
                include_geometry=include_geometry, 
                max_results=1  # Only need the single parcel
            )
            
            # Query the service
            query_url = f"{self.service_url}/0/query"
            response = requests.get(query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if not features:
                return None
            
            # Process the single feature
            processed_features = CadastralDataProcessor.process_feature_list(
                features, include_geometry=include_geometry
            )
            
            return processed_features[0] if processed_features else None
            
        except Exception as e:
            print(f"Error getting single cadastral: {e}")
            return None

    def get_single_cadastral_number(
        self,
        longitude: float,
        latitude: float
    ) -> Optional[str]:
        """
        Get just the cadastral number where a point lies.
        
        Args:
            longitude: Longitude in WGS84 (EPSG:4326)
            latitude: Latitude in WGS84 (EPSG:4326)
            
        Returns:
            Cadastral number string or None if not found
        """
        cadastral_data = self.get_single_cadastral(longitude, latitude, include_geometry=False)
        return cadastral_data['cadastral_number'] if cadastral_data else None

# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("MIPR POINT LOOKUP EXAMPLES")
    print("=" * 70)
    
    # Initialize point lookup
    lookup = MIPRPointLookup()
    
    # Example coordinates
    test_points = [
        (-65.92583397128593, 18.2278044380104),
        (-65.92585542895804, 18.227957294948787),
        (-65.92576959826958, 18.227977675863762)
    ]
    
    print("\n1. Exact point lookup (single cadastral)...")
    print("-" * 40)
    
    lon, lat = test_points[0]
    result = lookup.lookup_point_exact(lon, lat)
    lookup.print_exact_point_summary(result)
    
    # Export result
    lookup.export_point_data(result, "mipr/example_exact_point_lookup.json")
    
    print("\n2. Buffer point lookup (primary cadastral only)...")
    print("-" * 40)
    
    result = lookup.lookup_point(lon, lat, buffer_meters=25)
    lookup.print_point_summary(result)
    
    # Export result
    lookup.export_point_data(result, "mipr/example_buffer_point_lookup.json")
    
    print("\n3. Single cadastral lookup (NEW METHODS)...")
    print("-" * 40)
    
    # Get the single cadastral parcel where the point lies
    single_cadastral = lookup.get_single_cadastral(lon, lat, include_geometry=False)
    if single_cadastral:
        print(f"   ✅ Found cadastral parcel:")
        print(f"      Cadastral: {single_cadastral['cadastral_number']}")
        print(f"      Classification: {single_cadastral['classification_code']} - {single_cadastral['classification_description']}")
        print(f"      Municipality: {single_cadastral['municipality']}")
        print(f"      Area: {single_cadastral['area_m2']:,.0f} m²")
    else:
        print(f"   ❌ No cadastral parcel found at this location")
    
    # Get just the cadastral number
    cadastral_number = lookup.get_single_cadastral_number(lon, lat)
    print(f"   Cadastral Number Only: {cadastral_number}")
    
    print("\n4. Quick lookup methods (existing)...")
    print("-" * 40)
    
    cadastral = lookup.get_cadastral_at_point(lon, lat, exact=True)
    classification = lookup.get_classification_at_point(lon, lat, exact=True)
    municipality = lookup.get_municipality_at_point(lon, lat, exact=True)
    
    print(f"   Cadastral: {cadastral}")
    print(f"   Classification: {classification}")
    print(f"   Municipality: {municipality}")
    
    print("\n5. Batch single cadastral lookup...")
    print("-" * 40)
    
    for i, (lon, lat) in enumerate(test_points):
        cadastral_number = lookup.get_single_cadastral_number(lon, lat)
        if cadastral_number:
            print(f"   Point {i+1}: {cadastral_number}")
        else:
            print(f"   Point {i+1}: No cadastral found")
    
    print("\n6. Batch exact lookup...")
    print("-" * 40)
    
    for i, (lon, lat) in enumerate(test_points):
        result = lookup.lookup_point_exact(lon, lat)
        if result['success'] and result['cadastral_data']:
            cadastral_data = result['cadastral_data']
            print(f"   Point {i+1}: {cadastral_data['cadastral_number']} - {cadastral_data['classification_code']}")
        else:
            print(f"   Point {i+1}: No data found")
    
    print("\n7. Batch buffer lookup...")
    print("-" * 40)
    
    batch_results = lookup.batch_lookup_points(test_points, buffer_meters=15)
    
    for i, result in enumerate(batch_results):
        coords = result['coordinates']
        cadastral_data = result.get('cadastral_data')
        if cadastral_data:
            print(f"   Point {i+1}: {cadastral_data['cadastral_number']} - {cadastral_data['classification_code']}")
        else:
            print(f"   Point {i+1}: No data found")
    
    print(f"\n✅ MIPR Point Lookup examples completed!") 