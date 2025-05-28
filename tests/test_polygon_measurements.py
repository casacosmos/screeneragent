#!/usr/bin/env python3
"""
Comprehensive test for polygon distance measurements
Tests all polygon types to ensure consistent distance calculations
"""

import json
from HabitatINFO.map_tools import find_nearest_critical_habitat, generate_adaptive_critical_habitat_map

def test_multiple_polygon_types():
    """Test distance calculations for different polygon types and locations"""
    
    print("🧪 COMPREHENSIVE POLYGON DISTANCE MEASUREMENT TEST")
    print("=" * 70)
    
    # Test locations with different expected habitat types
    test_locations = [
        {
            "name": "Puerto Rico - Guajon (Polygon)",
            "lon": -65.925357,
            "lat": 18.228125,
            "expected_species": "Guajon",
            "expected_geometry": "Polygon",
            "expected_distance_range": (1.0, 1.2)
        },
        {
            "name": "Texas Coast - Whooping Crane (Polygon)",
            "lon": -96.7970,
            "lat": 28.1595,
            "expected_species": "Whooping crane",
            "expected_geometry": "Polygon",
            "expected_distance_range": (0.0, 0.5)  # Should be within habitat
        },
        {
            "name": "Colorado River - Razorback Sucker (Linear/Polygon)",
            "lon": -114.0719,
            "lat": 36.1699,
            "expected_species": "Razorback sucker",
            "expected_geometry": ["Polygon", "Linear"],
            "expected_distance_range": (0.0, 2.0)
        },
        {
            "name": "California Coast - Test Location",
            "lon": -118.2437,
            "lat": 34.0522,
            "expected_species": None,  # Unknown what we'll find
            "expected_geometry": None,
            "expected_distance_range": (0.0, 50.0)
        }
    ]
    
    results = []
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n🔍 TEST {i}: {location['name']}")
        print("-" * 50)
        print(f"📍 Coordinates: {location['lon']}, {location['lat']}")
        
        try:
            # Test direct nearest habitat function
            nearest = find_nearest_critical_habitat(location['lon'], location['lat'], 50)
            
            if nearest:
                distance = nearest['distance_miles']
                species = nearest['species_common_name']
                geometry = nearest['geometry_type']
                
                print(f"✅ Found habitat:")
                print(f"   Species: {species}")
                print(f"   Distance: {distance:.2f} miles")
                print(f"   Geometry: {geometry}")
                print(f"   Layer: {nearest['layer_id']} ({nearest['layer_type']})")
                print(f"   Object ID: {nearest['objectid']}")
                
                # Validate expected results
                test_result = {
                    "location": location['name'],
                    "coordinates": [location['lon'], location['lat']],
                    "found_species": species,
                    "found_geometry": geometry,
                    "distance_miles": distance,
                    "layer_info": f"{nearest['layer_id']} ({nearest['layer_type']})",
                    "object_id": nearest['objectid'],
                    "validation": {}
                }
                
                # Check species match
                if location['expected_species']:
                    if location['expected_species'].lower() in species.lower():
                        test_result["validation"]["species_match"] = "✅ PASS"
                        print(f"   ✅ Species match: Expected '{location['expected_species']}', found '{species}'")
                    else:
                        test_result["validation"]["species_match"] = "❌ FAIL"
                        print(f"   ❌ Species mismatch: Expected '{location['expected_species']}', found '{species}'")
                else:
                    test_result["validation"]["species_match"] = "ℹ️  No expectation set"
                
                # Check geometry type
                if location['expected_geometry']:
                    if isinstance(location['expected_geometry'], list):
                        if geometry in location['expected_geometry']:
                            test_result["validation"]["geometry_match"] = "✅ PASS"
                            print(f"   ✅ Geometry match: Found '{geometry}' in expected {location['expected_geometry']}")
                        else:
                            test_result["validation"]["geometry_match"] = "❌ FAIL"
                            print(f"   ❌ Geometry mismatch: Expected {location['expected_geometry']}, found '{geometry}'")
                    else:
                        if geometry == location['expected_geometry']:
                            test_result["validation"]["geometry_match"] = "✅ PASS"
                            print(f"   ✅ Geometry match: Expected and found '{geometry}'")
                        else:
                            test_result["validation"]["geometry_match"] = "❌ FAIL"
                            print(f"   ❌ Geometry mismatch: Expected '{location['expected_geometry']}', found '{geometry}'")
                else:
                    test_result["validation"]["geometry_match"] = "ℹ️  No expectation set"
                
                # Check distance range
                min_dist, max_dist = location['expected_distance_range']
                if min_dist <= distance <= max_dist:
                    test_result["validation"]["distance_range"] = "✅ PASS"
                    print(f"   ✅ Distance in range: {distance:.2f} miles within [{min_dist}, {max_dist}]")
                else:
                    test_result["validation"]["distance_range"] = "⚠️  OUTSIDE RANGE"
                    print(f"   ⚠️  Distance outside range: {distance:.2f} miles not in [{min_dist}, {max_dist}]")
                
                # Test adaptive map generation
                print(f"   🗺️  Testing adaptive map generation...")
                try:
                    map_result_json = generate_adaptive_critical_habitat_map.invoke({
                        "longitude": location['lon'],
                        "latitude": location['lat'],
                        "location_name": f"Test_{i}_{species.replace(' ', '_')}",
                        "base_map": "World_Imagery",
                        "include_proposed": True,
                        "include_legend": True,
                        "habitat_transparency": 0.8
                    })
                    
                    map_result = json.loads(map_result_json)
                    
                    if map_result["status"] == "success":
                        map_distance = map_result["habitat_analysis"].get("distance_to_nearest_habitat_miles")
                        map_buffer = map_result["habitat_analysis"]["adaptive_buffer_miles"]
                        
                        # Verify distance consistency
                        if map_distance is not None:
                            distance_diff = abs(distance - map_distance)
                            if distance_diff < 0.1:
                                test_result["validation"]["map_distance_consistency"] = "✅ PASS"
                                print(f"   ✅ Map distance consistent: {map_distance:.2f} miles")
                            else:
                                test_result["validation"]["map_distance_consistency"] = "❌ INCONSISTENT"
                                print(f"   ❌ Distance inconsistency: Direct={distance:.2f}, Map={map_distance:.2f}")
                        
                        # Verify buffer calculation
                        if map_distance is not None and map_distance > 0:
                            expected_buffer = map_distance + 1.0
                            if abs(map_buffer - expected_buffer) < 0.1:
                                test_result["validation"]["buffer_calculation"] = "✅ PASS"
                                print(f"   ✅ Buffer calculation correct: {map_buffer:.2f} miles")
                            else:
                                test_result["validation"]["buffer_calculation"] = "❌ INCORRECT"
                                print(f"   ❌ Buffer calculation error: Expected {expected_buffer:.2f}, got {map_buffer:.2f}")
                        
                        test_result["map_generation"] = "✅ SUCCESS"
                        test_result["pdf_path"] = map_result["pdf_path"]
                        print(f"   ✅ Map generated: {map_result['pdf_path']}")
                        
                    else:
                        test_result["map_generation"] = "❌ FAILED"
                        test_result["map_error"] = map_result.get("message", "Unknown error")
                        print(f"   ❌ Map generation failed: {map_result.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    test_result["map_generation"] = "❌ EXCEPTION"
                    test_result["map_error"] = str(e)
                    print(f"   ❌ Map generation exception: {e}")
                
            else:
                print(f"❌ No habitat found within 50 miles")
                test_result = {
                    "location": location['name'],
                    "coordinates": [location['lon'], location['lat']],
                    "found_species": None,
                    "distance_miles": None,
                    "validation": {"habitat_found": "❌ NO HABITAT"}
                }
            
            results.append(test_result)
            
        except Exception as e:
            print(f"❌ Exception during test: {e}")
            results.append({
                "location": location['name'],
                "coordinates": [location['lon'], location['lat']],
                "error": str(e),
                "validation": {"test_execution": "❌ EXCEPTION"}
            })
    
    # Summary report
    print(f"\n📊 TEST SUMMARY REPORT")
    print("=" * 70)
    
    total_tests = len(results)
    successful_tests = len([r for r in results if r.get('found_species')])
    
    print(f"Total test locations: {total_tests}")
    print(f"Habitats found: {successful_tests}")
    print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        print(f"\n🔍 {result['location']}:")
        if result.get('found_species'):
            print(f"   Species: {result['found_species']}")
            print(f"   Distance: {result['distance_miles']:.2f} miles")
            print(f"   Geometry: {result['found_geometry']}")
            
            # Validation summary
            validations = result.get('validation', {})
            for check, status in validations.items():
                print(f"   {check}: {status}")
                
            if result.get('pdf_path'):
                print(f"   PDF: {result['pdf_path']}")
        else:
            print(f"   Status: No habitat found or error occurred")
            if result.get('error'):
                print(f"   Error: {result['error']}")
    
    print(f"\n✅ Comprehensive polygon measurement test completed!")
    return results


if __name__ == "__main__":
    test_multiple_polygon_types() 