#!/usr/bin/env python3
"""
Wetland Data Tools for LangGraph Agents

This module provides LangGraph tools for querying wetland data and generating
various wetland maps and reports for given coordinates.

Tools:
- query_wetland_data: Query comprehensive wetland data for coordinates
- generate_detailed_wetland_map: Generate detailed wetland map (0.3 mile buffer)
- generate_overview_wetland_map: Generate overview wetland map (1.0 mile buffer)
- generate_adaptive_wetland_map: Generate adaptive wetland map with intelligent buffer sizing
- generate_custom_wetland_map: Generate custom wetland map with specified parameters
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.tools import tool
from query_wetland_location import WetlandLocationAnalyzer, save_results_to_file, generate_summary_report
from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Pydantic models for tool input schemas
class CoordinateInput(BaseModel):
    """Input schema for coordinate-based queries"""
    longitude: float = Field(description="Longitude coordinate (e.g., -66.199399 for Puerto Rico)")
    latitude: float = Field(description="Latitude coordinate (e.g., 18.408303 for Puerto Rico)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location (e.g., 'Bayamón, Puerto Rico')")

class CustomMapInput(BaseModel):
    """Input schema for custom wetland map generation"""
    longitude: float = Field(description="Longitude coordinate")
    latitude: float = Field(description="Latitude coordinate")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location")
    buffer_miles: float = Field(default=0.5, description="Buffer radius in miles (0.1 to 5.0)")
    base_map: str = Field(default="World_Imagery", description="Base map style: World_Imagery, World_Topo_Map, or World_Street_Map")
    wetland_transparency: float = Field(default=0.8, description="Wetland layer transparency (0.0 to 1.0)")

@tool("query_wetland_data", args_schema=CoordinateInput)
def query_wetland_data(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Query comprehensive wetland data for specific coordinates.
    
    This tool queries multiple wetland data sources to retrieve:
    - USFWS National Wetlands Inventory (NWI) data
    - EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)
    - EPA National Hydrography Dataset (NHD)
    - USFWS Riparian Mapping data
    - Watershed information
    
    Performs progressive search:
    - Checks for wetlands at exact coordinates
    - If none found, searches within 0.5 mile radius
    - If still none found, expands to 1.0 mile radius
    
    Returns detailed wetland classifications, NWI codes, areas, distances, and regulatory implications.
    Automatically saves detailed results to JSON files in logs/.
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere)
        latitude: Latitude coordinate (positive for northern hemisphere)
        location_name: Optional descriptive name for the location
        
    Returns:
        Dictionary containing:
        - location: Location identifier
        - coordinates: (longitude, latitude) tuple
        - is_in_wetland: Boolean indicating if location is within a wetland
        - wetlands_at_location: List of wetlands at exact coordinates
        - nearest_wetlands: List of nearby wetlands with distances and bearings
        - search_summary: Statistics about the search results
        - analysis: Environmental significance and regulatory implications
        - recommendations: List of recommended actions
    """
    
    if location_name is None:
        location_name = f"({longitude}, {latitude})"
    
    print(f"🌿 Querying wetland data for {location_name}")
    
    # Initialize analyzer
    analyzer = WetlandLocationAnalyzer()
    
    # Query the data using the core function
    results = analyzer.analyze_location(longitude, latitude, location_name)
    
    # Auto-save results
    save_results_to_file(results)
    
    # Create a summary for the agent
    summary = {
        "location": results['location'],
        "coordinates": results['coordinates'],
        "query_time": results['query_time'],
        "is_in_wetland": results['is_in_wetland'],
        "search_summary": results['search_summary'],
        "key_findings": {}
    }
    
    # Extract key findings for the agent
    if results['search_summary']['total_wetlands_analyzed'] > 0:
        summary["key_findings"]["wetlands_found"] = True
        summary["key_findings"]["total_wetlands"] = results['search_summary']['total_wetlands_analyzed']
        summary["key_findings"]["search_radius_used"] = results['search_summary']['search_radius_used']
        
        # Wetland types found
        wetland_types = set()
        for wetland in results.get('wetlands_at_location', []) + [nw['wetland'] for nw in results.get('nearest_wetlands', [])]:
            if isinstance(wetland, dict):
                wetland_types.add(wetland.get('type', 'Unknown'))
            else:
                wetland_types.add(getattr(wetland, 'wetland_type', 'Unknown'))
        
        summary["key_findings"]["wetland_types"] = list(wetland_types)
        summary["key_findings"]["environmental_significance"] = results['analysis']['environmental_significance']
        
        # Regulatory status
        if results['is_in_wetland']:
            summary["key_findings"]["regulatory_status"] = "Direct wetland impacts - permits likely required"
        else:
            nearest_distance = results['nearest_wetlands'][0]['distance_miles'] if results['nearest_wetlands'] else None
            if nearest_distance and nearest_distance <= 0.5:
                summary["key_findings"]["regulatory_status"] = f"Wetlands within {nearest_distance} miles - buffer requirements may apply"
            else:
                summary["key_findings"]["regulatory_status"] = "No immediate wetland impacts expected"
    else:
        summary["key_findings"]["wetlands_found"] = False
        summary["key_findings"]["message"] = f"No wetlands found within {results['search_summary']['search_radius_used']} mile radius"
        summary["key_findings"]["regulatory_status"] = "No wetland impacts expected"
    
    # Add data sources
    summary["data_sources"] = [
        "USFWS National Wetlands Inventory (NWI)",
        "EPA RIBITS",
        "EPA National Hydrography Dataset (NHD)",
        "USFWS Riparian Mapping"
    ]
    
    return summary



