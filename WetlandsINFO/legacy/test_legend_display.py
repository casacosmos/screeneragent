#!/usr/bin/env python3
"""
Test Legend Display in Wetland PDFs

Quick test to verify that the legend is now displaying correctly in generated PDFs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

def test_legend_display():
    """Test that legend displays correctly in PDF"""
    
    print("🧪 Testing Legend Display")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    # Puerto Rico coordinates with known wetlands
    longitude = -66.196
    latitude = 18.452
    location_name = "Legend Test - Puerto Rico"
    
    print(f"📍 Testing coordinates: {longitude}, {latitude}")
    print(f"🎯 Focus: Legend display with wetland classifications")
    
    try:
        # Generate map with legend enabled
        pdf_path = generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.4,  # Good size for wetlands
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            output_filename="legend_test_with_legend.pdf"
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)
            print(f"\n✅ SUCCESS: PDF with legend generated")
            print(f"   📁 File: {pdf_path}")
            print(f"   📊 Size: {file_size:.2f} MB")
        else:
            print(f"\n❌ FAILED: No PDF file created")
            return False
        
        # Generate map without legend for comparison
        pdf_path_no_legend = generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.4,
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),
            include_legend=False,
            output_filename="legend_test_no_legend.pdf"
        )
        
        if pdf_path_no_legend and os.path.exists(pdf_path_no_legend):
            file_size_no_legend = os.path.getsize(pdf_path_no_legend) / (1024 * 1024)
            print(f"\n✅ SUCCESS: PDF without legend generated")
            print(f"   📁 File: {pdf_path_no_legend}")
            print(f"   📊 Size: {file_size_no_legend:.2f} MB")
        else:
            print(f"\n❌ FAILED: No comparison PDF created")
            return False
        
        print(f"\n📋 Manual Verification Required:")
        print(f"   1. Open: {pdf_path}")
        print(f"      ✓ Should have legend showing wetland types/colors")
        print(f"      ✓ Should have scale bar with miles/kilometers")
        print(f"      ✓ Should show wetland polygons in blue/green")
        print(f"   2. Open: {pdf_path_no_legend}")
        print(f"      ✓ Should NOT have legend")
        print(f"      ✓ Should still show wetland polygons")
        print(f"      ✓ Should have scale bar")
        
        return True
            
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run legend display test"""
    
    print("📊 Legend Display Test")
    print("="*60)
    
    success = test_legend_display()
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    if success:
        print("🎉 Test completed successfully!")
        print("📋 Please manually verify the PDFs to confirm legend display.")
        print("   The legend should show wetland classifications with colors.")
    else:
        print("⚠️  Test failed. Check error messages above.")
    
    # List all output files
    output_files = [f for f in os.listdir('output') if f.endswith('.pdf')]
    if output_files:
        print(f"\n📁 Generated PDF files:")
        for pdf_file in sorted(output_files):
            file_path = os.path.join('output', pdf_file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            print(f"   • {pdf_file} ({file_size:.2f} MB)")

if __name__ == "__main__":
    main() 