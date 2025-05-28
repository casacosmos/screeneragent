#!/usr/bin/env python3
"""
Test PRAPEC Karst Layer Query
Test script to understand how to query the PRAPEC (Carso) layer
"""

import sys
import os
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mapmaker.common import MapServerClient

def test_prapec_layer():
    """Test querying the PRAPEC karst layer."""
    
    # Use the Reglamentario_va2 service (both seem to have the same layer)
    service_url = "https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer"
    prapec_layer_id = 15
    
    print(f"🔍 Testing PRAPEC karst layer query...")
    print(f"Service: {service_url}")
    print(f"Layer ID: {prapec_layer_id}")
    
    # Test 1: Get all features (limited) to see what data looks like
    print(f"\n1️⃣  Getting sample PRAPEC features...")
    
    query_url = f"{service_url}/{prapec_layer_id}/query"
    params = {
        'where': '1=1',  # Get all features
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json',
        'resultRecordCount': 5  # Limit to 5 features for testing
    }
    
    try:
        response = requests.get(query_url, params=params, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('features', [])
        print(f"   Found {len(features)} sample features")
        
        if features:
            print(f"   Sample feature attributes:")
            for key, value in features[0]['attributes'].items():
                print(f"     {key}: {value}")
        
        # Get total count
        count_params = {
            'where': '1=1',
            'returnCountOnly': 'true',
            'f': 'json'
        }
        count_response = requests.get(query_url, params=count_params, verify=False, timeout=10)
        count_data = count_response.json()
        total_count = count_data.get('count', 0)
        print(f"   Total PRAPEC features: {total_count}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Test point intersection query
    print(f"\n2️⃣  Testing point intersection query...")
    
    # Test coordinates in Puerto Rico (somewhere that might be in karst area)
    test_lon, test_lat = -66.1057, 18.4655  # San Juan area
    
    # Convert to Web Mercator for query
    client = MapServerClient(service_url)
    x_merc, y_merc = client.lonlat_to_webmercator(test_lon, test_lat)
    
    geometry = {
        "x": x_merc,
        "y": y_merc,
        "spatialReference": {"wkid": 102100}
    }
    
    point_params = {
        'geometry': json.dumps(geometry),
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': 102100,
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }
    
    try:
        response = requests.get(query_url, params=point_params, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('features', [])
        print(f"   Point ({test_lon}, {test_lat}) intersection results:")
        print(f"   Found {len(features)} intersecting PRAPEC features")
        
        if features:
            print(f"   ✅ Point IS in PRAPEC karst area!")
            for feature in features:
                attrs = feature['attributes']
                print(f"     Nombre: {attrs.get('Nombre', 'N/A')}")
                print(f"     Regla: {attrs.get('Regla', 'N/A')}")
        else:
            print(f"   ❌ Point is NOT in PRAPEC karst area")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test with a different point (more likely to be in karst)
    print(f"\n3️⃣  Testing with another point (karst area)...")
    
    # Try coordinates in the karst region (north-central PR)
    test_lon2, test_lat2 = -66.3, 18.3  # More central/north area
    
    x_merc2, y_merc2 = client.lonlat_to_webmercator(test_lon2, test_lat2)
    
    geometry2 = {
        "x": x_merc2,
        "y": y_merc2,
        "spatialReference": {"wkid": 102100}
    }
    
    point_params2 = {
        'geometry': json.dumps(geometry2),
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': 102100,
        'outFields': '*',
        'returnGeometry': 'false',
        'f': 'json'
    }
    
    try:
        response = requests.get(query_url, params=point_params2, verify=False, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        features = data.get('features', [])
        print(f"   Point ({test_lon2}, {test_lat2}) intersection results:")
        print(f"   Found {len(features)} intersecting PRAPEC features")
        
        if features:
            print(f"   ✅ Point IS in PRAPEC karst area!")
            for feature in features:
                attrs = feature['attributes']
                print(f"     Nombre: {attrs.get('Nombre', 'N/A')}")
                print(f"     Regla: {attrs.get('Regla', 'N/A')}")
        else:
            print(f"   ❌ Point is NOT in PRAPEC karst area")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_prapec_layer() 