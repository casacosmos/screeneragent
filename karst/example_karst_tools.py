#!/usr/bin/env python3
"""
Example Usage of MIPR Karst Tools for LangGraph

This script demonstrates how to use the LangGraph tools for PRAPEC karst checking
with cadastral numbers as input, including nearest karst identification.
"""

import json
from karst_tools import (
    check_cadastral_karst,
    check_multiple_cadastrals_karst,
    find_nearest_karst,
    analyze_cadastral_karst_proximity
)

def example_single_cadastral_check():
    """Example 1: Check a single cadastral for karst areas."""
    print("🏔️ Example 1: Single Cadastral Karst Check")
    print("=" * 60)
    
    # Test with a cadastral from Juncos (likely not in karst)
    cadastral = "227-052-007-20"
    
    result = check_cadastral_karst.invoke({
        "cadastral_number": cadastral,
        "buffer_miles": 1.0,
        "include_buffer_search": True
    })
    
    print(f"Cadastral: {cadastral}")
    print(f"Karst Status: {result.get('karst_status', 'Unknown')}")
    print(f"Regulatory Impact: {result.get('regulatory_impact', 'Unknown')}")
    print(f"Message: {result.get('message', 'No message')}")
    
    if result.get('property_details'):
        details = result['property_details']
        print(f"Municipality: {details['municipality']}")
        print(f"Classification: {details['land_use_classification']}")
        print(f"Area: {details['area_hectares']:.2f} hectares")
    
    if result.get('karst_area_details'):
        karst = result['karst_area_details']
        print(f"Karst Area: {karst['official_name']}")
        print(f"Regulation: {karst['regulation_number']}")

