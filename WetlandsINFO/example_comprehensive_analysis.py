#!/usr/bin/env python3
"""
Example Usage of Comprehensive Wetland Analysis Tool

This script demonstrates how to use the comprehensive wetland analysis tool
that combines wetland data querying and adaptive map generation.
"""

import sys
import os
from pprint import pprint

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from wetland_analysis_tool import analyze_wetland_location_with_map

def run_example_analysis():
    """Run example wetland analysis for different scenarios"""
    
    print("🌿 Comprehensive Wetland Analysis Tool - Examples")
    print("=" * 70)
    
    # Example coordinates for different scenarios
    test_locations = [
        {
            "name": "Puerto Rico Coastal Area",
            "longitude": -66.199399,
            "latitude": 18.408303,
            "description": "Coastal area in Puerto Rico - likely to have wetlands"
        },
        {
            "name": "Florida Everglades",
            "longitude": -80.8,
            "latitude": 25.5,
            "description": "Everglades area - high wetland density"
        },
        {
            "name": "Urban Area Example",
            "longitude": -74.006,
            "latitude": 40.7128,
            "description": "New York City area - minimal wetlands expected"
        }
    ]
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n📍 Example {i}: {location['name']}")
        print(f"   Description: {location['description']}")
        print(f"   Coordinates: ({location['longitude']}, {location['latitude']})")
        print("-" * 50)
        
        try:
            # Run comprehensive analysis
            result = analyze_wetland_location_with_map(
                longitude=location['longitude'],
                latitude=location['latitude'],
                location_name=location['name']
            )
            
            # Display key results
            print("📊 ANALYSIS RESULTS:")
            print(f"   Location: {result['location_analysis']['location']}")
            print(f"   In Wetland: {result['location_analysis']['is_in_wetland']}")
            print(f"   Wetlands Found: {result['location_analysis']['total_wetlands_found']}")
            
            if result['wetlands_in_radius']['wetlands']:
                print(f"   Wetlands in 0.5-mile radius: {result['wetlands_in_radius']['wetlands_count']}")
                
                # Show first few wetlands
                for j, wetland in enumerate(result['wetlands_in_radius']['wetlands'][:3], 1):
                    print(f"     {j}. {wetland['wetland_type']} - {wetland['distance_miles']:.2f} miles {wetland['bearing']}")
                    print(f"        NWI Code: {wetland['nwi_code']}")
                    print(f"        Regulatory: {wetland['regulatory_significance']}")
            
            print(f"\n🗺️  MAP GENERATION:")
            if result['map_generation']['success']:
                print(f"   Status: ✅ Success")
                print(f"   File: {result['map_generation']['filename']}")
                print(f"   Buffer: {result['map_generation']['adaptive_settings']['buffer_miles']} miles")
                print(f"   Reasoning: {result['map_generation']['adaptive_settings']['reasoning']}")
            else:
                print(f"   Status: ❌ Failed")
                print(f"   Error: {result['map_generation']['message']}")
            
            print(f"\n⚖️  REGULATORY ASSESSMENT:")
            print(f"   Risk Level: {result['regulatory_assessment']['immediate_impact_risk']}")
            print(f"   Complexity: {result['analysis_summary']['regulatory_complexity']}")
            
            print(f"\n💡 TOP RECOMMENDATIONS:")
            for rec in result['recommendations'][:3]:
                print(f"   • {rec}")
            
            if len(result['recommendations']) > 3:
                print(f"   ... and {len(result['recommendations']) - 3} more recommendations")
                
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
        
        print("\n" + "=" * 70)

def run_single_analysis():
    """Run analysis for a single location with full output"""
    
    print("\n🔍 DETAILED SINGLE LOCATION ANALYSIS")
    print("=" * 70)
    
    # Example coordinates (you can modify these)
    longitude = -66.199399
    latitude = 18.408303
    location_name = "Puerto Rico Test Site"
    
    print(f"Analyzing: {location_name}")
    print(f"Coordinates: ({longitude}, {latitude})")
    print("-" * 50)
    
    try:
        result = analyze_wetland_location_with_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        print("\n📋 COMPLETE ANALYSIS RESULTS:")
        print("=" * 50)
        pprint(result, width=80, depth=3)
        
    except Exception as e:
        print(f"❌ Error during detailed analysis: {str(e)}")

if __name__ == "__main__":
    print("🌿 Comprehensive Wetland Analysis Tool - Example Usage")
    print("This script demonstrates the comprehensive wetland analysis tool")
    print("that combines data querying and adaptive map generation.\n")
    
    # Run examples
    run_example_analysis()
    
    # Uncomment the line below to run detailed single analysis
    # run_single_analysis()
    
    print("\n✅ Example analysis completed!")
    print("\nTo use this tool in your own code:")
    print("  from wetland_analysis_tool import analyze_wetland_location_with_map")
    print("  result = analyze_wetland_location_with_map(longitude, latitude, location_name)") 