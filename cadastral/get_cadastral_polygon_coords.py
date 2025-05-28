#!/usr/bin/env python3
"""
Get Cadastral Polygon Coordinates

Utility script to extract polygon coordinates from cadastral numbers for testing.
"""

import sys
import os
import math
from typing import List, Tuple, Optional

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .cadastral_search import MIPRCadastralSearch

def get_cadastral_polygon_coords(cadastral_number: str) -> Optional[List[Tuple[float, float]]]:
    """
    Get polygon coordinates for a cadastral number.
    
    Args:
        cadastral_number: The cadastral number to search for
        
    Returns:
        List of (longitude, latitude) coordinate pairs, or None if not found
    """
    
    print(f"🔍 Searching for cadastral: {cadastral_number}")
    
    # Initialize search with geometry enabled
    search = MIPRCadastralSearch()
    
    try:
        # Search for cadastral with geometry
        result = search.search_by_cadastral(cadastral_number, exact_match=True, include_geometry=True)
        
        if not result['success'] or result['feature_count'] == 0:
            print(f"❌ Cadastral {cadastral_number} not found")
            return None
        
        feature = result['results'][0]
        print(f"✅ Found cadastral: {feature['cadastral_number']}")
        print(f"   Municipality: {feature['municipality']}")
        print(f"   Area: {feature['area_m2']:.2f} m²")
        
        # Extract geometry
        geometry = feature.get('geometry')
        if not geometry or 'rings' not in geometry:
            print(f"❌ No polygon geometry found for cadastral {cadastral_number}")
            return None
        
        rings = geometry['rings']
        if not rings:
            print(f"❌ No coordinate rings found for cadastral {cadastral_number}")
            return None
        
        # Use the outer ring (first ring)
        outer_ring = rings[0]
        print(f"📍 Found {len(outer_ring)} coordinate points")
        
        # Convert from Web Mercator to WGS84
        wgs84_coords = []
        for point in outer_ring:
            if len(point) >= 2:
                x, y = point[0], point[1]
                
                # Convert from Web Mercator (EPSG:3857) to WGS84 (EPSG:4326)
                lon = x / 20037508.34 * 180
                lat = y / 20037508.34 * 180
                lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
                
                wgs84_coords.append((lon, lat))
        
        print(f"✅ Converted {len(wgs84_coords)} coordinates to WGS84")
        return wgs84_coords
        
    except Exception as e:
        print(f"❌ Error getting polygon coordinates: {str(e)}")
        return None

def print_polygon_coords(coords: List[Tuple[float, float]], format_type: str = "python"):
    """
    Print polygon coordinates in different formats.
    
    Args:
        coords: List of (longitude, latitude) coordinate pairs
        format_type: Format type ("python", "json", "wkt")
    """
    
    if not coords:
        print("No coordinates to display")
        return
    
    print(f"\n📋 Polygon coordinates ({len(coords)} points) - {format_type.upper()} format:")
    print("=" * 60)
    
    if format_type == "python":
        print("polygon_coords = [")
        for i, (lon, lat) in enumerate(coords):
            if i < len(coords) - 1:
                print(f"    ({lon}, {lat}),")
            else:
                print(f"    ({lon}, {lat})")
        print("]")
        
    elif format_type == "json":
        print("[")
        for i, (lon, lat) in enumerate(coords):
            if i < len(coords) - 1:
                print(f"    [{lon}, {lat}],")
            else:
                print(f"    [{lon}, {lat}]")
        print("]")
        
    elif format_type == "wkt":
        coord_str = ", ".join([f"{lon} {lat}" for lon, lat in coords])
        print(f"POLYGON(({coord_str}))")
    
    print("=" * 60)

def test_known_cadastrals():
    """Test with known cadastral numbers from the database."""
    
    print("🧪 Testing with known cadastral numbers")
    print("=" * 60)
    
    # Known cadastrals from test data
    test_cadastrals = [
        "227-062-084-05",  # Small mixed-use parcel in Juncos
        "227-052-007-20",  # Public land parcel in Juncos
        "227-062-084-04",  # Another mixed-use parcel in Juncos
    ]
    
    for cadastral in test_cadastrals:
        print(f"\n🏠 Testing cadastral: {cadastral}")
        print("-" * 40)
        
        coords = get_cadastral_polygon_coords(cadastral)
        if coords:
            print_polygon_coords(coords, "python")
            
            # Calculate approximate area
            area_deg2 = calculate_polygon_area_approx(coords)
            print(f"📏 Approximate area: {area_deg2:.8f} square degrees")
        
        print("-" * 40)

def calculate_polygon_area_approx(coords: List[Tuple[float, float]]) -> float:
    """Calculate approximate polygon area using shoelace formula."""
    if len(coords) < 3:
        return 0
    
    area = 0
    n = len(coords)
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2

if __name__ == "__main__":
    print("🗺️  Cadastral Polygon Coordinates Extractor")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Command line usage
        cadastral_number = sys.argv[1]
        format_type = sys.argv[2] if len(sys.argv) > 2 else "python"
        
        coords = get_cadastral_polygon_coords(cadastral_number)
        if coords:
            print_polygon_coords(coords, format_type)
    else:
        # Test mode
        test_known_cadastrals()
    
    print("\n💡 Usage:")
    print("   python get_cadastral_polygon_coords.py <cadastral_number> [format]")
    print("   python get_cadastral_polygon_coords.py 227-062-084-05 python")
    print("   python get_cadastral_polygon_coords.py 227-062-084-05 json")
    print("   python get_cadastral_polygon_coords.py 227-062-084-05 wkt") 