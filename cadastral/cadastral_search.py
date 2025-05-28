#!/usr/bin/env python3
"""
MIPR Cadastral Search
Search and retrieve MIPR data by cadastral numbers
"""

import sys
import os
import json
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict

# Add the parent directory to the path to access mapmaker
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mapmaker.common import MapServerClient
from .cadastral_utils import CadastralDataProcessor, CadastralQueryBuilder

class MIPRCadastralSearch:
    """
    Search and retrieve MIPR data by cadastral numbers.
    
    This class provides search capabilities for finding MIPR land use classification
    and related data using cadastral numbers as the search criteria.
    """
    
    def __init__(self):
        """Initialize the MIPR Cadastral Search service."""
        self.service_url = "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer"
        self.query_builder = CadastralQueryBuilder(self.service_url)
    
    def search_by_cadastral(
        self,
        cadastral_number: str,
        exact_match: bool = True,
        include_geometry: bool = False
    ) -> Dict[str, Any]:
        """
        Search for MIPR data by cadastral number.
        
        Args:
            cadastral_number: Cadastral number to search for
            exact_match: If True, search for exact match; if False, search for partial match
            include_geometry: Whether to include geometry data in results
            
        Returns:
            Dictionary with search results
        """
        try:
            # Build query parameters using centralized utility
            params = self.query_builder.build_cadastral_query_params(
                [cadastral_number], exact_match, include_geometry, max_results=100
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
                    'search_cadastral': cadastral_number,
                    'exact_match': exact_match,
                    'feature_count': 0,
                    'results': [],
                    'message': f'No data found for cadastral number: {cadastral_number}'
                }
            
            # Process results using centralized utility
            processed_features = CadastralDataProcessor.process_feature_list(features, include_geometry)
            analysis = CadastralDataProcessor.analyze_cadastral_distribution(processed_features)
            
            return {
                'success': True,
                'search_cadastral': cadastral_number,
                'exact_match': exact_match,
                'feature_count': len(features),
                'total_area_m2': analysis['total_area_m2'],
                'total_area_hectares': analysis['total_area_hectares'],
                'unique_classifications': analysis['unique_classifications'],
                'unique_municipalities': analysis['unique_municipalities'],
                'results': processed_features
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_cadastral': cadastral_number,
                'exact_match': exact_match,
                'feature_count': 0,
                'results': []
            }
    
    def search_multiple_cadastrals(
        self,
        cadastral_numbers: List[str],
        exact_match: bool = True,
        include_geometry: bool = False
    ) -> Dict[str, Any]:
        """
        Search for MIPR data by multiple cadastral numbers.
        
        Args:
            cadastral_numbers: List of cadastral numbers to search for
            exact_match: If True, search for exact matches; if False, search for partial matches
            include_geometry: Whether to include geometry data in results
            
        Returns:
            Dictionary with search results for all cadastrals
        """
        try:
            # Build query parameters using centralized utility
            params = self.query_builder.build_cadastral_query_params(
                cadastral_numbers, exact_match, include_geometry, max_results=1000
            )
            
            # Query the service
            query_url = f"{self.service_url}/0/query"
            
            response = requests.get(query_url, params=params, verify=False, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            if not features:
                return {
                    'success': True,
                    'search_cadastrals': cadastral_numbers,
                    'exact_match': exact_match,
                    'feature_count': 0,
                    'results_by_cadastral': {},
                    'summary': {},
                    'message': f'No data found for any of the provided cadastral numbers'
                }
            
            # Process results using centralized utilities
            processed_features = CadastralDataProcessor.process_feature_list(features, include_geometry)
            analysis = CadastralDataProcessor.analyze_cadastral_distribution(processed_features)
            grouped_features = CadastralDataProcessor.group_features_by_cadastral(processed_features)
            
            # Check which cadastrals were found vs not found
            found_cadastrals = list(grouped_features.keys())
            not_found_cadastrals = []
            
            if exact_match:
                not_found_cadastrals = [cad for cad in cadastral_numbers if cad not in found_cadastrals]
            
            return {
                'success': True,
                'search_cadastrals': cadastral_numbers,
                'exact_match': exact_match,
                'feature_count': len(processed_features),
                'total_area_m2': analysis['total_area_m2'],
                'total_area_hectares': analysis['total_area_hectares'],
                'found_cadastrals': sorted(found_cadastrals),
                'not_found_cadastrals': not_found_cadastrals,
                'unique_classifications': analysis['unique_classifications'],
                'unique_municipalities': analysis['unique_municipalities'],
                'results_by_cadastral': grouped_features,
                'summary': analysis['cadastral_summary'],
                'all_features': processed_features
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_cadastrals': cadastral_numbers,
                'exact_match': exact_match,
                'feature_count': 0,
                'results_by_cadastral': {},
                'summary': {}
            }
    

    
    def get_cadastral_info(
        self,
        cadastral_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get basic information for a single cadastral number.
        
        Args:
            cadastral_number: Cadastral number to look up
            
        Returns:
            Dictionary with basic cadastral information or None if not found
        """
        result = self.search_by_cadastral(cadastral_number, exact_match=True, include_geometry=False)
        
        if result['success'] and result['feature_count'] > 0:
            # Return the first (largest) result
            first_result = result['results'][0]
            return {
                'cadastral_number': first_result['cadastral_number'],
                'classification_code': first_result['classification_code'],
                'classification_description': first_result['classification_description'],
                'sub_classification': first_result.get('sub_classification', ''),
                'sub_classification_description': first_result.get('sub_classification_description', ''),
                'municipality': first_result['municipality'],
                'neighborhood': first_result['neighborhood'],
                'region': first_result.get('region', ''),
                'area_m2': first_result['area_m2'],
                'area_hectares': first_result['area_m2'] / 10000 if first_result['area_m2'] else 0,
                'status': first_result['status']
            }
        
        return None
    
    def search_by_classification(
        self,
        classification_code: str,
        municipality: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search for cadastrals by land use classification.
        
        Args:
            classification_code: Classification code to search for (e.g., 'R-1', 'C-1')
            municipality: Optional municipality filter
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Build the where clause
            where_clause = f"cali = '{classification_code}'"
            if municipality:
                where_clause += f" AND municipio = '{municipality}'"
            
            # Query the service
            query_url = f"{self.service_url}/0/query"
            params = {
                'where': where_clause,
                'outFields': 'num_catast,cali,descrip,municipio,barrio,SHAPE.STArea()',
                'returnGeometry': 'false',
                'f': 'json',
                'resultRecordCount': limit,
                'orderByFields': 'SHAPE.STArea() DESC'
            }
            
            response = requests.get(query_url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            features = data.get('features', [])
            
            cadastrals = []
            total_area = 0
            municipalities = set()
            
            for feature in features:
                attrs = feature.get('attributes', {})
                cadastral_num = (attrs.get('num_catast', '') or '').strip()
                municipality_name = attrs.get('municipio', 'Unknown')
                area_m2 = attrs.get('SHAPE.STArea()', 0)
                
                if cadastral_num:
                    cadastrals.append({
                        'cadastral_number': cadastral_num,
                        'municipality': municipality_name,
                        'neighborhood': attrs.get('barrio', ''),
                        'area_m2': area_m2
                    })
                    total_area += area_m2
                    municipalities.add(municipality_name)
            
            return {
                'success': True,
                'search_classification': classification_code,
                'search_municipality': municipality,
                'feature_count': len(cadastrals),
                'total_area_m2': total_area,
                'total_area_hectares': total_area / 10000,
                'municipalities': sorted(list(municipalities)),
                'cadastrals': cadastrals
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_classification': classification_code,
                'search_municipality': municipality,
                'feature_count': 0,
                'cadastrals': []
            }
    
    def export_search_results(
        self,
        search_results: Dict[str, Any],
        output_file: str,
        format: str = 'json'
    ) -> str:
        """
        Export search results to a file.
        
        Args:
            search_results: Results from any search method
            output_file: Path to output file
            format: Output format ('json', 'csv')
            
        Returns:
            Path to exported file
        """
        try:
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(search_results, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == 'csv':
                import csv
                
                # Determine which results to export
                features_to_export = []
                
                if 'results' in search_results:
                    # Single cadastral search
                    features_to_export = search_results['results']
                elif 'all_features' in search_results:
                    # Multiple cadastral search
                    features_to_export = search_results['all_features']
                elif 'cadastrals' in search_results:
                    # Classification search
                    features_to_export = search_results['cadastrals']
                
                if features_to_export:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=features_to_export[0].keys())
                        writer.writeheader()
                        for feature in features_to_export:
                            # Remove geometry for CSV export
                            feature_copy = {k: v for k, v in feature.items() if k != 'geometry'}
                            writer.writerow(feature_copy)
            
            print(f"✅ Search results exported to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error exporting search results: {e}")
            return ""
    
    def print_search_summary(self, search_results: Dict[str, Any]):
        """Print a formatted summary of search results."""
        
        if not search_results['success']:
            print(f"❌ Search failed: {search_results.get('error', 'Unknown error')}")
            return
        
        print(f"\n🔍 MIPR CADASTRAL SEARCH SUMMARY")
        print("=" * 60)
        
        # Handle different types of search results
        if 'search_cadastral' in search_results:
            # Single cadastral search
            print(f"Search Cadastral: {search_results['search_cadastral']}")
            print(f"Exact Match: {search_results['exact_match']}")
            print(f"Features Found: {search_results['feature_count']}")
            
            if search_results['feature_count'] > 0:
                print(f"Total Area: {search_results['total_area_hectares']:.2f} hectares")
                print(f"Classifications: {', '.join(search_results['unique_classifications'])}")
                print(f"Municipalities: {', '.join(search_results['unique_municipalities'])}")
        
        elif 'search_cadastrals' in search_results:
            # Multiple cadastral search
            print(f"Search Cadastrals: {len(search_results['search_cadastrals'])} numbers")
            print(f"Found: {len(search_results['found_cadastrals'])}")
            print(f"Not Found: {len(search_results['not_found_cadastrals'])}")
            print(f"Total Features: {search_results['feature_count']}")
            
            if search_results['feature_count'] > 0:
                print(f"Total Area: {search_results['total_area_hectares']:.2f} hectares")
                
                print(f"\n📋 Found Cadastrals:")
                for cadastral in search_results['found_cadastrals'][:10]:
                    summary = search_results['summary'].get(cadastral, {})
                    area = summary.get('total_area_hectares', 0)
                    classifications = ', '.join(summary.get('classifications', []))
                    print(f"   • {cadastral}: {area:.2f} ha ({classifications})")
                
                if len(search_results['found_cadastrals']) > 10:
                    print(f"   ... and {len(search_results['found_cadastrals']) - 10} more")
                
                if search_results['not_found_cadastrals']:
                    print(f"\n❌ Not Found:")
                    for cadastral in search_results['not_found_cadastrals'][:5]:
                        print(f"   • {cadastral}")
        
        elif 'search_classification' in search_results:
            # Classification search
            print(f"Search Classification: {search_results['search_classification']}")
            if search_results.get('search_municipality'):
                print(f"Municipality Filter: {search_results['search_municipality']}")
            print(f"Cadastrals Found: {search_results['feature_count']}")
            
            if search_results['feature_count'] > 0:
                print(f"Total Area: {search_results['total_area_hectares']:.2f} hectares")
                print(f"Municipalities: {', '.join(search_results['municipalities'])}")

# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("MIPR CADASTRAL SEARCH EXAMPLES")
    print("=" * 70)
    
    # Initialize cadastral search
    search = MIPRCadastralSearch()
    
    # Example cadastral numbers (you would use real ones)
    example_cadastrals = ["123-456-789", "987-654-321", "111-222-333"]
    
    print("\n1. Single cadastral search...")
    print("-" * 40)
    
    # Search for a single cadastral (this will likely not find anything with fake numbers)
    result = search.search_by_cadastral(example_cadastrals[0], exact_match=True)
    search.print_search_summary(result)
    
    print("\n2. Multiple cadastral search...")
    print("-" * 40)
    
    # Search for multiple cadastrals
    result = search.search_multiple_cadastrals(example_cadastrals, exact_match=True)
    search.print_search_summary(result)
    
    print("\n3. Search by classification...")
    print("-" * 40)
    
    # Search for residential classifications
    result = search.search_by_classification("R-1", limit=10)
    search.print_search_summary(result)
    
    if result['success'] and result['feature_count'] > 0:
        # Export results
        search.export_search_results(result, "mipr/example_classification_search.json")
        
        print(f"\n4. Quick cadastral info lookup...")
        print("-" * 40)
        
        # Get info for the first cadastral found
        first_cadastral = result['cadastrals'][0]['cadastral_number']
        info = search.get_cadastral_info(first_cadastral)
        
        if info:
            print(f"   Cadastral: {info['cadastral_number']}")
            print(f"   Classification: {info['classification_code']} - {info['classification_description']}")
            print(f"   Municipality: {info['municipality']}")
            print(f"   Area: {info['area_m2']:,.0f} m²")
    
    print(f"\n✅ MIPR Cadastral Search examples completed!") 