#!/usr/bin/env python3
"""
Example Critical Habitat Map Generation

This script demonstrates how to generate professional critical habitat maps
using the HabitatINFO module. Shows various map types and configurations.
"""

import sys
import os
sys.path.append('.')

from HabitatINFO.generate_critical_habitat_map_pdf import CriticalHabitatMapGenerator

def example_critical_habitat_maps():
    """Generate example critical habitat maps for different scenarios"""
    
    print("🗺️  CRITICAL HABITAT MAP GENERATION EXAMPLES")
    print("="*60)
    
    generator = CriticalHabitatMapGenerator()
    
    # Example locations with known critical habitat
    test_locations = [
        {
            "name": "Juncos - Whooping Crane Habitat",
            "longitude": -65.925357,
            "latitude": 18.228125,
            "description": "Coastal area with critical habitat for whooping cranes"
        }
        
    ]
    
    print(f"\n📍 Testing {len(test_locations)} locations with known critical habitat")
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n🗺️  EXAMPLE {i}: {location['name']}")
        print(f"📍 Coordinates: {location['longitude']}, {location['latitude']}")
        print(f"📝 Description: {location['description']}")
        
        try:
            # Generate standard map
            print(f"\n   📋 Generating standard critical habitat map...")
            pdf_path = generator.generate_critical_habitat_map_pdf(
                longitude=location['longitude'],
                latitude=location['latitude'],
                location_name=location['name'].replace(' ', '_'),
                buffer_miles=10.5,
                base_map="World_Imagery",
                include_proposed=True,
                include_legend=True,
                habitat_transparency=0.8
            )
            
            if pdf_path:
                file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
                print(f"   ✅ Standard map generated: {pdf_path}")
                print(f"   📊 File size: {file_size:,} bytes")
                
                # Generate detailed map
                print(f"\n   📋 Generating detailed critical habitat map...")
                detailed_pdf = generator.generate_detailed_critical_habitat_map(
                    longitude=location['longitude'],
                    latitude=location['latitude'],
                    location_name=f"{location['name'].replace(' ', '_')}_Detailed"
                )
                
                if detailed_pdf:
                    detailed_size = os.path.getsize(detailed_pdf) if os.path.exists(detailed_pdf) else 0
                    print(f"   ✅ Detailed map generated: {detailed_pdf}")
                    print(f"   📊 File size: {detailed_size:,} bytes")
                
                # Generate overview map
                print(f"\n   📋 Generating overview critical habitat map...")
                overview_pdf = generator.generate_overview_critical_habitat_map(
                    longitude=location['longitude'],
                    latitude=location['latitude'],
                    location_name=f"{location['name'].replace(' ', '_')}_Overview"
                )
                
                if overview_pdf:
                    overview_size = os.path.getsize(overview_pdf) if os.path.exists(overview_pdf) else 0
                    print(f"   ✅ Overview map generated: {overview_pdf}")
                    print(f"   📊 File size: {overview_size:,} bytes")
                
            else:
                print(f"   ❌ Failed to generate map for {location['name']}")
                
        except Exception as e:
            print(f"   ❌ Error generating maps for {location['name']}: {e}")
    
    # Demonstrate custom configuration
    print(f"\n🎨 CUSTOM CONFIGURATION EXAMPLE")
    print("-" * 40)
    
    try:
        print(f"📋 Generating custom critical habitat map...")
        print(f"   • Topographic base map")
        print(f"   • Final designations only")
        print(f"   • High transparency")
        print(f"   • Large buffer area")
        
        custom_pdf = generator.generate_critical_habitat_map_pdf(
            longitude=-96.7970,
            latitude=28.1595,
            location_name="Custom_Critical_Habitat_Map",
            buffer_miles=1.0,  # Larger area
            base_map="World_Topo_Map",  # Topographic base
            include_proposed=False,  # Final only
            include_legend=True,
            habitat_transparency=0.6,  # More transparent
            dpi=300
        )
        
        if custom_pdf:
            custom_size = os.path.getsize(custom_pdf) if os.path.exists(custom_pdf) else 0
            print(f"✅ Custom map generated: {custom_pdf}")
            print(f"📊 File size: {custom_size:,} bytes")
        else:
            print(f"❌ Failed to generate custom map")
            
    except Exception as e:
        print(f"❌ Error generating custom map: {e}")
    
    print(f"\n📋 SUMMARY")
    print("="*60)
    print(f"✅ Critical habitat map generation examples completed")
    print(f"🗂️  Generated maps are saved in the 'output' directory")
    print(f"📄 Maps include:")
    print(f"   • Critical habitat polygons and linear features")
    print(f"   • Final and proposed habitat designations")
    print(f"   • Professional legends and scale bars")
    print(f"   • Location markers and attribution")
    print(f"   • High-quality base map imagery")
    
    print(f"\n💡 USAGE TIPS:")
    print(f"   • Use smaller buffer (0.3-0.5 miles) for detailed site analysis")
    print(f"   • Use larger buffer (1.0+ miles) for regional context")
    print(f"   • Include proposed habitat for comprehensive assessment")
    print(f"   • Use topographic base maps for terrestrial habitat")
    print(f"   • Use imagery base maps for aquatic/coastal habitat")

def main():
    """Run the example critical habitat map generation"""
    
    print("🦎 Critical Habitat Map Generation Examples")
    print("="*50)
    print("This script demonstrates various critical habitat map generation capabilities.")
    print("Maps will be saved to the 'output' directory.")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    try:
        example_critical_habitat_maps()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 