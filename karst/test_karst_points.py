#!/usr/bin/env python3
"""
Test multiple points in known karst regions to find PRAPEC intersections
"""

import sys
import os
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from mapmaker.common import MapServerClient

def test_karst_points():
    """Test multiple coordinates in known karst regions."""
    
    # Test with coordinates from known karst regions in Puerto Rico
    test_points = [
        (-66.7, 18.4, 'Arecibo area'),
        (-66.6, 18.4, 'Camuy area'),
        (-66.5, 18.3, 'Ciales area'),
        (-66.4, 18.35, 'Morovis area'),
        (-66.3, 18.4, 'Manati area'),
        (-66.65, 18.45, 'Hatillo area'),
        (-66.55, 18.35, 'Utuado area'),
        (-66.45, 18.4, 'Barceloneta area'),
        (-66.35, 18.45, 'Vega Baja area'),
        (-66.25, 18.4, 'Vega Alta area'),
        # Add some points that are likely outside karst for testing buffer
        (-66.1, 18.4, 'San Juan area'),
        (-66.0, 18.2, 'Carolina area'),
        (-67.0, 18.2, 'Mayaguez area')
    ]

    service_url = 'https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer'
    query_url = f'{service_url}/15/query'
    client = MapServerClient(service_url)

    karst_points = []
    non_karst_points = []
    buffer_karst_points = []

    # Convert 0.5 miles to meters (1 mile = 1609.34 meters)
    buffer_distance_meters = 0.5 * 1609.34

    for lon, lat, area_name in test_points:
        print(f'Testing {area_name}: ({lon}, {lat})')
        
        x_merc, y_merc = client.lonlat_to_webmercator(lon, lat)
        
        geometry = {
            'x': x_merc,
            'y': y_merc,
            'spatialReference': {'wkid': 102100}
        }
        
        # First check: exact point intersection
        params = {
            'geometry': json.dumps(geometry),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'inSR': 102100,
            'outFields': '*',
            'returnGeometry': 'false',
            'f': 'json'
        }
        
        try:
            response = requests.get(query_url, params=params, verify=False, timeout=10)
            data = response.json()
            features = data.get('features', [])
            
            if features:
                print(f'  ✅ DIRECTLY IN KARST AREA!')
                karst_points.append((lon, lat, area_name))
                for feature in features:
                    attrs = feature['attributes']
                    print(f'    Nombre: {attrs.get("Nombre", "N/A")}')
                    print(f'    Regla: {attrs.get("Regla", "N/A")}')
                    print(f'    Area: {attrs.get("Shape.STArea()", "N/A"):,.0f} sq meters')
            else:
                print(f'  ❌ Not directly in karst area')
                
                # Second check: buffer search within 0.5 miles
                print(f'    🔍 Checking within 0.5 mile radius...')
                
                buffer_params = {
                    'geometry': json.dumps(geometry),
                    'geometryType': 'esriGeometryPoint',
                    'spatialRel': 'esriSpatialRelIntersects',
                    'distance': buffer_distance_meters,
                    'units': 'esriSRUnit_Meter',
                    'inSR': 102100,
                    'outFields': '*',
                    'returnGeometry': 'false',
                    'f': 'json'
                }
                
                try:
                    buffer_response = requests.get(query_url, params=buffer_params, verify=False, timeout=10)
                    buffer_data = buffer_response.json()
                    buffer_features = buffer_data.get('features', [])
                    
                    if buffer_features:
                        print(f'    ✅ KARST FOUND WITHIN 0.5 MILES!')
                        buffer_karst_points.append((lon, lat, area_name))
                        for feature in buffer_features:
                            attrs = feature['attributes']
                            print(f'      Nombre: {attrs.get("Nombre", "N/A")}')
                            print(f'      Regla: {attrs.get("Regla", "N/A")}')
                            print(f'      Area: {attrs.get("Shape.STArea()", "N/A"):,.0f} sq meters')
                            print(f'      Distance: Within 0.5 miles')
                    else:
                        print(f'    ❌ No karst within 0.5 miles')
                        non_karst_points.append((lon, lat, area_name))
                        
                except Exception as e:
                    print(f'    Error in buffer search: {e}')
                    non_karst_points.append((lon, lat, area_name))
                
        except Exception as e:
            print(f'  Error: {e}')
            non_karst_points.append((lon, lat, area_name))
        print()

    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Points DIRECTLY in karst area: {len(karst_points)}")
    for lon, lat, name in karst_points:
        print(f"  ✅ {name}: ({lon}, {lat})")
    
    print(f"\nPoints with karst WITHIN 0.5 miles: {len(buffer_karst_points)}")
    for lon, lat, name in buffer_karst_points:
        print(f"  🔍 {name}: ({lon}, {lat})")
    
    print(f"\nPoints with NO karst within 0.5 miles: {len(non_karst_points)}")
    for lon, lat, name in non_karst_points:
        print(f"  ❌ {name}: ({lon}, {lat})")

if __name__ == "__main__":
    test_karst_points() 