@tool("generate_overview_wetland_map", args_schema=CoordinateInput)
def generate_overview_wetland_map(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an overview wetland map with a clean 0.5-mile radius circle around the coordinate point.
    
    This map provides:
    - High-resolution satellite imagery background
    - Clean 0.5-mile radius circle with enhanced orange outline (no center point marker)
    - Wetland classifications and boundaries within and around the circle
    - Professional legend and scale bar
    - 300 DPI resolution for detailed analysis
    - 1.0 mile map extent for regional context
    
    The circle clearly shows exactly which wetlands fall within the 0.5-mile radius for regulatory 
    and environmental assessment purposes, with no obstructing center point marker.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Optional descriptive name for the location
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation was successful
        - message: Status message or error description
        - filename: Path to generated PDF file (if successful)
        - map_settings: Details about map configuration
        - circle_info: Information about the radius circle
        - wetlands_in_circle: Number of wetlands within the circle
    """
    
    if location_name is None:
        location_name = f"Wetland Map with 0.5 Mile Radius at ({longitude}, {latitude})"
    
    print(f"🗺️  Generating overview wetland map with 0.5-mile circle for {location_name}")
    
    # Initialize map generator
    map_generator = WetlandMapGeneratorV3()
    
    try:
        # Generate overview map with circle
        map_path = map_generator.generate_overview_wetland_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            wetland_transparency=0.8,
            layout_template="Letter ANSI A Landscape"  # use landscape to minimize distortion
        )
        
        if map_path:
            # Calculate circle area (π * r²)
            import math
            circle_area = round(math.pi * (0.5 ** 2), 2)
            map_coverage_area = round(math.pi * (1.0 ** 2), 2)
            
            # Check wetlands within circle
            wetlands_in_circle = map_generator._check_wetlands_in_area(longitude, latitude, 0.5)
            
            return {
                "success": True,
                "message": f"Overview wetland map with 0.5-mile radius circle successfully generated",
                "filename": map_path,
                "location": location_name,
                "coordinates": (longitude, latitude),
                "map_settings": {
                    "circle_radius_miles": 0.5,
                    "map_buffer_miles": 1.0,
                    "base_map": "World_Imagery",
                    "resolution_dpi": 300,
                    "wetland_transparency": 0.8,
                    "includes_legend": True,
                    "includes_scale_bar": True,
                    "circle_color": "Orange"
                },
                "circle_info": {
                    "radius_miles": 0.5,
                    "area_square_miles": circle_area,
                    "circumference_miles": round(2 * math.pi * 0.5, 2),
                    "purpose": "Regulatory buffer zone visualization"
                },
                "coverage_info": {
                    "circle_area": f"{circle_area} square miles",
                    "map_coverage": f"{map_coverage_area} square miles",
                    "scale_optimized": "Wetlands clearly visible"
                },
                "wetlands_in_circle": wetlands_in_circle,
                "document_type": "Wetland Radius Analysis Map",
                "use_cases": [
                    "Regulatory buffer assessment", 
                    "Environmental impact analysis", 
                    "Wetland proximity studies",
                    "Permit application support"
                ]
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate overview wetland map with circle",
                "location": location_name,
                "coordinates": (longitude, latitude),
                "suggestion": "Try using detailed map or check coordinate validity"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during overview map generation: {str(e)}",
            "location": location_name,
            "coordinates": (longitude, latitude),
            "suggestion": "Verify coordinates are valid and try again"
        }

@tool("generate_adaptive_wetland_map", args_schema=CoordinateInput)
def generate_adaptive_wetland_map(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an adaptive wetland map with intelligent buffer sizing based on wetland analysis.
    
    This map automatically determines optimal settings:
    - Analyzes wetland presence at location
    - Calculates optimal buffer based on nearest wetland distance
    - Selects appropriate base map and transparency
    - Ensures wetlands are visible with good context
    
    Buffer calculation:
    - Wetlands at exact location: 0.5 mile buffer
    - Wetlands found at 0.5 miles: Nearest distance + 1.5 miles buffer
    - No wetlands found: 2.0 mile regional view
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Optional descriptive name for the location
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation was successful
        - message: Status message or error description
        - filename: Path to generated PDF file (if successful)
        - adaptive_settings: Details about automatically determined settings
        - wetland_analysis: Summary of wetland analysis that drove map settings
    """
    
    if location_name is None:
        location_name = f"Adaptive Wetland Map at ({longitude}, {latitude})"
    
    print(f"🗺️  Generating adaptive wetland map for {location_name}")
    
    try:
        # Initialize components
        analyzer = WetlandLocationAnalyzer()
        map_generator = WetlandMapGeneratorV3()
        
        # First analyze the location to determine optimal settings
        print(f"🔍 Analyzing location to determine optimal map settings...")
        results = analyzer.analyze_location(longitude, latitude, location_name)
        
        # Determine optimal settings based on analysis results
        if results['is_in_wetland']:
            # If wetlands are present at exact location, use smaller buffer for detail
            buffer_miles = 0.5
            wetland_transparency = 0.75
            base_map = "World_Imagery"
            reasoning = "Wetlands at exact location - using detailed view"
        else:
            # If no wetlands at exact location, use buffer based on search results
            search_radius = results['search_summary']['search_radius_used']
            wetlands_found = len(results.get('nearest_wetlands', []))
            
            if wetlands_found > 0:
                # Calculate buffer based on actual distance to nearest wetland
                nearest_wetland = results['nearest_wetlands'][0]
                nearest_distance = nearest_wetland['distance_miles']
                
                # Add 1.5 miles to the nearest wetland distance to ensure it's visible with good context
                buffer_miles = nearest_distance + 1.5
                
                # Ensure minimum buffer for good context (at least 1.5 miles)
                if buffer_miles < 1.5:
                    buffer_miles = 1.5
                
                # Ensure maximum buffer for reasonable scale (no more than 4.0 miles)
                if buffer_miles > 4.0:
                    buffer_miles = 4.0
                
                wetland_transparency = 0.8
                base_map = "World_Imagery"
                reasoning = f"Nearest wetland at {nearest_distance} miles - using {buffer_miles} mile buffer"
            else:
                # No wetlands found even after expanded search, use larger buffer to show regional context
                buffer_miles = 2.0
                wetland_transparency = 0.8
                base_map = "World_Topo_Map"
                reasoning = f"No wetlands found within {search_radius} miles - using regional view"
        
        print(f"🎯 {reasoning}")
        
        # Generate the map with adaptive configuration
        map_path = map_generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            wetland_transparency=wetland_transparency
        )
        
        if map_path:
            return {
                "success": True,
                "message": f"Adaptive wetland map successfully generated",
                "filename": map_path,
                "location": location_name,
                "coordinates": (longitude, latitude),
                "adaptive_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "wetland_transparency": wetland_transparency,
                    "reasoning": reasoning,
                    "resolution_dpi": 300
                },
                "wetland_analysis": {
                    "is_in_wetland": results['is_in_wetland'],
                    "total_wetlands_found": results['search_summary']['total_wetlands_analyzed'],
                    "search_radius_used": results['search_summary']['search_radius_used'],
                    "nearest_distance": results['nearest_wetlands'][0]['distance_miles'] if results['nearest_wetlands'] else None
                },
                "document_type": "Intelligent Adaptive Wetland Map",
                "use_cases": ["Optimal wetland visualization", "Context-aware mapping", "Automated analysis"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate adaptive wetland map",
                "location": location_name,
                "coordinates": (longitude, latitude),
                "adaptive_settings": {
                    "buffer_miles": buffer_miles,
                    "reasoning": reasoning
                },
                "suggestion": "Try using detailed or overview map instead"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during adaptive map generation: {str(e)}",
            "location": location_name,
            "coordinates": (longitude, latitude),
            "suggestion": "Verify coordinates are valid and try again"
        }

