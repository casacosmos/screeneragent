#!/usr/bin/env python3
"""
Cadastral Data Tool for LangGraph Agents

This module provides focused tools for retrieving cadastral data from coordinates
or cadastral numbers without map generation complexity. Designed specifically
for LangGraph agents that need clean, structured cadastral information.

Tools:
- get_cadastral_data_from_coordinates: Get cadastral data for given coordinates
- get_cadastral_data_from_number: Get detailed data for a specific cadastral number
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
from .point_lookup import MIPRPointLookup
from .cadastral_search import MIPRCadastralSearch
from output_directory_manager import get_output_manager

# Import pyproj for accurate coordinate transformations
try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    print("⚠️  pyproj not available - using approximate coordinate transformations")

# Coordinate system constants for Puerto Rico
# Fallback approximate values if pyproj is not available
NAD83_TO_WGS84_OFFSET_LAT = -0.00001  # Approximate latitude offset in degrees
NAD83_TO_WGS84_OFFSET_LON = 0.00002   # Approximate longitude offset in degrees

# Define coordinate systems
WEB_MERCATOR_EPSG = 3857  # EPSG:3857 - WGS 84 / Pseudo-Mercator
WGS84_EPSG = 4326         # EPSG:4326 - WGS 84
NAD83_PR_EPSG = 2866      # EPSG:2866 - NAD83(HARN) / Puerto Rico and Virgin Is.

class CoordinateCadastralInput(BaseModel):
    """Input schema for coordinate-based cadastral lookup"""
    longitude: float = Field(description="Longitude coordinate (e.g., -66.150906 for Puerto Rico)")
    latitude: float = Field(description="Latitude coordinate (e.g., 18.434059 for Puerto Rico)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location")
    coordinate_system: str = Field(default="auto", description="Coordinate system: 'NAD83', 'WGS84', or 'auto' to detect automatically")

class CadastralNumberInput(BaseModel):
    """Input schema for cadastral number lookup"""
    cadastral_number: str = Field(description="Cadastral number (e.g., '227-052-007-20')")
    include_geometry: bool = Field(default=False, description="Whether to include polygon geometry coordinates and center point")
    return_polygon_coordinates: bool = Field(default=False, description="Whether to return the full polygon coordinates array (can be large)")
    output_coordinate_system: str = Field(default="NAD83", description="Output coordinate system for center point: 'NAD83' or 'WGS84'")

@tool("get_cadastral_data_from_coordinates", args_schema=CoordinateCadastralInput)
def get_cadastral_data_from_coordinates(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    coordinate_system: str = "auto"
) -> Dict[str, Any]:
    """
    Get cadastral data for the parcel containing the given coordinates.
    
    This tool performs a point-in-polygon query to find the cadastral parcel
    that contains the specified coordinates and returns detailed information
    about that parcel. All data files are organized into a custom project directory.
    
    **Information Provided:**
    - Cadastral number and identification
    - Land use classification and zoning
    - Municipality, neighborhood, and region
    - Area measurements (square meters, hectares, acres)
    - Regulatory status and case information
    - Property details and administrative data
    
    **Data Source:**
    - Puerto Rico MIPR (Land Use Planning) Database
    - SIGE (Geographic Information System of Puerto Rico)
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere, e.g., -66.150906)
        latitude: Latitude coordinate (positive for northern hemisphere, e.g., 18.434059)
        location_name: Optional descriptive name for the location
        coordinate_system: Coordinate system of the input coordinates
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if lookup was successful
        - coordinates: Input coordinates
        - cadastral_info: Complete cadastral parcel information
        - land_use: Land use classification and zoning details
        - location_details: Municipality, neighborhood, and regional information
        - area_measurements: Area in various units
        - regulatory_status: Status, case numbers, and regulatory information
        - query_metadata: Query timestamp and data source information
        - project_directory: Information about the custom output directory
    """
    
    if location_name is None:
        location_name = f"Coordinates ({longitude:.6f}, {latitude:.6f})"
    
    # Determine coordinate system
    if coordinate_system.lower() == "auto":
        detected_system = _detect_coordinate_system(longitude, latitude)
        print(f"🔍 Auto-detected coordinate system: {detected_system}")
    else:
        detected_system = coordinate_system.upper()
        print(f"🔍 Using specified coordinate system: {detected_system}")
    
    # Convert coordinates to WGS84 if needed (MIPR service expects WGS84)
    if detected_system == "NAD83":
        wgs84_lon, wgs84_lat = _convert_nad83_to_wgs84(longitude, latitude)
        print(f"🔄 Converting NAD83 to WGS84: ({longitude:.8f}, {latitude:.8f}) → ({wgs84_lon:.8f}, {wgs84_lat:.8f})")
        lookup_lon, lookup_lat = wgs84_lon, wgs84_lat
    else:
        lookup_lon, lookup_lat = longitude, latitude
        print(f"📍 Using coordinates as-is (WGS84): ({longitude:.8f}, {latitude:.8f})")
    
    print(f"🔍 Looking up cadastral data at: {location_name}")
    print(f"📍 Input coordinates ({detected_system}): ({longitude:.8f}, {latitude:.8f})")
    if detected_system == "NAD83":
        print(f"📍 Lookup coordinates (WGS84): ({lookup_lon:.8f}, {lookup_lat:.8f})")
    
    # Get or create project directory
    output_manager = get_output_manager()
    if not output_manager.current_project_dir:
        # Create project directory if not already created
        project_dir = output_manager.create_project_directory(
            location_name=location_name,
            coordinates=(lookup_lon, lookup_lat)
        )
        print(f"📁 Created project directory: {project_dir}")
    else:
        project_dir = output_manager.current_project_dir
        print(f"📁 Using existing project directory: {project_dir}")
    
    try:
        # Initialize point lookup
        lookup = MIPRPointLookup()
        
        # Perform exact point lookup
        result = lookup.lookup_point_exact(lookup_lon, lookup_lat)
        
        if not result['success']:
            error_response = {
                "success": False,
                "error": result.get('error', 'Lookup failed'),
                "coordinates": {"longitude": lookup_lon, "latitude": lookup_lat},
                "location_name": location_name,
                "query_time": datetime.now().isoformat(),
                "project_directory": output_manager.get_project_info()
            }
            return error_response
        
        if result['feature_count'] == 0:
            no_data_response = {
                "success": True,
                "found_cadastral": False,
                "coordinates": {"longitude": lookup_lon, "latitude": lookup_lat},
                "location_name": location_name,
                "message": "No cadastral parcel found at the specified coordinates",
                "suggestion": "Verify coordinates are within Puerto Rico boundaries",
                "query_time": datetime.now().isoformat(),
                "project_directory": output_manager.get_project_info()
            }
            return no_data_response
        
        # Extract cadastral data
        cadastral_data = result['cadastral_data']
        
        # Save cadastral data to project data directory
        data_dir = output_manager.get_subdirectory("data")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{lookup_lon}_{lookup_lat}".replace('-', 'neg').replace('.', 'p')
        cadastral_data_file = os.path.join(data_dir, f"cadastral_data_{coords}_{timestamp}.json")
        
        import json
        with open(cadastral_data_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Cadastral data saved to: {cadastral_data_file}")
        
        # Format response
        response = {
            "success": True,
            "found_cadastral": True,
            "coordinates": {"longitude": lookup_lon, "latitude": lookup_lat},
            "location_name": location_name,
            "query_time": datetime.now().isoformat(),
            
            "cadastral_info": {
                "cadastral_number": cadastral_data.get('cadastral_number'),
                "municipality": cadastral_data.get('municipality'),
                "neighborhood": cadastral_data.get('neighborhood'),
                "region": cadastral_data.get('region'),
                "property_type": "Cadastral Parcel"
            },
            
            "land_use": {
                "classification_code": cadastral_data.get('classification_code'),
                "classification_description": cadastral_data.get('classification_description'),
                "sub_classification": cadastral_data.get('sub_classification'),
                "sub_classification_description": cadastral_data.get('sub_classification_description'),
                "zoning_category": _determine_zoning_category(cadastral_data.get('classification_description', ''))
            },
            
            "location_details": {
                "municipality": cadastral_data.get('municipality'),
                "neighborhood": cadastral_data.get('neighborhood'),
                "region": cadastral_data.get('region'),
                "administrative_level": "Municipal",
                "island": "Puerto Rico"
            },
            
            "area_measurements": {
                "area_square_meters": cadastral_data.get('area_m2', 0),
                "area_hectares": cadastral_data.get('area_hectares', 0),
                "area_acres": cadastral_data.get('area_hectares', 0) * 2.47105 if cadastral_data.get('area_hectares') else 0,
                "area_square_feet": cadastral_data.get('area_m2', 0) * 10.7639 if cadastral_data.get('area_m2') else 0
            },
            
            "regulatory_status": {
                "status": cadastral_data.get('status'),
                "case_number": cadastral_data.get('case_number'),
                "resolution": cadastral_data.get('resolution'),
                "regulatory_implications": _assess_regulatory_implications(cadastral_data)
            },
            
            "data_source": {
                "database": "Puerto Rico MIPR (Land Use Planning) Database",
                "service_url": "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer",
                "coordinate_system": "WGS84 (EPSG:4326)",
                "data_type": "Official Cadastral Records",
                "lookup_method": "Point-in-polygon exact intersection"
            },
            
            "project_directory": output_manager.get_project_info(),
            "files_generated": {
                "cadastral_data_file": cadastral_data_file
            }
        }
        
        print(f"✅ Found cadastral: {cadastral_data.get('cadastral_number')}")
        print(f"📍 Municipality: {cadastral_data.get('municipality')}")
        print(f"🏷️  Land use: {cadastral_data.get('classification_code')} - {cadastral_data.get('classification_description')}")
        print(f"📁 Data saved to project directory: {project_dir}")
        
        return response
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Cadastral lookup failed: {str(e)}",
            "coordinates": {"longitude": lookup_lon, "latitude": lookup_lat},
            "location_name": location_name,
            "query_time": datetime.now().isoformat(),
            "project_directory": output_manager.get_project_info() if output_manager.current_project_dir else {"error": "No project directory"}
        }
        return error_response

@tool("get_cadastral_data_from_number", args_schema=CadastralNumberInput)
def get_cadastral_data_from_number(
    cadastral_number: str,
    include_geometry: bool = False,
    return_polygon_coordinates: bool = False,
    output_coordinate_system: str = "NAD83"
) -> Dict[str, Any]:
    """
    Get detailed data for a specific cadastral number with optional polygon coordinates.
    
    This tool searches the MIPR database for a specific cadastral number
    and returns comprehensive information about that property parcel.
    All data files are organized into a custom project directory.
    
    **Information Provided:**
    - Complete property identification and details
    - Land use classification and zoning information
    - Location details (municipality, neighborhood, region)
    - Area measurements in multiple units
    - Regulatory status and administrative information
    - Center point coordinates (if geometry is included)
    - Optional full polygon geometry coordinates
    
    **Data Source:**
    - Puerto Rico MIPR (Land Use Planning) Database
    - SIGE (Geographic Information System of Puerto Rico)
    
    Args:
        cadastral_number: Cadastral number to look up (e.g., '227-052-007-20')
        include_geometry: Whether to include center point and geometry metadata
        return_polygon_coordinates: Whether to return the full polygon coordinates array
        output_coordinate_system: Output coordinate system for center point
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if lookup was successful
        - cadastral_number: Input cadastral number
        - property_info: Complete property information
        - land_use_details: Land use classification and zoning
        - location_details: Municipality, neighborhood, and regional information
        - area_measurements: Area in various units
        - regulatory_status: Status, case numbers, and regulatory information
        - center_point: Property center coordinates (if include_geometry=True)
        - geometry_data: Polygon coordinates and metadata (if requested)
        - query_metadata: Query timestamp and data source information
        - project_directory: Information about the custom output directory
    """
    
    print(f"🔍 Looking up cadastral number: {cadastral_number}")
    if include_geometry:
        print(f"📍 Including geometry data (center point calculation)")
    if return_polygon_coordinates:
        print(f"🗺️  Including full polygon coordinates")
    
    # Get or create project directory
    output_manager = get_output_manager()
    if not output_manager.current_project_dir:
        # Create project directory if not already created
        project_dir = output_manager.create_project_directory(
            cadastral_number=cadastral_number
        )
        print(f"📁 Created project directory: {project_dir}")
    else:
        project_dir = output_manager.current_project_dir
        print(f"📁 Using existing project directory: {project_dir}")
    
    try:
        # Initialize cadastral search
        search = MIPRCadastralSearch()
        
        # Perform cadastral search with geometry if needed
        result = search.search_by_cadastral(
            cadastral_number, 
            exact_match=True, 
            include_geometry=include_geometry
        )
        
        if not result['success']:
            error_response = {
                "success": False,
                "error": result.get('error', 'Search failed'),
                "cadastral_number": cadastral_number,
                "query_time": datetime.now().isoformat(),
                "project_directory": output_manager.get_project_info()
            }
            return error_response
        
        if result['feature_count'] == 0:
            no_data_response = {
                "success": True,
                "found_cadastral": False,
                "cadastral_number": cadastral_number,
                "message": "Cadastral number not found in database",
                "suggestion": "Verify the cadastral number format and try again",
                "query_time": datetime.now().isoformat(),
                "project_directory": output_manager.get_project_info()
            }
            return no_data_response
        
        # Get the primary result (largest area if multiple)
        cadastral_data = result['results'][0]
        
        # Save cadastral search results to project data directory
        data_dir = output_manager.get_subdirectory("data")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cadastral = cadastral_number.replace('-', '_').replace('/', '_')
        cadastral_search_file = os.path.join(data_dir, f"cadastral_search_{safe_cadastral}_{timestamp}.json")
        
        import json
        with open(cadastral_search_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"💾 Cadastral search results saved to: {cadastral_search_file}")
        
        # Format response
        response = {
            "success": True,
            "found_cadastral": True,
            "cadastral_number": cadastral_number,
            "query_time": datetime.now().isoformat(),
            
            "property_info": {
                "cadastral_number": cadastral_data.get('cadastral_number'),
                "official_designation": cadastral_data.get('cadastral_number'),
                "property_type": "Cadastral Parcel",
                "database_id": cadastral_data.get('objectid')
            },
            
            "land_use_details": {
                "classification_code": cadastral_data.get('classification_code'),
                "classification_description": cadastral_data.get('classification_description'),
                "sub_classification": cadastral_data.get('sub_classification'),
                "sub_classification_description": cadastral_data.get('sub_classification_description'),
                "zoning_category": _determine_zoning_category(cadastral_data.get('classification_description', '')),
                "development_potential": _assess_development_potential(cadastral_data.get('classification_description', ''))
            },
            
            "location_details": {
                "municipality": cadastral_data.get('municipality'),
                "neighborhood": cadastral_data.get('neighborhood'),
                "region": cadastral_data.get('region'),
                "administrative_level": "Municipal",
                "island": "Puerto Rico",
                "country": "United States"
            },
            
            "area_measurements": {
                "area_square_meters": cadastral_data.get('area_m2', 0),
                "area_hectares": cadastral_data.get('area_hectares', 0),
                "area_acres": cadastral_data.get('area_hectares', 0) * 2.47105 if cadastral_data.get('area_hectares') else 0,
                "area_square_feet": cadastral_data.get('area_m2', 0) * 10.7639 if cadastral_data.get('area_m2') else 0,
                "area_cuerdas": cadastral_data.get('area_hectares', 0) * 2.59 if cadastral_data.get('area_hectares') else 0  # Puerto Rico traditional unit
            },
            
            "regulatory_status": {
                "status": cadastral_data.get('status'),
                "case_number": cadastral_data.get('case_number'),
                "resolution": cadastral_data.get('resolution'),
                "last_updated": cadastral_data.get('status'),  # Status often contains date info
                "regulatory_implications": _assess_regulatory_implications(cadastral_data)
            },
            
            "data_source": {
                "database": "Puerto Rico MIPR (Land Use Planning) Database",
                "service_url": "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer",
                "coordinate_system": "WGS84 (EPSG:4326)",
                "data_type": "Official Cadastral Records",
                "search_method": "Exact cadastral number match"
            },
            
            "project_directory": output_manager.get_project_info(),
            "files_generated": {
                "cadastral_search_file": cadastral_search_file
            }
        }
        
        # Process geometry data if requested
        if include_geometry and cadastral_data.get('geometry'):
            geometry = cadastral_data['geometry']
            
            # Extract polygon coordinates
            polygon_coords = _extract_polygon_coordinates(geometry)
            
            if polygon_coords:
                # Calculate center point using improved method
                print(f"🔍 Calculating centroid from {len(polygon_coords)} polygon coordinates")
                
                if PYPROJ_AVAILABLE:
                    print(f"🎯 Using high-accuracy projected centroid calculation (NAD83 Puerto Rico)")
                    center_lon_wgs84, center_lat_wgs84 = _calculate_polygon_center_projected(polygon_coords)
                else:
                    print(f"⚠️  Using standard geographic centroid calculation (pyproj not available)")
                    center_lon_wgs84, center_lat_wgs84 = _calculate_polygon_center(polygon_coords)
                
                print(f"📍 Calculated center point (WGS84): ({center_lon_wgs84:.8f}, {center_lat_wgs84:.8f})")
                
                # Convert to requested output coordinate system
                if output_coordinate_system.upper() == "NAD83":
                    center_lon, center_lat = _convert_wgs84_to_nad83(center_lon_wgs84, center_lat_wgs84)
                    coord_system_name = "NAD83(HARN) Puerto Rico (EPSG:4152)"
                    if PYPROJ_AVAILABLE:
                        print(f"🔄 Converting center point WGS84 to NAD83 (high-accuracy): ({center_lon_wgs84:.8f}, {center_lat_wgs84:.8f}) → ({center_lon:.8f}, {center_lat:.8f})")
                    else:
                        print(f"🔄 Converting center point WGS84 to NAD83 (approximate): ({center_lon_wgs84:.8f}, {center_lat_wgs84:.8f}) → ({center_lon:.8f}, {center_lat:.8f})")
                else:
                    center_lon, center_lat = center_lon_wgs84, center_lat_wgs84
                    coord_system_name = "WGS84 (EPSG:4326)"
                    print(f"📍 Using WGS84 coordinates: ({center_lon:.8f}, {center_lat:.8f})")
                
                # Always include center point if geometry is requested
                response["center_point"] = {
                    "longitude": center_lon,
                    "latitude": center_lat,
                    "coordinate_system": coord_system_name
                }
                
                # Add geometry metadata
                response["geometry_data"] = {
                    "coordinate_count": len(polygon_coords),
                    "coordinate_format": f"{output_coordinate_system.upper()} (longitude, latitude)",
                    "geometry_type": "Polygon",
                    "rings_count": len(geometry.get('rings', [])),
                    "has_holes": len(geometry.get('rings', [])) > 1,
                    "center_point": {
                        "longitude": center_lon,
                        "latitude": center_lat
                    },
                    "coordinate_system_info": {
                        "input_system": "WGS84 (from MIPR service)",
                        "output_system": coord_system_name,
                        "conversion_applied": output_coordinate_system.upper() == "NAD83"
                    }
                }
                
                # Include full polygon coordinates only if specifically requested
                if return_polygon_coordinates:
                    response["geometry_data"]["polygon_coordinates"] = polygon_coords
                    print(f"📍 Extracted {len(polygon_coords)} polygon coordinates")
                    
                    # Save geometry data to separate file
                    geometry_file = os.path.join(data_dir, f"cadastral_geometry_{safe_cadastral}_{timestamp}.json")
                    geometry_data = {
                        "cadastral_number": cadastral_number,
                        "center_point": {"longitude": center_lon, "latitude": center_lat},
                        "polygon_coordinates": polygon_coords,
                        "coordinate_count": len(polygon_coords),
                        "geometry_metadata": response["geometry_data"]
                    }
                    with open(geometry_file, 'w') as f:
                        json.dump(geometry_data, f, indent=2, default=str)
                    print(f"🗺️  Geometry data saved to: {geometry_file}")
                    response["files_generated"]["geometry_file"] = geometry_file
                else:
                    response["geometry_data"]["polygon_coordinates_available"] = True
                    response["geometry_data"]["note"] = "Full polygon coordinates available - set return_polygon_coordinates=True to retrieve"
                
                print(f"📍 Center point: ({center_lon:.6f}, {center_lat:.6f})")
            else:
                response["center_point"] = None
                response["geometry_data"] = {
                    "error": "Could not extract valid polygon coordinates from geometry data"
                }
        elif include_geometry:
            response["center_point"] = None
            response["geometry_data"] = {
                "error": "No geometry data available for this cadastral parcel"
            }
        
        print(f"✅ Found cadastral data for: {cadastral_number}")
        print(f"📍 Municipality: {cadastral_data.get('municipality')}")
        print(f"🏷️  Land use: {cadastral_data.get('classification_code')} - {cadastral_data.get('classification_description')}")
        print(f"📏 Area: {cadastral_data.get('area_hectares', 0):.2f} hectares")
        print(f"📁 Data saved to project directory: {project_dir}")
        
        return response
        
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Cadastral search failed: {str(e)}",
            "cadastral_number": cadastral_number,
            "query_time": datetime.now().isoformat(),
            "project_directory": output_manager.get_project_info() if output_manager.current_project_dir else {"error": "No project directory"}
        }
        return error_response

def _determine_zoning_category(classification_description: str) -> str:
    """Determine zoning category from classification description"""
    
    if not classification_description:
        return "Unknown"
    
    desc_upper = classification_description.upper()
    
    if "RESIDENCIAL" in desc_upper:
        return "Residential"
    elif "COMERCIAL" in desc_upper:
        return "Commercial"
    elif "INDUSTRIAL" in desc_upper:
        return "Industrial"
    elif "AGRICOLA" in desc_upper or "AGROPECUARIO" in desc_upper:
        return "Agricultural"
    elif "CONSERVACION" in desc_upper or "PROTECCION" in desc_upper:
        return "Conservation/Protected"
    elif "MIXTO" in desc_upper:
        return "Mixed Use"
    elif "INSTITUCIONAL" in desc_upper:
        return "Institutional"
    elif "RECREATIVO" in desc_upper:
        return "Recreational"
    else:
        return "Other/Special"

def _assess_development_potential(classification_description: str) -> str:
    """Assess development potential based on land use classification"""
    
    if not classification_description:
        return "Unknown"
    
    desc_upper = classification_description.upper()
    
    if "RESIDENCIAL" in desc_upper or "COMERCIAL" in desc_upper or "MIXTO" in desc_upper:
        return "High - Suitable for development"
    elif "INDUSTRIAL" in desc_upper:
        return "High - Suitable for industrial development"
    elif "AGRICOLA" in desc_upper:
        return "Limited - Agricultural use preferred"
    elif "CONSERVACION" in desc_upper or "PROTECCION" in desc_upper:
        return "Very Limited - Protected area"
    elif "INSTITUCIONAL" in desc_upper:
        return "Moderate - Institutional use"
    else:
        return "Requires specific analysis"

def _assess_regulatory_implications(cadastral_data: Dict[str, Any]) -> List[str]:
    """Assess regulatory implications based on cadastral data"""
    
    implications = []
    
    classification = cadastral_data.get('classification_description', '').upper()
    status = cadastral_data.get('status', '').upper()
    
    # Classification-based implications
    if "CONSERVACION" in classification or "PROTECCION" in classification:
        implications.append("Environmental protection regulations apply")
        implications.append("Development restrictions likely in place")
    
    if "AGRICOLA" in classification:
        implications.append("Agricultural zoning regulations apply")
        implications.append("May have agricultural preservation requirements")
    
    if "RESIDENCIAL" in classification:
        implications.append("Residential zoning regulations apply")
        implications.append("Building codes and density requirements apply")
    
    if "COMERCIAL" in classification:
        implications.append("Commercial zoning regulations apply")
        implications.append("Business licensing requirements may apply")
    
    # Status-based implications
    if "PENDIENTE" in status:
        implications.append("Land use classification is pending - status may change")
    
    if "APROBADO" in status:
        implications.append("Current land use classification is approved")
    
    # General implications
    implications.append("Municipal permits required for development")
    implications.append("Consult local planning office for specific requirements")
    
    return implications

def _convert_web_mercator_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """
    Convert Web Mercator (EPSG:3857) coordinates to WGS84 (EPSG:4326) with high accuracy.
    
    Args:
        x: X coordinate in Web Mercator (meters)
        y: Y coordinate in Web Mercator (meters)
        
    Returns:
        Tuple of (longitude, latitude) in WGS84
    """
    if PYPROJ_AVAILABLE:
        # Use pyproj for accurate transformation
        transformer = Transformer.from_crs(WEB_MERCATOR_EPSG, WGS84_EPSG, always_xy=True)
        lon, lat = transformer.transform(x, y)
        return (lon, lat)
    else:
        # Fallback to approximate conversion
        lon = x / 20037508.34 * 180
        lat = y / 20037508.34 * 180
        lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180)) - math.pi / 2)
        return (lon, lat)

def _calculate_polygon_center(coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Calculate the true geometric centroid of a polygon using the polygon centroid formula.
    
    This method calculates the area-weighted centroid, which is more accurate than
    the simple arithmetic mean of vertices, especially for irregular polygons.
    
    For geographic coordinates, this calculation is performed in the original
    coordinate system to maintain accuracy.
    
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
    
    # For better accuracy with geographic coordinates, we can optionally
    # project to a local coordinate system, calculate centroid, then project back
    # For now, we'll use the standard geographic centroid calculation
    
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
    if abs(area) < 1e-12:  # Increased precision threshold
        # Fall back to arithmetic mean
        unique_coords = list(set(coords[:-1]))  # Exclude duplicate closing point
        center_lon = sum(coord[0] for coord in unique_coords) / len(unique_coords)
        center_lat = sum(coord[1] for coord in unique_coords) / len(unique_coords)
        return (center_lon, center_lat)
    
    # Complete centroid calculation
    centroid_x = centroid_x / (6.0 * area)
    centroid_y = centroid_y / (6.0 * area)
    
    return (centroid_x, centroid_y)

def _calculate_polygon_center_projected(coords: List[Tuple[float, float]], 
                                      target_epsg: int = NAD83_PR_EPSG) -> Tuple[float, float]:
    """
    Calculate polygon centroid using projected coordinates for higher accuracy.
    
    This method projects the polygon to a local coordinate system (like NAD83 Puerto Rico),
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
        return _calculate_polygon_center(coords)
    
    try:
        # Transform to projected coordinates
        transformer_to_proj = Transformer.from_crs(WGS84_EPSG, target_epsg, always_xy=True)
        projected_coords = []
        
        for lon, lat in coords:
            x, y = transformer_to_proj.transform(lon, lat)
            projected_coords.append((x, y))
        
        # Calculate centroid in projected coordinates
        proj_center_x, proj_center_y = _calculate_polygon_center(projected_coords)
        
        # Transform back to geographic coordinates
        transformer_to_geo = Transformer.from_crs(target_epsg, WGS84_EPSG, always_xy=True)
        center_lon, center_lat = transformer_to_geo.transform(proj_center_x, proj_center_y)
        
        return (center_lon, center_lat)
        
    except Exception as e:
        print(f"⚠️  Projected centroid calculation failed: {e}")
        # Fall back to standard calculation
        return _calculate_polygon_center(coords)

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

