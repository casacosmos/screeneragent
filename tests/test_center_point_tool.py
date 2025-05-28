#!/usr/bin/env python3
"""
Test script for the Cadastral Center Point Calculator Tool

This script demonstrates the usage of the new cadastral center point tool
with various calculation methods and coordinate systems.
"""

import sys
import os
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cadastral.cadastral_center_point_tool import calculate_cadastral_center_point

def test_center_point_calculation():
    """Test the center point calculation tool with different parameters."""
    
    print("🎯 Testing Cadastral Center Point Calculator Tool")
    print("=" * 70)
    
    # Test cadastral numbers (known to exist in the database)
    test_cadastrals = [
        "227-052-007-20",  # Public land parcel in Juncos
        "227-062-084-05",  # Small mixed-use parcel in Juncos
    ]
    
    for i, cadastral_number in enumerate(test_cadastrals, 1):
        print(f"\n🧪 Test {i}: Cadastral {cadastral_number}")
        print("-" * 50)
        
        # Test 1: Basic calculation with projected method (default)
        print(f"\n📊 Test {i}.1: Projected method (high accuracy)")
        result = calculate_cadastral_center_point(
            cadastral_number=cadastral_number,
            output_coordinate_system="WGS84",
            calculation_method="projected",
            include_polygon_data=False,
            save_to_file=True
        )
        
        if result['success']:
            center = result['center_point']
            print(f"✅ Success! Center point: ({center['longitude']:.8f}, {center['latitude']:.8f})")
            print(f"   Coordinate system: {center['coordinate_system']}")
            print(f"   Calculation method: {center['calculation_method']}")
            print(f"   Polygon coordinates: {result['polygon_metadata']['coordinate_count']}")
            print(f"   Area: {result['cadastral_info']['area_hectares']:.4f} hectares")
        else:
            print(f"❌ Failed: {result['error']}")
        
        # Test 2: Both methods for comparison
        print(f"\n📊 Test {i}.2: Both methods (comparison)")
        result = calculate_cadastral_center_point(
            cadastral_number=cadastral_number,
            output_coordinate_system="WGS84",
            calculation_method="both",
            include_polygon_data=False,
            save_to_file=False
        )
        
        if result['success']:
            center = result['center_point']
            print(f"✅ Primary center point: ({center['longitude']:.8f}, {center['latitude']:.8f})")
            
            # Show comparison if available
            if 'comparison' in result['calculation_details']:
                comparison = result['calculation_details']['comparison']
                print(f"   Method difference: {comparison['difference_meters']:.2f} meters")
                print(f"   Assessment: {comparison['difference_assessment']}")
                print(f"   Recommended: {comparison['recommended_method']}")
            
            # Show both calculation results
            for method, details in result['calculation_details'].items():
                if method != 'comparison':
                    coords = details['center_point_wgs84']
                    print(f"   {method.title()}: ({coords[0]:.8f}, {coords[1]:.8f})")
        else:
            print(f"❌ Failed: {result['error']}")
        
        # Test 3: NAD83 output coordinates
        print(f"\n📊 Test {i}.3: NAD83 output coordinates")
        result = calculate_cadastral_center_point(
            cadastral_number=cadastral_number,
            output_coordinate_system="NAD83",
            calculation_method="projected",
            include_polygon_data=False,
            save_to_file=False
        )
        
        if result['success']:
            center = result['center_point']
            print(f"✅ NAD83 center point: ({center['longitude']:.8f}, {center['latitude']:.8f})")
            print(f"   Coordinate system: {center['coordinate_system']}")
            
            # Show coordinate system conversion info
            coord_info = result['coordinate_system_info']
            print(f"   Conversion applied: {coord_info['conversion_applied']}")
            print(f"   Input system: {coord_info['input_system']}")
            print(f"   Output system: {coord_info['output_system']}")
        else:
            print(f"❌ Failed: {result['error']}")
        
        # Test 4: Include polygon data
        print(f"\n📊 Test {i}.4: Include polygon coordinates")
        result = calculate_cadastral_center_point(
            cadastral_number=cadastral_number,
            output_coordinate_system="WGS84",
            calculation_method="geographic",
            include_polygon_data=True,
            save_to_file=False
        )
        
        if result['success']:
            center = result['center_point']
            print(f"✅ Geographic center point: ({center['longitude']:.8f}, {center['latitude']:.8f})")
            
            if 'polygon_coordinates' in result:
                coords_count = len(result['polygon_coordinates'])
                print(f"   Polygon coordinates included: {coords_count} points")
                
                # Show first few coordinates as sample
                if coords_count > 0:
                    print(f"   Sample coordinates:")
                    for j, (lon, lat) in enumerate(result['polygon_coordinates'][:3]):
                        print(f"     Point {j+1}: ({lon:.8f}, {lat:.8f})")
                    if coords_count > 3:
                        print(f"     ... and {coords_count - 3} more points")
        else:
            print(f"❌ Failed: {result['error']}")
        
        print("-" * 50)

def test_error_handling():
    """Test error handling with invalid inputs."""
    
    print(f"\n🧪 Testing Error Handling")
    print("-" * 50)
    
    # Test with non-existent cadastral
    print(f"\n📊 Test: Non-existent cadastral number")
    result = calculate_cadastral_center_point(
        cadastral_number="999-999-999-99",
        save_to_file=False
    )
    
    if not result['success']:
        print(f"✅ Expected error: {result['error']}")
    else:
        print(f"❌ Unexpected success for non-existent cadastral")
    
    # Test with invalid calculation method
    print(f"\n📊 Test: Invalid calculation method")
    result = calculate_cadastral_center_point(
        cadastral_number="227-052-007-20",
        calculation_method="invalid_method",
        save_to_file=False
    )
    
    if not result['success']:
        print(f"✅ Expected error: {result['error']}")
    else:
        print(f"❌ Unexpected success for invalid method")
    
    # Test with invalid coordinate system
    print(f"\n📊 Test: Invalid coordinate system")
    result = calculate_cadastral_center_point(
        cadastral_number="227-052-007-20",
        output_coordinate_system="INVALID",
        save_to_file=False
    )
    
    if not result['success']:
        print(f"✅ Expected error: {result['error']}")
    else:
        print(f"❌ Unexpected success for invalid coordinate system")

def main():
    """Main test function."""
    
    print("🎯 Cadastral Center Point Calculator Tool - Test Suite")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run main functionality tests
        test_center_point_calculation()
        
        # Run error handling tests
        test_error_handling()
        
        print(f"\n✅ All tests completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 