def example_multiple_cadastrals_check():
    """Example 2: Check multiple cadastrals for karst areas."""
    print("\n🏔️ Example 2: Multiple Cadastrals Karst Check")
    print("=" * 60)
    
    # Test with multiple cadastrals from different areas
    cadastrals = [
        "227-062-084-05",  # Juncos
        "227-052-007-20",  # Juncos
        "227-062-084-04"   # Juncos
    ]
    
    result = check_multiple_cadastrals_karst.invoke({
        "cadastral_numbers": cadastrals,
        "buffer_miles": 0.5,
        "include_buffer_search": True
    })
    
    print(f"Total Cadastrals Checked: {result.get('total_cadastrals', 0)}")
    
    if result.get('batch_summary'):
        summary = result['batch_summary']
        print(f"Directly in Karst: {summary['directly_in_karst']}")
        print(f"Nearby Karst: {summary['nearby_karst']}")
        print(f"No Karst: {summary['no_karst']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    if result.get('karst_analysis'):
        analysis = result['karst_analysis']
        print(f"Percentage Affected: {analysis['percentage_affected']:.1f}%")
    
    print(f"Message: {result.get('message', 'No message')}")
    
    # Show individual results
    if result.get('individual_results'):
        print("\nIndividual Results:")
        for i, cad_result in enumerate(result['individual_results'], 1):
            cadastral_num = cad_result.get('cadastral_number', 'Unknown')
            karst_status = cad_result.get('karst_status', 'Unknown')
            print(f"  {i}. {cadastral_num}: {karst_status}")

def example_find_nearest_karst():
    """Example 3: Find nearest karst area to a cadastral."""
    print("\n🔍 Example 3: Find Nearest Karst Area")
    print("=" * 60)
    
    # Test with a cadastral that's likely not in karst but might be near it
    cadastral = "227-052-007-20"
    
    result = find_nearest_karst.invoke({
        "cadastral_number": cadastral,
        "max_search_miles": 10.0
    })
    
    print(f"Cadastral: {cadastral}")
    print(f"Nearest Karst Found: {result.get('nearest_karst_found', False)}")
    
    if result.get('cadastral_location'):
        location = result['cadastral_location']
        print(f"Location: {location['municipality']}, {location.get('neighborhood', 'N/A')}")
        print(f"Classification: {location['classification']}")
    
    if result.get('distance_analysis'):
        distance = result['distance_analysis']
        print(f"Distance: {distance['distance_miles']} miles")
        print(f"Category: {distance['distance_category']}")
    
    if result.get('proximity_assessment'):
        assessment = result['proximity_assessment']
        print(f"Risk Level: {assessment['risk_level']}")
        print(f"Regulatory Impact: {assessment['regulatory_impact']}")
    
    print(f"Message: {result.get('message', 'No message')}")

def example_comprehensive_analysis():
    """Example 4: Comprehensive karst proximity analysis."""
    print("\n📊 Example 4: Comprehensive Karst Proximity Analysis")
    print("=" * 60)
    
    # Test with multiple cadastrals for comprehensive analysis
    cadastrals = [
        "227-062-084-05",
        "227-052-007-20",
        "227-062-084-04"
    ]
    
    result = analyze_cadastral_karst_proximity.invoke({
        "cadastral_numbers": cadastrals,
        "analysis_radius_miles": 3.0
    })
    
    print(f"Total Cadastrals: {result.get('total_cadastrals', 0)}")
    print(f"Analysis Radius: {result.get('analysis_radius_miles', 0)} miles")
    
    if result.get('spatial_analysis'):
        spatial = result['spatial_analysis']
        print(f"\nSpatial Analysis:")
        print(f"  Direct Intersection: {spatial['direct_karst_intersection']['count']} ({spatial['direct_karst_intersection']['percentage']:.1f}%)")
        print(f"  Immediate Proximity: {spatial['immediate_proximity']['count']} ({spatial['immediate_proximity']['percentage']:.1f}%)")
        print(f"  Close Proximity: {spatial['close_proximity']['count']} ({spatial['close_proximity']['percentage']:.1f}%)")
        print(f"  No Impact: {spatial['no_karst_impact']['count']} ({spatial['no_karst_impact']['percentage']:.1f}%)")
    
    if result.get('risk_assessment'):
        risk = result['risk_assessment']
        print(f"\nRisk Assessment:")
        print(f"  Overall Risk Level: {risk['overall_risk_level']}")
        print(f"  High Risk: {risk['high_risk_cadastrals']}")
        print(f"  Moderate Risk: {risk['moderate_risk_cadastrals']}")
        print(f"  Low Risk: {risk['low_risk_cadastrals']}")
    
    if result.get('development_planning'):
        planning = result['development_planning']
        print(f"\nDevelopment Planning:")
        print(f"  Phased Approach Recommended: {planning['phased_approach_recommended']}")
        print(f"  Timeline Implications: {planning['timeline_implications']}")
        
        if planning.get('priority_areas'):
            print(f"  Priority Areas:")
            for area in planning['priority_areas']:
                print(f"    - {area['priority']}: {area['action']} ({area['cadastral_count']} cadastrals)")
    
    if result.get('recommendations'):
        print(f"\nRecommendations:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"  {i}. {rec['strategy']}: {rec['description']}")
    
    print(f"\nMessage: {result.get('message', 'No message')}")

def main():
    """Run all karst tools examples."""
    print("🏔️ MIPR KARST TOOLS - LANGGRAPH EXAMPLES")
    print("=" * 70)
    print("Demonstrating LangGraph tools for PRAPEC karst checking with cadastral inputs")
    
    try:
        example_single_cadastral_check()
        example_multiple_cadastrals_check()
        example_find_nearest_karst()
        example_comprehensive_analysis()
        
        print("\n" + "=" * 70)
        print("💡 TOOL USAGE SUMMARY:")
        print("✅ check_cadastral_karst - Single cadastral karst checking")
        print("✅ check_multiple_cadastrals_karst - Batch cadastral checking")
        print("✅ find_nearest_karst - Nearest karst area identification")
        print("✅ analyze_cadastral_karst_proximity - Comprehensive analysis")
        print("\n🔧 Integration with LangGraph:")
        print("   from mipr.karst import KARST_TOOLS")
        print("   # Add KARST_TOOLS to your agent's tool list")
        print("   # Tools provide comprehensive karst analysis for development planning")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure all dependencies are installed and services are accessible")

if __name__ == "__main__":
    main() 