def _convert_nad83_to_wgs84(longitude_nad83: float, latitude_nad83: float) -> Tuple[float, float]:
    """
    Convert NAD83 coordinates to WGS84 for Puerto Rico with high accuracy.
    
    Uses pyproj for precise coordinate transformation between NAD83(HARN) Puerto Rico
    (EPSG:2866) and WGS84 (EPSG:4326).
    
    Args:
        longitude_nad83: Longitude in NAD83 (degrees)
        latitude_nad83: Latitude in NAD83 (degrees)
        
    Returns:
        Tuple of (longitude_wgs84, latitude_wgs84)
    """
    if PYPROJ_AVAILABLE:
        # Use pyproj for accurate transformation
        # Note: NAD83 geographic coordinates are in EPSG:4152, but for Puerto Rico
        # we often work with the projected system EPSG:2866. Since input is in degrees,
        # we assume it's geographic NAD83 (EPSG:4152)
        transformer = Transformer.from_crs(4152, WGS84_EPSG, always_xy=True)  # NAD83(HARN) to WGS84
        lon_wgs84, lat_wgs84 = transformer.transform(longitude_nad83, latitude_nad83)
        return (lon_wgs84, lat_wgs84)
    else:
        # Fallback to approximate conversion
        longitude_wgs84 = longitude_nad83 + NAD83_TO_WGS84_OFFSET_LON
        latitude_wgs84 = latitude_nad83 + NAD83_TO_WGS84_OFFSET_LAT
        return (longitude_wgs84, latitude_wgs84)

