#!/usr/bin/env python3
"""
Explore EPA Services for NonAttainment Areas

This script explores various EPA ArcGIS services to understand nonattainment data sources,
their metadata, capabilities, and available layers for air quality analysis.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class EPAServiceExplorer:
    """Explore EPA services and their capabilities for nonattainment areas"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EPAServiceExplorer/1.0'
        })
        
        # Known EPA service base URLs
        self.service_bases = [
            "https://gispub.epa.gov/arcgis/rest/services",  # EPA GIS Public
            "https://geodata.epa.gov/arcgis/rest/services",  # EPA Geodata
            "https://epa.maps.arcgis.com/sharing/rest/content/items",  # EPA ArcGIS Online
            "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services",  # EPA Portal
        ]
        
        # Known nonattainment and air quality services
        self.air_quality_services = [
            "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer",
            "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS",  # Folder
            "https://geodata.epa.gov/arcgis/rest/services/OAR/NonAttainmentAreas/MapServer",
            "https://gispub.epa.gov/arcgis/rest/services/Air/MapServer",
            "https://gispub.epa.gov/arcgis/rest/services/AirQuality/MapServer",
        ]
        
        # Test coordinates for queries
        self.test_coords = [
            {"name": "Los Angeles, CA", "x": -118.2437, "y": 34.0522},
            {"name": "Houston, TX", "x": -95.3698, "y": 29.7604},
            {"name": "Phoenix, AZ", "x": -112.0740, "y": 33.4484}
        ]
    
    def explore_all_services(self):
        """Explore all EPA services for nonattainment data"""
        print("🔍 EXPLORING EPA SERVICES FOR NONATTAINMENT AREAS")
        print("="*80)
        
        # First, explore the base service catalogs
        self.explore_base_services()
        
        # Test known air quality services
        self.test_air_quality_services()
        
        # Search for additional air quality services
        self.search_air_quality_services()
        
        # Focus on the primary nonattainment service
        self.analyze_primary_nonattainment_service()
    
    def explore_base_services(self):
        """Explore the base EPA service catalogs"""
        print("\n📋 EXPLORING BASE EPA SERVICE CATALOGS")
        print("-"*60)
        
        for base_url in self.service_bases:
            self.explore_service_catalog(base_url)
    
    def explore_service_catalog(self, base_url: str):
        """Explore a service catalog"""
        print(f"\n🌐 Exploring: {base_url}")
        
        try:
            response = self.session.get(f"{base_url}?f=json", timeout=15)
            response.raise_for_status()
            catalog = response.json()
            
            print(f"✅ Accessible")
            print(f"   Services: {len(catalog.get('services', []))}")
            print(f"   Folders: {len(catalog.get('folders', []))}")
            
            # Look for air quality related services
            if 'services' in catalog:
                air_services = [s for s in catalog['services'] 
                               if any(term in s.get('name', '').lower() 
                                     for term in ['air', 'ozone', 'nonattain', 'naaqs', 'oar', 'oaqps', 'pm', 'pollut'])]
                
                if air_services:
                    print(f"   🎯 Potential air quality services:")
                    for service in air_services:
                        print(f"     • {service.get('name')} ({service.get('type')})")
                        # Store full URL for later testing
                        full_url = f"{base_url}/{service.get('name')}/{service.get('type')}"
                        if full_url not in self.air_quality_services:
                            self.air_quality_services.append(full_url)
            
            # Look for air quality folders
            if 'folders' in catalog:
                air_folders = [f for f in catalog['folders'] 
                              if any(term in f.lower() 
                                    for term in ['air', 'ozone', 'nonattain', 'naaqs', 'oar', 'oaqps', 'pm', 'pollut'])]
                
                if air_folders:
                    print(f"   📁 Potential air quality folders:")
                    for folder in air_folders:
                        print(f"     • {folder}")
                        self.explore_folder(base_url, folder)
        
        except Exception as e:
            print(f"❌ Failed to access: {e}")
    
    def explore_folder(self, base_url: str, folder: str):
        """Explore a specific folder for air quality services"""
        try:
            response = self.session.get(f"{base_url}/{folder}?f=json", timeout=15)
            response.raise_for_status()
            folder_info = response.json()
            
            if 'services' in folder_info:
                print(f"       Services in {folder}:")
                for service in folder_info['services'][:10]:  # Limit to first 10
                    print(f"         - {service.get('name')} ({service.get('type')})")
                    # Store full URL for later testing
                    full_url = f"{base_url}/{folder}/{service.get('name')}/{service.get('type')}"
                    if full_url not in self.air_quality_services:
                        self.air_quality_services.append(full_url)
        
        except Exception as e:
            print(f"       ❌ Cannot access folder {folder}: {e}")
    
    def test_air_quality_services(self):
        """Test the discovered air quality services"""
        print(f"\n🔧 TESTING AIR QUALITY SERVICES")
        print("-"*60)
        
        working_services = []
        
        for service_url in self.air_quality_services:
            print(f"\n📍 Testing: {service_url}")
            
            try:
                response = self.session.get(f"{service_url}?f=json", timeout=15)
                response.raise_for_status()
                service_info = response.json()
                
                if 'error' in service_info:
                    print(f"   ❌ Service error: {service_info['error']}")
                    continue
                
                print(f"   ✅ Accessible")
                print(f"   Description: {service_info.get('serviceDescription', 'N/A')[:100]}...")
                
                # Check layers
                layers = service_info.get('layers', [])
                if layers:
                    print(f"   Layers: {len(layers)}")
                    for layer in layers[:5]:  # Show first 5 layers
                        print(f"     • Layer {layer.get('id')}: {layer.get('name')}")
                
                # Check capabilities
                if 'capabilities' in service_info:
                    capabilities = service_info['capabilities'].split(',')
                    print(f"   Capabilities: {', '.join(capabilities)}")
                
                working_services.append(service_url)
                
                # Explore layers in detail if this looks like a nonattainment service
                if any(term in service_url.lower() for term in ['nonattain', 'oar_oaqps']):
                    self.explore_service_layers(service_url, service_info)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return working_services
    
    def explore_service_layers(self, service_url: str, service_info: Dict):
        """Explore layers within an air quality service"""
        layers = service_info.get('layers', [])
        
        if not layers:
            return
        
        print(f"   🔍 Exploring layers in detail:")
        
        for layer in layers:  # Explore all layers for nonattainment services
            layer_id = layer.get('id')
            layer_name = layer.get('name', 'Unknown')
            
            try:
                layer_response = self.session.get(f"{service_url}/{layer_id}?f=json", timeout=10)
                layer_response.raise_for_status()
                layer_info = layer_response.json()
                
                print(f"     📋 Layer {layer_id}: {layer_name}")
                print(f"        Type: {layer_info.get('type', 'Unknown')}")
                print(f"        Geometry: {layer_info.get('geometryType', 'Unknown')}")
                print(f"        Min Scale: {layer_info.get('minScale', 'N/A')}")
                print(f"        Max Scale: {layer_info.get('maxScale', 'N/A')}")
                
                # Check fields
                fields = layer_info.get('fields', [])
                if fields:
                    key_fields = [f for f in fields[:15] if any(term in f.get('name', '').lower() 
                                                               for term in ['pollutant', 'area', 'status', 'name', 'state', 'classification', 'design'])]
                    if key_fields:
                        print(f"        Key fields:")
                        for field in key_fields:
                            print(f"          - {field.get('name')}: {field.get('type')}")
                
                # Test a simple query
                self.test_layer_query(service_url, layer_id, layer_name)
                
            except Exception as e:
                print(f"     ❌ Cannot explore layer {layer_id}: {e}")
    
    def test_layer_query(self, service_url: str, layer_id: int, layer_name: str):
        """Test a simple query on a layer"""
        try:
            # Test with Los Angeles coordinates (known nonattainment area)
            test_point = {"x": -118.2437, "y": 34.0522, "spatialReference": {"wkid": 4326}}
            
            query_params = {
                "geometry": json.dumps(test_point),
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
                print(f"        Test query (LA): {count} features found")
                
                # If features found, get sample data
                if count > 0:
                    self.get_sample_data(service_url, layer_id)
            else:
                print(f"        Test query failed: {result['error']}")
                
        except Exception as e:
            print(f"        Test query error: {e}")
    
    def get_sample_data(self, service_url: str, layer_id: int):
        """Get sample data from a layer"""
        try:
            query_params = {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": "2",
                "f": "json"
            }
            
            response = self.session.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                return
            
            features = result.get('features', [])
            if features:
                print(f"        Sample data:")
                for i, feature in enumerate(features[:1]):  # Show first record
                    attributes = feature.get('attributes', {})
                    key_attrs = {}
                    for key, value in attributes.items():
                        if any(term in key.lower() for term in ['pollutant', 'area', 'status', 'name', 'state', 'classification']):
                            if value and str(value).strip():
                                key_attrs[key] = value
                    
                    for key, value in list(key_attrs.items())[:4]:  # Show first 4 key attributes
                        print(f"          {key}: {value}")
                        
        except Exception as e:
            print(f"        Sample data error: {e}")
    
    def search_air_quality_services(self):
        """Search for additional air quality services using common patterns"""
        print(f"\n🔍 SEARCHING FOR ADDITIONAL AIR QUALITY SERVICES")
        print("-"*60)
        
        # Common air quality service patterns
        service_patterns = [
            "NonAttainmentAreas",
            "AirQuality",
            "NAAQS",
            "Ozone",
            "PM25",
            "PM10",
            "AirPollution",
            "EmissionsInventory"
        ]
        
        base_urls = [
            "https://gispub.epa.gov/arcgis/rest/services",
            "https://geodata.epa.gov/arcgis/rest/services",
            "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS"
        ]
        
        for base_url in base_urls:
            for pattern in service_patterns:
                test_url = f"{base_url}/{pattern}/MapServer"
                print(f"🔍 Testing pattern: {test_url}")
                
                try:
                    response = self.session.get(f"{test_url}?f=json", timeout=10)
                    if response.status_code == 200:
                        service_info = response.json()
                        if 'error' not in service_info:
                            print(f"   ✅ FOUND: {test_url}")
                            print(f"      Description: {service_info.get('serviceDescription', 'N/A')[:100]}...")
                            if test_url not in self.air_quality_services:
                                self.air_quality_services.append(test_url)
                        else:
                            print(f"   ❌ Service error")
                    else:
                        print(f"   ❌ HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    def analyze_primary_nonattainment_service(self):
        """Detailed analysis of the primary EPA nonattainment service"""
        print(f"\n🎯 DETAILED ANALYSIS: PRIMARY NONATTAINMENT SERVICE")
        print("-"*60)
        
        primary_service = "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer"
        
        try:
            response = self.session.get(f"{primary_service}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            print(f"Service: {primary_service}")
            print(f"Description: {service_info.get('serviceDescription', 'N/A')}")
            print(f"Capabilities: {service_info.get('capabilities', 'N/A')}")
            print(f"Max Record Count: {service_info.get('maxRecordCount', 'N/A')}")
            print(f"Supported Query Formats: {service_info.get('supportedQueryFormats', 'N/A')}")
            
            layers = service_info.get('layers', [])
            print(f"\nTotal Layers: {len(layers)}")
            
            # Analyze each layer in detail
            for layer in layers:
                self.analyze_nonattainment_layer(primary_service, layer)
                
        except Exception as e:
            print(f"❌ Error analyzing primary service: {e}")
    
    def analyze_nonattainment_layer(self, service_url: str, layer: Dict):
        """Detailed analysis of a nonattainment layer"""
        layer_id = layer.get('id')
        layer_name = layer.get('name', 'Unknown')
        
        print(f"\n  🔬 LAYER {layer_id}: {layer_name}")
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
            print(f"    Default Visibility: {layer_info.get('defaultVisibility', 'N/A')}")
            
            # Analyze fields in detail
            self.analyze_layer_fields(layer_info)
            
            # Test queries with different locations
            self.test_comprehensive_queries(service_url, layer_id, layer_name)
            
            # Get comprehensive sample data
            self.get_comprehensive_sample_data(service_url, layer_id, layer_name)
            
        except Exception as e:
            print(f"    ❌ Error analyzing layer: {e}")
    
    def analyze_layer_fields(self, layer_info: Dict):
        """Comprehensive analysis of layer fields"""
        fields = layer_info.get('fields', [])
        
        if not fields:
            print("    No fields found")
            return
        
        print(f"    Fields ({len(fields)} total):")
        
        # Categorize fields
        pollutant_fields = []
        location_fields = []
        status_fields = []
        date_fields = []
        measurement_fields = []
        id_fields = []
        other_fields = []
        
        for field in fields:
            field_name = field.get('name', '').lower()
            field_type = field.get('type', '')
            field_alias = field.get('alias', field.get('name', ''))
            
            if any(term in field_name for term in ['pollutant', 'pol_', 'chemical']):
                pollutant_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['area', 'state', 'county', 'region', 'location', 'city']):
                location_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['status', 'classification', 'attainment', 'maintenance']):
                status_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['date', 'effective', 'designation', 'statutory']):
                date_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['design_value', 'dv_', 'concentration', 'level', 'population']):
                measurement_fields.append((field.get('name'), field_type, field_alias))
            elif any(term in field_name for term in ['id', 'objectid', 'fid', 'composite']):
                id_fields.append((field.get('name'), field_type, field_alias))
            else:
                other_fields.append((field.get('name'), field_type, field_alias))
        
        # Display categorized fields
        if pollutant_fields:
            print("      🌫️ Pollutant Fields:")
            for name, ftype, alias in pollutant_fields:
                print(f"        • {name} ({ftype}): {alias}")
        
        if location_fields:
            print("      📍 Location Fields:")
            for name, ftype, alias in location_fields:
                print(f"        • {name} ({ftype}): {alias}")
        
        if status_fields:
            print("      📊 Status Fields:")
            for name, ftype, alias in status_fields:
                print(f"        • {name} ({ftype}): {alias}")
        
        if date_fields:
            print("      📅 Date Fields:")
            for name, ftype, alias in date_fields:
                print(f"        • {name} ({ftype}): {alias}")
        
        if measurement_fields:
            print("      📏 Measurement Fields:")
            for name, ftype, alias in measurement_fields:
                print(f"        • {name} ({ftype}): {alias}")
        
        if other_fields:
            print(f"      📋 Other Fields ({len(other_fields)} total):")
            for name, ftype, alias in other_fields[:5]:
                print(f"        • {name} ({ftype}): {alias}")
            if len(other_fields) > 5:
                print(f"        ... and {len(other_fields) - 5} more")
    
    def test_comprehensive_queries(self, service_url: str, layer_id: int, layer_name: str):
        """Test comprehensive queries on different locations"""
        print("    🧪 Testing queries:")
        
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
                    print(f"      {location['name']}: {count} features")
                else:
                    print(f"      {location['name']}: Query failed")
                    
            except Exception as e:
                print(f"      {location['name']}: Error - {e}")
    
    def get_comprehensive_sample_data(self, service_url: str, layer_id: int, layer_name: str):
        """Get comprehensive sample data from the layer"""
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
                
                # Show all non-null attributes
                for key, value in attributes.items():
                    if value is not None and str(value).strip():
                        print(f"          {key}: {value}")
                print()
                    
        except Exception as e:
            print(f"      ❌ Error getting sample data: {e}")
    
    def generate_service_summary(self):
        """Generate a comprehensive summary of findings"""
        print(f"\n📋 EPA SERVICE EXPLORATION SUMMARY")
        print("="*80)
        
        print("🎯 PRIMARY NONATTAINMENT SERVICE:")
        print("   https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer")
        print("   - Official EPA Office of Air and Radiation (OAR) service")
        print("   - Office of Air Quality Planning and Standards (OAQPS)")
        print("   - Comprehensive nonattainment area data for all criteria pollutants")
        print("   - Multiple layers for different pollutants and standards")
        
        print("\n🔧 RECOMMENDED IMPLEMENTATION:")
        print("   1. Use OAR_OAQPS/NonattainmentAreas as primary service")
        print("   2. Query specific layers based on pollutant of interest")
        print("   3. Include both active and revoked standards for comprehensive analysis")
        print("   4. Key fields: pollutant_name, area_name, state_name, current_status")
        
        print("\n📊 LAYER STRUCTURE:")
        print("   - Layer 0: Ozone 8-hr (1997 standard) - REVOKED")
        print("   - Layer 1: Ozone 8-hr (2008 standard) - ACTIVE")
        print("   - Layer 2: Ozone 8-hr (2015 Standard) - ACTIVE")
        print("   - Layer 3: Lead (2008 standard) - ACTIVE")
        print("   - Layer 4: SO2 1-hr (2010 standard) - ACTIVE")
        print("   - Layer 5: PM2.5 24hr (2006 standard) - ACTIVE")
        print("   - Layer 6: PM2.5 Annual (1997 standard) - ACTIVE")
        print("   - Layer 7: PM2.5 Annual (2012 standard) - ACTIVE")
        print("   - Layer 8: PM10 (1987 standard) - ACTIVE")
        print("   - Layer 9: CO (1971 Standard) - ACTIVE")
        print("   - Layer 10: Ozone 1-hr (1979 standard-revoked) - REVOKED")
        print("   - Layer 11: NO2 (1971 Standard) - ACTIVE")
        
        print("\n📊 QUERY CAPABILITIES:")
        print("   - Spatial intersection queries")
        print("   - Attribute filtering by pollutant, state, status")
        print("   - Geometry return for mapping")
        print("   - Statistical queries for analysis")

def main():
    """Main exploration function"""
    print("🌫️ EPA Service Explorer for NonAttainment Areas")
    print("="*80)
    
    explorer = EPAServiceExplorer()
    explorer.explore_all_services()
    explorer.generate_service_summary()
    
    print(f"\n✅ EXPLORATION COMPLETE")
    print(f"="*80)
    print(f"💡 Ready to build NonAttainmentINFO client based on findings")

if __name__ == "__main__":
    main() 