#!/usr/bin/env python3
"""
Detailed Analysis of EPA Services for NonAttainment Areas

This script performs detailed analysis of the most promising EPA nonattainment services
to understand their data structure, fields, and capabilities for building the client.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class EPAServiceAnalyzer:
    """Analyze EPA nonattainment services in detail"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EPAServiceAnalyzer/1.0'
        })
        
        # Most promising services from exploration
        self.primary_services = [
            {
                "name": "EPA OAR_OAQPS Folder",
                "url": "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS",
                "description": "EPA Office of Air and Radiation - Office of Air Quality Planning and Standards folder"
            },
            {
                "name": "EPA NonAttainment Areas",
                "url": "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer",
                "description": "Primary EPA nonattainment areas service with all criteria pollutants"
            }
        ]
        
        # Test coordinates for queries
        self.test_coords = [
            {"name": "Los Angeles, CA", "x": -118.2437, "y": 34.0522},
            {"name": "Houston, TX", "x": -95.3698, "y": 29.7604},
            {"name": "Phoenix, AZ", "x": -112.0740, "y": 33.4484},
            {"name": "New York, NY", "x": -74.0060, "y": 40.7128},
            {"name": "Chicago, IL", "x": -87.6298, "y": 41.8781}
        ]
    
    def analyze_all_services(self):
        """Analyze all primary services in detail"""
        print("🔬 DETAILED EPA SERVICE ANALYSIS")
        print("="*80)
        
        for service in self.primary_services:
            print(f"\n📊 ANALYZING: {service['name']}")
            print("-"*60)
            print(f"URL: {service['url']}")
            print(f"Description: {service['description']}")
            
            if service['name'] == "EPA OAR_OAQPS Folder":
                self.analyze_oar_oaqps_folder(service)
            else:
                self.analyze_service_detailed(service)
    
    def analyze_oar_oaqps_folder(self, service: Dict):
        """Analyze the OAR_OAQPS folder structure"""
        try:
            response = self.session.get(f"{service['url']}?f=json", timeout=15)
            response.raise_for_status()
            folder_info = response.json()
            
            if 'error' in folder_info:
                print(f"❌ Folder error: {folder_info['error']}")
                return
            
            print(f"✅ Folder accessible")
            
            # Analyze services in the folder
            services = folder_info.get('services', [])
            print(f"Services in OAR_OAQPS folder: {len(services)}")
            
            for service_item in services:
                service_name = service_item.get('name', 'Unknown')
                service_type = service_item.get('type', 'Unknown')
                print(f"  • {service_name} ({service_type})")
                
                # Analyze the NonattainmentAreas service in detail
                if 'NonattainmentAreas' in service_name:
                    full_url = f"{service['url']}/{service_name}/{service_type}"
                    print(f"    🎯 Analyzing NonattainmentAreas service: {full_url}")
                    self.analyze_nonattainment_service(full_url)
                    
        except Exception as e:
            print(f"❌ Error analyzing OAR_OAQPS folder: {e}")
    
    def analyze_nonattainment_service(self, service_url: str):
        """Perform detailed analysis of the nonattainment service"""
        try:
            response = self.session.get(f"{service_url}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            if 'error' in service_info:
                print(f"      ❌ Service error: {service_info['error']}")
                return
            
            print(f"      ✅ Service accessible")
            print(f"      Description: {service_info.get('serviceDescription', 'N/A')}")
            print(f"      Capabilities: {service_info.get('capabilities', 'N/A')}")
            print(f"      Max Record Count: {service_info.get('maxRecordCount', 'N/A')}")
            print(f"      Supported Query Formats: {service_info.get('supportedQueryFormats', 'N/A')}")
            
            # Analyze layers
            layers = service_info.get('layers', [])
            print(f"      Total layers: {len(layers)}")
            
            # Create layer summary
            print(f"      📋 Layer Summary:")
            for layer in layers:
                layer_id = layer.get('id')
                layer_name = layer.get('name', 'Unknown')
                print(f"        Layer {layer_id}: {layer_name}")
            
            # Analyze each layer in detail
            for layer in layers:
                self.analyze_layer_comprehensive(service_url, layer)
                
        except Exception as e:
            print(f"      ❌ Error analyzing nonattainment service: {e}")
    
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
                self.analyze_layer_comprehensive(service['url'], layer)
                
        except Exception as e:
            print(f"❌ Error analyzing service: {e}")
    
    def analyze_layer_comprehensive(self, service_url: str, layer: Dict):
        """Perform comprehensive analysis of a layer"""
        layer_id = layer.get('id')
        layer_name = layer.get('name', 'Unknown')
        
        print(f"\n    🔍 LAYER {layer_id}: {layer_name}")
        print(f"    {'-'*50}")
        
        try:
            # Get layer metadata
            layer_response = self.session.get(f"{service_url}/{layer_id}?f=json", timeout=10)
            layer_response.raise_for_status()
            layer_info = layer_response.json()
            
            if 'error' in layer_info:
                print(f"      ❌ Layer error: {layer_info['error']}")
                return
            
            # Basic layer info
            print(f"      Type: {layer_info.get('type', 'Unknown')}")
            print(f"      Geometry: {layer_info.get('geometryType', 'Unknown')}")
            print(f"      Min Scale: {layer_info.get('minScale', 'N/A')}")
            print(f"      Max Scale: {layer_info.get('maxScale', 'N/A')}")
            print(f"      Default Visibility: {layer_info.get('defaultVisibility', 'N/A')}")
            
            # Analyze fields comprehensively
            self.analyze_layer_fields_comprehensive(layer_info)
            
            # Test queries with multiple locations
            self.test_layer_queries_comprehensive(service_url, layer_id, layer_name)
            
            # Get detailed sample data
            self.get_detailed_sample_data(service_url, layer_id, layer_name)
            
        except Exception as e:
            print(f"      ❌ Error analyzing layer: {e}")
    
    def analyze_layer_fields_comprehensive(self, layer_info: Dict):
        """Comprehensive analysis of layer fields"""
        fields = layer_info.get('fields', [])
        
        if not fields:
            print("      No fields found")
            return
        
        print(f"      Fields ({len(fields)} total):")
        
        # Categorize all fields comprehensively
        field_categories = {
            'pollutant': [],
            'location': [],
            'status': [],
            'dates': [],
            'measurements': [],
            'identifiers': [],
            'geometry': [],
            'population': [],
            'regulatory': [],
            'other': []
        }
        
        for field in fields:
            field_name = field.get('name', '').lower()
            field_type = field.get('type', '')
            field_alias = field.get('alias', field.get('name', ''))
            field_info = (field.get('name'), field_type, field_alias)
            
            # Categorize fields
            if any(term in field_name for term in ['pollutant', 'pol_', 'chemical']):
                field_categories['pollutant'].append(field_info)
            elif any(term in field_name for term in ['area', 'state', 'county', 'region', 'location', 'city', 'fips']):
                field_categories['location'].append(field_info)
            elif any(term in field_name for term in ['status', 'classification', 'attainment', 'maintenance', 'meets_naaqs']):
                field_categories['status'].append(field_info)
            elif any(term in field_name for term in ['date', 'effective', 'designation', 'statutory', 'pub_date']):
                field_categories['dates'].append(field_info)
            elif any(term in field_name for term in ['design_value', 'dv_', 'concentration', 'level', 'units', 'original']):
                field_categories['measurements'].append(field_info)
            elif any(term in field_name for term in ['population', 'totpop', 'pop_']):
                field_categories['population'].append(field_info)
            elif any(term in field_name for term in ['citation', 'url', 'epa_region', 'office']):
                field_categories['regulatory'].append(field_info)
            elif any(term in field_name for term in ['id', 'objectid', 'fid', 'composite']):
                field_categories['identifiers'].append(field_info)
            elif any(term in field_name for term in ['shape', 'geometry']):
                field_categories['geometry'].append(field_info)
            else:
                field_categories['other'].append(field_info)
        
        # Display categorized fields
        category_icons = {
            'pollutant': '🌫️',
            'location': '📍',
            'status': '📊',
            'dates': '📅',
            'measurements': '📏',
            'population': '👥',
            'regulatory': '📋',
            'identifiers': '🆔',
            'geometry': '🗺️',
            'other': '📄'
        }
        
        for category, fields_list in field_categories.items():
            if fields_list:
                icon = category_icons.get(category, '📄')
                print(f"        {icon} {category.title()} Fields ({len(fields_list)}):")
                for name, ftype, alias in fields_list[:5]:  # Show first 5
                    print(f"          • {name} ({ftype}): {alias}")
                if len(fields_list) > 5:
                    print(f"          ... and {len(fields_list) - 5} more")
    
    def test_layer_queries_comprehensive(self, service_url: str, layer_id: int, layer_name: str):
        """Test comprehensive queries on multiple locations"""
        print("      🧪 Testing queries:")
        
        for location in self.test_coords:
            try:
                query_params = {
                    "geometry": json.dumps({"x": location["x"], "y": location["y"], "spatialReference": {"wkid": 4326}}),
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
                    status = "✅" if count > 0 else "⭕"
                    print(f"        {status} {location['name']}: {count} features")
                else:
                    print(f"        ❌ {location['name']}: Query failed - {result['error']}")
                    
            except Exception as e:
                print(f"        ❌ {location['name']}: Error - {e}")
    
    def get_detailed_sample_data(self, service_url: str, layer_id: int, layer_name: str):
        """Get detailed sample data from the layer"""
        print("      📄 Sample data analysis:")
        
        try:
            # Get sample records
            query_params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": "5",
                "f": "json"
            }
            
            response = self.session.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                print(f"        ❌ Sample query failed: {result['error']}")
                return
            
            features = result.get('features', [])
            if not features:
                print("        No sample data available")
                return
            
            print(f"        Found {len(features)} sample records")
            
            # Analyze data patterns
            self.analyze_data_patterns(features)
            
            # Show detailed sample record
            if features:
                print(f"        📋 Sample record details:")
                sample_record = features[0].get('attributes', {})
                
                # Show key fields
                key_fields = ['pollutant_name', 'area_name', 'state_name', 'current_status', 
                             'classification', 'design_value', 'dv_units', 'meets_naaqs']
                
                for field in key_fields:
                    value = sample_record.get(field, 'N/A')
                    if value and str(value).strip():
                        print(f"          {field}: {value}")
                    
        except Exception as e:
            print(f"        ❌ Error getting sample data: {e}")
    
    def analyze_data_patterns(self, features: List[Dict]):
        """Analyze patterns in the sample data"""
        if not features:
            return
        
        print(f"        🔍 Data pattern analysis:")
        
        # Analyze pollutant types
        pollutants = set()
        statuses = set()
        states = set()
        
        for feature in features:
            attrs = feature.get('attributes', {})
            
            pollutant = attrs.get('pollutant_name')
            if pollutant:
                pollutants.add(pollutant)
            
            status = attrs.get('current_status')
            if status:
                statuses.add(status)
            
            state = attrs.get('state_name')
            if state:
                states.add(state)
        
        if pollutants:
            print(f"          Pollutants: {', '.join(list(pollutants)[:3])}")
        if statuses:
            print(f"          Statuses: {', '.join(list(statuses)[:3])}")
        if states:
            print(f"          States: {', '.join(list(states)[:3])}")
    
    def generate_implementation_summary(self):
        """Generate a comprehensive implementation summary"""
        print(f"\n📋 EPA SERVICE IMPLEMENTATION SUMMARY")
        print("="*80)
        
        print("🎯 PRIMARY SERVICE RECOMMENDATION:")
        print("   Service: https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer")
        print("   Authority: EPA Office of Air and Radiation (OAR)")
        print("   Division: Office of Air Quality Planning and Standards (OAQPS)")
        print("   Coverage: All criteria pollutants with current and historical data")
        
        print("\n🗂️ LAYER STRUCTURE (12 layers total):")
        layer_structure = [
            ("0", "Ozone 8-hr (1997 standard)", "REVOKED", "Historical data"),
            ("1", "Ozone 8-hr (2008 standard)", "ACTIVE", "Current standard"),
            ("2", "Ozone 8-hr (2015 Standard)", "ACTIVE", "Current standard"),
            ("3", "Lead (2008 standard)", "ACTIVE", "Current standard"),
            ("4", "SO2 1-hr (2010 standard)", "ACTIVE", "Current standard"),
            ("5", "PM2.5 24hr (2006 standard)", "ACTIVE", "Current standard"),
            ("6", "PM2.5 Annual (1997 standard)", "ACTIVE", "Current standard"),
            ("7", "PM2.5 Annual (2012 standard)", "ACTIVE", "Current standard"),
            ("8", "PM10 (1987 standard)", "ACTIVE", "Current standard"),
            ("9", "CO (1971 Standard)", "ACTIVE", "Current standard"),
            ("10", "Ozone 1-hr (1979 standard-revoked)", "REVOKED", "Historical data"),
            ("11", "NO2 (1971 Standard)", "ACTIVE", "Current standard")
        ]
        
        for layer_id, name, status, note in layer_structure:
            status_icon = "🟢" if status == "ACTIVE" else "🔴"
            print(f"   {status_icon} Layer {layer_id}: {name} ({status})")
        
        print("\n🔧 KEY IMPLEMENTATION FIELDS:")
        key_fields = [
            ("pollutant_name", "String", "Pollutant type (e.g., 'PM-2.5 (2012 Standard)')"),
            ("area_name", "String", "Nonattainment area name"),
            ("state_name", "String", "State name"),
            ("state_abbreviation", "String", "State abbreviation"),
            ("current_status", "String", "Nonattainment, Maintenance, etc."),
            ("classification", "String", "Marginal, Moderate, Serious, Severe, Extreme"),
            ("design_value", "Float", "Current air quality measurement"),
            ("dv_units", "String", "Design value units (µg/m³, ppm, ppb)"),
            ("meets_naaqs", "String", "Yes/No - meets National Ambient Air Quality Standards"),
            ("epa_region", "Integer", "EPA region number (1-10)"),
            ("population_2020", "Double", "2020 population in area")
        ]
        
        for field, ftype, description in key_fields:
            print(f"   • {field} ({ftype}): {description}")
        
        print("\n📊 QUERY CAPABILITIES:")
        print("   ✅ Spatial intersection queries (point, polygon, buffer)")
        print("   ✅ Attribute filtering by pollutant, state, status")
        print("   ✅ Geometry return for mapping applications")
        print("   ✅ Statistical queries and aggregation")
        print("   ✅ Export capabilities (JSON, GeoJSON, KML)")
        
        print("\n🎨 RECOMMENDED CLIENT ARCHITECTURE:")
        print("   1. NonAttainmentAreasClient class")
        print("   2. Layer-specific query methods")
        print("   3. Pollutant-specific analysis functions")
        print("   4. Status classification utilities")
        print("   5. Geographic aggregation capabilities")
        
        print("\n⚡ PERFORMANCE CONSIDERATIONS:")
        print("   • Max record count: 2000 per query")
        print("   • Use spatial indexing for large area queries")
        print("   • Cache frequently accessed data")
        print("   • Implement pagination for large result sets")
        print("   • Consider layer-specific queries for better performance")

def main():
    """Main analysis function"""
    print("🌫️ EPA Service Detailed Analysis for NonAttainment Areas")
    print("="*80)
    
    analyzer = EPAServiceAnalyzer()
    analyzer.analyze_all_services()
    analyzer.generate_implementation_summary()
    
    print(f"\n✅ DETAILED ANALYSIS COMPLETE")
    print(f"="*80)
    print(f"💡 Ready to implement NonAttainmentINFO client with comprehensive understanding")

if __name__ == "__main__":
    main() 