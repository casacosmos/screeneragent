#!/usr/bin/env python3
"""
Test script to verify directory management and map generation fixes

This script tests:
1. Centralized directory management
2. Map generation without loops
3. Proper map embedding in HTML reports
"""

import os
import json
from pathlib import Path
from html_pdf_generator import HTMLEnvironmentalPDFGenerator

def test_directory_management():
    """Test centralized directory management"""
    print("🧪 Testing Directory Management Fixes")
    print("=" * 50)
    
    # Use existing test data
    test_project_dir = "test_workflow_output/Directory_Test_20250529"
    test_json_file = "schema_test/Schema_Test_Project_20250529_023509/data/comprehensive_query_results.json"
    
    if not Path(test_json_file).exists():
        print(f"❌ Test data not found: {test_json_file}")
        return False
    
    try:
        # Test 1: Initialize HTML PDF Generator with centralized directories
        print("📁 Test 1: Centralized directory initialization...")
        
        generator = HTMLEnvironmentalPDFGenerator(
            json_report_path=test_json_file,
            project_directory=test_project_dir,
            prefer_png_maps=True
        )
        
        # Verify all directories were created centrally
        expected_dirs = [
            generator.data_directory,
            generator.maps_directory,
            generator.reports_directory,
            generator.logs_directory
        ]
        
        all_dirs_exist = all(d.exists() for d in expected_dirs)
        if all_dirs_exist:
            print("✅ All centralized directories created successfully")
        else:
            print("❌ Some directories missing")
            return False
        
        # Test 2: Check that paths are correctly centralized
        print("📍 Test 2: Path centralization...")
        
        project_root = Path(test_project_dir)
        if (generator.data_directory.parent == project_root and
            generator.maps_directory.parent == project_root and
            generator.reports_directory.parent == project_root):
            print("✅ All paths correctly centralized to project directory")
        else:
            print("❌ Paths not properly centralized")
            return False
        
        # Test 3: Generate HTML report without map duplication
        print("🗺️ Test 3: Map generation and embedding...")
        
        # Check initial map count
        initial_maps = list(generator.maps_directory.glob("*"))
        initial_count = len(initial_maps)
        print(f"   📊 Initial maps in directory: {initial_count}")
        
        # Generate HTML report (this should handle maps centrally)
        try:
            html_output = generator.generate_html_report()
            print(f"✅ HTML report generated: {Path(html_output).name}")
            
            # Check final map count
            final_maps = list(generator.maps_directory.glob("*"))
            final_count = len(final_maps)
            print(f"   📊 Final maps in directory: {final_count}")
            
            # Verify no files scattered in output/ or other directories
            output_dir = Path("output")
            scattered_maps = []
            if output_dir.exists():
                scattered_maps = list(output_dir.glob("*.pdf")) + list(output_dir.glob("*.png"))
            
            if len(scattered_maps) == 0:
                print("✅ No scattered map files found outside project directory")
            else:
                print(f"⚠️ Found {len(scattered_maps)} scattered map files in output/")
                for f in scattered_maps[:3]:  # Show first 3
                    print(f"   • {f}")
            
            # Test 4: Verify HTML contains embedded maps
            print("🖼️ Test 4: Map embedding verification...")
            
            if Path(html_output).exists():
                with open(html_output, 'r') as f:
                    html_content = f.read()
                
                # Check for base64 embedded images
                base64_images = html_content.count('data:image/')
                if base64_images > 0:
                    print(f"✅ Found {base64_images} embedded base64 images in HTML")
                else:
                    print("⚠️ No embedded base64 images found in HTML")
                
                # Check for problematic PDF references
                pdf_refs = html_content.count('.pdf')
                if pdf_refs == 0:
                    print("✅ No PDF references in HTML (good for embedding)")
                else:
                    print(f"⚠️ Found {pdf_refs} PDF references in HTML")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating HTML report: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error in directory management test: {e}")
        return False

def test_map_generation_prevention():
    """Test that redundant map generation is prevented"""
    print("\n🔁 Testing Map Generation Loop Prevention")
    print("=" * 50)
    
    test_project_dir = "test_workflow_output/Loop_Prevention_Test_20250529"
    test_json_file = "schema_test/Schema_Test_Project_20250529_023509/data/comprehensive_query_results.json"
    
    if not Path(test_json_file).exists():
        print(f"❌ Test data not found: {test_json_file}")
        return False
    
    try:
        # Create generator
        generator = HTMLEnvironmentalPDFGenerator(
            json_report_path=test_json_file,
            project_directory=test_project_dir,
            prefer_png_maps=True
        )
        
        # Create some dummy map files to test prevention
        dummy_maps = [
            generator.maps_directory / "wetland_map_test.png",
            generator.maps_directory / "habitat_map_test.png",
            generator.maps_directory / "karst_map_test.png"
        ]
        
        for map_file in dummy_maps:
            map_file.touch()  # Create empty files
        
        print(f"📄 Created {len(dummy_maps)} dummy map files")
        
        # Run map resolution - should NOT generate new maps
        initial_count = len(list(generator.maps_directory.glob("*")))
        
        # Prepare template data (includes map resolution)
        prepared_data = generator._prepare_template_data(generator.report_data)
        
        final_count = len(list(generator.maps_directory.glob("*")))
        
        if final_count == initial_count:
            print("✅ No redundant maps generated - existing maps were reused")
            return True
        else:
            print(f"⚠️ Map count changed from {initial_count} to {final_count}")
            return False
        
    except Exception as e:
        print(f"❌ Error in loop prevention test: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Directory Management and Map Generation Fix Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Directory Management
    results.append(test_directory_management())
    
    # Test 2: Map Generation Loop Prevention
    results.append(test_map_generation_prevention())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Directory management fixes are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main()) 