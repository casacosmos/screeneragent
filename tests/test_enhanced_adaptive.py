#!/usr/bin/env python3
"""
Test script for enhanced adaptive critical habitat tool
"""

import json
from HabitatINFO.map_tools import generate_adaptive_critical_habitat_map, find_nearest_critical_habitat
import requests

def test_enhanced_adaptive_tool():
    """Test the enhanced adaptive critical habitat mapping tool"""
    
    print("🧪 TESTING ENHANCED ADAPTIVE CRITICAL HABITAT TOOL")
    print("=" * 60)
    
    # Test coordinates in Puerto Rico (Juncos area)
    test_location = {
        "name": "Juncos - Whooping Crane Habitat",
        "longitude": -65.925357,
        "latitude": 18.228125,
        "description": "Coastal area with critical habitat for whooping cranes"
    }
    
    print(f"\n📍 TEST: {test_location['name']}")
    print(f"   Coordinates: {test_location['longitude']}, {test_location['latitude']}")
    print(f"   Expected: {test_location['description']}")
    print("-" * 50)
    
    # First, let's specifically search for Guajon habitat
    print("🦎 Searching specifically for Guajon habitat...")
    guajon_habitats = search_for_species(test_location['longitude'], test_location['latitude'], "Guajon", 50)
    
    if guajon_habitats:
        print(f"✅ Found {len(guajon_habitats)} Guajon habitat(s):")
        for i, habitat in enumerate(guajon_habitats, 1):
            print(f"   {i}. {habitat['species_common_name']} ({habitat['species_scientific_name']})")
            print(f"      Distance: {habitat['distance_miles']:.2f} miles")
            print(f"      Unit: {habitat['unit_name']}")
            print(f"      Status: {habitat['status']} ({habitat['layer_type']})")
            print(f"      Layer: {habitat['layer_id']}, Object ID: {habitat['objectid']}")
            print(f"      Species Code: {habitat['spcode']}")
            print(f"      Geometry: {habitat['geometry_type']}")
            print()
    else:
        print("❌ No Guajon habitat found within 50 miles")
    
    # Also search for Eleutherodactylus cooki
    print("🔬 Searching by scientific name: Eleutherodactylus cooki...")
    cooki_habitats = search_for_species(test_location['longitude'], test_location['latitude'], "Eleutherodactylus cooki", 50)
    
    if cooki_habitats:
        print(f"✅ Found {len(cooki_habitats)} Eleutherodactylus cooki habitat(s):")
        for i, habitat in enumerate(cooki_habitats, 1):
            print(f"   {i}. {habitat['species_common_name']} ({habitat['species_scientific_name']})")
            print(f"      Distance: {habitat['distance_miles']:.2f} miles")
            print(f"      Layer: {habitat['layer_id']} ({habitat['layer_type']})")
            print(f"      Geometry: {habitat['geometry_type']}")
            print()
    else:
        print("❌ No Eleutherodactylus cooki habitat found within 50 miles")
    
    # Search for all nearby habitats within 10 miles
    print("\n🔍 Searching for ALL nearby critical habitats within 10 miles...")
    all_nearby = find_all_nearby_habitats(test_location['longitude'], test_location['latitude'], 10)
    
    if all_nearby:
        print(f"📊 Found {len(all_nearby)} nearby habitat(s):")
        for i, habitat in enumerate(all_nearby[:10], 1):  # Show top 10
            print(f"   {i}. {habitat['species_common_name']} ({habitat['species_scientific_name']})")
            print(f"      Distance: {habitat['distance_miles']:.2f} miles")
            print(f"      Unit: {habitat['unit_name']}")
            print(f"      Status: {habitat['status']} ({habitat['layer_type']})")
            print(f"      Layer: {habitat['layer_id']}, Object ID: {habitat['objectid']}")
            print(f"      Species Code: {habitat['spcode']}")
            print()
    else:
        print("❌ No nearby habitats found within 10 miles")
        print("🔍 Let's try a larger search radius...")
        
        # Try 25 miles
        all_nearby_25 = find_all_nearby_habitats(test_location['longitude'], test_location['latitude'], 25)
        if all_nearby_25:
            print(f"📊 Found {len(all_nearby_25)} habitat(s) within 25 miles:")
            for i, habitat in enumerate(all_nearby_25[:5], 1):  # Show top 5
                print(f"   {i}. {habitat['species_common_name']} ({habitat['species_scientific_name']})")
                print(f"      Distance: {habitat['distance_miles']:.2f} miles")
                print(f"      Species Code: {habitat['spcode']}")
                print()
        else:
            print("❌ No habitats found even within 25 miles")
    
    # Test the direct nearest habitat function
    print("\n🔍 Testing direct nearest habitat search...")
    nearest = find_nearest_critical_habitat(test_location['longitude'], test_location['latitude'], 25)
    if nearest:
        print(f"📍 Direct search found: {nearest['species_common_name']}")
        print(f"   Distance: {nearest['distance_miles']:.2f} miles")
        print(f"   Species Code: {nearest.get('spcode', 'Unknown')}")
        print(f"   Layer: {nearest['layer_id']} ({nearest['layer_type']})")
    else:
        print("❌ Direct search found no habitat")
    
    # Now test the adaptive tool using proper invoke method
    try:
        print("\n🗺️  Testing adaptive map generation...")
        result_json = generate_adaptive_critical_habitat_map.invoke({
            "longitude": test_location['longitude'],
            "latitude": test_location['latitude'],
            "location_name": test_location['name'],
            "base_map": "World_Imagery",
            "include_proposed": True,
            "include_legend": True,
            "habitat_transparency": 0.8
        })
        
        result = json.loads(result_json)
        
        if result["status"] == "success":
            print("✅ SUCCESS: Enhanced adaptive map generated!")
            
            # Display habitat analysis
            habitat_analysis = result["habitat_analysis"]
            print(f"\n🔍 HABITAT ANALYSIS:")
            print(f"   Status: {habitat_analysis['habitat_status']}")
            print(f"   Has Critical Habitat: {habitat_analysis['has_critical_habitat']}")
            print(f"   Adaptive Buffer: {habitat_analysis['adaptive_buffer_miles']:.2f} miles")
            if habitat_analysis.get('distance_to_nearest_habitat_miles'):
                print(f"   Distance to Nearest: {habitat_analysis['distance_to_nearest_habitat_miles']:.2f} miles")
            
            # Display nearest habitat details if available
            if 'nearest_habitat' in habitat_analysis:
                nearest = habitat_analysis['nearest_habitat']['basic_info']
                print(f"\n📍 DETAILED NEAREST HABITAT ANALYSIS:")
                print(f"   Species: {nearest['species_common_name']}")
                print(f"   Scientific Name: {nearest['species_scientific_name']}")
                print(f"   Unit: {nearest['unit_name']}")
                print(f"   Status: {nearest['status']}")
                print(f"   Type: {nearest['layer_type']}")
                print(f"   Object ID: {nearest['objectid']}")
                
                # Show detailed attributes if available
                if 'detailed_analysis' in habitat_analysis['nearest_habitat']:
                    detailed = habitat_analysis['nearest_habitat']['detailed_analysis']
                    if 'habitat_attributes' in detailed:
                        attrs = detailed['habitat_attributes']
                        print(f"\n🔬 DETAILED HABITAT ATTRIBUTES:")
                        for key, value in attrs.items():
                            if value and value != 'Unknown':
                                print(f"     {key.replace('_', ' ').title()}: {value}")
                    
                    if 'geometry_details' in detailed:
                        geom = detailed['geometry_details']
                        print(f"\n📐 GEOMETRY DETAILS:")
                        for key, value in geom.items():
                            if key != 'note':
                                print(f"     {key.replace('_', ' ').title()}: {value}")
                        if 'note' in geom:
                            print(f"     Note: {geom['note']}")
            
            # Show map details
            pdf_path = result["pdf_path"]
            print(f"\n📄 MAP GENERATED:")
            print(f"   PDF Path: {pdf_path}")
            
            # Check file size
            import os
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"   File Size: {file_size:,} bytes")
                if file_size > 100000:  # > 100KB
                    print("   ✅ File size looks reasonable")
                else:
                    print("   ⚠️  File size seems small - check content")
            else:
                print("   ❌ PDF file not found")
                
        else:
            print(f"❌ ERROR: {result['message']}")
            if 'error' in result:
                print(f"   Details: {result['error']}")
                
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n📋 TEST SUMMARY")
    print("=" * 60)
    print("✅ Enhanced adaptive tool test completed")


