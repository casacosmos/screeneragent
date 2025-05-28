#!/usr/bin/env python3
"""
Cadastral Center Point Calculator Tool

This module provides a specialized tool for calculating center point coordinates
from cadastral geometry data. It retrieves cadastral polygon geometry and computes
accurate center points using both standard geographic and projected coordinate methods.

Tool:
- calculate_cadastral_center_point: Calculate center point coordinates for a cadastral number
"""

import sys
import os
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.tools import tool
from .cadastral_search import MIPRCadastralSearch
from output_directory_manager import get_output_manager

# Import pyproj for accurate coordinate transformations
try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    print("⚠️  pyproj not available - using standard geographic calculations only")

# Coordinate system constants for Puerto Rico
WGS84_EPSG = 4326         # EPSG:4326 - WGS 84
NAD83_PR_EPSG = 2866      # EPSG:2866 - NAD83(HARN) / Puerto Rico and Virgin Is.
NAD83_HARN_EPSG = 4152    # EPSG:4152 - NAD83(HARN) geographic

class CadastralCenterPointInput(BaseModel):
    """Input schema for cadastral center point calculation"""
    cadastral_number: str = Field(description="Cadastral number to calculate center point for (e.g., '227-052-007-20')")
    output_coordinate_system: str = Field(default="WGS84", description="Output coordinate system: 'WGS84' or 'NAD83'")
    calculation_method: str = Field(default="projected", description="Calculation method: 'geographic', 'projected', or 'both'")
    include_polygon_data: bool = Field(default=False, description="Whether to include full polygon coordinates in response")
    save_to_file: bool = Field(default=True, description="Whether to save results to project data directory")

