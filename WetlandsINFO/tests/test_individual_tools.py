#!/usr/bin/env python3
"""
Test Individual Environmental Tools

This script tests the critical habitat, nonattainment, and karst analysis tools
individually to ensure they're working correctly with map generation.
"""

import sys
import os
from datetime import datetime

def test_critical_habitat_tool():
    """Test the critical habitat analysis tool"""
    print("🦎 Testing Critical Habitat Analysis Tool")
    print("=" * 50)
    
    try:
        # Import the tool (correct name from tools.py)
        from HabitatINFO.tools import analyze_critical_habitat
        
        # Test coordinates (Puerto Rico - known to have critical habitat)
        longitude = -66.1689712
        latitude = 18.4282314
        
        print(f"📍 Testing coordinates: {longitude}, {latitude}")
        print(f"🏷️  Location: Cataño, Puerto Rico - Critical Habitat Test")
        
        # Run the analysis using invoke method
        result_json = analyze_critical_habitat.invoke({
            "longitude": longitude,
            "latitude": latitude,
            "include_proposed": True,
            "buffer_meters": 0
        })
        
        # Parse JSON result
        import json
        result = json.loads(result_json)
        
        print("\n✅ Critical Habitat Tool Results:")
        if 'critical_habitat_analysis' in result:
            analysis = result['critical_habitat_analysis']
            print(f"   Status: {analysis.get('status', 'Unknown')}")
            print(f"   Location: {analysis.get('location', 'Unknown')}")
            
            if analysis.get('status') == 'critical_habitat_found':
                print(f"   Species Affected: {analysis.get('regulatory_implications', {}).get('total_species_affected', 0)}")
                print(f"   ESA Consultation Required: {analysis.get('regulatory_implications', {}).get('esa_consultation_required', False)}")
            else:
                print(f"   Message: {analysis.get('message', 'No additional info')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Critical Habitat Tool Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_nonattainment_tool():
    """Test the nonattainment analysis tool"""
    print("\n🌫️ Testing Nonattainment Analysis Tool")
    print("=" * 50)
    
    try:
        # Import the tool (correct name from nonattainment_analysis_tool.py)
        from nonattainment_analysis_tool import analyze_nonattainment_with_map
        
        # Test coordinates (Los Angeles - known nonattainment area)
        longitude = -118.2437
        latitude = 34.0522
        location_name = "Los Angeles, CA - Nonattainment Test"
        
        print(f"📍 Testing coordinates: {longitude}, {latitude}")
        print(f"🏷️  Location: {location_name}")
        
        # Run the analysis using invoke method
        result = analyze_nonattainment_with_map.invoke({
            "longitude": longitude,
            "latitude": latitude,
            "location_name": location_name
        })
        
        print("\n✅ Nonattainment Tool Results:")
        if 'location_analysis' in result:
            analysis = result['location_analysis']
            print(f"   Location: {analysis.get('location', 'Unknown')}")
            print(f"   Has Violations: {analysis.get('has_violations', 'Unknown')}")
            print(f"   Total Violations: {analysis.get('total_violations', 0)}")
        
        if 'map_generation' in result:
            map_info = result['map_generation']
            print(f"   Map Generated: {map_info.get('success', False)}")
            if map_info.get('success'):
                print(f"   Map File: {map_info.get('filename', 'Unknown')}")
        
        if 'analysis_summary' in result:
            summary = result['analysis_summary']
            print(f"   Air Quality Status: {summary.get('air_quality_status', 'Unknown')}")
            print(f"   Regulatory Complexity: {summary.get('regulatory_complexity', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Nonattainment Tool Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_karst_tool():
    """Test the karst analysis tool"""
    print("\n🏔️ Testing Karst Analysis Tool")
    print("=" * 50)
    
    try:
        # Import the tool (correct name from karst_tools.py)
        from karst.karst_tools import check_cadastral_karst
        
        # Test with a Puerto Rico cadastral number
        cadastral_number = "227-052-007-20"  # Example Puerto Rico cadastral
        
        print(f"📍 Testing cadastral: {cadastral_number}")
        print(f"🏷️  Location: Puerto Rico - Karst Test")
        
        # Run the analysis using invoke method
        result = check_cadastral_karst.invoke({
            "cadastral_number": cadastral_number,
            "buffer_miles": 0.5,
            "include_buffer_search": True
        })
        
        print("\n✅ Karst Tool Results:")
        print(f"   Success: {result.get('success', 'Unknown')}")
        print(f"   Cadastral: {result.get('cadastral_number', 'Unknown')}")
        print(f"   Karst Status: {result.get('karst_status', 'Unknown')}")
        print(f"   Karst Proximity: {result.get('karst_proximity', 'Unknown')}")
        print(f"   Regulatory Impact: {result.get('regulatory_impact', 'Unknown')}")
        
        if 'property_details' in result:
            prop = result['property_details']
            print(f"   Municipality: {prop.get('municipality', 'Unknown')}")
            print(f"   Area (hectares): {prop.get('area_hectares', 0):.2f}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Karst Tool Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_puerto_rico_coordinates():
    """Test critical habitat and nonattainment tools with Puerto Rico coordinates"""
    print("\n🌴 Testing Tools with Puerto Rico Coordinates")
    print("=" * 60)
    
    # Puerto Rico coordinates - should have good data for all analyses
    longitude = -66.150906
    latitude = 18.434059
    location_name = "Bayamón, Puerto Rico - Multi-Tool Test"
    
    print(f"📍 Testing coordinates: {longitude}, {latitude}")
    print(f"🏷️  Location: {location_name}")
    
    results = {}
    
    # Test critical habitat
    print("\n🦎 Testing Critical Habitat...")
    try:
        from HabitatINFO.tools import analyze_critical_habitat
        habitat_result_json = analyze_critical_habitat.invoke({
            "longitude": longitude,
            "latitude": latitude,
            "include_proposed": True,
            "buffer_meters": 0
        })
        import json
        habitat_result = json.loads(habitat_result_json)
        results['critical_habitat'] = 'critical_habitat_analysis' in habitat_result
        print(f"   Critical Habitat: {'✅ Success' if results['critical_habitat'] else '❌ Failed'}")
    except Exception as e:
        results['critical_habitat'] = False
        print(f"   Critical Habitat: ❌ Error - {e}")
    
    # Test nonattainment (Puerto Rico is typically attainment)
    print("\n🌫️ Testing Nonattainment...")
    try:
        from nonattainment_analysis_tool import analyze_nonattainment_with_map
        nonattainment_result = analyze_nonattainment_with_map.invoke({
            "longitude": longitude,
            "latitude": latitude,
            "location_name": f"{location_name} - Air Quality"
        })
        results['nonattainment'] = 'location_analysis' in nonattainment_result
        print(f"   Nonattainment: {'✅ Success' if results['nonattainment'] else '❌ Failed'}")
    except Exception as e:
        results['nonattainment'] = False
        print(f"   Nonattainment: ❌ Error - {e}")
    
    return results

def test_coordinate_based_karst():
    """Test coordinate-based karst analysis if available"""
    print("\n🗺️ Testing Coordinate-Based Karst Analysis")
    print("=" * 50)
    
    try:
        # Check if coordinate-based karst analysis is available
        from karst.comprehensive_karst_analysis import ComprehensiveKarstAnalyzer
        
        # Puerto Rico coordinates (known karst area)
        longitude = -66.1689712
        latitude = 18.4282314
        
        print(f"📍 Testing coordinates: {longitude}, {latitude}")
        print(f"🏷️  Location: Cataño, Puerto Rico - Coordinate Karst Test")
        
        # Create analyzer and run analysis
        analyzer = ComprehensiveKarstAnalyzer()
        result = analyzer.analyze_comprehensive_karst(longitude, latitude, 1.0)
        
        print("\n✅ Coordinate-Based Karst Results:")
        print(f"   Success: {result.get('success', 'Unknown')}")
        if result.get('success'):
            prapec = result.get('prapec_analysis', {})
            print(f"   PRAPEC Karst Found: {prapec.get('karst_found', False)}")
            
            buffer = result.get('buffer_zone_analysis', {})
            print(f"   Buffer Zones Found: {buffer.get('buffer_zones_found', False)}")
            
            combined = result.get('combined_assessment', {})
            print(f"   Overall Impact: {combined.get('overall_karst_impact', 'none')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Coordinate-Based Karst Error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Environmental Tools Individual Testing")
    print("=" * 70)
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test each tool individually
    critical_habitat_success = test_critical_habitat_tool()
    nonattainment_success = test_nonattainment_tool()  
    karst_success = test_karst_tool()
    coordinate_karst_success = test_coordinate_based_karst()
    
    # Test tools with same coordinates
    multi_test_results = test_puerto_rico_coordinates()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    individual_tests = {
        'Critical Habitat': critical_habitat_success,
        'Nonattainment': nonattainment_success,
        'Karst (Cadastral)': karst_success,
        'Karst (Coordinate)': coordinate_karst_success
    }
    
    print("\n🔍 Individual Tool Tests:")
    for tool_name, success in individual_tests.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {tool_name}: {status}")
    
    print("\n🌴 Puerto Rico Multi-Tool Test:")
    for tool_name, success in multi_test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {tool_name.replace('_', ' ').title()}: {status}")
    
    # Overall results
    total_tests = len(individual_tests) + len(multi_test_results)
    passed_tests = sum(individual_tests.values()) + sum(multi_test_results.values())
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Tests Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ALL TESTS PASSED! Environmental tools are working correctly.")
    elif passed_tests >= total_tests * 0.5:
        print(f"\n✅ MAJORITY PASSED! Most environmental tools are working correctly.")
    else:
        print(f"\n⚠️  Many tests failed. Check the error messages above for details.")
    
    print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 