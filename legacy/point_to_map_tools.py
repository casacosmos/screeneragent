#!/usr/bin/env python3
"""
Point to Map Tools for LangGraph Agents

This module provides LangGraph tools for generating maps from point coordinates 
or cadastral numbers, integrating point lookup, cadastral data retrieval, 
and map generation into single tool calls.

Tools:
- create_map_from_coordinates: Generate map from longitude/latitude coordinates
- create_map_from_cadastral_number: Generate map from cadastral number
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic.v1 import BaseModel, Field

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.tools import tool
from point_to_map import PointToMapGenerator

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Pydantic models for tool input schemas
class CoordinateMapInput(BaseModel):
    """Input schema for coordinate-based map generation"""
    longitude: float = Field(description="Longitude coordinate (e.g., -65.9258 for Puerto Rico)")
    latitude: float = Field(description="Latitude coordinate (e.g., 18.2278 for Puerto Rico)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location")
    buffer_meters: Optional[float] = Field(default=0, description="Buffer distance in meters for cadastral lookup (0 for exact point)")
    service: Optional[str] = Field(default="foto_pr_2017", description="Map service: 'topografico' or 'foto_pr_2017'")
    show_circle: Optional[bool] = Field(default=True, description="Whether to show buffer circle on map")
    circle_radius: Optional[float] = Field(default=0.05, description="Radius of buffer circle in miles")
    style: Optional[str] = Field(default="yellow_filled", description="Map style: 'default', 'yellow_filled', or 'blue_classic'")
    template: Optional[str] = Field(default="JP_print", description="Print template: 'JP_print' or 'MAP_ONLY'")

class CadastralMapInput(BaseModel):
    """Input schema for cadastral-based map generation"""
    cadastral_number: str = Field(description="Cadastral number (e.g., '227-052-007-20')")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the cadastral")
    service: Optional[str] = Field(default="foto_pr_2017", description="Map service: 'topografico' or 'foto_pr_2017'")
    show_circle: Optional[bool] = Field(default=True, description="Whether to show buffer circle on map")
    circle_radius: Optional[float] = Field(default=0.1, description="Radius of buffer circle in miles")
    style: Optional[str] = Field(default="blue_classic", description="Map style: 'default', 'yellow_filled', or 'blue_classic'")
    template: Optional[str] = Field(default="JP_print", description="Print template: 'JP_print' or 'MAP_ONLY'")

@tool("create_map_from_coordinates", args_schema=CoordinateMapInput)
def create_map_from_coordinates(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    buffer_meters: Optional[float] = 0,
    service: Optional[str] = "foto_pr_2017",
    show_circle: Optional[bool] = True,
    circle_radius: Optional[float] = 0.05,
    style: Optional[str] = "yellow_filled",
    template: Optional[str] = "JP_print"
) -> Dict[str, Any]:
    """
    Generate a complete map from point coordinates with cadastral information.
    
    This tool performs a complete workflow:
    1. Looks up the cadastral parcel at the given coordinates
    2. Retrieves detailed cadastral information (land use, municipality, area, etc.)
    3. Gets the polygon coordinates for the cadastral parcel
    4. Generates a professional map with the cadastral polygon highlighted
    
    Perfect for property analysis, site planning, and zoning research.
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere, e.g., -65.9258)
        latitude: Latitude coordinate (positive for northern hemisphere, e.g., 18.2278)
        location_name: Optional descriptive name for the location
        buffer_meters: Buffer distance in meters for cadastral lookup (0 for exact point)
        service: Map service ('topografico' for topographic, 'foto_pr_2017' for satellite)
        show_circle: Whether to show buffer circle on map
        circle_radius: Radius of buffer circle in miles
        style: Map style ('default', 'yellow_filled', 'blue_classic')
        template: Print template ('JP_print' for full layout, 'MAP_ONLY' for map only)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation was successful
        - coordinates: Input coordinates
        - cadastral_info: Complete cadastral information
        - land_use_details: Land use classification and zoning
        - property_details: Area, municipality, neighborhood information
        - map_info: Generated map details and file path
        - polygon_data: Cadastral polygon coordinates
    """
    
    if location_name is None:
        location_name = f"Property at ({longitude:.6f}, {latitude:.6f})"
    
    print(f"🗺️ Creating map from coordinates: {location_name}")
    
    # Initialize generator
    generator = PointToMapGenerator()
    
    try:
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/coordinate_map_{timestamp}.png"
        
        # Create map from point
        result = generator.create_map_from_point(
            longitude=longitude,
            latitude=latitude,
            save_path=filename,
            buffer_meters=buffer_meters,
            service=service,
            show_circle=show_circle,
            circle_radius=circle_radius,
            style=style,
            show_on_screen=False,
            template=template,
            return_cadastral_data=True
        )
        
        if not result['success']:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "location": location_name,
                "coordinates": {"longitude": longitude, "latitude": latitude},
                "query_time": datetime.now().isoformat()
            }
        
        # Format response for agent consumption
        cadastral_data = result.get('cadastral_data', {})
        
        response = {
            "success": True,
            "location": location_name,
            "coordinates": {
                "longitude": longitude,
                "latitude": latitude
            },
            "query_time": datetime.now().isoformat(),
            "lookup_method": "exact_point" if buffer_meters == 0 else f"buffer_search_{buffer_meters}m"
        }
        
        # Add cadastral information
        if cadastral_data:
            response.update({
                "cadastral_info": {
                    "cadastral_number": cadastral_data.get('cadastral_number'),
                    "municipality": cadastral_data.get('municipality'),
                    "neighborhood": cadastral_data.get('neighborhood'),
                    "region": cadastral_data.get('region')
                },
                "land_use_details": {
                    "classification_code": cadastral_data.get('classification_code'),
                    "classification_description": cadastral_data.get('classification_description'),
                    "sub_classification": cadastral_data.get('sub_classification'),
                    "sub_description": cadastral_data.get('sub_classification_description')
                },
                "property_details": {
                    "area_m2": cadastral_data.get('area_m2'),
                    "area_hectares": cadastral_data.get('area_hectares'),
                    "area_acres": cadastral_data.get('area_m2', 0) * 0.000247105 if cadastral_data.get('area_m2') else None
                },
                "regulatory_info": {
                    "status": cadastral_data.get('status'),
                    "case_number": cadastral_data.get('case_number'),
                    "resolution": cadastral_data.get('resolution')
                }
            })
        
        # Add map information
        if result.get('map_created'):
            response["map_info"] = {
                "filename": result['map_path'],
                "service": service,
                "style": style,
                "template": template,
                "show_circle": show_circle,
                "circle_radius_miles": circle_radius,
                "generation_successful": True
            }
        else:
            response["map_info"] = {
                "generation_successful": False,
                "error": "Map generation failed"
            }
        
        # Add polygon data
        if result.get('polygon_coords'):
            response["polygon_data"] = {
                "coordinate_count": len(result['polygon_coords']),
                "coordinates": result['polygon_coords'][:10],  # First 10 coordinates for preview
                "full_coordinates_available": True,
                "coordinate_format": "WGS84 (longitude, latitude)"
            }
        
        # Add data source information
        response["data_source"] = {
            "mipr_database": "Puerto Rico MIPR (Land Use Planning) Database",
            "service_url": "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer",
            "coordinate_system": "WGS84 (EPSG:4326)"
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "query_time": datetime.now().isoformat()
        }

@tool("create_map_from_cadastral_number", args_schema=CadastralMapInput)
def create_map_from_cadastral_number(
    cadastral_number: str,
    location_name: Optional[str] = None,
    service: Optional[str] = "foto_pr_2017",
    show_circle: Optional[bool] = True,
    circle_radius: Optional[float] = 0.1,
    style: Optional[str] = "blue_classic",
    template: Optional[str] = "JP_print"
) -> Dict[str, Any]:
    """
    Generate a complete map from a cadastral number with property information.
    
    This tool performs a complete workflow:
    1. Looks up the cadastral number in the MIPR database
    2. Retrieves detailed property information (land use, area, municipality, etc.)
    3. Gets the polygon coordinates for the cadastral parcel
    4. Generates a professional map with the property polygon highlighted
    
    Perfect for property research, legal documentation, and planning applications.
    
    Args:
        cadastral_number: Cadastral number (e.g., '227-052-007-20')
        location_name: Optional descriptive name for the cadastral
        service: Map service ('topografico' for topographic, 'foto_pr_2017' for satellite)
        show_circle: Whether to show buffer circle on map
        circle_radius: Radius of buffer circle in miles
        style: Map style ('default', 'yellow_filled', 'blue_classic')
        template: Print template ('JP_print' for full layout, 'MAP_ONLY' for map only)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation was successful
        - cadastral_number: Input cadastral number
        - property_info: Complete property information
        - land_use_details: Land use classification and zoning
        - location_details: Municipality, neighborhood, and regional information
        - area_measurements: Area in various units
        - map_info: Generated map details and file path
        - polygon_data: Property polygon coordinates
    """
    
    if location_name is None:
        location_name = f"Property {cadastral_number}"
    
    print(f"🗺️ Creating map from cadastral: {location_name}")
    
    # Initialize generator
    generator = PointToMapGenerator()
    
    try:
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/cadastral_map_{timestamp}.png"
        
        # Create map from cadastral
        result = generator.create_map_from_cadastral(
            cadastral_number=cadastral_number,
            save_path=filename,
            service=service,
            show_circle=show_circle,
            circle_radius=circle_radius,
            style=style,
            show_on_screen=False,
            template=template,
            return_cadastral_data=True
        )
        
        if not result['success']:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "cadastral_number": cadastral_number,
                "location": location_name,
                "query_time": datetime.now().isoformat()
            }
        
        # Format response for agent consumption
        cadastral_data = result.get('cadastral_data', {})
        
        response = {
            "success": True,
            "cadastral_number": cadastral_number,
            "location": location_name,
            "query_time": datetime.now().isoformat(),
            "lookup_method": "cadastral_number_search"
        }
        
        # Add property information
        if cadastral_data:
            response.update({
                "property_info": {
                    "cadastral_number": cadastral_data.get('cadastral_number'),
                    "official_name": cadastral_data.get('cadastral_number'),  # Same as cadastral number
                    "property_type": "Cadastral Parcel"
                },
                "land_use_details": {
                    "classification_code": cadastral_data.get('classification_code'),
                    "classification_description": cadastral_data.get('classification_description'),
                    "sub_classification": cadastral_data.get('sub_classification'),
                    "sub_description": cadastral_data.get('sub_classification_description'),
                    "zoning_category": cadastral_data.get('classification_code')
                },
                "location_details": {
                    "municipality": cadastral_data.get('municipality'),
                    "neighborhood": cadastral_data.get('neighborhood'),
                    "region": cadastral_data.get('region'),
                    "administrative_level": "Municipal"
                },
                "area_measurements": {
                    "area_m2": cadastral_data.get('area_m2'),
                    "area_hectares": cadastral_data.get('area_hectares'),
                    "area_acres": cadastral_data.get('area_m2', 0) * 0.000247105 if cadastral_data.get('area_m2') else None,
                    "area_square_feet": cadastral_data.get('area_m2', 0) * 10.7639 if cadastral_data.get('area_m2') else None
                },
                "regulatory_info": {
                    "status": cadastral_data.get('status'),
                    "case_number": cadastral_data.get('case_number'),
                    "resolution": cadastral_data.get('resolution'),
                    "last_updated": cadastral_data.get('status')  # Status often contains date
                }
            })
        
        # Add map information
        if result.get('map_created'):
            response["map_info"] = {
                "filename": result['map_path'],
                "service": service,
                "style": style,
                "template": template,
                "show_circle": show_circle,
                "circle_radius_miles": circle_radius,
                "generation_successful": True,
                "map_type": "Property Boundary Map"
            }
        else:
            response["map_info"] = {
                "generation_successful": False,
                "error": "Map generation failed"
            }
        
        # Add polygon data
        if result.get('polygon_coords'):
            # Calculate approximate center point
            coords = result['polygon_coords']
            center_lon = sum(coord[0] for coord in coords) / len(coords)
            center_lat = sum(coord[1] for coord in coords) / len(coords)
            
            response["polygon_data"] = {
                "coordinate_count": len(coords),
                "center_point": {"longitude": center_lon, "latitude": center_lat},
                "coordinates": coords[:10],  # First 10 coordinates for preview
                "full_coordinates_available": True,
                "coordinate_format": "WGS84 (longitude, latitude)",
                "polygon_type": "Property Boundary"
            }
        
        # Add data source information
        response["data_source"] = {
            "mipr_database": "Puerto Rico MIPR (Land Use Planning) Database",
            "service_url": "https://sige.pr.gov/server/rest/services/MIPR/Calificacion/MapServer",
            "coordinate_system": "WGS84 (EPSG:4326)",
            "data_type": "Official Cadastral Records"
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "cadastral_number": cadastral_number,
            "location": location_name,
            "query_time": datetime.now().isoformat()
        }

# Tool list for easy import
POINT_TO_MAP_TOOLS = [
    create_map_from_coordinates,
    create_map_from_cadastral_number
]

def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available point-to-map tools"""
    return {
        "create_map_from_coordinates": "Generate complete map from longitude/latitude coordinates - includes cadastral lookup, property info, and professional map generation",
        "create_map_from_cadastral_number": "Generate complete map from cadastral number - includes property lookup, land use details, and professional map generation"
    }

if __name__ == "__main__":
    print("🗺️ Point to Map Tools for LangGraph")
    print("=" * 50)
    print("Available tools:")
    
    descriptions = get_tool_descriptions()
    for tool_name, description in descriptions.items():
        print(f"\n📋 {tool_name}:")
        print(f"   {description}")
    
    print(f"\n💡 Usage:")
    print(f"   from point_to_map_tools import POINT_TO_MAP_TOOLS")
    print(f"   # Use with LangGraph agents or ToolNode")
    print(f"   # Coordinate tool: longitude, latitude + optional parameters")
    print(f"   # Cadastral tool: cadastral_number + optional parameters")
    print(f"   # Both tools return comprehensive property and map information")
    
    print(f"\n🧪 Example usage:")
    print(f"   # Test coordinate tool")
    print(f"   result = create_map_from_coordinates(-65.925834, 18.227804)")
    print(f"   # Test cadastral tool")
    print(f"   result = create_map_from_cadastral_number('227-052-007-20')")
    print("=" * 50) 