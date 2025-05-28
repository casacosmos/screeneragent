#!/usr/bin/env python3
"""
Explore Critical Habitat Services

This script explores various ArcGIS services to understand critical habitat data sources,
their metadata, capabilities, and available layers for habitat analysis.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class HabitatServiceExplorer:
    """Explore critical habitat services and their capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HabitatServiceExplorer/1.0'
        })
        
        # Known critical habitat service base URLs
        self.service_bases = [
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services",  # USFWS
            "https://fwsprimary.wim.usgs.gov/server/rest/services",  # USFWS WIM
            "https://gis.fws.gov/arcgis/rest/services",  # USFWS GIS
            "https://ecos.fws.gov/arcgis/rest/services",  # ECOS
            "https://services1.arcgis.com/6677msI40mnLuuLr/arcgis/rest/services",  # NOAA
            "https://geopub.epa.gov/arcgis/rest/services",  # EPA
        ]
        
        # Potential critical habitat services
        self.habitat_services = [
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWS_Critical_Habitat/MapServer",
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/CRITHAB_POLY/MapServer",
            "https://fwsprimary.wim.usgs.gov/server/rest/services/Critical_Habitat/MapServer",
            "https://gis.fws.gov/arcgis/rest/services/FWS_Critical_Habitat/MapServer",
            "https://ecos.fws.gov/arcgis/rest/services/Species/MapServer",
        ]
    
    def explore_all_services(self):
        """Explore all potential habitat services"""
        print("🔍 Exploring Critical Habitat Services")
        print("="*80)
        
        # First, explore the base service catalogs
        self.explore_base_services()
        
        # Test known habitat services
        self.test_habitat_services()
        
        # Search for additional habitat-related services
        self.search_habitat_services()
    
    def explore_base_services(self):
        """Explore the base service catalogs for habitat-related services"""
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
            
            # Look for habitat-related services
            if 'services' in catalog:
                habitat_services = [s for s in catalog['services'] 
                                   if any(term in s.get('name', '').lower() 
                                         for term in ['habitat', 'critical', 'species', 'endangered', 'threatened', 'ecos'])]
                
                if habitat_services:
                    print(f"   🎯 Potential habitat services:")
                    for service in habitat_services:
                        print(f"     • {service.get('name')} ({service.get('type')})")
                        # Store full URL for later testing
                        full_url = f"{base_url}/{service.get('name')}/{service.get('type')}"
                        if full_url not in self.habitat_services:
                            self.habitat_services.append(full_url)
            
            # Look for habitat folders
            if 'folders' in catalog:
                habitat_folders = [f for f in catalog['folders'] 
                                 if any(term in f.lower() 
                                       for term in ['habitat', 'critical', 'species', 'endangered', 'threatened', 'ecos'])]
                
                if habitat_folders:
                    print(f"   📁 Potential habitat folders:")
                    for folder in habitat_folders:
                        print(f"     • {folder}")
                        self.explore_folder(base_url, folder)
        
        except Exception as e:
            print(f"❌ Failed to access: {e}")
    
    def explore_folder(self, base_url: str, folder: str):
        """Explore a specific folder for habitat services"""
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
                    if full_url not in self.habitat_services:
                        self.habitat_services.append(full_url)
        
        except Exception as e:
            print(f"       ❌ Cannot access folder {folder}: {e}")
    
    def test_habitat_services(self):
        """Test the discovered habitat services"""
        print(f"\n🔧 TESTING HABITAT SERVICES")
        print("-"*60)
        
        working_services = []
        
        for service_url in self.habitat_services:
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
    
    def explore_service_layers(self, service_url: str, service_info: Dict):
        """Explore layers within a habitat service"""
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
                
                # Check fields
                fields = layer_info.get('fields', [])
                if fields:
                    key_fields = [f for f in fields[:10] if any(term in f.get('name', '').lower() 
                                                               for term in ['species', 'habitat', 'critical', 'status', 'name', 'type'])]
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
            # Test with Puerto Rico coordinates
            test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
            
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
                print(f"        Test query: {count} features found at test location")
            else:
                print(f"        Test query failed: {result['error']}")
                
        except Exception as e:
            print(f"        Test query error: {e}")
    
    def search_habitat_services(self):
        """Search for additional habitat services using common patterns"""
        print(f"\n🔍 SEARCHING FOR ADDITIONAL HABITAT SERVICES")
        print("-"*60)
        
        # Common habitat service patterns
        service_patterns = [
            "Critical_Habitat",
            "Endangered_Species",
            "Threatened_Species", 
            "Species_Habitat",
            "CRITHAB",
            "ESA_Species",
            "Protected_Species"
        ]
        
        base_urls = [
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services",
            "https://fwsprimary.wim.usgs.gov/server/rest/services",
            "https://gis.fws.gov/arcgis/rest/services"
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
                            if test_url not in self.habitat_services:
                                self.habitat_services.append(test_url)
                        else:
                            print(f"   ❌ Service error")
                    else:
                        print(f"   ❌ HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")

def main():
    """Main exploration function"""
    print("🌿 Critical Habitat Service Explorer")
    print("="*80)
    
    explorer = HabitatServiceExplorer()
    explorer.explore_all_services()
    
    print(f"\n✅ EXPLORATION COMPLETE")
    print(f"="*80)
    print(f"💡 Key findings will be used to build the HabitatINFO client")

if __name__ == "__main__":
    main() 