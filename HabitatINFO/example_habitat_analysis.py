#!/usr/bin/env python3
"""
Example Critical Habitat Analysis

This script demonstrates how to use the HabitatINFO tools to analyze locations
for critical habitat intersections and search for species habitat information.
"""

import sys
import os
import json
from datetime import datetime

# Add the parent directory to the path to import HabitatINFO modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from HabitatINFO.tools import analyze_critical_habitat, search_species_habitat

def test_location_analysis():
    """Test critical habitat analysis for various locations"""
    
    print("🌿 CRITICAL HABITAT LOCATION ANALYSIS")
    print("="*80)
    
    # Test locations across different regions
    test_locations = [
        {
            "name": "San Francisco Bay Area, CA",
            "longitude": -122.4194,
            "latitude": 37.7749,
            "description": "Urban area with potential endangered species habitat"
        },
        {
            "name": "Everglades, Florida",
            "longitude": -80.9326,
            "latitude": 25.4663,
            "description": "Known habitat for multiple endangered species"
        },
        {
            "name": "Pacific Northwest Coast, WA",
            "longitude": -124.1077,
            "latitude": 47.9073,
            "description": "Marine and coastal habitat area"
        },
        {
            "name": "Great Plains, Kansas",
            "longitude": -98.5795,
            "latitude": 39.8283,
            "description": "Agricultural area with potential grassland species"
        },
        {
            "name": "Puerto Rico",
            "longitude": -66.199399,
            "latitude": 18.408303,
            "description": "Tropical island with endemic species"
        }
    ]
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n📍 TEST {i}: {location['name']}")
        print(f"   Coordinates: {location['longitude']}, {location['latitude']}")
        print(f"   Description: {location['description']}")
        print("-" * 60)
        
        try:
            # Analyze the location using the LangChain tool
            result = analyze_critical_habitat.invoke({
                "longitude": location["longitude"],
                "latitude": location["latitude"],
                "include_proposed": True,
                "buffer_meters": 0
            })
            
            # Parse and display results
            result_data = json.loads(result)
            display_location_results(result_data, location["name"])
            
        except Exception as e:
            print(f"   ❌ Error analyzing location: {e}")
        
        print("\n" + "="*80)

def test_species_search():
    """Test species habitat search functionality"""
    
    print("\n🔍 SPECIES HABITAT SEARCH")
    print("="*80)
    
    # Test species searches
    test_species = [
        {
            "name": "salmon",
            "search_type": "common",
            "description": "Search for salmon species critical habitat"
        },
        {
            "name": "sea turtle",
            "search_type": "common", 
            "description": "Search for sea turtle critical habitat"
        },
        {
            "name": "Strix occidentalis",
            "search_type": "scientific",
            "description": "Northern Spotted Owl by scientific name"
        },
        {
            "name": "manatee",
            "search_type": "common",
            "description": "Search for manatee critical habitat"
        }
    ]
    
    for i, species in enumerate(test_species, 1):
        print(f"\n🐾 SPECIES SEARCH {i}: {species['name']}")
        print(f"   Search Type: {species['search_type']}")
        print(f"   Description: {species['description']}")
        print("-" * 60)
        
        try:
            # Search for species habitat using the LangChain tool
            result = search_species_habitat.invoke({
                "species_name": species["name"],
                "search_type": species["search_type"]
            })
            
            # Parse and display results
            result_data = json.loads(result)
            display_species_results(result_data, species["name"])
            
        except Exception as e:
            print(f"   ❌ Error searching for species: {e}")
        
        print("\n" + "="*80)

