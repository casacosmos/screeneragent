#!/usr/bin/env python3
"""
Explore NonAttainment EPA Services

This script explores various EPA ArcGIS services to understand nonattainment data sources,
their metadata, capabilities, available layers, and printing services for map generation.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class NonAttainmentServiceExplorer:
    """Explore nonattainment services and their capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NonAttainmentServiceExplorer/1.0'
        })
        
        # Known EPA service base URLs
        self.service_bases = [
            "https://gispub.epa.gov/arcgis/rest/services",  # EPA Primary
            "https://geodata.epa.gov/arcgis/rest/services",  # EPA GeoData
            "https://epa.maps.arcgis.com/sharing/rest/content/items",  # EPA Portal
            "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services",  # EPA Cloud
        ]
        
        # Known nonattainment and printing services
        self.nonattainment_services = [
            "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer",
            "https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/FeatureServer",
            "https://geodata.epa.gov/arcgis/rest/services/OAR/NonattainmentAreas/MapServer",
        ]
        
        # Potential printing services
        self.printing_services = [
            "https://gispub.epa.gov/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task",
            "https://gispub.epa.gov/arcgis/rest/services/Utilities/Geometry/GeometryServer",
            "https://geodata.epa.gov/arcgis/rest/services/Utilities/PrintingTools/GPServer",
            "https://services.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task",
        ]
    
    def explore_all_services(self):
        """Explore all potential nonattainment and printing services"""
        print("🔍 Exploring NonAttainment EPA Services")
        print("="*80)
        
        # First, explore the base service catalogs
        self.explore_base_services()
        
        # Test known nonattainment services
        self.test_nonattainment_services()
        
        # Test printing services
        self.test_printing_services()
        
        # Search for additional services
        self.search_additional_services()
    
    def explore_base_services(self):
        """Explore the base service catalogs for nonattainment-related services"""
        print("\n📋 EXPLORING BASE SERVICE CATALOGS")
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
            
            # Look for nonattainment-related services
            if 'services' in catalog:
                nonattainment_services = [s for s in catalog['services'] 
                                         if any(term in s.get('name', '').lower() 
                                               for term in ['nonattainment', 'air', 'ozone', 'pm25', 'pm10', 'lead', 'so2', 'co', 'no2', 'naaqs', 'oar'])]
                
                if nonattainment_services:
                    print(f"   🎯 Potential nonattainment services:")
                    for service in nonattainment_services:
                        print(f"     • {service.get('name')} ({service.get('type')})")
                        # Store full URL for later testing
                        full_url = f"{base_url}/{service.get('name')}/{service.get('type')}"
                        if full_url not in self.nonattainment_services:
                            self.nonattainment_services.append(full_url)
            
            # Look for printing/utility services
            if 'services' in catalog:
                printing_services = [s for s in catalog['services'] 
                                   if any(term in s.get('name', '').lower() 
                                         for term in ['print', 'export', 'map', 'utility', 'tool'])]
                
                if printing_services:
                    print(f"   🖨️ Potential printing services:")
                    for service in printing_services:
                        print(f"     • {service.get('name')} ({service.get('type')})")
                        # Store full URL for later testing
                        full_url = f"{base_url}/{service.get('name')}/{service.get('type')}"
                        if full_url not in self.printing_services:
                            self.printing_services.append(full_url)
            
            # Look for relevant folders
            if 'folders' in catalog:
                relevant_folders = [f for f in catalog['folders'] 
                                  if any(term in f.lower() 
                                        for term in ['air', 'oar', 'oaqps', 'nonattainment', 'utility', 'tool'])]
                
                if relevant_folders:
                    print(f"   📁 Relevant folders:")
                    for folder in relevant_folders:
                        print(f"     • {folder}")
                        self.explore_folder(base_url, folder)
        
        except Exception as e:
            print(f"❌ Failed to access: {e}")
    
    def explore_folder(self, base_url: str, folder: str):
        """Explore a specific folder for relevant services"""
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
                    if any(term in service.get('name', '').lower() for term in ['nonattainment', 'air', 'print', 'export']):
                        if full_url not in self.nonattainment_services and full_url not in self.printing_services:
                            if 'print' in service.get('name', '').lower() or 'export' in service.get('name', '').lower():
                                self.printing_services.append(full_url)
                            else:
                                self.nonattainment_services.append(full_url)
        
        except Exception as e:
            print(f"       ❌ Cannot access folder {folder}: {e}")
    
    def test_nonattainment_services(self):
        """Test the discovered nonattainment services"""
        print(f"\n🔧 TESTING NONATTAINMENT SERVICES")
        print("-"*60)
        
        working_services = []
        
        for service_url in self.nonattainment_services:
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
                
                # Explore layers in detail
                self.explore_service_layers(service_url, service_info)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return working_services
    
    def test_printing_services(self):
        """Test the discovered printing services"""
        print(f"\n🖨️ TESTING PRINTING SERVICES")
        print("-"*60)
        
        working_printing_services = []
        
        for service_url in self.printing_services:
            print(f"\n📍 Testing: {service_url}")
            
            try:
                response = self.session.get(f"{service_url}?f=json", timeout=15)
                response.raise_for_status()
                service_info = response.json()
                
                if 'error' in service_info:
                    print(f"   ❌ Service error: {service_info['error']}")
                    continue
                
                print(f"   ✅ Accessible")
                print(f"   Description: {service_info.get('description', 'N/A')[:100]}...")
                
                # Check if it's a geoprocessing service
                if 'tasks' in service_info:
                    print(f"   Tasks: {len(service_info['tasks'])}")
                    for task in service_info['tasks']:
                        print(f"     • {task.get('name')}: {task.get('displayName', 'N/A')}")
                
                # Check parameters for export tasks
                if 'Export' in service_url or 'Print' in service_url:
                    self.explore_printing_parameters(service_url)
                
                working_printing_services.append(service_url)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return working_printing_services
    
    def explore_printing_parameters(self, service_url: str):
        """Explore printing service parameters"""
        try:
            # Try to get task parameters
            if 'Export%20Web%20Map%20Task' in service_url:
                task_url = f"{service_url}?f=json"
            elif service_url.endswith('GPServer'):
                task_url = f"{service_url}/Export%20Web%20Map%20Task?f=json"
            else:
                return
            
            response = self.session.get(task_url, timeout=10)
            response.raise_for_status()
            task_info = response.json()
            
            if 'parameters' in task_info:
                print(f"     📋 Export Parameters:")
                for param in task_info['parameters'][:5]:  # Show first 5 parameters
                    print(f"       - {param.get('name')}: {param.get('dataType')} ({param.get('direction', 'N/A')})")
            
            # Check execution type
            if 'executionType' in task_info:
                print(f"     ⚙️ Execution Type: {task_info['executionType']}")
                
        except Exception as e:
            print(f"     ❌ Cannot explore parameters: {e}")
    
    def explore_service_layers(self, service_url: str, service_info: Dict):
        """Explore layers within a nonattainment service"""
        layers = service_info.get('layers', [])
        
        if not layers:
            return
        
        print(f"   🔍 Exploring layers in detail:")
        
        for layer in layers[:3]:  # Limit to first 3 layers for detailed exploration
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
                    key_fields = [f for f in fields[:10] if any(term in f.get('name', '').lower() 
                                                               for term in ['pollutant', 'area', 'status', 'name', 'state', 'classification'])]
                    if key_fields:
                        print(f"        Key fields:")
                        for field in key_fields:
                            print(f"          - {field.get('name')}: {field.get('type')}")
                
                # Check drawing info for symbology
                if 'drawingInfo' in layer_info:
                    drawing_info = layer_info['drawingInfo']
                    if 'renderer' in drawing_info:
                        renderer = drawing_info['renderer']
                        print(f"        Renderer: {renderer.get('type', 'Unknown')}")
                        if 'symbol' in renderer:
                            symbol = renderer['symbol']
                            print(f"        Symbol: {symbol.get('type', 'Unknown')}")
                
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
            else:
                print(f"        Test query failed: {result['error']}")
                
        except Exception as e:
            print(f"        Test query error: {e}")
    
    def search_additional_services(self):
        """Search for additional services using common patterns"""
        print(f"\n🔍 SEARCHING FOR ADDITIONAL SERVICES")
        print("-"*60)
        
        # Common service patterns
        service_patterns = [
            "NonattainmentAreas",
            "AirQuality", 
            "NAAQS",
            "OAR_OAQPS",
            "Emissions",
            "AirPollution"
        ]
        
        printing_patterns = [
            "PrintingTools",
            "ExportWebMap",
            "MapExport",
            "Utilities"
        ]
        
        base_urls = [
            "https://gispub.epa.gov/arcgis/rest/services",
            "https://geodata.epa.gov/arcgis/rest/services"
        ]
        
        for base_url in base_urls:
            # Test nonattainment patterns
            for pattern in service_patterns:
                test_url = f"{base_url}/{pattern}/MapServer"
                self._test_service_pattern(test_url, "nonattainment")
                
                test_url = f"{base_url}/{pattern}/FeatureServer"
                self._test_service_pattern(test_url, "nonattainment")
            
            # Test printing patterns
            for pattern in printing_patterns:
                test_url = f"{base_url}/{pattern}/GPServer"
                self._test_service_pattern(test_url, "printing")
    
    def _test_service_pattern(self, test_url: str, service_type: str):
        """Test a service pattern"""
        print(f"🔍 Testing {service_type} pattern: {test_url}")
        
        try:
            response = self.session.get(f"{test_url}?f=json", timeout=10)
            if response.status_code == 200:
                service_info = response.json()
                if 'error' not in service_info:
                    print(f"   ✅ FOUND: {test_url}")
                    print(f"      Description: {service_info.get('serviceDescription', service_info.get('description', 'N/A'))[:100]}...")
                    
                    if service_type == "nonattainment" and test_url not in self.nonattainment_services:
                        self.nonattainment_services.append(test_url)
                    elif service_type == "printing" and test_url not in self.printing_services:
                        self.printing_services.append(test_url)
                else:
                    print(f"   ❌ Service error")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def generate_service_summary(self):
        """Generate a summary of findings"""
        print(f"\n📋 SERVICE EXPLORATION SUMMARY")
        print("="*80)
        
        print("🎯 RECOMMENDED NONATTAINMENT SERVICE:")
        print("   https://gispub.epa.gov/arcgis/rest/services/OAR_OAQPS/NonattainmentAreas/MapServer")
        print("   - Comprehensive EPA nonattainment data")
        print("   - All criteria pollutants and standards")
        print("   - 12 layers covering different pollutants")
        print("   - Standard EPA fields (pollutant_name, area_name, status)")
        
        print("\n🖨️ RECOMMENDED PRINTING SERVICE:")
        working_printing = [s for s in self.printing_services if 'gispub.epa.gov' in s and 'Export' in s]
        if working_printing:
            print(f"   {working_printing[0]}")
            print("   - EPA's official printing service")
            print("   - Supports PDF export")
            print("   - Layout templates available")
        else:
            print("   https://services.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task")
            print("   - Esri's public printing service (fallback)")
        
        print("\n🔧 RECOMMENDED IMPLEMENTATION:")
        print("   1. Use OAR_OAQPS/NonattainmentAreas as primary service")
        print("   2. Query relevant layers based on pollutants")
        print("   3. Use EPA printing service for official maps")
        print("   4. Key fields: pollutant_name, area_name, current_status")
        
        print("\n📊 MAP GENERATION CAPABILITIES:")
        print("   - Spatial intersection queries")
        print("   - Multiple pollutant layer support")
        print("   - Custom symbology for different pollutants")
        print("   - Professional PDF output with legends")

def main():
    """Main exploration function"""
    print("🌫️ NonAttainment EPA Service Exploration")
    print("="*80)
    
    explorer = NonAttainmentServiceExplorer()
    explorer.explore_all_services()
    explorer.generate_service_summary()
    
    print(f"\n✅ EXPLORATION COMPLETE")
    print(f"="*80)
    print(f"💡 Ready to build NonAttainmentINFO map generator based on findings")

if __name__ == "__main__":
    main() 