#!/usr/bin/env python3
"""
Example NonAttainment Map Generation

This script demonstrates how to generate professional nonattainment maps
using the NonAttainmentINFO module. Shows various map types and configurations.
"""

import sys
import os
sys.path.append('.')

from NonAttainmentINFO.generate_nonattainment_map_pdf import NonAttainmentMapGenerator

def example_nonattainment_maps():
    """Generate example nonattainment maps for different scenarios"""
    
    print("🗺️  NONATTAINMENT MAP GENERATION EXAMPLES")
    print("="*60)
    
    generator = NonAttainmentMapGenerator()
    
    # Example locations with known nonattainment areas
    test_locations = [
        {
            "name": "Juncos - Whooping Crane Habitat",
            "longitude": -65.925357,
            "latitude": 18.228125,
            "description": "Coastal area with critical habitat for whooping cranes"
        }
        
    ]
    
    print(f"\n📍 Testing {len(test_locations)} locations with known nonattainment areas")
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n🗺️  EXAMPLE {i}: {location['name']}")
        print(f"📍 Coordinates: {location['longitude']}, {location['latitude']}")
        print(f"📝 Description: {location['description']}")
        
        try:
            # Generate standard map
            print(f"\n   📋 Generating standard nonattainment map...")
            pdf_path = generator.generate_nonattainment_map_pdf(
                longitude=location['longitude'],
                latitude=location['latitude'],
                location_name=location['name'],
                buffer_miles=20.0,
                base_map="World_Imagery",
                include_revoked=False,
                include_legend=True,
                nonattainment_transparency=0.7
            )
            
            if pdf_path:
                file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
                print(f"   ✅ Standard map generated: {pdf_path}")
                print(f"   📊 File size: {file_size:,} bytes")
                
                # Generate detailed map
                print(f"\n   📋 Generating detailed nonattainment map...")
                detailed_pdf = generator.generate_detailed_nonattainment_map(
                    longitude=location['longitude'],
                    latitude=location['latitude'],
                    location_name=f"{location['name']}_Detailed"
                )
                
                if detailed_pdf:
                    detailed_size = os.path.getsize(detailed_pdf) if os.path.exists(detailed_pdf) else 0
                    print(f"   ✅ Detailed map generated: {detailed_pdf}")
                    print(f"   📊 File size: {detailed_size:,} bytes")
                
                # Generate overview map
                print(f"\n   📋 Generating overview nonattainment map...")
                overview_pdf = generator.generate_overview_nonattainment_map(
                    longitude=location['longitude'],
                    latitude=location['latitude'],
                    location_name=f"{location['name']}_Overview"
                )
                
                if overview_pdf:
                    overview_size = os.path.getsize(overview_pdf) if os.path.exists(overview_pdf) else 0
                    print(f"   ✅ Overview map generated: {overview_pdf}")
                    print(f"   📊 File size: {overview_size:,} bytes")
                
            else:
                print(f"   ❌ Failed to generate map for {location['name']}")
                
        except Exception as e:
            print(f"   ❌ Error generating maps for {location['name']}: {e}")
    
    # Demonstrate pollutant-specific maps
    print(f"\n🌫️ POLLUTANT-SPECIFIC MAP EXAMPLES")
    print("-" * 40)
    
    pollutant_examples = [
        ("Ozone", -118.2437, 34.0522, "Los Angeles - Ozone Focus"),
        ("PM2.5", -112.0740, 33.4484, "Phoenix - PM2.5 Focus"),
        ("Lead", -87.6298, 41.8781, "Chicago - Lead Focus")
    ]
    
    for pollutant, lon, lat, description in pollutant_examples:
        try:
            print(f"\n📋 Generating {pollutant} specific map for {description}...")
            
            pollutant_pdf = generator.generate_pollutant_specific_map(
                pollutant_name=pollutant,
                longitude=lon,
                latitude=lat,
                location_name=f"{pollutant}_Nonattainment_Map",
                buffer_miles=30.0
            )
            
            if pollutant_pdf:
                pollutant_size = os.path.getsize(pollutant_pdf) if os.path.exists(pollutant_pdf) else 0
                print(f"✅ {pollutant} map generated: {pollutant_pdf}")
                print(f"📊 File size: {pollutant_size:,} bytes")
            else:
                print(f"❌ Failed to generate {pollutant} map")
                
        except Exception as e:
            print(f"❌ Error generating {pollutant} map: {e}")
    
    # Demonstrate custom configuration
    print(f"\n🎨 CUSTOM CONFIGURATION EXAMPLE")
    print("-" * 40)
    
    try:
        print(f"📋 Generating custom nonattainment map...")
        print(f"   • Satellite imagery base map")
        print(f"   • Including revoked standards")
        print(f"   • High transparency")
        print(f"   • Large buffer area")
        
        custom_pdf = generator.generate_nonattainment_map_pdf(
            longitude=-65.925357,
            latitude=18.228125,
            location_name="Custom_Juncos_Nonattainment_Map",
            buffer_miles=10.0,  # Larger area
            base_map="World_Imagery",  # Satellite base
            include_revoked=True,  # Include all standards
            include_legend=True,
            nonattainment_transparency=0.5,  # More transparent
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
    
    # Demonstrate clean air area
    print(f"\n🌿 CLEAN AIR AREA EXAMPLE")
    print("-" * 40)
    
    try:
        print(f"📋 Generating map for clean air area...")
        
        clean_pdf = generator.generate_nonattainment_map_pdf(
            longitude=-106.6504,
            latitude=35.0844,
            location_name="Santa_Fe_NM_Clean_Air",
            buffer_miles=50.0,
            base_map="World_Topo_Map",
            include_legend=True,
            nonattainment_transparency=0.8
        )
        
        if clean_pdf:
            clean_size = os.path.getsize(clean_pdf) if os.path.exists(clean_pdf) else 0
            print(f"✅ Clean air map generated: {clean_pdf}")
            print(f"📊 File size: {clean_size:,} bytes")
        else:
            print(f"❌ Failed to generate clean air map")
            
    except Exception as e:
        print(f"❌ Error generating clean air map: {e}")
    
    print(f"\n📋 SUMMARY")
    print("="*60)
    print(f"✅ Nonattainment map generation examples completed")
    print(f"🗂️  Generated maps are saved in the 'output' directory")
    print(f"📄 Maps include:")
    print(f"   • EPA nonattainment area polygons for all criteria pollutants")
    print(f"   • Active and revoked NAAQS standards")
    print(f"   • Professional legends and scale bars")
    print(f"   • Location markers and attribution")
    print(f"   • High-quality base map imagery")
    
    print(f"\n💡 USAGE TIPS:")
    print(f"   • Use smaller buffer (10-15 miles) for detailed site analysis")
    print(f"   • Use larger buffer (25-50 miles) for regional context")
    print(f"   • Include revoked standards for historical analysis")
    print(f"   • Use topographic base maps for general analysis")
    print(f"   • Use imagery base maps for detailed site assessment")
    print(f"   • Filter by specific pollutants for focused analysis")

def main():
    """Run the example nonattainment map generation"""
    
    print("🌫️ NonAttainment Map Generation Examples")
    print("="*50)
    print("This script demonstrates various nonattainment map generation capabilities.")
    print("Maps will be saved to the 'output' directory.")
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    try:
        example_nonattainment_maps()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 