def _convert_wgs84_to_nad83(longitude_wgs84: float, latitude_wgs84: float) -> Tuple[float, float]:
    """
    Convert WGS84 coordinates to NAD83 for Puerto Rico with high accuracy.
    
    Uses pyproj for precise coordinate transformation between WGS84 (EPSG:4326)
    and NAD83(HARN) (EPSG:4152).
    
    Args:
        longitude_wgs84: Longitude in WGS84 (degrees)
        latitude_wgs84: Latitude in WGS84 (degrees)
        
    Returns:
        Tuple of (longitude_nad83, latitude_nad83)
    """
    if PYPROJ_AVAILABLE:
        # Use pyproj for accurate transformation
        transformer = Transformer.from_crs(WGS84_EPSG, 4152, always_xy=True)  # WGS84 to NAD83(HARN)
        lon_nad83, lat_nad83 = transformer.transform(longitude_wgs84, latitude_wgs84)
        return (lon_nad83, lat_nad83)
    else:
        # Fallback to approximate conversion
        longitude_nad83 = longitude_wgs84 - NAD83_TO_WGS84_OFFSET_LON
        latitude_nad83 = latitude_wgs84 - NAD83_TO_WGS84_OFFSET_LAT
        return (longitude_nad83, latitude_nad83)

def _detect_coordinate_system(longitude: float, latitude: float) -> str:
    """
    Attempt to detect if coordinates are in NAD83 or WGS84.
    
    This is a heuristic approach - for Puerto Rico, both systems are very close.
    Returns best guess based on typical usage patterns.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        
    Returns:
        String indicating likely coordinate system: 'NAD83' or 'WGS84'
    """
    # For Puerto Rico, both NAD83 and WGS84 coordinates are very similar
    # This is just a placeholder - in practice, you'd need metadata or user input
    # to know the source coordinate system
    
    # Puerto Rico bounds check
    if -67.97 <= longitude <= -64.51 and 17.62 <= latitude <= 18.57:
        # Default assumption for Puerto Rico cadastral data is NAD83
        return 'NAD83'
    else:
        # Outside Puerto Rico, assume WGS84
        return 'WGS84'

