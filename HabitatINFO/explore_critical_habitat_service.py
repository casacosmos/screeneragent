#!/usr/bin/env python3
"""
Explore Critical Habitat Service for Map Generation

This script explores the USFWS Critical Habitat service to understand its structure,
capabilities, and available print templates for map generation.
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

def explore_critical_habitat_service():
    """Explore the USFWS Critical Habitat service"""
    
    print("🔍 EXPLORING USFWS CRITICAL HABITAT SERVICE FOR MAP GENERATION")
    print("="*80)
    
    # Primary service URL
    service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'CriticalHabitatExplorer/1.0'})
    
    try:
        # Get service metadata
        print(f"\n📊 SERVICE METADATA")
        print("-" * 40)
        response = session.get(f"{service_url}?f=json", timeout=15)
        response.raise_for_status()
        service_info = response.json()
        
        print(f"✅ Service accessible")
        print(f"Description: {service_info.get('serviceDescription', 'N/A')[:200]}...")
        print(f"Capabilities: {service_info.get('capabilities', 'N/A')}")
        print(f"Max Record Count: {service_info.get('maxRecordCount', 'N/A')}")
        print(f"Spatial Reference: {service_info.get('spatialReference', {}).get('wkid', 'N/A')}")
        
        # Explore layers
        layers = service_info.get('layers', [])
        print(f"\n🗂️  LAYERS ({len(layers)} total)")
        print("-" * 40)
        
        for layer in layers:
            layer_id = layer.get('id')
            layer_name = layer.get('name', 'Unknown')
            
            print(f"\n  📋 Layer {layer_id}: {layer_name}")
            print(f"     Type: {layer.get('type', 'Unknown')}")
            print(f"     Geometry: {layer.get('geometryType', 'Unknown')}")
            print(f"     Min Scale: {layer.get('minScale', 'N/A')}")
            print(f"     Max Scale: {layer.get('maxScale', 'N/A')}")
            
            # Get detailed layer info
            try:
                layer_response = session.get(f"{service_url}/{layer_id}?f=json", timeout=10)
                layer_response.raise_for_status()
                layer_info = layer_response.json()
                
                # Show key fields
                fields = layer_info.get('fields', [])
                key_fields = [f for f in fields if any(term in f.get('name', '').lower() 
                                                     for term in ['comname', 'sciname', 'unitname', 'status', 'species'])]
                
                if key_fields:
                    print(f"     Key Fields:")
                    for field in key_fields[:5]:
                        print(f"       • {field.get('name')}: {field.get('type')} - {field.get('alias', '')}")
                
                # Test query to see if layer has data
                test_query_params = {
                    "where": "1=1",
                    "returnCountOnly": "true",
                    "f": "json"
                }
                
                count_response = session.get(f"{service_url}/{layer_id}/query", params=test_query_params, timeout=10)
                if count_response.status_code == 200:
                    count_result = count_response.json()
                    if 'count' in count_result:
                        print(f"     Record Count: {count_result['count']:,}")
                
            except Exception as e:
                print(f"     ❌ Error getting layer details: {e}")
        
        # Check for print/export capabilities
        print(f"\n🖨️  PRINT/EXPORT CAPABILITIES")
        print("-" * 40)
        
        # Look for export web map service
        export_services = [
            "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/ExportWebMap/GPServer/Export%20Web%20Map",
            "https://utility.arcgisonline.com/arcgis/rest/services/Utilities/PrintingTools/GPServer/Export%20Web%20Map%20Task",
            "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map"
        ]
        
        working_export_service = None
        for export_url in export_services:
            try:
                print(f"Testing export service: {export_url}")
                export_response = session.get(f"{export_url}?f=json", timeout=10)
                if export_response.status_code == 200:
                    export_info = export_response.json()
                    if 'error' not in export_info:
                        print(f"  ✅ Export service available")
                        working_export_service = export_url
                        
                        # Check parameters
                        if 'parameters' in export_info:
                            print(f"  📋 Parameters available:")
                            for param in export_info['parameters'][:5]:
                                print(f"    • {param.get('name')}: {param.get('dataType')}")
                        break
                    else:
                        print(f"  ❌ Service error: {export_info.get('error', {}).get('message', 'Unknown')}")
                else:
                    print(f"  ❌ HTTP {export_response.status_code}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        if working_export_service:
            print(f"\n✅ Found working export service: {working_export_service}")
        else:
            print(f"\n⚠️  No working export service found - will use alternative approach")
        
        # Test sample query
        print(f"\n🧪 TESTING SAMPLE QUERIES")
        print("-" * 40)
        
        # Test coordinates (San Francisco Bay Area)
        test_coords = {"x": -122.4194, "y": 37.7749, "spatialReference": {"wkid": 4326}}
        
        for layer in layers[:2]:  # Test first 2 layers
            layer_id = layer.get('id')
            layer_name = layer.get('name', 'Unknown')
            
            try:
                query_params = {
                    "geometry": json.dumps(test_coords),
                    "geometryType": "esriGeometryPoint",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "*",
                    "returnGeometry": "false",
                    "returnCountOnly": "true",
                    "f": "json"
                }
                
                query_response = session.get(f"{service_url}/{layer_id}/query", params=query_params, timeout=10)
                query_response.raise_for_status()
                query_result = query_response.json()
                
                if 'error' not in query_result:
                    count = query_result.get('count', 0)
                    print(f"  Layer {layer_id} ({layer_name}): {count} features at test location")
                else:
                    print(f"  Layer {layer_id}: Query failed - {query_result['error']}")
                    
            except Exception as e:
                print(f"  Layer {layer_id}: Error - {e}")
        
        return {
            'service_url': service_url,
            'working_export_service': working_export_service,
            'layers': layers,
            'service_info': service_info
        }
        
    except Exception as e:
        print(f"❌ Error exploring service: {e}")
        return None

def main():
    """Main exploration function"""
    result = explore_critical_habitat_service()
    
    if result:
        print(f"\n📋 SUMMARY FOR MAP GENERATION")
        print("="*80)
        print(f"✅ Primary Service: {result['service_url']}")
        print(f"✅ Export Service: {result.get('working_export_service', 'None found')}")
        print(f"✅ Available Layers: {len(result['layers'])}")
        
        print(f"\n💡 RECOMMENDED APPROACH:")
        if result.get('working_export_service'):
            print("   1. Use ArcGIS Export Web Map service for PDF generation")
            print("   2. Create Web Map JSON with critical habitat layers")
            print("   3. Include base map and location markers")
            print("   4. Use standard print templates")
        else:
            print("   1. Use alternative map generation approach")
            print("   2. Query critical habitat data directly")
            print("   3. Create custom map visualization")
            print("   4. Export as image or PDF using other tools")
        
        print(f"\n🗂️  LAYER CONFIGURATION:")
        for layer in result['layers']:
            print(f"   • Layer {layer.get('id')}: {layer.get('name')}")
    else:
        print(f"\n❌ Service exploration failed")

if __name__ == "__main__":
    main() 