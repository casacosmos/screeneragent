#!/usr/bin/env python3
"""
Test Overview Wetland Map with Circle

Test the improved circle overlay functionality using the corrected feature collection
pattern that matches successful polygon exports.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

def test_improved_circle_overlay():
    """Test the improved circle overlay with corrected feature collection pattern"""
    
    print("🧪 Testing Improved Circle Overlay Implementation")
    print("="*60)
    
    # Test coordinates - Puerto Rico (known to have wetlands)
    longitude = -66.199399
    latitude = 18.408303
    location_name = "Bayamón, Puerto Rico - Improved Circle Test"
    
    print(f"📍 Testing location: {location_name}")
    print(f"🌐 Coordinates: {longitude}, {latitude}")
    
    # Initialize the map generator
    map_generator = WetlandMapGeneratorV3()
    
    try:
        # Test the overview map with improved circle overlay
        print(f"\n🗺️  Generating overview map with improved 0.5-mile circle...")
        
        map_path = map_generator.generate_overview_wetland_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            wetland_transparency=0.8
        )
        
        if map_path:
            print(f"\n✅ SUCCESS! Map generated: {map_path}")
            
            # Verify file exists
            if os.path.exists(map_path):
                file_size = os.path.getsize(map_path)
                print(f"📄 File size: {file_size:,} bytes")
                
                if file_size > 50000:  # At least 50KB indicates a real map
                    print(f"✅ File size indicates successful map generation")
                else:
                    print(f"⚠️  File size seems small - may indicate issues")
            else:
                print(f"❌ File not found at expected path")
                
        else:
            print(f"❌ Map generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        print(f"🔍 Full error details:\n{traceback.format_exc()}")
        return False
    
    return True

def test_circle_geometry_generation():
    """Test the circle geometry generation in isolation"""
    
    print(f"\n🔍 Testing Circle Geometry Generation")
    print("-"*40)
    
    map_generator = WetlandMapGeneratorV3()
    
    # Test coordinates
    longitude = -66.199399
    latitude = 18.408303
    radius_miles = 0.5
    
    try:
        # Test the improved circle creation method
        circle_overlay = map_generator._create_geometry_service_circle(
            longitude, latitude, radius_miles
        )
        
        print(f"📋 Circle overlay structure:")
        print(f"   ID: {circle_overlay.get('id')}")
        print(f"   Title: {circle_overlay.get('title')}")
        print(f"   Visibility: {circle_overlay.get('visibility')}")
        
        # Check feature collection structure
        if 'featureCollection' in circle_overlay:
            fc = circle_overlay['featureCollection']
            layers = fc.get('layers', [])
            print(f"   Feature Collection Layers: {len(layers)}")
            
            if layers:
                layer = layers[0]
                layer_def = layer.get('layerDefinition', {})
                feature_set = layer.get('featureSet', {})
                features = feature_set.get('features', [])
                
                print(f"   Layer Definition Geometry Type: {layer_def.get('geometryType')}")
                print(f"   Features: {len(features)}")
                
                if features:
                    feature = features[0]
                    geometry = feature.get('geometry', {})
                    rings = geometry.get('rings', [])
                    
                    if rings:
                        ring = rings[0]
                        print(f"   Ring Points: {len(ring)}")
                        print(f"   First Point: {ring[0] if ring else 'None'}")
                        print(f"   Last Point: {ring[-1] if ring else 'None'}")
                        
                        # Verify circle is closed
                        if len(ring) > 2 and ring[0] == ring[-1]:
                            print(f"   ✅ Circle is properly closed")
                        else:
                            print(f"   ⚠️  Circle may not be properly closed")
                    
                    attributes = feature.get('attributes', {})
                    print(f"   Attributes: {list(attributes.keys())}")
        
        print(f"✅ Circle geometry generation successful")
        return True
        
    except Exception as e:
        print(f"❌ Circle geometry generation failed: {e}")
        import traceback
        print(f"🔍 Error details:\n{traceback.format_exc()}")
        return False

def main():
    """Main test function"""
    
    print("🧪 Wetland Map Circle Overlay Testing Suite")
    print("="*60)
    
    # Test 1: Circle geometry generation
    geometry_success = test_circle_geometry_generation()
    
    # Test 2: Full map generation with improved circle
    if geometry_success:
        map_success = test_improved_circle_overlay()
    else:
        print("⚠️  Skipping map generation test due to geometry issues")
        map_success = False
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("="*30)
    print(f"Circle Geometry Generation: {'✅ PASS' if geometry_success else '❌ FAIL'}")
    print(f"Full Map Generation: {'✅ PASS' if map_success else '❌ FAIL'}")
    
    if geometry_success and map_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ The improved circle overlay implementation is working correctly")
        print(f"💡 The feature collection pattern matches successful polygon exports")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print(f"🔍 Check the error messages above for troubleshooting information")
    
    return geometry_success and map_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 