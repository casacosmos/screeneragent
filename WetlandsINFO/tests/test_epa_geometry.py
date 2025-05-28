#!/usr/bin/env python3
"""
Test EPA Geometry Services

Test the EPA geometry services we discovered within the same infrastructure
that's already working for wetlands data.
"""

import requests
import json
import sys

def test_epa_geometry_services():
    """Test the EPA geometry services for buffer operations"""
    
    print("🧪 Testing EPA Geometry Services")
    print("="*60)
    
    # EPA geometry services discovered
    epa_geometry_services = [
        "https://geopub.epa.gov/arcgis/rest/services/Utilities/Geometry/GeometryServer",
        "https://watersgeo.epa.gov/arcgis/rest/services/Utilities/Geometry/GeometryServer"
    ]
    
    # Test point (Puerto Rico)
    test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
    radius_meters = 804.67  # 0.5 miles
    
    for service_url in epa_geometry_services:
        print(f"\n🔧 Testing: {service_url}")
        
        # First check service metadata
        try:
            response = requests.get(f"{service_url}?f=json", timeout=15)
            response.raise_for_status()
            service_info = response.json()
            
            print(f"✅ Service accessible")
            print(f"   Description: {service_info.get('serviceDescription', 'N/A')}")
            print(f"   Current Version: {service_info.get('currentVersion', 'N/A')}")
            
            # Check available operations
            if 'tasks' in service_info:
                print(f"   Available operations: {', '.join(service_info['tasks'])}")
                
                # Test buffer if available
                if any('buffer' in task.lower() for task in service_info['tasks']):
                    test_buffer_operation(service_url, test_point, radius_meters)
                else:
                    print(f"   ❌ No buffer operation found")
            else:
                # Try buffer operation anyway
                test_buffer_operation(service_url, test_point, radius_meters)
                
        except Exception as e:
            print(f"❌ Cannot access service: {e}")

def test_buffer_operation(service_url: str, test_point: dict, radius_meters: float):
    """Test buffer operation on a geometry service"""
    
    print(f"\n   🧪 Testing buffer operation...")
    
    # Multiple parameter formats to try
    test_formats = [
        # Format 1: Standard ArcGIS REST format
        {
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
        },
        # Format 2: Without geodesic
        {
            "f": "json",
            "geometries": json.dumps({
                "geometryType": "esriGeometryPoint",
                "geometries": [test_point]
            }),
            "inSR": "4326",
            "outSR": "4326",
            "distances": str(radius_meters),
            "unit": "esriSRUnit_Meter"
        },
        # Format 3: Simpler format
        {
            "f": "json",
            "geometries": json.dumps([test_point]),
            "inSR": "4326",
            "outSR": "4326",
            "distances": str(radius_meters),
            "unit": "esriSRUnit_Meter"
        },
        # Format 4: Using Web Mercator
        {
            "f": "json",
            "geometries": json.dumps({
                "geometryType": "esriGeometryPoint",
                "geometries": [{"x": -7365518.19, "y": 2104079.78, "spatialReference": {"wkid": 102100}}]
            }),
            "inSR": "102100",
            "outSR": "4326",
            "distances": str(radius_meters),
            "unit": "esriSRUnit_Meter"
        }
    ]
    
    for i, buffer_params in enumerate(test_formats, 1):
        print(f"      Format {i}: ", end="")
        
        try:
            response = requests.get(f"{service_url}/buffer", params=buffer_params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                print(f"❌ Error: {result['error'].get('message', 'Unknown error')}")
            elif 'geometries' in result and len(result['geometries']) > 0:
                geom = result['geometries'][0]
                print(f"✅ SUCCESS! Polygon with {len(geom.get('rings', []))} ring(s)")
                
                # Show first few points of the buffer
                if 'rings' in geom and len(geom['rings']) > 0:
                    ring = geom['rings'][0]
                    print(f"         First ring has {len(ring)} points")
                    print(f"         Sample points: {ring[:3]}...")
                
                return result  # Return successful result
            else:
                print(f"❌ No geometries returned")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    return None

def test_working_buffer_with_wetlands():
    """Test creating a working buffer and using it with wetlands data"""
    
    print(f"\n🎯 INTEGRATION TEST: Buffer + Wetlands")
    print("="*60)
    
    # Try to get a working buffer from EPA services
    epa_services = [
        "https://geopub.epa.gov/arcgis/rest/services/Utilities/Geometry/GeometryServer",
        "https://watersgeo.epa.gov/arcgis/rest/services/Utilities/Geometry/GeometryServer"
    ]
    
    test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
    radius_meters = 804.67  # 0.5 miles
    
    for service_url in epa_services:
        print(f"\n🔧 Trying buffer creation with: {service_url}")
        
        buffer_result = test_buffer_operation(service_url, test_point, radius_meters)
        
        if buffer_result and 'geometries' in buffer_result:
            print(f"\n   ✅ Buffer created successfully!")
            buffer_geom = buffer_result['geometries'][0]
            
            # Now test using this buffer with wetlands query
            print(f"   🌿 Testing buffer with wetlands query...")
            
            # Use the buffer to query wetlands
            wetlands_url = "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0"
            
            wetlands_params = {
                "geometry": json.dumps(buffer_geom),
                "geometryType": "esriGeometryPolygon",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "OBJECTID,WETLAND_TYPE,ATTRIBUTE,ACRES",
                "f": "json"
            }
            
            try:
                response = requests.get(f"{wetlands_url}/query", params=wetlands_params, timeout=30)
                response.raise_for_status()
                wetlands_data = response.json()
                
                if 'features' in wetlands_data:
                    print(f"   ✅ Found {len(wetlands_data['features'])} wetland features in buffer!")
                    
                    # Show some results
                    for i, feature in enumerate(wetlands_data['features'][:3]):
                        attrs = feature.get('attributes', {})
                        print(f"      {i+1}. {attrs.get('WETLAND_TYPE', 'Unknown')} - {attrs.get('ATTRIBUTE', 'N/A')}")
                    
                    return True
                else:
                    print(f"   ❌ No wetlands found in buffer")
                    
            except Exception as e:
                print(f"   ❌ Error querying wetlands: {e}")
        
        else:
            print(f"   ❌ Buffer creation failed")
    
    return False

def main():
    """Main test function"""
    
    # Test EPA geometry services
    test_epa_geometry_services()
    
    # Test integration with wetlands
    success = test_working_buffer_with_wetlands()
    
    print(f"\n✅ TEST SUMMARY")
    print("="*60)
    if success:
        print(f"🎉 SUCCESS! Found working buffer service within EPA infrastructure")
        print(f"💡 This can be integrated into the main wetlands mapping system")
    else:
        print(f"❌ No working buffer services found")
        print(f"💡 Continue using manual geodesic calculations as fallback")

if __name__ == "__main__":
    main() 