@tool("calculate_cadastral_center_point", args_schema=CadastralCenterPointInput)
def calculate_cadastral_center_point(
    cadastral_number: str,
    output_coordinate_system: str = "WGS84",
    calculation_method: str = "projected",
    include_polygon_data: bool = False,
    save_to_file: bool = True
) -> Dict[str, Any]:
    """
    Calculate accurate center point coordinates for a cadastral parcel using geometry data.
    
    This tool retrieves the polygon geometry for a specified cadastral number and calculates
    the geometric centroid (center point) using advanced mathematical methods. It supports
    multiple calculation approaches and coordinate systems for maximum accuracy.
    
    **Calculation Methods:**
    - **Geographic**: Standard centroid calculation using geographic coordinates (WGS84)
    - **Projected**: High-accuracy calculation using projected coordinates (NAD83 Puerto Rico)
    - **Both**: Performs both calculations and compares results for validation
    
    **Coordinate Systems:**
    - **WGS84**: World Geodetic System 1984 (EPSG:4326) - Global standard
    - **NAD83**: North American Datum 1983 (EPSG:4152) - Local Puerto Rico datum
    
    **Applications:**
    - Property surveying and mapping
    - Geographic analysis and planning
    - Coordinate reference for development projects
    - Integration with GIS systems
    - Legal property documentation
    
    **Data Source:**
    - Puerto Rico MIPR (Land Use Planning) Database
    - SIGE (Geographic Information System of Puerto Rico)
    
    Args:
        cadastral_number: Cadastral number to analyze (e.g., '227-052-007-20')
        output_coordinate_system: Output coordinate system ('WGS84' or 'NAD83')
        calculation_method: Method to use ('geographic', 'projected', or 'both')
        include_polygon_data: Whether to include full polygon coordinates
        save_to_file: Whether to save results to project data directory
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if calculation was successful
        - cadastral_number: Input cadastral number
        - center_point: Calculated center point coordinates
        - calculation_details: Information about calculation methods used
        - polygon_metadata: Polygon geometry metadata
        - coordinate_system_info: Details about coordinate systems
        - accuracy_assessment: Assessment of calculation accuracy
        - project_directory: Information about output files (if saved)
    """
    
    print(f"🎯 Calculating center point for cadastral: {cadastral_number}")
    print(f"📊 Calculation method: {calculation_method}")
    print(f"🗺️  Output coordinate system: {output_coordinate_system}")
    
    # Validate inputs
    if calculation_method not in ["geographic", "projected", "both"]:
        return {
            "success": False,
            "error": "Invalid calculation_method. Must be 'geographic', 'projected', or 'both'",
            "cadastral_number": cadastral_number
        }
    
    if output_coordinate_system.upper() not in ["WGS84", "NAD83"]:
        return {
            "success": False,
            "error": "Invalid output_coordinate_system. Must be 'WGS84' or 'NAD83'",
            "cadastral_number": cadastral_number
        }
    
    # Get or create project directory
    output_manager = get_output_manager()
    if not output_manager.current_project_dir and save_to_file:
        project_dir = output_manager.create_project_directory(
            cadastral_number=cadastral_number
        )
        print(f"📁 Created project directory: {project_dir}")
    elif save_to_file:
        project_dir = output_manager.current_project_dir
        print(f"📁 Using existing project directory: {project_dir}")
    
    try:
        # Initialize cadastral search
        search = MIPRCadastralSearch()
        
        # Search for cadastral with geometry
        print(f"🔍 Retrieving geometry data for cadastral {cadastral_number}")
        result = search.search_by_cadastral(cadastral_number, exact_match=True, include_geometry=True)
        
        if not result['success']:
            return {
                "success": False,
                "error": f"Failed to retrieve cadastral data: {result.get('error', 'Unknown error')}",
                "cadastral_number": cadastral_number
            }
        
        if result['feature_count'] == 0:
            return {
                "success": False,
                "error": f"Cadastral number {cadastral_number} not found in database",
                "cadastral_number": cadastral_number,
                "suggestion": "Verify the cadastral number format and try again"
            }
        
        # Get the primary result (largest area if multiple)
        cadastral_data = result['results'][0]
        
        print(f"✅ Found cadastral: {cadastral_data['cadastral_number']}")
        print(f"📍 Municipality: {cadastral_data['municipality']}")
        print(f"📏 Area: {cadastral_data['area_m2']:.2f} m²")
        
        # Extract geometry
        geometry = cadastral_data.get('geometry')
        if not geometry or 'rings' not in geometry:
            return {
                "success": False,
                "error": f"No polygon geometry found for cadastral {cadastral_number}",
                "cadastral_number": cadastral_number,
                "cadastral_info": {
                    "municipality": cadastral_data['municipality'],
                    "area_m2": cadastral_data['area_m2']
                }
            }
        
        # Extract polygon coordinates
        polygon_coords = _extract_polygon_coordinates(geometry)
        
        if not polygon_coords:
            return {
                "success": False,
                "error": f"Could not extract valid polygon coordinates for cadastral {cadastral_number}",
                "cadastral_number": cadastral_number
            }
        
        print(f"📍 Extracted {len(polygon_coords)} polygon coordinates")
        
        # Perform center point calculations based on method
        calculation_results = {}
        
        if calculation_method in ["geographic", "both"]:
            print(f"🧮 Calculating geographic centroid...")
            geo_center = _calculate_geographic_centroid(polygon_coords)
            calculation_results["geographic"] = {
                "method": "Geographic Centroid (Shoelace Formula)",
                "center_point_wgs84": geo_center,
                "description": "Standard geometric centroid calculated in WGS84 coordinates",
                "accuracy": "Standard accuracy for geographic coordinates"
            }
            print(f"📍 Geographic centroid (WGS84): ({geo_center[0]:.8f}, {geo_center[1]:.8f})")
        
        if calculation_method in ["projected", "both"] and PYPROJ_AVAILABLE:
            print(f"🎯 Calculating projected centroid (high accuracy)...")
            proj_center = _calculate_projected_centroid(polygon_coords)
            calculation_results["projected"] = {
                "method": "Projected Centroid (NAD83 Puerto Rico)",
                "center_point_wgs84": proj_center,
                "description": "High-accuracy centroid calculated using projected coordinates",
                "accuracy": "High accuracy using local projected coordinate system"
            }
            print(f"📍 Projected centroid (WGS84): ({proj_center[0]:.8f}, {proj_center[1]:.8f})")
        elif calculation_method in ["projected", "both"] and not PYPROJ_AVAILABLE:
            print(f"⚠️  pyproj not available - falling back to geographic calculation")
            if "geographic" not in calculation_results:
                geo_center = _calculate_geographic_centroid(polygon_coords)
                calculation_results["geographic"] = {
                    "method": "Geographic Centroid (Fallback)",
                    "center_point_wgs84": geo_center,
                    "description": "Geographic centroid (pyproj not available for projected calculation)",
                    "accuracy": "Standard accuracy - projected calculation unavailable"
                }
        
        # Determine the primary center point
        if calculation_method == "both" and len(calculation_results) > 1:
            # Use projected result as primary if available
            primary_method = "projected" if "projected" in calculation_results else "geographic"
            primary_center_wgs84 = calculation_results[primary_method]["center_point_wgs84"]
            
            # Calculate difference between methods for validation
            if "geographic" in calculation_results and "projected" in calculation_results:
                geo_center = calculation_results["geographic"]["center_point_wgs84"]
                proj_center = calculation_results["projected"]["center_point_wgs84"]
                
                # Calculate distance difference in meters (approximate)
                lat_diff = abs(geo_center[1] - proj_center[1])
                lon_diff = abs(geo_center[0] - proj_center[0])
                
                # Approximate conversion to meters (at Puerto Rico latitude ~18°)
                lat_meters = lat_diff * 111320  # 1 degree latitude ≈ 111,320 meters
                lon_meters = lon_diff * 111320 * math.cos(math.radians(18))  # Adjust for longitude
                
                total_diff_meters = math.sqrt(lat_meters**2 + lon_meters**2)
                
                calculation_results["comparison"] = {
                    "difference_meters": total_diff_meters,
                    "difference_assessment": _assess_calculation_difference(total_diff_meters),
                    "recommended_method": primary_method
                }
                print(f"📊 Method comparison: {total_diff_meters:.2f} meters difference")
        else:
            # Single method calculation
            primary_method = list(calculation_results.keys())[0]
            primary_center_wgs84 = calculation_results[primary_method]["center_point_wgs84"]
        
        # Convert to requested output coordinate system
        if output_coordinate_system.upper() == "NAD83":
            center_lon, center_lat = _convert_wgs84_to_nad83(primary_center_wgs84[0], primary_center_wgs84[1])
            coord_system_name = "NAD83(HARN) (EPSG:4152)"
            print(f"🔄 Converting to NAD83: ({primary_center_wgs84[0]:.8f}, {primary_center_wgs84[1]:.8f}) → ({center_lon:.8f}, {center_lat:.8f})")
        else:
            center_lon, center_lat = primary_center_wgs84
            coord_system_name = "WGS84 (EPSG:4326)"
            print(f"📍 Using WGS84 coordinates: ({center_lon:.8f}, {center_lat:.8f})")
        
        # Build response
        response = {
            "success": True,
            "cadastral_number": cadastral_number,
            "query_time": datetime.now().isoformat(),
            
            "center_point": {
                "longitude": center_lon,
                "latitude": center_lat,
                "coordinate_system": coord_system_name,
                "precision": "8 decimal places",
                "calculation_method": primary_method
            },
            
            "calculation_details": calculation_results,
            
            "polygon_metadata": {
                "coordinate_count": len(polygon_coords),
                "geometry_type": "Polygon",
                "rings_count": len(geometry.get('rings', [])),
                "has_holes": len(geometry.get('rings', [])) > 1,
                "area_m2": cadastral_data['area_m2'],
                "area_hectares": cadastral_data['area_hectares']
            },
            
            "coordinate_system_info": {
                "input_system": "WGS84 (from MIPR service)",
                "output_system": coord_system_name,
                "conversion_applied": output_coordinate_system.upper() == "NAD83",
                "pyproj_available": PYPROJ_AVAILABLE
            },
            
            "accuracy_assessment": {
                "method_used": primary_method,
                "accuracy_level": "High" if primary_method == "projected" else "Standard",
                "notes": _get_accuracy_notes(primary_method, PYPROJ_AVAILABLE)
            },
            
            "cadastral_info": {
                "municipality": cadastral_data['municipality'],
                "neighborhood": cadastral_data['neighborhood'],
                "region": cadastral_data['region'],
                "classification": cadastral_data['classification_description'],
                "area_m2": cadastral_data['area_m2'],
                "area_hectares": cadastral_data['area_hectares']
            }
        }
        
        # Include polygon data if requested
        if include_polygon_data:
            response["polygon_coordinates"] = polygon_coords
            print(f"📍 Including {len(polygon_coords)} polygon coordinates in response")
        
        # Save results to file if requested
        if save_to_file and output_manager.current_project_dir:
            data_dir = output_manager.get_subdirectory("data")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_cadastral = cadastral_number.replace('-', '_').replace('/', '_')
            
            # Save center point results
            center_point_file = os.path.join(data_dir, f"center_point_{safe_cadastral}_{timestamp}.json")
            
            import json
            with open(center_point_file, 'w') as f:
                json.dump(response, f, indent=2, default=str)
            print(f"💾 Center point results saved to: {center_point_file}")
            
            response["project_directory"] = output_manager.get_project_info()
            response["files_generated"] = {
                "center_point_file": center_point_file
            }
            
            # Save polygon coordinates to separate file if included
            if include_polygon_data:
                polygon_file = os.path.join(data_dir, f"polygon_coords_{safe_cadastral}_{timestamp}.json")
                polygon_data = {
                    "cadastral_number": cadastral_number,
                    "polygon_coordinates": polygon_coords,
                    "coordinate_count": len(polygon_coords),
                    "coordinate_system": "WGS84 (EPSG:4326)"
                }
                with open(polygon_file, 'w') as f:
                    json.dump(polygon_data, f, indent=2, default=str)
                print(f"🗺️  Polygon coordinates saved to: {polygon_file}")
                response["files_generated"]["polygon_file"] = polygon_file
        
        print(f"✅ Center point calculation completed successfully")
        print(f"📍 Final center point ({coord_system_name}): ({center_lon:.6f}, {center_lat:.6f})")
        
        return response
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Center point calculation failed: {str(e)}",
            "cadastral_number": cadastral_number,
            "query_time": datetime.now().isoformat()
        }
        
        if save_to_file and output_manager.current_project_dir:
            error_response["project_directory"] = output_manager.get_project_info()
        
        return error_response