# Export tools for easy import
CADASTRAL_DATA_TOOLS = [
    get_cadastral_data_from_coordinates,
    get_cadastral_data_from_number
]

def get_cadastral_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available cadastral data tools"""
    return {
        "get_cadastral_data_from_coordinates": "Get cadastral data for the parcel containing given coordinates - includes land use, zoning, area, and regulatory information",
        "get_cadastral_data_from_number": "Get detailed data for a specific cadastral number - includes property details, land use classification, center point coordinates, and optional full polygon geometry"
    }

if __name__ == "__main__":
    print("🏗️ Cadastral Data Tools for LangGraph")
    print("=" * 60)
    print("Available tools:")
    
    descriptions = get_cadastral_tool_descriptions()
    for tool_name, description in descriptions.items():
        print(f"\n📋 {tool_name}:")
        print(f"   {description}")
    
    print(f"\n💡 Usage:")
    print(f"   from cadastral_data_tool import CADASTRAL_DATA_TOOLS")
    print(f"   # Use with LangGraph agents or ToolNode")
    print(f"   # Coordinate tool: longitude, latitude")
    print(f"   # Cadastral tool: cadastral_number + optional geometry")
    print(f"   # Both tools return structured cadastral information")
    
    print(f"\n🧪 Example usage:")
    print(f"   # Test coordinate tool")
    print(f"   result = get_cadastral_data_from_coordinates(-66.150906, 18.434059)")
    print(f"   # Test cadastral tool")
    print(f"   result = get_cadastral_data_from_number('227-052-007-20')")
    print("=" * 60) 