def search_for_species(longitude: float, latitude: float, species_name: str, search_radius_miles: float = 50):
    """Search for specific species habitat by name"""
    
    habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
    session = requests.Session()
    session.headers.update({'User-Agent': 'CriticalHabitatFinder/1.0'})
    
    # Convert search radius to degrees (approximate)
    search_radius_degrees = search_radius_miles / 69.0
    
    # Create search envelope
    envelope = {
        "xmin": longitude - search_radius_degrees,
        "ymin": latitude - search_radius_degrees,
        "xmax": longitude + search_radius_degrees,
        "ymax": latitude + search_radius_degrees,
        "spatialReference": {"wkid": 4326}
    }
    
    species_habitats = []
    
    # Search in all habitat layers
    for layer_id in [0, 1, 2, 3]:
        try:
            # Search by species name in common name or scientific name
            where_clause = f"comname LIKE '%{species_name}%' OR sciname LIKE '%{species_name}%'"
            
            params = {
                "where": where_clause,
                "geometry": json.dumps(envelope),
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "true",
                "f": "json"
            }
            
            print(f"   Searching layer {layer_id} for '{species_name}'...")
            response = session.get(f"{habitat_service_url}/{layer_id}/query", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                print(f"   Layer {layer_id}: {len(features)} features found")
                
                for feature in features:
                    geometry = feature.get('geometry', {})
                    attributes = feature.get('attributes', {})
                    
                    # Calculate approximate distance to feature centroid
                    if 'rings' in geometry and geometry['rings']:
                        # For polygons, use first point of first ring as approximation
                        first_ring = geometry['rings'][0]
                        if first_ring:
                            approx_lon, approx_lat = first_ring[0][0], first_ring[0][1]
                    elif 'paths' in geometry and geometry['paths']:
                        # For lines, use first point of first path
                        first_path = geometry['paths'][0]
                        if first_path:
                            approx_lon, approx_lat = first_path[0][0], first_path[0][1]
                    else:
                        continue
                    
                    # Calculate distance using Haversine
                    from HabitatINFO.map_tools import calculate_distance_miles
                    distance = calculate_distance_miles(longitude, latitude, approx_lon, approx_lat)
                    
                    if distance <= search_radius_miles:
                        # Determine layer type
                        layer_type = "Final" if layer_id in [0, 1] else "Proposed"
                        geometry_type = "Polygon" if 'rings' in geometry else "Linear"
                        
                        habitat_info = {
                            "distance_miles": distance,
                            "species_common_name": attributes.get('comname', 'Unknown'),
                            "species_scientific_name": attributes.get('sciname', 'Unknown'),
                            "unit_name": attributes.get('unitname', 'Unknown'),
                            "status": attributes.get('status', 'Unknown'),
                            "layer_type": layer_type,
                            "geometry_type": geometry_type,
                            "layer_id": layer_id,
                            "objectid": attributes.get('OBJECTID'),
                            "spcode": attributes.get('spcode', 'Unknown'),
                            "fedreg": attributes.get('fedreg', 'Unknown'),
                            "pubdate": attributes.get('pubdate', 'Unknown')
                        }
                        
                        species_habitats.append(habitat_info)
                        
            else:
                print(f"   Layer {layer_id}: HTTP {response.status_code}")
                        
        except Exception as e:
            print(f"⚠️  Error searching layer {layer_id}: {e}")
            continue
    
    # Sort by distance
    species_habitats.sort(key=lambda x: x['distance_miles'])
    return species_habitats


def find_all_nearby_habitats(longitude: float, latitude: float, search_radius_miles: float = 10):
    """Find all critical habitat areas within a given radius"""
    
    habitat_service_url = "https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/USFWS_Critical_Habitat/FeatureServer"
    session = requests.Session()
    session.headers.update({'User-Agent': 'CriticalHabitatFinder/1.0'})
    
    # Convert search radius to degrees (approximate)
    search_radius_degrees = search_radius_miles / 69.0
    
    # Create search envelope
    envelope = {
        "xmin": longitude - search_radius_degrees,
        "ymin": latitude - search_radius_degrees,
        "xmax": longitude + search_radius_degrees,
        "ymax": latitude + search_radius_degrees,
        "spatialReference": {"wkid": 4326}
    }
    
    all_habitats = []
    
    print(f"🔍 Searching envelope: {envelope}")
    
    # Search in all habitat layers
    for layer_id in [0, 1, 2, 3]:
        try:
            params = {
                "geometry": json.dumps(envelope),
                "geometryType": "esriGeometryEnvelope",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "true",
                "f": "json"
            }
            
            print(f"   Searching layer {layer_id}...")
            response = session.get(f"{habitat_service_url}/{layer_id}/query", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                print(f"   Layer {layer_id}: {len(features)} features found")
                
                for feature in features:
                    geometry = feature.get('geometry', {})
                    attributes = feature.get('attributes', {})
                    
                    # Calculate approximate distance to feature centroid
                    if 'rings' in geometry and geometry['rings']:
                        # For polygons, use first point of first ring as approximation
                        first_ring = geometry['rings'][0]
                        if first_ring:
                            approx_lon, approx_lat = first_ring[0][0], first_ring[0][1]
                    elif 'paths' in geometry and geometry['paths']:
                        # For lines, use first point of first path
                        first_path = geometry['paths'][0]
                        if first_path:
                            approx_lon, approx_lat = first_path[0][0], first_path[0][1]
                    else:
                        continue
                    
                    # Calculate distance using Haversine
                    from HabitatINFO.map_tools import calculate_distance_miles
                    distance = calculate_distance_miles(longitude, latitude, approx_lon, approx_lat)
                    
                    if distance <= search_radius_miles:
                        # Determine layer type
                        layer_type = "Final" if layer_id in [0, 1] else "Proposed"
                        geometry_type = "Polygon" if 'rings' in geometry else "Linear"
                        
                        habitat_info = {
                            "distance_miles": distance,
                            "species_common_name": attributes.get('comname', 'Unknown'),
                            "species_scientific_name": attributes.get('sciname', 'Unknown'),
                            "unit_name": attributes.get('unitname', 'Unknown'),
                            "status": attributes.get('status', 'Unknown'),
                            "layer_type": layer_type,
                            "geometry_type": geometry_type,
                            "layer_id": layer_id,
                            "objectid": attributes.get('OBJECTID'),
                            "spcode": attributes.get('spcode', 'Unknown'),
                            "fedreg": attributes.get('fedreg', 'Unknown'),
                            "pubdate": attributes.get('pubdate', 'Unknown')
                        }
                        
                        all_habitats.append(habitat_info)
                        
            else:
                print(f"   Layer {layer_id}: HTTP {response.status_code}")
                        
        except Exception as e:
            print(f"⚠️  Error searching layer {layer_id}: {e}")
            continue
    
    # Sort by distance
    all_habitats.sort(key=lambda x: x['distance_miles'])
    return all_habitats


if __name__ == "__main__":
    test_enhanced_adaptive_tool() 