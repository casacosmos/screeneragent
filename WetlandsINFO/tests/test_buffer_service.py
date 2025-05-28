#!/usr/bin/env python3
"""
Test ArcGIS Buffer Services

Focused test script to understand exactly why buffer services are failing
and find the correct parameter format.
"""

import requests
import json
import sys

def test_geometry_server():
    """Test the ArcGIS Geometry Server buffer operation"""
    
    base_url = "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer"
    
    # Get service metadata
    print("🔍 Getting Geometry Server metadata...")
    response = requests.get(f"{base_url}?f=json")
    if response.status_code == 200:
        service_info = response.json()
        print(f"✅ Service Description: {service_info.get('serviceDescription', 'N/A')}")
        print(f"✅ Current Version: {service_info.get('currentVersion', 'N/A')}")
        
        # Check if buffer is available
        if hasattr(response, 'url'):
            print(f"📍 Service URL: {base_url}")
    
    # Test different parameter formats
    test_point = {"x": -66.199399, "y": 18.408303, "spatialReference": {"wkid": 4326}}
    
    # Format 1: Single geometry in array
    print("\n🧪 Test 1: Single point geometry")
    test_buffer_format_1(base_url, test_point)
    
    # Format 2: FeatureSet format
    print("\n🧪 Test 2: FeatureSet format")
    test_buffer_format_2(base_url, test_point)
    
    # Format 3: Direct geometry array
    print("\n🧪 Test 3: Direct geometry array")
    test_buffer_format_3(base_url, test_point)

def test_buffer_format_1(base_url, test_point):
    """Test buffer with single geometry format"""
    
    buffer_params = {
        "f": "json",
        "geometries": json.dumps([test_point]),
        "inSR": "4326",
        "outSR": "4326", 
        "distances": "804.67",
        "unit": "esriSRUnit_Meter",
        "geodesic": "true"
    }
    
    try:
        response = requests.get(f"{base_url}/buffer", params=buffer_params, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success: {len(result.get('geometries', []))} geometries")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_buffer_format_2(base_url, test_point):
    """Test buffer with FeatureSet format"""
    
    feature_set = {
        "geometryType": "esriGeometryPoint",
        "spatialReference": {"wkid": 4326},
        "features": [
            {
                "geometry": test_point,
                "attributes": {"OBJECTID": 1}
            }
        ]
    }
    
    buffer_params = {
        "f": "json", 
        "geometries": json.dumps(feature_set),
        "inSR": "4326",
        "outSR": "4326",
        "distances": "804.67",
        "unit": "esriSRUnit_Meter",
        "geodesic": "true"
    }
    
    try:
        response = requests.get(f"{base_url}/buffer", params=buffer_params, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success: {len(result.get('geometries', []))} geometries")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_buffer_format_3(base_url, test_point):
    """Test buffer with direct geometry array format"""
    
    geometries = {
        "geometryType": "esriGeometryPoint",
        "geometries": [test_point]
    }
    
    buffer_params = {
        "f": "json",
        "geometries": json.dumps(geometries),
        "inSR": "4326", 
        "outSR": "4326",
        "distances": "804.67", 
        "unit": "esriSRUnit_Meter",
        "geodesic": "true"
    }
    
    try:
        response = requests.get(f"{base_url}/buffer", params=buffer_params, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
                
                # Try without geodesic
                print(f"   🔄 Retrying without geodesic...")
                buffer_params_no_geodesic = buffer_params.copy()
                del buffer_params_no_geodesic['geodesic']
                
                response2 = requests.get(f"{base_url}/buffer", params=buffer_params_no_geodesic, timeout=30)
                if response2.status_code == 200:
                    result2 = response2.json()
                    if 'error' in result2:
                        print(f"   ❌ Still failed: {result2['error']}")
                    else:
                        print(f"   ✅ Success without geodesic: {len(result2.get('geometries', []))} geometries")
                        return result2
            else:
                print(f"   ✅ Success: {len(result.get('geometries', []))} geometries")
                return result
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_working_example():
    """Test with a known working example from ArcGIS documentation"""
    
    print("\n🎯 Testing with ArcGIS documentation example...")
    
    # Example from ArcGIS REST API documentation
    base_url = "https://utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer"
    
    # Simple point buffer test 
    buffer_params = {
        "f": "json",
        "geometries": '{"geometryType":"esriGeometryPoint","geometries":[{"x":-117,"y":34,"spatialReference":{"wkid":4326}}]}',
        "inSR": "4326",
        "outSR": "4326",
        "distances": "1000",
        "unit": "esriSRUnit_Meter"
    }
    
    try:
        response = requests.get(f"{base_url}/buffer", params=buffer_params, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ Success: {len(result.get('geometries', []))} geometries")
                
                # Show geometry structure
                if result.get('geometries'):
                    geom = result['geometries'][0]
                    if 'rings' in geom:
                        print(f"   📐 Polygon with {len(geom['rings'])} rings")
                        print(f"   📍 First ring has {len(geom['rings'][0])} points")
                
                return result
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def main():
    """Main test function"""
    print("🧪 ArcGIS Buffer Service Test")
    print("="*50)
    
    # Test the main geometry server
    test_geometry_server()
    
    # Test with a known working example
    test_working_example()
    
    print("\n✅ Test Summary")
    print("="*50)
    print("💡 If all tests fail, the issue might be:")
    print("   • Service authentication requirements")
    print("   • Parameter format differences")
    print("   • Service availability/maintenance")
    print("   • Network/proxy issues")

if __name__ == "__main__":
    main() 