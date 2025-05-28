#!/usr/bin/env python3
"""
Example Usage of PRAPEC Karst Checker

Simple examples showing how to use the PRAPEC karst checker for different scenarios.
"""

from prapec_karst_checker import (
    PrapecKarstChecker,
    check_coordinates_for_karst,
    check_cadastral_for_karst,
    check_multiple_cadastrals_for_karst
)

def main():
    """Run example usage scenarios."""
    
    print("🏔️  PRAPEC KARST CHECKER - USAGE EXAMPLES")
    print("=" * 70)
    
    # Example 1: Check if coordinates are in karst area
    print("\n📍 Example 1: Check coordinates")
    print("-" * 40)
    
    # Test coordinates in known karst area (Arecibo region)
    lon, lat = -66.7, 18.4
    result = check_coordinates_for_karst(lon, lat, buffer_miles=0.5)
    
    if result['success']:
        if result['in_karst']:
            print(f"✅ Coordinates ({lon}, {lat}) are DIRECTLY in PRAPEC karst area!")
            print(f"   Karst area: {result['karst_info']['nombre']}")
            print(f"   Regulation: {result['karst_info']['regla']}")
        elif result['karst_proximity'] == 'nearby':
            print(f"🔍 Coordinates ({lon}, {lat}) have karst NEARBY (within {result['distance_miles']} miles)")
            print(f"   Karst area: {result['karst_info']['nombre']}")
        else:
            print(f"❌ Coordinates ({lon}, {lat}) are NOT in karst area")
    else:
        print(f"❌ Error checking coordinates: {result['error']}")
    
    # Example 2: Check coordinates outside karst area
    print("\n📍 Example 2: Check coordinates outside karst")
    print("-" * 40)
    
    # Test coordinates in San Juan (not in karst)
    lon2, lat2 = -66.1, 18.4
    result2 = check_coordinates_for_karst(lon2, lat2, buffer_miles=0.5)
    
    if result2['success']:
        if result2['in_karst']:
            print(f"✅ Coordinates ({lon2}, {lat2}) are DIRECTLY in PRAPEC karst area!")
        elif result2['karst_proximity'] == 'nearby':
            print(f"🔍 Coordinates ({lon2}, {lat2}) have karst NEARBY (within {result2['distance_miles']} miles)")
            print(f"   Karst area: {result2['karst_info']['nombre']}")
        else:
            print(f"❌ Coordinates ({lon2}, {lat2}) are NOT in karst area (no karst within 0.5 miles)")
    else:
        print(f"❌ Error checking coordinates: {result2['error']}")
    
    # Example 3: Check a single cadastral number
    print("\n🏠 Example 3: Check single cadastral")
    print("-" * 40)
    
    cadastral = "227-052-007-20"
    result3 = check_cadastral_for_karst(cadastral, buffer_miles=1.0)  # Use 1 mile buffer
    
    if result3['success']:
        print(f"Cadastral: {cadastral}")
        print(f"Municipality: {result3['cadastral_info']['municipality']}")
        print(f"Classification: {result3['cadastral_info']['classification']}")
        
        if result3['in_karst']:
            print(f"✅ Cadastral INTERSECTS with PRAPEC karst area!")
            print(f"   Karst area: {result3['karst_info']['nombre']}")
        elif result3['karst_proximity'] == 'nearby':
            print(f"🔍 Cadastral has karst NEARBY (within {result3['distance_miles']} miles)")
            print(f"   Karst area: {result3['karst_info']['nombre']}")
        else:
            print(f"❌ Cadastral has NO karst within {result3['buffer_miles']} miles")
    else:
        print(f"❌ Error checking cadastral: {result3['error']}")
    
    # Example 4: Check multiple cadastrals
    print("\n🏠 Example 4: Check multiple cadastrals")
    print("-" * 40)
    
    cadastrals = [
        "227-062-084-05",  # Juncos
        "227-052-007-20",  # Juncos
        "227-062-084-04"   # Juncos
    ]
    
    result4 = check_multiple_cadastrals_for_karst(cadastrals, buffer_miles=0.5)
    
    if result4['success']:
        summary = result4['summary']
        print(f"Checked {result4['total_cadastrals']} cadastrals:")
        print(f"  ✅ Directly in karst: {summary['in_karst']}")
        print(f"  🔍 Karst nearby: {summary['nearby_karst']}")
        print(f"  ❌ No karst: {summary['no_karst']}")
        print(f"  ⚠️  Errors: {summary['errors']}")
        
        if result4.get('karst_info'):
            print(f"\nKarst found: {result4['karst_info']['nombre']}")
        else:
            print(f"\nNo karst areas found for any cadastrals")
    
    # Example 5: Using the class directly for more control
    print("\n🔧 Example 5: Using the class directly")
    print("-" * 40)
    
    checker = PrapecKarstChecker()
    
    # Check coordinates with custom buffer
    result5 = checker.check_coordinates(-66.6, 18.4, buffer_miles=2.0, include_buffer_search=True)
    checker.print_result(result5)
    
    print("\n" + "=" * 70)
    print("💡 USAGE TIPS:")
    print("- Use buffer_miles to control search radius (default: 0.5 miles)")
    print("- Set include_buffer_search=False to only check exact intersections")
    print("- Coordinates should be in WGS84 (longitude, latitude)")
    print("- The PRAPEC karst area covers approximately 87,375 hectares")
    print("- Regulation 259 governs the PRAPEC area")
    print("=" * 70)

if __name__ == "__main__":
    main() 