def _extract_polygon_coordinates(geometry: Dict[str, Any]) -> Optional[List[Tuple[float, float]]]:
    """
    Extract and convert polygon coordinates from geometry data.
    
    Args:
        geometry: Geometry dictionary from MIPR service
        
    Returns:
        List of (longitude, latitude) coordinate pairs in WGS84, or None if no valid geometry
    """
    if not geometry or 'rings' not in geometry:
        return None
    
    rings = geometry['rings']
    if not rings:
        return None
    
    # Use the outer ring (first ring)
    outer_ring = rings[0]
    if not outer_ring:
        return None
    
    # Convert coordinates from Web Mercator to WGS84
    wgs84_coords = []
    for point in outer_ring:
        if len(point) >= 2:
            x, y = point[0], point[1]
            lon, lat = _convert_web_mercator_to_wgs84(x, y)
            wgs84_coords.append((lon, lat))
    
    return wgs84_coords if wgs84_coords else None

def _convert_web_mercator_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """
    Convert Web Mercator (EPSG:3857) coordinates to WGS84 (EPSG:4326).
    
    Args:
        x: X coordinate in Web Mercator (meters)
        y: Y coordinate in Web Mercator (meters)
        
    Returns:
        Tuple of (longitude, latitude) in WGS84
    """
    if PYPROJ_AVAILABLE:
        # Use pyproj for accurate transformation
        transformer = Transformer.from_crs(3857, WGS84_EPSG, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return (lon, lat)
    else:
        # Fallback to approximate conversion
        lon = x / 20037508.34 * 180
        lat = y / 20037508.34 * 180
        lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
        return (lon, lat)

def _calculate_geographic_centroid(coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate the geometric centroid of a polygon using the shoelace formula.
    
    This method calculates the area-weighted centroid, which is more accurate than
    the simple arithmetic mean of vertices, especially for irregular polygons.
    
    Args:
        coords: List of (longitude, latitude) coordinate pairs forming a closed polygon
        
    Returns:
        Tuple of (center_longitude, center_latitude)
    """
    if not coords:
        return (0.0, 0.0)
    
    # Ensure polygon is closed (first and last points are the same)
    if len(coords) > 1 and coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    
    if len(coords) < 4:  # Need at least 3 unique points plus closure
        # Fall back to arithmetic mean for degenerate cases
        unique_coords = list(set(coords))
        center_lon = sum(coord[0] for coord in unique_coords) / len(unique_coords)
        center_lat = sum(coord[1] for coord in unique_coords) / len(unique_coords)
        return (center_lon, center_lat)
    
    # Calculate polygon area and centroid coordinates using the shoelace formula
    area = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    
    n = len(coords) - 1  # Exclude the duplicate closing point
    
    for i in range(n):
        j = (i + 1) % n
        xi, yi = coords[i]
        xj, yj = coords[j]
        
        # Cross product for area calculation
        cross = xi * yj - xj * yi
        area += cross
        
        # Accumulate centroid coordinates
        centroid_x += (xi + xj) * cross
        centroid_y += (yi + yj) * cross
    
    area = area / 2.0
    
    # Handle degenerate case where area is zero or very small
    if abs(area) < 1e-12:
        # Fall back to arithmetic mean
        unique_coords = list(set(coords[:-1]))  # Exclude duplicate closing point
        center_lon = sum(coord[0] for coord in unique_coords) / len(unique_coords)
        center_lat = sum(coord[1] for coord in unique_coords) / len(unique_coords)
        return (center_lon, center_lat)
    
    # Complete centroid calculation
    centroid_x = centroid_x / (6.0 * area)
    centroid_y = centroid_y / (6.0 * area)
    
    return (centroid_x, centroid_y)

def _calculate_projected_centroid(coords: List[Tuple[float, float]], 
                                target_epsg: int = NAD83_PR_EPSG) -> Tuple[float, float]:
    """
    Calculate polygon centroid using projected coordinates for higher accuracy.
    
    This method projects the polygon to a local coordinate system (NAD83 Puerto Rico),
    calculates the centroid in projected coordinates, then converts back to geographic.
    This approach is more accurate for irregular polygons over larger areas.
    
    Args:
        coords: List of (longitude, latitude) coordinate pairs in WGS84
        target_epsg: EPSG code for the projected coordinate system to use
        
    Returns:
        Tuple of (center_longitude, center_latitude) in WGS84
    """
    if not PYPROJ_AVAILABLE or not coords:
        # Fall back to standard calculation
        return _calculate_geographic_centroid(coords)
    
    try:
        # Transform to projected coordinates
        transformer_to_proj = Transformer.from_crs(WGS84_EPSG, target_epsg, always_xy=True)
        projected_coords = []
        
        for lon, lat in coords:
            x, y = transformer_to_proj.transform(lon, lat)
            projected_coords.append((x, y))
        
        # Calculate centroid in projected coordinates
        proj_center_x, proj_center_y = _calculate_geographic_centroid(projected_coords)
        
        # Transform back to geographic coordinates
        transformer_to_geo = Transformer.from_crs(target_epsg, WGS84_EPSG, always_xy=True)
        center_lon, center_lat = transformer_to_geo.transform(proj_center_x, proj_center_y)
        
        return (center_lon, center_lat)
        
    except Exception as e:
        print(f"⚠️  Projected centroid calculation failed: {e}")
        # Fall back to standard calculation
        return _calculate_geographic_centroid(coords)

def _convert_wgs84_to_nad83(longitude_wgs84: float, latitude_wgs84: float) -> Tuple[float, float]:
    """
    Convert WGS84 coordinates to NAD83 for Puerto Rico.
    
    Args:
        longitude_wgs84: Longitude in WGS84 (degrees)
        latitude_wgs84: Latitude in WGS84 (degrees)
        
    Returns:
        Tuple of (longitude_nad83, latitude_nad83)
    """
    if PYPROJ_AVAILABLE:
        # Use pyproj for accurate transformation
        transformer = Transformer.from_crs(WGS84_EPSG, NAD83_HARN_EPSG, always_xy=True)
        lon_nad83, lat_nad83 = transformer.transform(longitude_wgs84, latitude_wgs84)
        return (lon_nad83, lat_nad83)
    else:
        # Fallback to approximate conversion (very small difference for Puerto Rico)
        longitude_nad83 = longitude_wgs84 - 0.00002
        latitude_nad83 = latitude_wgs84 - 0.00001
        return (longitude_nad83, latitude_nad83)

def _assess_calculation_difference(difference_meters: float) -> str:
    """Assess the significance of the difference between calculation methods."""
    if difference_meters < 1.0:
        return "Excellent agreement - difference less than 1 meter"
    elif difference_meters < 5.0:
        return "Good agreement - difference less than 5 meters"
    elif difference_meters < 10.0:
        return "Acceptable agreement - difference less than 10 meters"
    elif difference_meters < 50.0:
        return "Moderate difference - may indicate irregular polygon shape"
    else:
        return "Significant difference - recommend using projected method"

def _get_accuracy_notes(method: str, pyproj_available: bool) -> List[str]:
    """Get accuracy notes based on calculation method and available tools."""
    notes = []
    
    if method == "projected" and pyproj_available:
        notes.extend([
            "High-accuracy calculation using projected coordinates",
            "Optimal for surveying and engineering applications",
            "Accounts for local coordinate system distortions"
        ])
    elif method == "projected" and not pyproj_available:
        notes.extend([
            "Projected calculation requested but pyproj not available",
            "Fallback to geographic calculation used",
            "Install pyproj for highest accuracy"
        ])
    elif method == "geographic":
        notes.extend([
            "Standard geographic centroid calculation",
            "Suitable for most mapping and GIS applications",
            "May have minor distortions for very large or irregular polygons"
        ])
    
    notes.append("Coordinates calculated to 8 decimal places precision")
    
    return notes

# Export the tool for easy import
CADASTRAL_CENTER_POINT_TOOL = [calculate_cadastral_center_point]

def get_center_point_tool_description() -> str:
    """Get description of the cadastral center point tool"""
    return "Calculate accurate center point coordinates for a cadastral parcel using polygon geometry data - supports multiple calculation methods and coordinate systems"

if __name__ == "__main__":
    print("🎯 Cadastral Center Point Calculator Tool")
    print("=" * 60)
    print("This module provides specialized center point calculation for cadastral parcels:")
    print("✓ Retrieves polygon geometry from MIPR database")
    print("✓ Calculates geometric centroid using advanced methods")
    print("✓ Supports both geographic and projected coordinate calculations")
    print("✓ Provides multiple coordinate system outputs")
    print("✓ Includes accuracy assessment and validation")
    print()
    print("Usage:")
    print("  from cadastral_center_point_tool import CADASTRAL_CENTER_POINT_TOOL")
    print("  # Use with LangGraph agents or ToolNode")
    print()
    print("Example:")
    print("  result = calculate_cadastral_center_point('227-052-007-20')")
    print("  center = result['center_point']")
    print("  print(f\"Center: ({center['longitude']}, {center['latitude']})\")")
    print("=" * 60) 