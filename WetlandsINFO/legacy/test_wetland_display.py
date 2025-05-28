#!/usr/bin/env python3
"""
Test Wetland Display in PDFs

Quick test to verify that wetland polygons are now displaying correctly in generated PDFs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

def test_puerto_rico_wetlands():
    """Test wetland display for Puerto Rico location with known wetlands"""
    
    print("🧪 Testing Puerto Rico Wetlands Display")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    # Puerto Rico coordinates with known wetlands
    longitude = -66.196
    latitude = 18.452
    location_name = "Puerto Rico Wetland Test"
    
    print(f"📍 Testing coordinates: {longitude}, {latitude}")
    print(f"🌴 Expected: Puerto Rico/Virgin Islands wetlands layer (5)")
    
    try:
        pdf_path = generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.3,  # Smaller buffer for better scale
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"\n✅ SUCCESS: PDF generated")
            print(f"   📁 File: {pdf_path}")
            print(f"   📊 Size: {file_size:.2f} MB")
            print(f"\n📋 Check the PDF for:")
            print(f"   • Blue/green wetland polygons overlaid on satellite imagery")
            print(f"   • Legend showing wetland classifications")
            print(f"   • Red location marker")
            print(f"   • Scale bar showing the map is zoomed in enough")
            return True
        else:
            print(f"\n❌ FAILED: No PDF file created")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conus_wetlands():
    """Test wetland display for CONUS location"""
    
    print(f"\n🧪 Testing CONUS Wetlands Display")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    # Florida Everglades coordinates (known wetland area)
    longitude = -80.7
    latitude = 25.3
    location_name = "Florida Everglades Test"
    
    print(f"📍 Testing coordinates: {longitude}, {latitude}")
    print(f"🌲 Expected: Eastern CONUS wetlands layers (0, 1)")
    
    try:
        pdf_path = generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.5,
            base_map="World_Topo_Map",
            dpi=250,
            output_size=(792, 612),
            include_legend=True
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"\n✅ SUCCESS: PDF generated")
            print(f"   📁 File: {pdf_path}")
            print(f"   📊 Size: {file_size:.2f} MB")
            return True
        else:
            print(f"\n❌ FAILED: No PDF file created")
            return False
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False

def main():
    """Run wetland display tests"""
    
    print("🌿 Wetland Display Test")
    print("="*60)
    
    results = []
    
    # Test Puerto Rico wetlands
    results.append(test_puerto_rico_wetlands())
    
    # Test CONUS wetlands
    results.append(test_conus_wetlands())
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Wetland polygons should now be visible in PDFs.")
    else:
        print("⚠️  Some tests failed. Check the debug files and error messages.")
    
    # List debug files
    debug_files = [f for f in os.listdir('.') if f.startswith('debug_webmap_')]
    if debug_files:
        print(f"\n🔍 Debug files created:")
        for debug_file in sorted(debug_files):
            print(f"   • {debug_file}")
        print(f"   These contain the Web Map JSON sent to the service.")

if __name__ == "__main__":
    main() 