def display_location_results(result_data: dict, location_name: str):
    """Display formatted results for location analysis"""
    
    analysis = result_data.get("critical_habitat_analysis", {})
    status = analysis.get("status", "unknown")
    
    if status == "error":
        print(f"   ❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
        return
    
    if status == "no_critical_habitat":
        print(f"   ✅ No critical habitat found at {location_name}")
        print(f"   📋 Regulatory Status: {analysis.get('regulatory_status', 'N/A')}")
        return
    
    if status == "critical_habitat_found":
        print(f"   ⚠️  CRITICAL HABITAT FOUND at {location_name}")
        
        # Display summary
        summary = analysis.get("summary", {})
        print(f"   📊 Summary:")
        print(f"      • Total habitat areas: {summary.get('total_habitat_areas', 0)}")
        print(f"      • Unique species: {summary.get('unique_species', 0)}")
        print(f"      • Final designations: {summary.get('final_designations', 0)}")
        print(f"      • Proposed designations: {summary.get('proposed_designations', 0)}")
        
        # Display affected species
        species_list = analysis.get("affected_species", [])
        if species_list:
            print(f"   🐾 Affected Species:")
            for species in species_list[:3]:  # Show first 3 species
                print(f"      • {species.get('common_name', 'Unknown')}")
                print(f"        Scientific: {species.get('scientific_name', 'Unknown')}")
                print(f"        Units: {species.get('unit_count', 0)}")
                print(f"        Types: {', '.join(species.get('designation_types', []))}")
            
            if len(species_list) > 3:
                print(f"      ... and {len(species_list) - 3} more species")
        
        # Display key recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"   💡 Key Recommendations:")
            for rec in recommendations[:2]:  # Show first 2 recommendations
                print(f"      • {rec}")

def display_species_results(result_data: dict, species_name: str):
    """Display formatted results for species search"""
    
    search_result = result_data.get("species_habitat_search", {})
    status = search_result.get("status", "unknown")
    
    if status == "error":
        print(f"   ❌ Search failed: {search_result.get('message', 'Unknown error')}")
        return
    
    if status == "no_habitat_found":
        print(f"   ❌ No critical habitat found for '{species_name}'")
        suggestions = search_result.get("suggestions", [])
        if suggestions:
            print(f"   💡 Suggestions:")
            for suggestion in suggestions[:2]:
                print(f"      • {suggestion}")
        return
    
    if status == "habitat_found":
        print(f"   ✅ CRITICAL HABITAT FOUND for '{species_name}'")
        
        # Display summary
        summary = search_result.get("summary", {})
        print(f"   📊 Summary:")
        print(f"      • Species found: {summary.get('species_found', 0)}")
        print(f"      • Total habitat areas: {summary.get('total_habitat_areas', 0)}")
        print(f"      • Habitat units: {summary.get('unique_habitat_units', 0)}")
        print(f"      • Final designations: {summary.get('final_designations', 0)}")
        print(f"      • Proposed designations: {summary.get('proposed_designations', 0)}")
        
        # Display species details
        species_details = search_result.get("species_details", [])
        if species_details:
            print(f"   🐾 Species Details:")
            for species in species_details[:2]:  # Show first 2 species
                print(f"      • {species.get('common_name', 'Unknown')}")
                print(f"        Scientific: {species.get('scientific_name', 'Unknown')}")
                print(f"        Habitat units: {species.get('unit_count', 0)}")
                print(f"        Final: {species.get('final_designations', 0)}, "
                      f"Proposed: {species.get('proposed_designations', 0)}")
            
            if len(species_details) > 2:
                print(f"      ... and {len(species_details) - 2} more species")

def test_buffer_analysis():
    """Test habitat analysis with buffer zones"""
    
    print("\n🎯 BUFFER ZONE ANALYSIS")
    print("="*80)
    
    # Test location near potential habitat
    test_location = {
        "name": "Coastal California",
        "longitude": -121.8947,
        "latitude": 36.6002
    }
    
    buffer_distances = [0, 100, 500, 1000]  # meters
    
    for buffer_m in buffer_distances:
        print(f"\n📏 Testing {buffer_m}m buffer around {test_location['name']}")
        print("-" * 40)
        
        try:
            result = analyze_critical_habitat.invoke({
                "longitude": test_location["longitude"],
                "latitude": test_location["latitude"],
                "include_proposed": True,
                "buffer_meters": buffer_m
            })
            
            result_data = json.loads(result)
            analysis = result_data.get("critical_habitat_analysis", {})
            
            if analysis.get("status") == "critical_habitat_found":
                summary = analysis.get("summary", {})
                print(f"   ✅ Found {summary.get('total_habitat_areas', 0)} habitat areas")
                print(f"   🐾 {summary.get('unique_species', 0)} species affected")
            else:
                print(f"   ❌ No critical habitat found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Main demonstration function"""
    
    print("🌿 CRITICAL HABITAT ANALYSIS DEMONSTRATION")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("This script demonstrates the HabitatINFO tools for analyzing")
    print("critical habitat areas and species protection status.")
    print("="*80)
    
    try:
        # Test location analysis
        test_location_analysis()
        
        # Test species search
        test_species_search()
        
        # Test buffer analysis
        test_buffer_analysis()
        
        print(f"\n✅ DEMONSTRATION COMPLETE")
        print("="*80)
        print("💡 The HabitatINFO tools are ready for use in your applications!")
        print("   • Use analyze_critical_habitat for location-based analysis")
        print("   • Use search_species_habitat for species-based searches")
        print("   • Both tools provide comprehensive regulatory guidance")
        
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    main() 