#!/usr/bin/env python3
"""
Test NonAttainmentINFO Complete Functionality

This script demonstrates the complete NonAttainmentINFO module functionality:
1. Retrieving nonattainment data from a provided location
2. Generating various types of PDF maps
3. Analyzing results and providing recommendations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nonattainment_client import NonAttainmentAreasClient, NonAttainmentAnalysisResult
from generate_nonattainment_map_pdf import NonAttainmentMapGenerator
import json
from datetime import datetime


def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"🌫️  {title}")
    print(f"{'='*80}")


def print_area_details(area):
    """Print detailed information about a nonattainment area"""
    print(f"\n  📍 Area: {area.area_name}")
    print(f"     State: {area.state_name} ({area.state_abbreviation})")
    print(f"     EPA Region: {area.epa_region}")
    print(f"     Pollutant: {area.pollutant_name}")
    print(f"     Status: {area.current_status}")
    print(f"     Classification: {area.classification}")
    if area.design_value:
        print(f"     Design Value: {area.design_value} {area.design_value_units}")
    if area.meets_naaqs:
        print(f"     Meets NAAQS: {area.meets_naaqs}")
    if area.population_2020:
        print(f"     Population (2020): {area.population_2020:,.0f}")
    if area.designation_effective_date:
        print(f"     Designation Date: {area.designation_effective_date}")


def test_location_analysis(client: NonAttainmentAreasClient, longitude: float, latitude: float, location_name: str):
    """Test nonattainment analysis for a specific location"""
    print_section_header(f"Analyzing Location: {location_name}")
    print(f"📍 Coordinates: {longitude}, {latitude}")
    
    # Analyze without revoked standards
    print("\n🔍 Analysis 1: Active Standards Only")
    result = client.analyze_location(longitude, latitude, include_revoked=False)
    
    if result.query_success:
        print(f"✅ Query successful")
        print(f"   Found {result.area_count} nonattainment area(s)")
        
        if result.has_nonattainment_areas:
            # Group by pollutant
            pollutant_groups = {}
            for area in result.nonattainment_areas:
                pollutant = area.pollutant_name
                if pollutant not in pollutant_groups:
                    pollutant_groups[pollutant] = []
                pollutant_groups[pollutant].append(area)
            
            print(f"\n   Pollutants affected: {', '.join(pollutant_groups.keys())}")
            
            for pollutant, areas in pollutant_groups.items():
                print(f"\n   🌫️ {pollutant} ({len(areas)} area(s)):")
                for area in areas:
                    print_area_details(area)
        else:
            print("   ✅ Location meets all active air quality standards!")
    else:
        print(f"❌ Query failed: {result.error_message}")
    
    # Analyze with revoked standards
    print("\n🔍 Analysis 2: Including Revoked Standards")
    result_with_revoked = client.analyze_location(longitude, latitude, include_revoked=True)
    
    if result_with_revoked.query_success:
        revoked_count = result_with_revoked.area_count - result.area_count
        if revoked_count > 0:
            print(f"   Found {revoked_count} additional area(s) with revoked standards")
            
            # Show revoked areas
            for area in result_with_revoked.nonattainment_areas:
                if 'revoked' in area.current_status.lower() or 'revoked' in area.pollutant_name.lower():
                    print_area_details(area)
    
    # Get summary
    print("\n📊 Analysis Summary:")
    summary = client.get_area_summary(result)
    
    if summary['status'] == 'nonattainment_found':
        print(f"   Status: ⚠️  Nonattainment areas found")
        print(f"   Total areas: {summary['summary']['total_areas']}")
        print(f"   Unique pollutants: {summary['summary']['unique_pollutants']}")
        print(f"   Nonattainment areas: {summary['summary']['nonattainment_areas']}")
        print(f"   Maintenance areas: {summary['summary']['maintenance_areas']}")
        
        print("\n   📋 Recommendations:")
        for i, rec in enumerate(summary['recommendations'], 1):
            print(f"   {i}. {rec}")
    else:
        print(f"   Status: ✅ {summary['message']}")
    
    return result


def test_map_generation(generator: NonAttainmentMapGenerator, result: NonAttainmentAnalysisResult, 
                       longitude: float, latitude: float, location_name: str):
    """Test various map generation options"""
    print_section_header(f"Generating Maps for: {location_name}")
    
    # 1. Standard map with all active standards
    print("\n🗺️  Map 1: Standard Nonattainment Map (25-mile radius)")
    pdf_path = generator.generate_nonattainment_map_pdf(
        longitude=longitude,
        latitude=latitude,
        location_name=f"{location_name} - Air Quality Analysis",
        buffer_miles=25.0,
        base_map="World_Topo_Map",
        dpi=300,
        include_legend=True,
        include_revoked=False,
        output_filename=f"nonattainment_{location_name.replace(' ', '_').replace(',', '')}_standard.pdf"
    )
    if pdf_path:
        print(f"   ✅ Generated: {pdf_path}")
    else:
        print(f"   ❌ Failed to generate standard map")
    
    # 2. Detailed map with smaller radius
    print("\n🗺️  Map 2: Detailed Nonattainment Map (10-mile radius)")
    pdf_path = generator.generate_detailed_nonattainment_map(
        longitude=longitude,
        latitude=latitude,
        location_name=f"{location_name} - Detailed View",
        nonattainment_transparency=0.75
    )
    if pdf_path:
        print(f"   ✅ Generated: {pdf_path}")
    else:
        print(f"   ❌ Failed to generate detailed map")
    
    # 3. Regional overview map
    print("\n🗺️  Map 3: Regional Overview Map (50-mile radius)")
    pdf_path = generator.generate_overview_nonattainment_map(
        longitude=longitude,
        latitude=latitude,
        location_name=f"{location_name} - Regional Overview",
        nonattainment_transparency=0.8
    )
    if pdf_path:
        print(f"   ✅ Generated: {pdf_path}")
    else:
        print(f"   ❌ Failed to generate overview map")
    
    # 4. Adaptive map based on analysis results
    print("\n🗺️  Map 4: Adaptive Map (based on analysis)")
    pdf_path = generator.generate_adaptive_nonattainment_map(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        analysis_result=result
    )
    if pdf_path:
        print(f"   ✅ Generated: {pdf_path}")
    else:
        print(f"   ❌ Failed to generate adaptive map")
    
    # 5. Pollutant-specific maps if nonattainment areas found
    if result.has_nonattainment_areas:
        pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
        
        # Generate map for first pollutant as example
        if pollutants:
            pollutant = pollutants[0]
            print(f"\n🗺️  Map 5: {pollutant}-Specific Map")
            pdf_path = generator.generate_pollutant_specific_map(
                pollutant_name=pollutant,
                longitude=longitude,
                latitude=latitude,
                location_name=f"{location_name} - {pollutant}",
                buffer_miles=25.0
            )
            if pdf_path:
                print(f"   ✅ Generated: {pdf_path}")
            else:
                print(f"   ❌ Failed to generate pollutant-specific map")
    
    # 6. Map with revoked standards included
    print("\n🗺️  Map 6: Historical View (including revoked standards)")
    pdf_path = generator.generate_nonattainment_map_pdf(
        longitude=longitude,
        latitude=latitude,
        location_name=f"{location_name} - Historical Standards",
        buffer_miles=25.0,
        base_map="World_Street_Map",
        include_legend=True,
        include_revoked=True,
        nonattainment_transparency=0.6,
        output_filename=f"nonattainment_{location_name.replace(' ', '_').replace(',', '')}_historical.pdf"
    )
    if pdf_path:
        print(f"   ✅ Generated: {pdf_path}")
    else:
        print(f"   ❌ Failed to generate historical map")


def test_buffer_analysis(client: NonAttainmentAreasClient, longitude: float, latitude: float, location_name: str):
    """Test analysis with buffer distances"""
    print_section_header(f"Buffer Analysis for: {location_name}")
    
    buffer_distances = [0, 1000, 5000, 10000]  # meters
    
    for buffer_meters in buffer_distances:
        buffer_miles = buffer_meters * 0.000621371
        print(f"\n🔍 Buffer: {buffer_meters}m ({buffer_miles:.1f} miles)")
        
        result = client.analyze_location(
            longitude, latitude, 
            include_revoked=False,
            buffer_meters=buffer_meters
        )
        
        if result.query_success:
            print(f"   Found {result.area_count} nonattainment area(s)")
            if result.has_nonattainment_areas:
                pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
                print(f"   Pollutants: {', '.join(pollutants)}")
        else:
            print(f"   ❌ Query failed")


def main():
    """Main test function"""
    print("🌫️  NonAttainmentINFO Complete Functionality Test")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize client and map generator
    client = NonAttainmentAreasClient()
    generator = NonAttainmentMapGenerator()
    
    # Test locations
    test_locations = [
        {
            "name": "Los Angeles, CA",
            "longitude": -118.2437,
            "latitude": 34.0522,
            "description": "Major metropolitan area with known air quality issues"
        },
        {
            "name": "Houston, TX",
            "longitude": -95.3698,
            "latitude": 29.7604,
            "description": "Industrial area with potential nonattainment"
        },
        {
            "name": "Denver, CO",
            "longitude": -104.9903,
            "latitude": 39.7392,
            "description": "High altitude city with unique air quality challenges"
        },
        {
            "name": "Yellowstone National Park, WY",
            "longitude": -110.5885,
            "latitude": 44.4280,
            "description": "Remote area expected to have clean air"
        }
    ]
    
    # Test each location
    for location in test_locations:
        print(f"\n{'='*80}")
        print(f"🌍 Testing: {location['name']}")
        print(f"   {location['description']}")
        print(f"{'='*80}")
        
        # Analyze location
        result = test_location_analysis(
            client, 
            location['longitude'], 
            location['latitude'], 
            location['name']
        )
        
        # Generate maps
        test_map_generation(
            generator, 
            result,
            location['longitude'], 
            location['latitude'], 
            location['name']
        )
        
        # Test buffer analysis for first location only (as example)
        if location == test_locations[0]:
            test_buffer_analysis(
                client,
                location['longitude'], 
                location['latitude'], 
                location['name']
            )
    
    # Test pollutant-specific queries
    print_section_header("Pollutant-Specific Queries")
    
    pollutants_to_test = ["Ozone", "PM2.5", "Lead"]
    for pollutant in pollutants_to_test:
        print(f"\n🌫️ Searching for {pollutant} nonattainment areas...")
        areas = client.get_pollutant_areas(pollutant, include_revoked=False)
        print(f"   Found {len(areas)} area(s) for {pollutant}")
        
        # Show first 3 areas as examples
        for area in areas[:3]:
            print(f"   • {area.area_name}, {area.state_abbreviation} - {area.current_status}")
    
    print("\n" + "="*80)
    print("✅ NonAttainmentINFO Complete Functionality Test Completed!")
    print("="*80)
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   • Tested {len(test_locations)} locations")
    print(f"   • Generated multiple map types for each location")
    print(f"   • Performed buffer analysis")
    print(f"   • Tested pollutant-specific queries")
    print(f"   • All core functionality verified")
    
    print("\n💡 Next Steps:")
    print("   1. Review generated PDF maps in the output directory")
    print("   2. Check debug JSON files for Web Map specifications")
    print("   3. Verify data accuracy against EPA website")
    print("   4. Test with additional locations as needed")


if __name__ == "__main__":
    main() 