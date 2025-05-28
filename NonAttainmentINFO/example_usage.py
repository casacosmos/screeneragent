#!/usr/bin/env python3
"""
NonAttainmentINFO Example Usage

Simple example demonstrating how to:
1. Check if a location is in a nonattainment area
2. Get detailed information about air quality violations
3. Generate a PDF map showing nonattainment areas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nonattainment_client import NonAttainmentAreasClient
from generate_nonattainment_map_pdf import NonAttainmentMapGenerator


def main():
    # Initialize the client and map generator
    client = NonAttainmentAreasClient()
    map_generator = NonAttainmentMapGenerator()
    
    # Example location: Los Angeles, CA
    longitude = -118.2437
    latitude = 34.0522
    location_name = "Los Angeles, CA"
    
    print(f"🌫️  NonAttainmentINFO Example")
    print(f"📍 Checking air quality status for: {location_name}")
    print(f"   Coordinates: {longitude}, {latitude}")
    print("-" * 50)
    
    # Step 1: Analyze the location for nonattainment areas
    result = client.analyze_location(longitude, latitude)
    
    if not result.query_success:
        print(f"❌ Error: {result.error_message}")
        return
    
    # Step 2: Display the results
    if result.has_nonattainment_areas:
        print(f"\n⚠️  Found {result.area_count} nonattainment area(s):")
        
        for area in result.nonattainment_areas:
            print(f"\n   🌫️ {area.pollutant_name}")
            print(f"      Area: {area.area_name}")
            print(f"      State: {area.state_name}")
            print(f"      Status: {area.current_status}")
            print(f"      Classification: {area.classification}")
            if area.design_value and area.design_value_units:
                print(f"      Design Value: {area.design_value} {area.design_value_units}")
    else:
        print("\n✅ This location meets all air quality standards!")
    
    # Step 3: Get summary and recommendations
    summary = client.get_area_summary(result)
    
    if summary['status'] == 'nonattainment_found':
        print("\n📋 Recommendations:")
        for rec in summary['recommendations']:
            print(f"   • {rec}")
    
    # Step 4: Generate a map
    print(f"\n🗺️  Generating nonattainment map...")
    
    pdf_path = map_generator.generate_nonattainment_map_pdf(
        longitude=longitude,
        latitude=latitude,
        location_name=location_name,
        buffer_miles=8.0,
        include_legend=True,
        output_filename=f"nonattainment_map_{location_name.replace(', ', '_')}.pdf"
    )
    
    if pdf_path:
        print(f"✅ Map saved to: {pdf_path}")
    else:
        print("❌ Failed to generate map")
    
    print("\n" + "-" * 50)
    print("✅ Example completed!")


if __name__ == "__main__":
    main() 