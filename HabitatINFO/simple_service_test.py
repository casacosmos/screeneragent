#!/usr/bin/env python3
"""
Simple Critical Habitat Service Test
"""

import requests
import json

def test_habitat_service():
    """Test critical habitat service"""
    
    print("🧪 TESTING CRITICAL HABITAT SERVICE")
    print("="*50)
    
    # Service URLs
    habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
    wetlands_service_url = "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer"
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'ServiceTester/1.0'})
    
    # Test coordinates - Everglades area
    longitude = -80.9326
    latitude = 25.4663
    
    print(f"📍 Test coordinates: {longitude}, {latitude}")
    
    # Test critical habitat service
    print(f"\n🦎 CRITICAL HABITAT SERVICE")
    print("-" * 30)
    
    try:
        response = session.get(f"{habitat_service_url}?f=json", timeout=15)
        if response.status_code == 200:
            service_info = response.json()
            print(f"✅ Service accessible")
            
            layers = service_info.get('layers', [])
            print(f"Layers: {len(layers)}")
            
            for layer in layers:
                layer_id = layer.get('id')
                layer_name = layer.get('name', 'Unknown')
                print(f"  Layer {layer_id}: {layer_name}")
                
                # Get layer details
                try:
                    layer_response = session.get(f"{habitat_service_url}/{layer_id}?f=json", timeout=10)
                    if layer_response.status_code == 200:
                        layer_info = layer_response.json()
                        print(f"    Geometry: {layer_info.get('geometryType', 'Unknown')}")
                        print(f"    Min Scale: {layer_info.get('minScale', 'N/A')}")
                        print(f"    Max Scale: {layer_info.get('maxScale', 'N/A')}")
                        print(f"    Visible: {layer_info.get('defaultVisibility', 'N/A')}")
                        
                        # Test query
                        params = {
                            "geometry": json.dumps({
                                "x": longitude, 
                                "y": latitude, 
                                "spatialReference": {"wkid": 4326}
                            }),
                            "geometryType": "esriGeometryPoint",
                            "spatialRel": "esriSpatialRelIntersects",
                            "outFields": "*",
                            "returnGeometry": "false",
                            "returnCountOnly": "true",
                            "f": "json"
                        }
                        
                        query_response = session.get(f"{habitat_service_url}/{layer_id}/query", params=params, timeout=10)
                        if query_response.status_code == 200:
                            query_result = query_response.json()
                            if 'error' not in query_result:
                                count = query_result.get('count', 0)
                                print(f"    Query result: {count} features")
                            else:
                                print(f"    Query error: {query_result.get('error', {}).get('message', 'Unknown')}")
                        else:
                            print(f"    Query failed: HTTP {query_response.status_code}")
                except Exception as e:
                    print(f"    Layer error: {e}")
        else:
            print(f"❌ Service error: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Service error: {e}")
    
    # Test wetlands service for comparison
    print(f"\n🌿 WETLANDS SERVICE (for comparison)")
    print("-" * 30)
    
    try:
        response = session.get(f"{wetlands_service_url}?f=json", timeout=15)
        if response.status_code == 200:
            service_info = response.json()
            print(f"✅ Service accessible")
            
            layers = service_info.get('layers', [])
            print(f"Layers: {len(layers)}")
            
            # Test layer 0
            if len(layers) > 0:
                layer_response = session.get(f"{wetlands_service_url}/0?f=json", timeout=10)
                if layer_response.status_code == 200:
                    layer_info = layer_response.json()
                    print(f"  Layer 0: {layer_info.get('name', 'Unknown')}")
                    print(f"    Geometry: {layer_info.get('geometryType', 'Unknown')}")
                    print(f"    Min Scale: {layer_info.get('minScale', 'N/A')}")
                    print(f"    Max Scale: {layer_info.get('maxScale', 'N/A')}")
                    print(f"    Visible: {layer_info.get('defaultVisibility', 'N/A')}")
        else:
            print(f"❌ Service error: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Service error: {e}")

if __name__ == "__main__":
    test_habitat_service() 