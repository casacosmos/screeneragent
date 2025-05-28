#!/usr/bin/env python3
"""
Detailed Analysis of Critical Habitat Services

This script performs detailed analysis of the most promising critical habitat services
to understand their data structure, fields, and capabilities for building the client.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class HabitatServiceAnalyzer:
    """Analyze critical habitat services in detail"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HabitatServiceAnalyzer/1.0'
        })
        
        # Most promising services from exploration
        self.primary_services = [
            {
                "name": "USFWS Critical Habitat",
                "url": "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer",
                "description": "Primary USFWS critical habitat data with final and proposed designations"
            },
            {
                "name": "Critical Habitat Conservation Inputs",
                "url": "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/Critical_Habitat_Conservation_Inputs/FeatureServer",
                "description": "Specific critical habitat areas for various species"
            },
            {
                "name": "Threatened and Endangered Plants",
                "url": "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/Threatened_and_Endangered_Plants_of_Washington_WFL1/FeatureServer",
                "description": "Federal ESA-listed plant species ranges"
            }
        ]
        
        # Test coordinates (Puerto Rico)
        self.test_coords = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
        
        # Test coordinates (Continental US - California)
        self.test_coords_ca = {"x": -122.4194, "y": 37.7749, "spatialReference": {"wkid": 4326}}
        
        # Test coordinates (Florida)
        self.test_coords_fl = {"x": -81.3792, "y": 28.5383, "spatialReference": {"wkid": 4326}}
    
    def analyze_all_services(self):
        """Analyze all primary services in detail"""
        print("🔬 DETAILED HABITAT SERVICE ANALYSIS")
        print("="*80)
        
        for service in self.primary_services:
            print(f"\n📊 ANALYZING: {service['name']}")
            print("-"*60)
            print(f"URL: {service['url']}")
            print(f"Description: {service['description']}")
            
            self.analyze_service_detailed(service)
    
    def analyze_service_detailed(self, service: Dict):
        """Perform detailed analysis of a service"""
        try:
            # Get service metadata
            response = self.session.get(f"{service['url']}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            if 'error' in service_info:
                print(f"❌ Service error: {service_info['error']}")
                return
            
            print(f"✅ Service accessible")
            print(f"Capabilities: {service_info.get('capabilities', 'N/A')}")
            print(f"Max record count: {service_info.get('maxRecordCount', 'N/A')}")
            
            # Analyze each layer
            layers = service_info.get('layers', [])
            print(f"Total layers: {len(layers)}")
            
            for layer in layers:
                self.analyze_layer_detailed(service['url'], layer)
                
        except Exception as e:
            print(f"❌ Error analyzing service: {e}")
    
    def analyze_layer_detailed(self, service_url: str, layer: Dict):
        """Perform detailed analysis of a layer"""
        layer_id = layer.get('id')
        layer_name = layer.get('name', 'Unknown')
        
        print(f"\n  🔍 LAYER {layer_id}: {layer_name}")
        print(f"  {'-'*50}")
        
        try:
            # Get layer metadata
            layer_response = self.session.get(f"{service_url}/{layer_id}?f=json", timeout=10)
            layer_response.raise_for_status()
            layer_info = layer_response.json()
            
            if 'error' in layer_info:
                print(f"    ❌ Layer error: {layer_info['error']}")
                return
            
            # Basic layer info
            print(f"    Type: {layer_info.get('type', 'Unknown')}")
            print(f"    Geometry: {layer_info.get('geometryType', 'Unknown')}")
            print(f"    Min Scale: {layer_info.get('minScale', 'N/A')}")
            print(f"    Max Scale: {layer_info.get('maxScale', 'N/A')}")
            
            # Analyze fields
            self.analyze_layer_fields(layer_info)
            
            # Test queries with different locations
            self.test_layer_queries(service_url, layer_id, layer_name)
            
            # Get sample data
            self.get_sample_data(service_url, layer_id, layer_name)
            
        except Exception as e:
            print(f"    ❌ Error analyzing layer: {e}")
    
    def analyze_layer_fields(self, layer_info: Dict):
        """Analyze the fields in a layer"""
        fields = layer_info.get('fields', [])
        
        if not fields:
            print("    No fields found")
            return
        
        print(f"    Fields ({len(fields)} total):")
        
        # Categorize fields
        key_fields = []
        id_fields = []
        name_fields = []
        status_fields = []
        other_fields = []
        
        for field in fields:
            field_name = field.get('name', '').lower()
            field_type = field.get('type', '')
            field_alias = field.get('alias', field.get('name', ''))
            
            if any(term in field_name for term in ['species', 'comname', 'sciname', 'common', 'scientific']):
                key_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['status', 'endangered', 'threatened', 'critical']):
                status_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['name', 'unit', 'area']):
                name_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['id', 'objectid', 'fid']):
                id_fields.append((field.get('name'), field_type, field_alias))
            else:
                other_fields.append((field.get('name'), field_type, field_alias))
        
        # Display categorized fields
        if key_fields:
            print("      🎯 Species/Key Fields:")
            for name, ftype, alias in key_fields[:5]:
                print(f"        • {name} ({ftype}): {alias}")
        
        if status_fields:
            print("      📊 Status Fields:")
            for name, ftype, alias in status_fields[:3]:
                print(f"        • {name} ({ftype}): {alias}")
        
        if name_fields:
            print("      🏷️  Name/Unit Fields:")
            for name, ftype, alias in name_fields[:3]:
                print(f"        • {name} ({ftype}): {alias}")
        
        if other_fields:
            print(f"      📋 Other Fields ({len(other_fields)} total):")
            for name, ftype, alias in other_fields[:3]:
                print(f"        • {name} ({ftype}): {alias}")
            if len(other_fields) > 3:
                print(f"        ... and {len(other_fields) - 3} more")
    
    def test_layer_queries(self, service_url: str, layer_id: int, layer_name: str):
        """Test queries on different locations"""
        print("    🧪 Testing queries:")
        
        test_locations = [
            ("Puerto Rico", self.test_coords),
            ("California", self.test_coords_ca),
            ("Florida", self.test_coords_fl)
        ]
        
        for location_name, coords in test_locations:
            try:
                query_params = {
                    "geometry": json.dumps(coords),
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "*",
                    "returnGeometry": "false",
                    "returnCountOnly": "true",
                    "f": "json"
                }
                
                response = self.session.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=10)
                response.raise_for_status()
                result = response.json()
                
                if 'error' not in result:
                    count = result.get('count', 0)
                    print(f"      {location_name}: {count} features")
                else:
                    print(f"      {location_name}: Query failed")
                    
            except Exception as e:
                print(f"      {location_name}: Error - {e}")
    
    def get_sample_data(self, service_url: str, layer_id: int, layer_name: str):
        """Get sample data from the layer"""
        print("    📄 Sample data:")
        
        try:
            # Get a few sample records
            query_params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": "3",
                "f": "json"
            }
            
            response = self.session.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                print(f"      ❌ Sample query failed: {result['error']}")
                return
            
            features = result.get('features', [])
            if not features:
                print("      No sample data available")
                return
            
            print(f"      Found {len(features)} sample records:")
            
            for i, feature in enumerate(features[:2]):  # Show first 2 records
                attributes = feature.get('attributes', {})
                print(f"        Record {i+1}:")
                
                # Show key attributes
                key_attrs = {}
                for key, value in attributes.items():
                    if any(term in key.lower() for term in ['name', 'species', 'status', 'unit', 'type']):
                        if value and str(value).strip():
                            key_attrs[key] = value
                
                for key, value in list(key_attrs.items())[:5]:  # Show first 5 key attributes
                    print(f"          {key}: {value}")
                
                if len(key_attrs) > 5:
                    print(f"          ... and {len(key_attrs) - 5} more attributes")
                    
        except Exception as e:
            print(f"      ❌ Error getting sample data: {e}")
    
    def generate_service_summary(self):
        """Generate a summary of findings"""
        print(f"\n📋 SERVICE ANALYSIS SUMMARY")
        print("="*80)
        
        print("🎯 RECOMMENDED PRIMARY SERVICE:")
        print("   USFWS_Critical_Habitat/FeatureServer")
        print("   - Comprehensive critical habitat data")
        print("   - Both final and proposed designations")
        print("   - Polygon and linear features")
        print("   - Standard species fields (comname, sciname, unitname)")
        
        print("\n🔧 RECOMMENDED IMPLEMENTATION:")
        print("   1. Use USFWS_Critical_Habitat as primary service")
        print("   2. Query Layer 0 (Final Polygon) and Layer 1 (Final Linear)")
        print("   3. Include Layer 2 (Proposed Polygon) for comprehensive analysis")
        print("   4. Key fields: comname, sciname, unitname, status")
        
        print("\n📊 QUERY CAPABILITIES:")
        print("   - Spatial intersection queries")
        print("   - Attribute filtering by species")
        print("   - Geometry return for mapping")
        print("   - Extract capability for bulk operations")

def main():
    """Main analysis function"""
    print("🌿 Critical Habitat Service Detailed Analysis")
    print("="*80)
    
    analyzer = HabitatServiceAnalyzer()
    analyzer.analyze_all_services()
    analyzer.generate_service_summary()
    
    print(f"\n✅ ANALYSIS COMPLETE")
    print(f"="*80)
    print(f"💡 Ready to build HabitatINFO client based on findings")

if __name__ == "__main__":
    main() 