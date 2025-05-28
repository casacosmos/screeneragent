#!/usr/bin/env python3
"""
Explore MIPR Reglamentario MapServers to find PRAPEC karst layer
"""

import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def explore_mapserver(server_url):
    """Explore a MapServer and return its metadata."""
    print(f'\n=== {server_url} ===')
    try:
        response = requests.get(f'{server_url}?f=pjson', verify=False, timeout=15)
        if response.status_code == 200:
            data = response.json()
            print(f'Service Name: {data.get("serviceName", "Unknown")}')
            print(f'Description: {data.get("serviceDescription", "No description")}')
            print(f'Layers ({len(data.get("layers", []))}):')
            
            layers = []
            for layer in data.get('layers', []):
                layer_info = {
                    'id': layer['id'],
                    'name': layer['name'],
                    'type': layer.get('type', 'Unknown')
                }
                layers.append(layer_info)
                print(f'  [{layer["id"]}] {layer["name"]} ({layer.get("type", "Unknown")})')
                
                # Check if this might be the PRAPEC karst layer
                if any(keyword in layer['name'].lower() for keyword in ['prapec', 'karst', 'carso']):
                    print(f'    *** POTENTIAL KARST LAYER ***')
            
            return {'success': True, 'data': data, 'layers': layers}
        else:
            print(f'Error: HTTP {response.status_code}')
            return {'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        print(f'Error: {e}')
        return {'success': False, 'error': str(e)}

def explore_layer_details(server_url, layer_id):
    """Get detailed information about a specific layer."""
    print(f'\n--- Layer {layer_id} Details ---')
    try:
        response = requests.get(f'{server_url}/{layer_id}?f=pjson', verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f'Name: {data.get("name", "Unknown")}')
            print(f'Type: {data.get("type", "Unknown")}')
            print(f'Geometry Type: {data.get("geometryType", "Unknown")}')
            print(f'Description: {data.get("description", "No description")}')
            
            # Show fields
            fields = data.get('fields', [])
            if fields:
                print(f'Fields ({len(fields)}):')
                for field in fields[:10]:  # Show first 10 fields
                    print(f'  - {field["name"]} ({field["type"]}) - {field.get("alias", "")}')
                if len(fields) > 10:
                    print(f'  ... and {len(fields) - 10} more fields')
            
            return data
        else:
            print(f'Error: HTTP {response.status_code}')
            return None
    except Exception as e:
        print(f'Error: {e}')
        return None

if __name__ == "__main__":
    # Map servers to explore
    servers = [
        'https://sige.pr.gov/server/rest/services/MIPR/Reglamentario_va2/MapServer',
        'https://sige.pr.gov/server/rest/services/MIPR/Reglamentario/MapServer'
    ]
    
    print("🔍 Exploring MIPR Reglamentario MapServers for PRAPEC karst layer...")
    
    all_results = {}
    
    for server_url in servers:
        result = explore_mapserver(server_url)
        all_results[server_url] = result
        
        # If successful, explore each layer for more details
        if result['success']:
            for layer in result['layers']:
                # Look for potential karst-related layers
                layer_name = layer['name'].lower()
                if any(keyword in layer_name for keyword in ['prapec', 'karst', 'carso', 'reglament', 'zona']):
                    explore_layer_details(server_url, layer['id'])
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for server_url, result in all_results.items():
        if result['success']:
            print(f"\n{server_url}:")
            print(f"  Total layers: {len(result['layers'])}")
            
            # Look for potential karst layers
            karst_layers = []
            for layer in result['layers']:
                layer_name = layer['name'].lower()
                if any(keyword in layer_name for keyword in ['prapec', 'karst', 'carso']):
                    karst_layers.append(layer)
            
            if karst_layers:
                print(f"  Potential karst layers:")
                for layer in karst_layers:
                    print(f"    [{layer['id']}] {layer['name']}")
            else:
                print(f"  No obvious karst layers found")
        else:
            print(f"\n{server_url}: FAILED - {result['error']}") 