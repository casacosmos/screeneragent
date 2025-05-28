#!/usr/bin/env python3
"""
Explore ArcGIS Services for Buffer Operations

This script explores various ArcGIS services to understand their metadata,
capabilities, and available operations for creating geodesic buffers.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

class ArcGISServiceExplorer:
    """Explore ArcGIS services and their capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ServiceExplorer/1.0'
        })
        
        # Known service base URLs to explore
        self.service_bases = [
            "https://utility.arcgisonline.com/ArcGIS/rest/services",
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services",
            "https://fwsprimary.wim.usgs.gov/server/rest/services",
            "https://services.arcgisonline.com/ArcGIS/rest/services"
        ]
        
        # Known geometry/utility services
        self.geometry_services = [
            "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer",
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Utilities/Geometry/GeometryServer"
        ]
        
        # Known GP (Geoprocessing) services
        self.gp_services = [
            "https://sampleserver6.arcgisonline.com/arcgis/rest/services/911CallsHotspot/GPServer",
            "https://fwsprimary.wim.usgs.gov/server/rest/services/Tools/GPServer"
        ]
    
    def explore_service_catalog(self, base_url: str) -> Dict[str, Any]:
        """Explore the service catalog at a base URL"""
        print(f"\n🔍 Exploring service catalog: {base_url}")
        
        try:
            response = self.session.get(f"{base_url}?f=json", timeout=15)
            response.raise_for_status()
            catalog = response.json()
            
            print(f"✅ Catalog retrieved successfully")
            print(f"   Services: {len(catalog.get('services', []))}")
            print(f"   Folders: {len(catalog.get('folders', []))}")
            
            # List services
            if 'services' in catalog:
                print(f"\n📋 Available Services:")
                for service in catalog['services'][:10]:  # Limit to first 10
                    print(f"   • {service.get('name')} ({service.get('type')})")
            
            # List folders  
            if 'folders' in catalog:
                print(f"\n📁 Available Folders:")
                for folder in catalog['folders'][:10]:  # Limit to first 10
                    print(f"   • {folder}")
            
            return catalog
            
        except Exception as e:
            print(f"❌ Failed to explore {base_url}: {e}")
            return {}
    
    def explore_geometry_service(self, service_url: str) -> Dict[str, Any]:
        """Explore a geometry service and its operations"""
        print(f"\n🔧 Exploring Geometry Service: {service_url}")
        
        try:
            response = self.session.get(f"{service_url}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            print(f"✅ Geometry Service accessible")
            print(f"   Service Description: {service_info.get('serviceDescription', 'N/A')}")
            print(f"   Current Version: {service_info.get('currentVersion', 'N/A')}")
            print(f"   Max Record Count: {service_info.get('maxRecordCount', 'N/A')}")
            
            # Check operations
            if 'tasks' in service_info:
                print(f"\n⚙️  Available Operations:")
                for task in service_info['tasks']:
                    print(f"   • {task}")
                    
                    # If buffer operation exists, explore it
                    if 'buffer' in task.lower():
                        self.explore_buffer_operation(f"{service_url}/{task}")
            
            return service_info
            
        except Exception as e:
            print(f"❌ Failed to explore geometry service {service_url}: {e}")
            return {}
    
    def explore_buffer_operation(self, buffer_url: str) -> Dict[str, Any]:
        """Explore buffer operation parameters and requirements"""
        print(f"\n🎯 Exploring Buffer Operation: {buffer_url}")
        
        try:
            response = self.session.get(f"{buffer_url}?f=json", timeout=15)
            response.raise_for_status()
            buffer_info = response.json()
            
            print(f"✅ Buffer operation accessible")
            print(f"   Description: {buffer_info.get('description', 'N/A')}")
            print(f"   Help URL: {buffer_info.get('helpUrl', 'N/A')}")
            
            # Check parameters
            if 'parameters' in buffer_info:
                print(f"\n📝 Required Parameters:")
                for param in buffer_info['parameters']:
                    name = param.get('name', 'Unknown')
                    param_type = param.get('dataType', 'Unknown')
                    required = "Required" if param.get('parameterType') == 'esriGPParameterTypeRequired' else "Optional"
                    print(f"   • {name} ({param_type}) - {required}")
                    
                    # Show choices if available
                    if 'choiceList' in param and param['choiceList']:
                        print(f"     Choices: {', '.join(param['choiceList'])}")
            
            return buffer_info
            
        except Exception as e:
            print(f"❌ Failed to explore buffer operation {buffer_url}: {e}")
            return {}
    
    def test_buffer_operation(self, service_url: str, test_point: Dict[str, float], radius_meters: float) -> bool:
        """Test a buffer operation with sample data"""
        print(f"\n🧪 Testing Buffer Operation: {service_url}")
        
        try:
            # Test with simple parameters
            test_params = {
                "f": "json",
                "geometries": json.dumps({
                    "geometryType": "esriGeometryPoint",
                    "geometries": [test_point]
                }),
                "inSR": "4326",
                "outSR": "4326",
                "distances": str(radius_meters),
                "unit": "esriSRUnit_Meter"
            }
            
            print(f"   Testing with basic parameters...")
            response = self.session.get(f"{service_url}/buffer", params=test_params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
                
                # Try with geodesic parameter
                print(f"   🔄 Retrying with geodesic=true...")
                test_params["geodesic"] = "true"
                
                response = self.session.get(f"{service_url}/buffer", params=test_params, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if 'error' in result:
                    print(f"   ❌ Still failed: {result['error']}")
                    return False
            
            if 'geometries' in result and len(result['geometries']) > 0:
                print(f"   ✅ Buffer operation successful!")
                print(f"   📐 Returned {len(result['geometries'])} geometry(s)")
                
                # Check geometry structure
                geom = result['geometries'][0]
                if 'rings' in geom:
                    print(f"   ⭕ Polygon with {len(geom['rings'])} ring(s)")
                    if len(geom['rings']) > 0:
                        print(f"   📍 First ring has {len(geom['rings'][0])} points")
                
                return True
            else:
                print(f"   ❌ No geometries returned")
                return False
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            return False
    
    def explore_gp_service(self, gp_url: str) -> Dict[str, Any]:
        """Explore a GP (Geoprocessing) service"""
        print(f"\n🔧 Exploring GP Service: {gp_url}")
        
        try:
            response = self.session.get(f"{gp_url}?f=json", timeout=15)
            response.raise_for_status()
            gp_info = response.json()
            
            print(f"✅ GP Service accessible")
            print(f"   Description: {gp_info.get('serviceDescription', 'N/A')}")
            print(f"   Tasks: {len(gp_info.get('tasks', []))}")
            
            # List tasks/tools
            if 'tasks' in gp_info:
                print(f"\n🛠️  Available Tools:")
                for task in gp_info['tasks']:
                    print(f"   • {task}")
                    
                    # If it's a buffer-related tool, explore it
                    if 'buffer' in task.lower():
                        self.explore_gp_task(f"{gp_url}/{task}")
            
            return gp_info
            
        except Exception as e:
            print(f"❌ Failed to explore GP service {gp_url}: {e}")
            return {}
    
    def explore_gp_task(self, task_url: str) -> Dict[str, Any]:
        """Explore a specific GP task"""
        print(f"\n🎯 Exploring GP Task: {task_url}")
        
        try:
            response = self.session.get(f"{task_url}?f=json", timeout=15)
            response.raise_for_status()
            task_info = response.json()
            
            print(f"✅ GP Task accessible")
            print(f"   Description: {task_info.get('description', 'N/A')}")
            print(f"   Execution Type: {task_info.get('executionType', 'N/A')}")
            
            # Check parameters
            if 'parameters' in task_info:
                print(f"\n📝 Task Parameters:")
                for param in task_info['parameters']:
                    name = param.get('name', 'Unknown')
                    direction = param.get('direction', 'Unknown')
                    param_type = param.get('dataType', 'Unknown')
                    print(f"   • {name} ({direction}, {param_type})")
            
            return task_info
            
        except Exception as e:
            print(f"❌ Failed to explore GP task {task_url}: {e}")
            return {}
    
    def find_working_buffer_services(self) -> List[str]:
        """Find services that can successfully create buffers"""
        print(f"\n🎯 TESTING BUFFER SERVICES")
        print(f"="*60)
        
        # Test point (Puerto Rico)
        test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
        radius_meters = 804.67  # 0.5 miles
        
        working_services = []
        
        # Test geometry services
        for service_url in self.geometry_services:
            print(f"\n🔧 Testing: {service_url}")
            if self.test_buffer_operation(service_url, test_point, radius_meters):
                working_services.append(service_url)
        
        return working_services

def main():
    """Main exploration function"""
    print("🔍 ArcGIS Service Explorer for Buffer Operations")
    print("="*60)
    
    explorer = ArcGISServiceExplorer()
    
    # Explore service catalogs
    print("\n📋 EXPLORING SERVICE CATALOGS")
    print("-"*40)
    for base_url in explorer.service_bases[:2]:  # Limit to first 2 for brevity
        explorer.explore_service_catalog(base_url)
    
    # Explore geometry services
    print("\n🔧 EXPLORING GEOMETRY SERVICES")
    print("-"*40)
    for geom_service in explorer.geometry_services:
        explorer.explore_geometry_service(geom_service)
    
    # Explore GP services
    print("\n🛠️  EXPLORING GEOPROCESSING SERVICES")
    print("-"*40)
    for gp_service in explorer.gp_services:
        explorer.explore_gp_service(gp_service)
    
    # Find working services
    working_services = explorer.find_working_buffer_services()
    
    print(f"\n✅ SUMMARY")
    print(f"="*60)
    if working_services:
        print(f"🎉 Found {len(working_services)} working buffer service(s):")
        for service in working_services:
            print(f"   ✅ {service}")
    else:
        print(f"❌ No working buffer services found")
        print(f"💡 Consider using manual geodesic calculations as fallback")

if __name__ == "__main__":
    main() 