#!/usr/bin/env python3
"""
Test the updated critical habitat distance calculation system
"""

import json
from HabitatINFO.map_tools import generate_adaptive_critical_habitat_map, find_nearest_critical_habitat

def test_guajon_distance():
    """Test that we correctly identify Guajon habitat at 1.1 miles"""
    
    print("🧪 TESTING UPDATED CRITICAL HABITAT DISTANCE CALCULATION")
    print("=" * 60)
    
    # Test coordinates in Puerto Rico (Juncos area)
    test_lon, test_lat = -65.925357, 18.228125
    
    print(f"📍 Test location: {test_lon}, {test_lat}")
    print(f"🎯 Expected: Guajon habitat at ~1.1 miles")
    print("-" * 50)
    
    # Test the direct nearest habitat function
    print("🔍 Finding nearest critical habitat...")
    nearest = find_nearest_critical_habitat(test_lon, test_lat, 25)
    
    if nearest:
        print(f"✅ Found nearest habitat:")
        print(f"   Species: {nearest['species_common_name']} ({nearest['species_scientific_name']})")
        print(f"   Distance: {nearest['distance_miles']:.2f} miles")
        print(f"   Species Code: {nearest.get('spcode', 'Unknown')}")
        print(f"   Layer: {nearest['layer_id']} ({nearest['layer_type']})")
        print(f"   Object ID: {nearest['objectid']}")
        print(f"   Geometry: {nearest['geometry_type']}")
        
        # Check if it's the expected Guajon habitat
        if nearest['species_common_name'] == 'Guajon':
            distance_diff = abs(nearest['distance_miles'] - 1.1)
            if distance_diff < 0.5:  # Within 0.5 miles of expected
                print(f"✅ SUCCESS: Found Guajon at {nearest['distance_miles']:.2f} miles (expected ~1.1)")
            else:
                print(f"⚠️  WARNING: Distance {nearest['distance_miles']:.2f} miles differs from expected 1.1 miles")
        else:
            print(f"❌ UNEXPECTED: Found {nearest['species_common_name']} instead of Guajon")
    else:
        print("❌ ERROR: No habitat found within search radius")
    
    print()
    
    # Test the adaptive map generation
    print("🗺️  Testing adaptive map generation...")
    try:
        result_json = generate_adaptive_critical_habitat_map.invoke({
            "longitude": test_lon,
            "latitude": test_lat,
            "location_name": "Guajon_Distance_Test",
            "base_map": "World_Imagery",
            "include_proposed": True,
            "include_legend": True,
            "habitat_transparency": 0.8
        })
        
        result = json.loads(result_json)
        
        if result["status"] == "success":
            habitat_analysis = result["habitat_analysis"]
            print(f"✅ Adaptive map generated successfully!")
            print(f"   Status: {habitat_analysis['habitat_status']}")
            print(f"   Adaptive Buffer: {habitat_analysis['adaptive_buffer_miles']:.2f} miles")
            
            if habitat_analysis.get('distance_to_nearest_habitat_miles'):
                distance = habitat_analysis['distance_to_nearest_habitat_miles']
                print(f"   Distance to Nearest: {distance:.2f} miles")
                
                # Verify the adaptive buffer calculation
                expected_buffer = distance + 1.0
                actual_buffer = habitat_analysis['adaptive_buffer_miles']
                
                if abs(actual_buffer - expected_buffer) < 0.1:
                    print(f"✅ Adaptive buffer calculation correct: {actual_buffer:.2f} miles")
                else:
                    print(f"⚠️  Buffer calculation issue: expected {expected_buffer:.2f}, got {actual_buffer:.2f}")
            
            # Check if we found the right species
            if 'nearest_habitat' in habitat_analysis:
                nearest_info = habitat_analysis['nearest_habitat']['basic_info']
                if nearest_info['species_common_name'] == 'Guajon':
                    print(f"✅ Correct species identified: {nearest_info['species_common_name']}")
                else:
                    print(f"❌ Wrong species: {nearest_info['species_common_name']}")
            
            print(f"   PDF Path: {result['pdf_path']}")
            
        else:
            print(f"❌ Map generation failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Exception during map generation: {e}")
    
    print(f"\n📋 TEST SUMMARY")
    print("=" * 60)
    print("✅ Distance calculation test completed")


if __name__ == "__main__":
    test_guajon_distance() 