@tool("generate_custom_wetland_map", args_schema=CustomMapInput)
def generate_custom_wetland_map(longitude: float, latitude: float, 
                               location_name: Optional[str] = None,
                               buffer_miles: float = 0.5,
                               base_map: str = "World_Imagery",
                               wetland_transparency: float = 0.8) -> Dict[str, Any]:
    """
    Generate a custom wetland map with user-specified parameters.
    
    This map allows full customization of:
    - Buffer radius (0.1 to 5.0 miles)
    - Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
    - Wetland layer transparency (0.0 to 1.0)
    - High-resolution output (300 DPI)
    - Professional legend and scale bar
    
    Ideal when specific map requirements are needed.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        location_name: Optional descriptive name for the location
        buffer_miles: Buffer radius in miles (0.1 to 5.0)
        base_map: Base map style (World_Imagery, World_Topo_Map, World_Street_Map)
        wetland_transparency: Wetland layer transparency (0.0 to 1.0)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation was successful
        - message: Status message or error description
        - filename: Path to generated PDF file (if successful)
        - custom_settings: Details about user-specified settings
        - validation_notes: Any parameter adjustments made
    """
    
    if location_name is None:
        location_name = f"Custom Wetland Map at ({longitude}, {latitude})"
    
    print(f"🗺️  Generating custom wetland map for {location_name}")
    
    # Validate and adjust parameters
    validation_notes = []
    
    # Validate buffer radius
    if buffer_miles < 0.1:
        buffer_miles = 0.1
        validation_notes.append("Buffer radius adjusted to minimum 0.1 miles")
    elif buffer_miles > 5.0:
        buffer_miles = 5.0
        validation_notes.append("Buffer radius adjusted to maximum 5.0 miles")
    
    # Validate base map
    valid_base_maps = ["World_Imagery", "World_Topo_Map", "World_Street_Map"]
    if base_map not in valid_base_maps:
        base_map = "World_Imagery"
        validation_notes.append(f"Base map adjusted to World_Imagery (valid options: {', '.join(valid_base_maps)})")
    
    # Validate transparency
    if wetland_transparency < 0.0:
        wetland_transparency = 0.0
        validation_notes.append("Transparency adjusted to minimum 0.0")
    elif wetland_transparency > 1.0:
        wetland_transparency = 1.0
        validation_notes.append("Transparency adjusted to maximum 1.0")
    
    print(f"📏 Buffer: {buffer_miles} miles, Base: {base_map}, Transparency: {wetland_transparency}")
    
    # Initialize map generator
    map_generator = WetlandMapGeneratorV3()
    
    try:
        # Generate custom map
        map_path = map_generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            wetland_transparency=wetland_transparency
        )
        
        if map_path:
            # Calculate coverage area
            import math
            coverage_area = round(math.pi * (buffer_miles ** 2), 2)
            
            return {
                "success": True,
                "message": f"Custom wetland map successfully generated",
                "filename": map_path,
                "location": location_name,
                "coordinates": (longitude, latitude),
                "custom_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "wetland_transparency": wetland_transparency,
                    "resolution_dpi": 300,
                    "coverage_area": f"{coverage_area} square miles"
                },
                "validation_notes": validation_notes if validation_notes else ["All parameters within valid ranges"],
                "document_type": "Custom Wetland Map",
                "use_cases": ["Specific requirements", "Custom analysis", "Tailored presentations"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate custom wetland map",
                "location": location_name,
                "coordinates": (longitude, latitude),
                "custom_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "wetland_transparency": wetland_transparency
                },
                "suggestion": "Check coordinate validity and parameter ranges"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during custom map generation: {str(e)}",
            "location": location_name,
            "coordinates": (longitude, latitude),
            "custom_settings": {
                "buffer_miles": buffer_miles,
                "base_map": base_map,
                "wetland_transparency": wetland_transparency
            },
            "suggestion": "Verify all parameters are valid and try again"
        }

