#!/usr/bin/env python3
"""
Explore Wetlands ArcGIS Service Infrastructure

This script explores the specific ArcGIS service infrastructure used by the 
wetlands client to discover any geometry or buffer services within the same 
service ecosystem.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class WetlandsServiceExplorer:
    """Explore the wetlands service infrastructure for buffer capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WetlandsServiceExplorer/1.0'
        })
        
        # Service URLs from wetlands_client.py
        self.epa_base_url = "https://geopub.epa.gov/arcgis/rest/services"
        self.usfws_base_url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services"
        self.usfws_wim_base = "https://fwsprimary.wim.usgs.gov/server/rest/services"
        self.epa_waters_url = "https://watersgeo.epa.gov/arcgis/rest/services"
        
        # Known working service endpoints
        self.working_services = {
            'ribits': f"{self.epa_base_url}/NEPAssist/RIBITS/MapServer",
            'nwi': f"{self.usfws_base_url}/Wetlands/MapServer",
            'nwi_raster': f"{self.usfws_base_url}/WetlandsRaster/ImageServer",
            'riparian': f"{self.usfws_base_url}/Riparian/MapServer",
            'watershed': f"{self.epa_waters_url}/NHDPlus_NP21/WBD_NP21_Simplified/MapServer",
            'wim_print': f"{self.usfws_wim_base}/ExportWebMap/GPServer/Export Web Map"
        }
        
        # Potential geometry/utility service locations
        self.potential_geometry_services = [
            f"{self.epa_base_url}/Geometry/GeometryServer",
            f"{self.usfws_base_url}/Geometry/GeometryServer", 
            f"{self.usfws_wim_base}/Utilities/Geometry/GeometryServer",
            f"{self.usfws_wim_base}/Tools/GPServer",
            f"{self.epa_waters_url}/Geometry/GeometryServer"
        ]
    
    def explore_service_infrastructure(self):
        """Explore the service infrastructure for geometry capabilities"""
        print("🔍 Exploring Wetlands Service Infrastructure for Buffer Capabilities")
        print("="*80)
        
        # First, explore the base service catalogs
        self.explore_base_services()
        
        # Test the known working services to understand their capabilities
        self.test_known_services()
        
        # Search for potential geometry services
        self.search_geometry_services()
        
        # Test buffer operations on discovered services
        self.test_buffer_capabilities()
    
    def explore_base_services(self):
        """Explore the base service catalogs"""
        print("\n📋 EXPLORING BASE SERVICE CATALOGS")
        print("-"*60)
        
        base_urls = [
            self.epa_base_url,
            self.usfws_base_url, 
            self.usfws_wim_base,
            self.epa_waters_url
        ]
        
        for base_url in base_urls:
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
            
            # Look for geometry-related services
            if 'services' in catalog:
                geometry_services = [s for s in catalog['services'] 
                                   if any(term in s.get('name', '').lower() 
                                         for term in ['geometry', 'buffer', 'utility', 'tool', 'gp'])]
                
                if geometry_services:
                    print(f"   🎯 Potential geometry services:")
                    for service in geometry_services:
                        print(f"     • {service.get('name')} ({service.get('type')})")
            
            # Look for utility folders
            if 'folders' in catalog:
                utility_folders = [f for f in catalog['folders'] 
                                 if any(term in f.lower() 
                                       for term in ['utility', 'utilities', 'geometry', 'tools'])]
                
                if utility_folders:
                    print(f"   📁 Potential utility folders:")
                    for folder in utility_folders:
                        print(f"     • {folder}")
                        self.explore_folder(base_url, folder)
        
        except Exception as e:
            print(f"❌ Failed to access: {e}")
    
    def explore_folder(self, base_url: str, folder: str):
        """Explore a specific folder for services"""
        try:
            response = self.session.get(f"{base_url}/{folder}?f=json", timeout=15)
            response.raise_for_status()
            folder_info = response.json()
            
            if 'services' in folder_info:
                print(f"       Services in {folder}:")
                for service in folder_info['services'][:5]:  # Limit to first 5
                    print(f"         - {service.get('name')} ({service.get('type')})")
        
        except Exception as e:
            print(f"       ❌ Cannot access folder {folder}: {e}")
    
    def test_known_services(self):
        """Test the known working services for additional capabilities"""
        print("\n🔧 TESTING KNOWN WORKING SERVICES")
        print("-"*60)
        
        for service_name, service_url in self.working_services.items():
            print(f"\n📍 Testing: {service_name}")
            print(f"   URL: {service_url}")
            
            try:
                response = self.session.get(f"{service_url}?f=json", timeout=15)
                response.raise_for_status()
                service_info = response.json()
                
                print(f"   ✅ Accessible")
                print(f"   Description: {service_info.get('serviceDescription', 'N/A')[:100]}...")
                
                # Check for additional capabilities
                if 'capabilities' in service_info:
                    capabilities = service_info['capabilities'].split(',')
                    print(f"   Capabilities: {', '.join(capabilities)}")
                
                # Check for related services or utilities
                if 'tasks' in service_info:
                    print(f"   Tasks/Tools: {len(service_info['tasks'])}")
                    for task in service_info['tasks'][:3]:  # Show first 3
                        print(f"     • {task}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    def search_geometry_services(self):
        """Search for potential geometry services"""
        print("\n🔍 SEARCHING FOR GEOMETRY SERVICES")
        print("-"*60)
        
        for service_url in self.potential_geometry_services:
            print(f"\n🎯 Testing: {service_url}")
            
            try:
                response = self.session.get(f"{service_url}?f=json", timeout=15)
                response.raise_for_status()
                service_info = response.json()
                
                print(f"   ✅ FOUND GEOMETRY SERVICE!")
                print(f"   Description: {service_info.get('serviceDescription', 'N/A')}")
                
                # Check available operations
                if 'tasks' in service_info:
                    print(f"   Available operations:")
                    for task in service_info['tasks']:
                        print(f"     • {task}")
                        
                        # If buffer operation exists, explore it
                        if 'buffer' in task.lower():
                            self.explore_buffer_operation(f"{service_url}/{task}")
                
                return service_url  # Return the first working one
                
            except Exception as e:
                print(f"   ❌ Not available: {e}")
        
        return None
    
    def explore_buffer_operation(self, buffer_url: str):
        """Explore a specific buffer operation"""
        print(f"\n       🎯 Exploring buffer operation: {buffer_url}")
        
        try:
            response = self.session.get(f"{buffer_url}?f=json", timeout=15)
            response.raise_for_status()
            buffer_info = response.json()
            
            print(f"       ✅ Buffer operation accessible")
            print(f"       Description: {buffer_info.get('description', 'N/A')[:100]}...")
            
            # Check parameters
            if 'parameters' in buffer_info:
                print(f"       Parameters ({len(buffer_info['parameters'])}):")
                for param in buffer_info['parameters'][:5]:  # Show first 5
                    name = param.get('name', 'Unknown')
                    param_type = param.get('dataType', 'Unknown')
                    required = "Required" if param.get('parameterType') == 'esriGPParameterTypeRequired' else "Optional"
                    print(f"         • {name} ({param_type}) - {required}")
            
        except Exception as e:
            print(f"       ❌ Cannot access buffer operation: {e}")
    
    def test_buffer_capabilities(self):
        """Test buffer capabilities on discovered services"""
        print("\n🧪 TESTING BUFFER CAPABILITIES")
        print("-"*60)
        
        # Test point (Puerto Rico - same as existing tests)
        test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
        radius_meters = 804.67  # 0.5 miles
        
        # Try the WIM service infrastructure specifically
        wim_geometry_urls = [
            f"{self.usfws_wim_base}/Utilities/Geometry/GeometryServer",
            f"{self.usfws_wim_base}/Tools/GPServer/Buffer",
            f"{self.usfws_wim_base}/Geometry/GeometryServer"
        ]
        
        for service_url in wim_geometry_urls:
            print(f"\n🔧 Testing buffer operation: {service_url}")
            
            # Test direct buffer endpoint
            if service_url.endswith('GeometryServer'):
                self.test_geometry_buffer(service_url, test_point, radius_meters)
            else:
                self.test_gp_buffer(service_url, test_point, radius_meters)
    
    def test_geometry_buffer(self, service_url: str, test_point: Dict, radius_meters: float):
        """Test geometry service buffer operation"""
        try:
            buffer_params = {
                "f": "json",
                "geometries": json.dumps({
                    "geometryType": "esriGeometryPoint",
                    "geometries": [test_point]
                }),
                "inSR": "4326",
                "outSR": "4326",
                "distances": str(radius_meters),
                "unit": "esriSRUnit_Meter",
                "geodesic": "true"
            }
            
            response = self.session.get(f"{service_url}/buffer", params=buffer_params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
                
                # Try without geodesic
                buffer_params_no_geodesic = buffer_params.copy()
                del buffer_params_no_geodesic['geodesic']
                
                response2 = self.session.get(f"{service_url}/buffer", params=buffer_params_no_geodesic, timeout=30)
                if response2.status_code == 200:
                    result2 = response2.json()
                    if 'error' not in result2 and 'geometries' in result2:
                        print(f"   ✅ SUCCESS without geodesic: {len(result2['geometries'])} geometries")
                        return True
            
            elif 'geometries' in result and len(result['geometries']) > 0:
                print(f"   ✅ SUCCESS: {len(result['geometries'])} geometries")
                print(f"   📐 Polygon with {len(result['geometries'][0].get('rings', []))} rings")
                return True
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        return False
    
    def test_gp_buffer(self, service_url: str, test_point: Dict, radius_meters: float):
        """Test GP service buffer operation"""
        try:
            # First check if the service exists
            response = self.session.get(f"{service_url}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            print(f"   ✅ GP Service accessible")
            print(f"   Description: {service_info.get('serviceDescription', 'N/A')[:100]}...")
            
            if 'tasks' in service_info:
                print(f"   Available tasks: {', '.join(service_info['tasks'])}")
            
        except Exception as e:
            print(f"   ❌ GP Service not accessible: {e}")
        
        return False

def main():
    """Main exploration function"""
    print("🌐 Wetlands Service Infrastructure Explorer")
    print("="*80)
    
    explorer = WetlandsServiceExplorer()
    explorer.explore_service_infrastructure()
    
    print(f"\n✅ EXPLORATION COMPLETE")
    print(f"="*80)
    print(f"💡 Key findings:")
    print(f"   • Checked EPA, USFWS, and WIM service infrastructure")
    print(f"   • Looked for geometry and utility services")
    print(f"   • Tested buffer capabilities where available")
    print(f"   • The manual geodesic calculation fallback remains the most reliable approach")

if __name__ == "__main__":
    main() 