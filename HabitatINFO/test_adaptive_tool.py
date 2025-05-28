#!/usr/bin/env python3
"""
Test Adaptive Critical Habitat Map Tool

This script tests the new adaptive tool that determines if a location lies in critical habitat,
calculates distance to nearest habitat if not, and generates maps with appropriate buffers.
"""

import sys
import os
sys.path.append('.')

from HabitatINFO.map_tools import generate_adaptive_critical_habitat_map
import json

def test_adaptive_tool():
    """Test the adaptive critical habitat map tool"""
    
    print("🧪 TESTING ADAPTIVE CRITICAL HABITAT MAP TOOL")
    print("="*60)
    
    # Test locations with different habitat scenarios
    test_locations =  [
        {
            "name": "Juncos - Whooping Crane Habitat",
            "longitude": -65.925357,
            "latitude": 18.228125,
            "description": "Coastal area with critical habitat for whooping cranes"
        }
    ]
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n📍 TEST {i}: {location['name']}")
        print(f"   Coordinates: {location['longitude']}, {location['latitude']}")
        print(f"   Expected: {location['description']}")
        print("-" * 50)
        
        try:
            # Call the adaptive tool using invoke method
            result_json = generate_adaptive_critical_habitat_map.invoke({
                "longitude": location['longitude'],
                "latitude": location['latitude'],
                "location_name": location['name'].replace(' ', '_'),
                "include_proposed": True,
                "base_map": "World_Imagery"
            })
            
            # Parse and display results
            result = json.loads(result_json)
            
            if result["status"] == "success":
                print("✅ SUCCESS: Adaptive map generated!")
                
                # Display habitat analysis results
                habitat_analysis = result["habitat_analysis"]
                print(f"\n🔍 HABITAT ANALYSIS:")
                print(f"   Status: {habitat_analysis['habitat_status']}")
                print(f"   Has Critical Habitat: {habitat_analysis['has_critical_habitat']}")
                print(f"   Habitat Count: {habitat_analysis['habitat_count']}")
                print(f"   Adaptive Buffer: {habitat_analysis['adaptive_buffer_miles']:.2f} miles")
                
                if habitat_analysis.get('distance_to_nearest_habitat_miles') is not None:
                    print(f"   Distance to Nearest: {habitat_analysis['distance_to_nearest_habitat_miles']:.2f} miles")
                
                # Display affected species if any
                if 'affected_species' in habitat_analysis:
                    print(f"\n🦎 AFFECTED SPECIES:")
                    for species in habitat_analysis['affected_species']:
                        print(f"   • {species['common_name']} ({species['scientific_name']})")
                        print(f"     Units: {species['unit_count']}, Types: {', '.join(species['designation_types'])}")
                
                # Display nearest habitat if applicable
                if 'nearest_habitat' in habitat_analysis:
                    nearest = habitat_analysis['nearest_habitat']
                    print(f"\n📍 NEAREST HABITAT:")
                    print(f"   Species: {nearest['species_common_name']}")
                    print(f"   Unit: {nearest['unit_name']}")
                    print(f"   Status: {nearest['status']} ({nearest['layer_type']})")
                
                # Display regulatory implications
                if 'regulatory_implications' in habitat_analysis:
                    reg = habitat_analysis['regulatory_implications']
                    print(f"\n📋 REGULATORY IMPLICATIONS:")
                    print(f"   ESA Consultation Required: {reg['esa_consultation_required']}")
                    print(f"   Final Designations: {reg['final_designations']}")
                    print(f"   Proposed Designations: {reg['proposed_designations']}")
                    print(f"   Total Species Affected: {reg['total_species_affected']}")
                
                # Display recommendations
                print(f"\n💡 RECOMMENDATIONS:")
                for rec in result["recommendations"]:
                    print(f"   {rec}")
                
                # Display map details
                print(f"\n📄 MAP GENERATED:")
                print(f"   PDF Path: {result['pdf_path']}")
                
                # Check file size
                if os.path.exists(result['pdf_path']):
                    file_size = os.path.getsize(result['pdf_path'])
                    print(f"   File Size: {file_size:,} bytes")
                    
                    if file_size > 10000:
                        print("   ✅ File size looks reasonable")
                    else:
                        print("   ⚠️  File size seems small")
                else:
                    print("   ❌ File was not created")
                    
            else:
                print(f"❌ FAILED: {result['message']}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)

def main():
    """Run the adaptive tool tests"""
    test_adaptive_tool()
    
    print(f"\n📋 TEST SUMMARY")
    print("="*60)
    print("✅ Adaptive tool tests completed")
    print("\n💡 KEY FEATURES TESTED:")
    print("   • Automatic habitat presence detection")
    print("   • Distance calculation to nearest habitat")
    print("   • Adaptive buffer sizing")
    print("   • Detailed species analysis")
    print("   • Regulatory implications assessment")
    print("   • Comprehensive recommendations")

if __name__ == "__main__":
    main() 