# Tool list for easy import
WETLAND_TOOLS = [
    query_wetland_data,
    generate_overview_wetland_map,
    generate_adaptive_wetland_map,
    generate_custom_wetland_map
]

def get_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available wetland tools"""
    return {
        "query_wetland_data": "Query comprehensive wetland data for coordinates - returns NWI classifications, distances, and regulatory implications",
        "generate_overview_wetland_map": "Generate wetland map with clean 0.5-mile radius circle - ideal for regulatory buffer assessment and wetland proximity analysis",
        "generate_adaptive_wetland_map": "Generate intelligent adaptive wetland map - automatically determines optimal settings based on wetland analysis",
        "generate_custom_wetland_map": "Generate custom wetland map with user-specified buffer, base map, and transparency settings"
    }

if __name__ == "__main__":
    print("🌿 Wetland Data Tools for LangGraph")
    print("=" * 50)
    print("Available tools:")
    
    descriptions = get_tool_descriptions()
    for tool_name, description in descriptions.items():
        print(f"\n📋 {tool_name}:")
        print(f"   {description}")
    
    print(f"\n💡 Usage:")
    print(f"   from tools import WETLAND_TOOLS")
    print(f"   # Use with LangGraph agents or ToolNode")
    print(f"   # Each tool accepts longitude, latitude, and optional location_name")
    print(f"   # Custom map tool accepts additional buffer, base_map, and transparency parameters")
    print("=" * 50) 