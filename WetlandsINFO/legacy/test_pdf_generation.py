#!/usr/bin/env python3
"""
Test Wetland PDF Generation

This script tests the wetland map PDF generation with different configurations
to ensure proper functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3
from datetime import datetime

def test_basic_pdf_generation():
    """Test basic PDF generation with default settings"""
    
    print("🧪 Test 1: Basic PDF Generation")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    # Test coordinates - Puerto Rico wetland area
    longitude = -66.196
    latitude = 18.452
    location_name = "Test Wetland Location"
    
    print(f"📍 Testing coordinates: {longitude}, {latitude}")
    
    try:
        pdf_path = generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=0.5,
            base_map="World_Imagery",
            dpi=300,
            output_size=(1224, 792),
            include_legend=True
        )
        
        if pdf_path and os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            print(f"✅ SUCCESS: PDF generated")
            print(f"   📁 File: {pdf_path}")
            print(f"   📊 Size: {file_size:.2f} MB")
            return True
        else:
            print(f"❌ FAILED: No PDF file created")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_configurations():
    """Test different map configurations"""
    
    print(f"\n🧪 Test 2: Different Configurations")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    # Test coordinates
    longitude = -66.196
    latitude = 18.452
    
    configurations = [
        {
            "name": "Detailed Site Map",
            "params": {
                "location_name": "Detailed Site Analysis",
                "buffer_miles": 0.3,
                "base_map": "World_Imagery",
                "dpi": 300,
                "output_size": (1224, 792),
                "include_legend": True
            }
        },
        {
            "name": "Regional Overview",
            "params": {
                "location_name": "Regional Context",
                "buffer_miles": 1.0,
                "base_map": "World_Topo_Map",
                "dpi": 150,
                "output_size": (792, 612),
                "include_legend": True
            }
        },
        {
            "name": "Quick Reference",
            "params": {
                "location_name": "Quick Reference Map",
                "buffer_miles": 0.5,
                "base_map": "World_Street_Map",
                "dpi": 96,
                "output_size": (792, 612),
                "include_legend": False
            }
        }
    ]
    
    results = []
    
    for config in configurations:
        print(f"\n📋 Testing: {config['name']}")
        
        try:
            pdf_path = generator.generate_wetland_map_pdf(
                longitude=longitude,
                latitude=latitude,
                **config['params']
            )
            
            if pdf_path and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / (1024 * 1024)
                print(f"   ✅ SUCCESS: {pdf_path} ({file_size:.2f} MB)")
                results.append(True)
            else:
                print(f"   ❌ FAILED: No file created")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 Configuration Test Results: {success_count}/{total_count} successful")
    return success_count == total_count

def test_error_handling():
    """Test error handling with invalid inputs"""
    
    print(f"\n🧪 Test 3: Error Handling")
    print("="*50)
    
    generator = WetlandMapGeneratorV3()
    
    error_tests = [
        {
            "name": "Invalid coordinates (middle of ocean)",
            "longitude": -180.0,
            "latitude": 0.0,
            "expected": "Should handle gracefully"
        },
        {
            "name": "Extreme buffer size",
            "longitude": -66.196,
            "latitude": 18.452,
            "buffer_miles": 10.0,
            "expected": "Should handle large extent"
        }
    ]
    
    for test in error_tests:
        print(f"\n📋 Testing: {test['name']}")
        
        try:
            pdf_path = generator.generate_wetland_map_pdf(
                longitude=test['longitude'],
                latitude=test['latitude'],
                location_name=f"Error Test - {test['name']}",
                buffer_miles=test.get('buffer_miles', 0.5),
                dpi=96,  # Lower DPI for faster processing
                output_size=(400, 300)  # Smaller size
            )
            
            if pdf_path:
                print(f"   ✅ Handled gracefully: {pdf_path}")
            else:
                print(f"   ⚠️  No output (expected): {test['expected']}")
                
        except Exception as e:
            print(f"   ⚠️  Exception (may be expected): {e}")

def test_service_connectivity():
    """Test connectivity to required services"""
    
    print(f"\n🧪 Test 4: Service Connectivity")
    print("="*50)
    
    import requests
    
    services = {
        "Export Web Map": "https://fwsprimary.wim.usgs.gov/server/rest/services/ExportWebMap/GPServer/Export%20Web%20Map?f=json",
        "Wetlands Service": "https://fwsprimary.wim.usgs.gov/server/rest/services/Wetlands/MapServer?f=json",
        "World Imagery": "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer?f=json"
    }
    
    all_accessible = True
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {service_name}: Accessible")
            else:
                print(f"   ⚠️  {service_name}: HTTP {response.status_code}")
                all_accessible = False
        except Exception as e:
            print(f"   ❌ {service_name}: {e}")
            all_accessible = False
    
    return all_accessible

def run_comprehensive_test():
    """Run all tests and provide summary"""
    
    print("🌿 Wetland PDF Generation Test Suite")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    test_results = []
    
    test_results.append(("Service Connectivity", test_service_connectivity()))
    test_results.append(("Basic PDF Generation", test_basic_pdf_generation()))
    test_results.append(("Different Configurations", test_different_configurations()))
    
    # Error handling test (doesn't count toward pass/fail)
    test_error_handling()
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PDF generation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check configuration and service availability.")
    
    # List generated files
    output_dir = "output"
    if os.path.exists(output_dir):
        pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
        if pdf_files:
            print(f"\n📁 Generated PDF files in {output_dir}/:")
            for pdf_file in sorted(pdf_files):
                file_path = os.path.join(output_dir, pdf_file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   • {pdf_file} ({file_size:.2f} MB)")
    
    return passed == total

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "basic":
            test_basic_pdf_generation()
        elif test_type == "config":
            test_different_configurations()
        elif test_type == "error":
            test_error_handling()
        elif test_type == "connectivity":
            test_service_connectivity()
        else:
            print("Available test types: basic, config, error, connectivity")
    else:
        # Run comprehensive test
        run_comprehensive_test()

if __name__ == "__main__":
    main() 