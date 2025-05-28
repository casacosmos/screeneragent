#!/usr/bin/env python3
"""
MIPR Cadastral Utilities
Centralized utilities for processing cadastral data across all MIPR modules
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict

# Add the parent directory to the path to access mapmaker
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mapmaker.common import MapServerClient

class CadastralDataProcessor:
    """
    Centralized processor for MIPR cadastral data.
    
    This class provides common functionality for extracting, processing, and 
    analyzing cadastral data from MIPR service responses.
    """
    
    @staticmethod
    def extract_cadastral_attributes(feature_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and standardize cadastral attributes from a feature.
        
        Args:
            feature_attributes: Raw attributes from MIPR service response
            
        Returns:
            Dictionary with standardized cadastral information
        """
        attrs = feature_attributes
        
        return {
            'object_id': attrs.get('OBJECTID'),
            'cadastral_number': (attrs.get('num_catast', '') or '').strip(),
            'classification_code': attrs.get('cali', 'Unknown'),
            'classification_description': attrs.get('descrip', 'No description'),
            'sub_classification': attrs.get('clasi', ''),
            'sub_classification_description': attrs.get('descrip1', ''),
            'municipality': attrs.get('municipio', 'Unknown'),
            'neighborhood': attrs.get('barrio', ''),
            'region': attrs.get('Region', ''),
            'case_number': attrs.get('numcaso', ''),
            'status': attrs.get('vigencia', ''),
            'resolution': attrs.get('resolucion', ''),
            'area_m2': attrs.get('SHAPE.STArea()', 0),
            'area_hectares': (attrs.get('SHAPE.STArea()', 0) / 10000) if attrs.get('SHAPE.STArea()', 0) else 0
        }
    
    @staticmethod
    def process_feature_list(features: List[Dict], include_geometry: bool = False) -> List[Dict[str, Any]]:
        """
        Process a list of features into standardized cadastral data.
        
        Args:
            features: List of features from MIPR service response
            include_geometry: Whether to include geometry data
            
        Returns:
            List of processed cadastral feature dictionaries
        """
        processed_features = []
        
        for feature in features:
            attrs = feature.get('attributes', {})
            cadastral_data = CadastralDataProcessor.extract_cadastral_attributes(attrs)
            
            if include_geometry:
                cadastral_data['geometry'] = feature.get('geometry')
            
            processed_features.append(cadastral_data)
        
        return processed_features
    
    @staticmethod
    def analyze_cadastral_distribution(features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the distribution of cadastrals, classifications, and municipalities.
        
        Args:
            features: List of processed cadastral features
            
        Returns:
            Dictionary with distribution analysis
        """
        cadastral_summary = defaultdict(lambda: {
            'count': 0, 'total_area': 0, 'classifications': set(), 'municipalities': set()
        })
        classification_summary = defaultdict(lambda: {
            'count': 0, 'total_area': 0, 'cadastrals': set(), 'description': ''
        })
        municipality_summary = defaultdict(lambda: {
            'count': 0, 'total_area': 0, 'classifications': set(), 'cadastrals': set()
        })
        
        unique_cadastrals = set()
        unique_classifications = set()
        unique_municipalities = set()
        total_area = 0
        
        for feature in features:
            cadastral_num = feature['cadastral_number']
            classification = feature['classification_code']
            description = feature['classification_description']
            municipality = feature['municipality']
            area_m2 = feature['area_m2']
            
            total_area += area_m2
            
            # Track unique values
            if cadastral_num:
                unique_cadastrals.add(cadastral_num)
            unique_classifications.add(classification)
            unique_municipalities.add(municipality)
            
            # Update cadastral summary
            if cadastral_num:
                cadastral_summary[cadastral_num]['count'] += 1
                cadastral_summary[cadastral_num]['total_area'] += area_m2
                cadastral_summary[cadastral_num]['classifications'].add(classification)
                cadastral_summary[cadastral_num]['municipalities'].add(municipality)
            
            # Update classification summary
            classification_summary[classification]['count'] += 1
            classification_summary[classification]['total_area'] += area_m2
            classification_summary[classification]['description'] = description
            if cadastral_num:
                classification_summary[classification]['cadastrals'].add(cadastral_num)
            
            # Update municipality summary
            municipality_summary[municipality]['count'] += 1
            municipality_summary[municipality]['total_area'] += area_m2
            municipality_summary[municipality]['classifications'].add(classification)
            if cadastral_num:
                municipality_summary[municipality]['cadastrals'].add(cadastral_num)
        
        # Convert sets to lists for JSON serialization
        processed_cadastral_summary = {}
        for cad_num, info in cadastral_summary.items():
            processed_cadastral_summary[cad_num] = {
                'count': info['count'],
                'total_area_m2': info['total_area'],
                'total_area_hectares': info['total_area'] / 10000,
                'classifications': sorted(list(info['classifications'])),
                'municipalities': sorted(list(info['municipalities']))
            }
        
        processed_classification_summary = {}
        for class_code, info in classification_summary.items():
            processed_classification_summary[class_code] = {
                'count': info['count'],
                'total_area_m2': info['total_area'],
                'total_area_hectares': info['total_area'] / 10000,
                'description': info['description'],
                'cadastrals': sorted(list(info['cadastrals']))
            }
        
        processed_municipality_summary = {}
        for municipality, info in municipality_summary.items():
            processed_municipality_summary[municipality] = {
                'count': info['count'],
                'total_area_m2': info['total_area'],
                'total_area_hectares': info['total_area'] / 10000,
                'classifications': sorted(list(info['classifications'])),
                'cadastrals': sorted(list(info['cadastrals']))
            }
        
        return {
            'total_area_m2': total_area,
            'total_area_hectares': total_area / 10000,
            'unique_cadastrals': sorted(list(unique_cadastrals)),
            'unique_classifications': sorted(list(unique_classifications)),
            'unique_municipalities': sorted(list(unique_municipalities)),
            'cadastral_summary': processed_cadastral_summary,
            'classification_summary': processed_classification_summary,
            'municipality_summary': processed_municipality_summary
        }
    
    @staticmethod
    def calculate_statistics(cadastral_summary: Dict, classification_summary: Dict, 
                           municipality_summary: Dict, total_area: float) -> Dict[str, Any]:
        """
        Calculate summary statistics from distribution analysis.
        
        Args:
            cadastral_summary: Cadastral distribution data
            classification_summary: Classification distribution data
            municipality_summary: Municipality distribution data
            total_area: Total area in square meters
            
        Returns:
            Dictionary with calculated statistics
        """
        stats = {
            'total_cadastrals': len(cadastral_summary),
            'total_classifications': len(classification_summary),
            'total_municipalities': len(municipality_summary),
            'total_area_m2': total_area,
            'total_area_hectares': total_area / 10000,
            'largest_cadastral': None,
            'dominant_classification': None,
            'primary_municipality': None
        }
        
        # Find largest cadastral by area
        if cadastral_summary:
            largest_cad = max(cadastral_summary.items(), key=lambda x: x[1]['total_area_m2'])
            stats['largest_cadastral'] = {
                'number': largest_cad[0],
                'area_m2': largest_cad[1]['total_area_m2'],
                'area_hectares': largest_cad[1]['total_area_hectares'],
                'percentage': (largest_cad[1]['total_area_m2'] / total_area) * 100 if total_area > 0 else 0
            }
        
        # Find dominant classification by area
        if classification_summary:
            dominant_class = max(classification_summary.items(), key=lambda x: x[1]['total_area_m2'])
            stats['dominant_classification'] = {
                'code': dominant_class[0],
                'description': dominant_class[1]['description'],
                'area_m2': dominant_class[1]['total_area_m2'],
                'area_hectares': dominant_class[1]['total_area_hectares'],
                'percentage': (dominant_class[1]['total_area_m2'] / total_area) * 100 if total_area > 0 else 0
            }
        
        # Find primary municipality by area
        if municipality_summary:
            primary_muni = max(municipality_summary.items(), key=lambda x: x[1]['total_area_m2'])
            stats['primary_municipality'] = {
                'name': primary_muni[0],
                'area_m2': primary_muni[1]['total_area_m2'],
                'area_hectares': primary_muni[1]['total_area_hectares'],
                'percentage': (primary_muni[1]['total_area_m2'] / total_area) * 100 if total_area > 0 else 0
            }
        
        return stats
    
    @staticmethod
    def find_primary_cadastral(features: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the primary (largest by area) cadastral from a list of features.
        
        Args:
            features: List of processed cadastral features
            
        Returns:
            Primary cadastral feature or None if no valid cadastrals found
        """
        valid_features = [f for f in features if f['cadastral_number']]
        if not valid_features:
            return None
        
        return max(valid_features, key=lambda x: x['area_m2'])
    
    @staticmethod
    def find_dominant_classification(features: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find the dominant (most common by count) classification from features.
        
        Args:
            features: List of processed cadastral features
            
        Returns:
            Dominant classification code or None if no features
        """
        if not features:
            return None
        
        classification_counts = defaultdict(int)
        for feature in features:
            classification_counts[feature['classification_code']] += 1
        
        return max(classification_counts.items(), key=lambda x: x[1])[0]
    
    @staticmethod
    def build_where_clause(cadastral_numbers: List[str], exact_match: bool = True) -> str:
        """
        Build SQL WHERE clause for cadastral number searches.
        
        Args:
            cadastral_numbers: List of cadastral numbers to search for
            exact_match: Whether to use exact or partial matching
            
        Returns:
            SQL WHERE clause string
        """
        if len(cadastral_numbers) == 1:
            cadastral_number = cadastral_numbers[0]
            if exact_match:
                return f"num_catast = '{cadastral_number}'"
            else:
                return f"num_catast LIKE '%{cadastral_number}%'"
        else:
            if exact_match:
                cadastral_list = "', '".join(cadastral_numbers)
                return f"num_catast IN ('{cadastral_list}')"
            else:
                like_conditions = [f"num_catast LIKE '%{cad}%'" for cad in cadastral_numbers]
                return " OR ".join(like_conditions)
    
    @staticmethod
    def group_features_by_cadastral(features: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group features by cadastral number.
        
        Args:
            features: List of processed cadastral features
            
        Returns:
            Dictionary mapping cadastral numbers to lists of features
        """
        grouped = defaultdict(list)
        
        for feature in features:
            cadastral_num = feature['cadastral_number']
            if cadastral_num:
                grouped[cadastral_num].append(feature)
        
        return dict(grouped)
    
    @staticmethod
    def create_cadastral_summary_for_tools(features: List[Dict[str, Any]], 
                                         search_type: str = "single") -> Dict[str, Any]:
        """
        Create a summary suitable for LangGraph tools from processed features.
        
        Args:
            features: List of processed cadastral features
            search_type: Type of search ("single" or "multiple")
            
        Returns:
            Dictionary formatted for tool responses
        """
        if not features:
            return {
                "total_area_hectares": 0,
                "unique_classifications": [],
                "unique_municipalities": [],
                "property_details": []
            }
        
        analysis = CadastralDataProcessor.analyze_cadastral_distribution(features)
        
        summary = {
            "total_area_hectares": analysis['total_area_hectares'],
            "unique_classifications": analysis['unique_classifications'],
            "unique_municipalities": analysis['unique_municipalities']
        }
        
        if search_type == "single":
            # Format for single cadastral search
            summary["property_details"] = []
            for feature in features:
                summary["property_details"].append({
                    "cadastral_number": feature['cadastral_number'],
                    "land_use": {
                        "code": feature['classification_code'],
                        "description": feature['classification_description'],
                        "sub_classification": feature['sub_classification']
                    },
                    "location": {
                        "municipality": feature['municipality'],
                        "neighborhood": feature['neighborhood'],
                        "region": feature['region']
                    },
                    "area": {
                        "area_m2": feature['area_m2'],
                        "area_hectares": feature['area_hectares']
                    },
                    "regulatory": {
                        "status": feature['status'],
                        "case_number": feature['case_number']
                    }
                })
        else:
            # Format for multiple cadastral search
            grouped = CadastralDataProcessor.group_features_by_cadastral(features)
            
            summary.update({
                "found_cadastrals": list(grouped.keys()),
                "cadastral_details": {}
            })
            
            for cadastral_num, cadastral_features in grouped.items():
                total_area = sum(f['area_m2'] for f in cadastral_features)
                classifications = list(set(f['classification_code'] for f in cadastral_features))
                municipalities = list(set(f['municipality'] for f in cadastral_features))
                
                summary["cadastral_details"][cadastral_num] = {
                    "area_hectares": total_area / 10000,
                    "feature_count": len(cadastral_features),
                    "classifications": classifications,
                    "municipalities": municipalities
                }
            
            # Add classification breakdown
            classification_breakdown = {}
            for classification in analysis['unique_classifications']:
                class_features = [f for f in features if f['classification_code'] == classification]
                total_area = sum(f['area_m2'] for f in class_features)
                
                classification_breakdown[classification] = {
                    "feature_count": len(class_features),
                    "total_area_hectares": total_area / 10000,
                    "percentage": (total_area / analysis['total_area_m2']) * 100 if analysis['total_area_m2'] > 0 else 0
                }
            
            summary["land_use_analysis"] = classification_breakdown
        
        return summary

class CadastralQueryBuilder:
    """
    Builder class for constructing MIPR service queries.
    """
    
    def __init__(self, service_url: str):
        """Initialize with MIPR service URL."""
        self.service_url = service_url
        self.client = MapServerClient(service_url)
        self.client.fetch_metadata()
    
    def build_point_query_params(self, longitude: float, latitude: float, 
                                buffer_meters: float = 0, include_geometry: bool = False,
                                max_results: int = 20) -> Dict[str, Any]:
        """
        Build query parameters for point-based searches.
        
        Args:
            longitude: Longitude in WGS84
            latitude: Latitude in WGS84
            buffer_meters: Buffer distance in meters
            include_geometry: Whether to include geometry
            max_results: Maximum number of results
            
        Returns:
            Dictionary with query parameters
        """
        # Convert point to Web Mercator
        x_merc, y_merc = self.client.lonlat_to_webmercator(longitude, latitude)
        
        geometry = {
            "x": x_merc,
            "y": y_merc,
            "spatialReference": {"wkid": 102100}
        }
        
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'inSR': 102100,
            'outFields': '*',
            'returnGeometry': str(include_geometry).lower(),
            'f': 'json',
            'resultRecordCount': max_results,
            'orderByFields': 'SHAPE.STArea() DESC'
        }
        
        if buffer_meters > 0:
            params.update({
                'distance': buffer_meters,
                'units': 'esriSRUnit_Meter'
            })
        
        return params
    
    def build_polygon_query_params(self, polygon_coords: List[Tuple[float, float]], 
                                 include_geometry: bool = False,
                                 max_results: int = 1000) -> Dict[str, Any]:
        """
        Build query parameters for polygon-based searches.
        
        Args:
            polygon_coords: List of (longitude, latitude) coordinate pairs
            include_geometry: Whether to include geometry
            max_results: Maximum number of results
            
        Returns:
            Dictionary with query parameters
        """
        # Convert polygon coordinates to Web Mercator
        merc_coords = []
        for lon, lat in polygon_coords:
            x, y = self.client.lonlat_to_webmercator(lon, lat)
            merc_coords.append([x, y])
        
        geometry = {
            "rings": [merc_coords],
            "spatialReference": {"wkid": 102100}
        }
        
        return {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'inSR': 102100,
            'outFields': '*',
            'returnGeometry': str(include_geometry).lower(),
            'f': 'json',
            'resultRecordCount': max_results,
            'orderByFields': 'num_catast,SHAPE.STArea() DESC'
        }
    
    def build_cadastral_query_params(self, cadastral_numbers: List[str], 
                                   exact_match: bool = True,
                                   include_geometry: bool = False,
                                   max_results: int = 1000) -> Dict[str, Any]:
        """
        Build query parameters for cadastral number searches.
        
        Args:
            cadastral_numbers: List of cadastral numbers
            exact_match: Whether to use exact matching
            include_geometry: Whether to include geometry
            max_results: Maximum number of results
            
        Returns:
            Dictionary with query parameters
        """
        where_clause = CadastralDataProcessor.build_where_clause(cadastral_numbers, exact_match)
        
        return {
            'where': where_clause,
            'outFields': '*',
            'returnGeometry': str(include_geometry).lower(),
            'f': 'json',
            'resultRecordCount': max_results,
            'orderByFields': 'SHAPE.STArea() DESC'
        }

# Convenience functions for backward compatibility
def extract_cadastral_data(feature_attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Extract cadastral data from feature attributes (backward compatibility)."""
    return CadastralDataProcessor.extract_cadastral_attributes(feature_attributes)

def process_cadastral_features(features: List[Dict], include_geometry: bool = False) -> List[Dict[str, Any]]:
    """Process cadastral features (backward compatibility)."""
    return CadastralDataProcessor.process_feature_list(features, include_geometry)

def analyze_cadastral_data(features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cadastral data distribution (backward compatibility)."""
    return CadastralDataProcessor.analyze_cadastral_distribution(features) 