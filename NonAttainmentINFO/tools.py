#!/usr/bin/env python3
"""
NonAttainment Areas Analysis Tools

This module provides LangChain-compatible tools for analyzing EPA nonattainment areas
and determining if locations violate National Ambient Air Quality Standards (NAAQS).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Type
import json
import logging
from datetime import datetime

# Handle imports with fallback for direct execution
try:
    from .nonattainment_client import NonAttainmentAreasClient, NonAttainmentAnalysisResult
    from .generate_nonattainment_map_pdf import NonAttainmentMapGenerator
except ImportError:
    try:
        from nonattainment_client import NonAttainmentAreasClient, NonAttainmentAnalysisResult
        from generate_nonattainment_map_pdf import NonAttainmentMapGenerator
    except ImportError:
        print("⚠️  Warning: Could not import NonAttainment modules")
        print("   Make sure you're running from the correct directory or as a package")
        # Create dummy classes to prevent import errors
        class NonAttainmentAreasClient:
            def __init__(self, *args, **kwargs):
                raise ImportError("NonAttainmentAreasClient could not be imported.")
        class NonAttainmentAnalysisResult:
            pass
        class NonAttainmentMapGenerator:
            def __init__(self, *args, **kwargs):
                raise ImportError("NonAttainmentMapGenerator could not be imported.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NonAttainmentAnalysisInput(BaseModel):
    """Input schema for nonattainment analysis"""
    longitude: float = Field(description="Longitude coordinate (decimal degrees)")
    latitude: float = Field(description="Latitude coordinate (decimal degrees)")
    include_revoked: bool = Field(
        default=False, 
        description="Whether to include revoked air quality standards"
    )
    buffer_meters: float = Field(
        default=0, 
        description="Buffer distance around point in meters (0 for exact point)"
    )
    pollutants: Optional[List[str]] = Field(
        default=None,
        description="List of specific pollutants to check (None for all): Ozone, PM2.5, PM10, Lead, Sulfur Dioxide, Carbon Monoxide, Nitrogen Dioxide"
    )

class NonAttainmentMapInput(BaseModel):
    """Input schema for nonattainment map generation"""
    longitude: float = Field(description="Longitude coordinate (decimal degrees)")
    latitude: float = Field(description="Latitude coordinate (decimal degrees)")
    location_name: Optional[str] = Field(default=None, description="Optional location name for map title")
    buffer_miles: float = Field(default=25.0, description="Buffer radius in miles for map extent")
    base_map: str = Field(default="World_Topo_Map", description="Base map style: World_Topo_Map, World_Street_Map, World_Imagery")
    include_legend: bool = Field(default=True, description="Whether to include legend on map")
    include_revoked: bool = Field(default=False, description="Whether to show revoked standards")
    pollutants: Optional[List[str]] = Field(default=None, description="Specific pollutants to show on map")

class PollutantSearchInput(BaseModel):
    """Input schema for pollutant-specific searches"""
    pollutant: str = Field(description="Pollutant name: Ozone, PM2.5, PM10, Lead, Sulfur Dioxide, Carbon Monoxide, Nitrogen Dioxide")
    include_revoked: bool = Field(default=False, description="Whether to include revoked standards")

@tool
def analyze_nonattainment_areas(
    longitude: float,
    latitude: float,
    include_revoked: bool = False,
    buffer_meters: float = 0,
    pollutants: Optional[List[str]] = None
) -> str:
    """
    Analyze a geographic location to determine if it intersects with EPA nonattainment areas
    for National Ambient Air Quality Standards (NAAQS) violations.
    
    This tool queries EPA OAR_OAQPS nonattainment data and provides:
    - Whether the location has air quality violations
    - Details about affected pollutants and standards
    - Current status (Nonattainment vs Maintenance)
    - Classification levels (Extreme, Serious, Moderate, etc.)
    - Design values and air quality measurements
    - Regulatory compliance recommendations
    
    Use this tool when you need to:
    - Check if a location violates air quality standards
    - Identify specific pollutants of concern
    - Assess Clean Air Act regulatory requirements
    - Understand air quality compliance for development
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        include_revoked: Whether to include revoked air quality standards
        buffer_meters: Buffer distance around point in meters (0 for exact point)
        pollutants: List of specific pollutants to check (None for all active standards)
        
    Returns:
        JSON string with detailed nonattainment analysis results
    """
    
    print(f"🌫️ Analyzing nonattainment areas at {longitude}, {latitude}")
    
    try:
        # Initialize client
        client = NonAttainmentAreasClient()
        
        # Perform analysis
        result = client.analyze_location(
            longitude=longitude,
            latitude=latitude,
            include_revoked=include_revoked,
            buffer_meters=buffer_meters,
            pollutants=pollutants
        )
        
        if not result.query_success:
            return json.dumps({
                "success": False,
                "error": result.error_message,
                "location": {"longitude": longitude, "latitude": latitude},
                "analysis_timestamp": result.analysis_timestamp
            })
        
        # Get detailed summary
        summary = client.get_area_summary(result)
        
        # Format response
        response = {
            "success": True,
            "location": {"longitude": longitude, "latitude": latitude},
            "analysis_timestamp": result.analysis_timestamp,
            "air_quality_status": {
                "has_violations": result.has_nonattainment_areas,
                "total_areas": result.area_count,
                "status": summary["status"]
            }
        }
        
        if result.has_nonattainment_areas:
            # Extract pollutant information
            pollutant_summary = {}
            for area in result.nonattainment_areas:
                pollutant = area.pollutant_name
                if pollutant not in pollutant_summary:
                    pollutant_summary[pollutant] = {
                        "areas": [],
                        "statuses": set(),
                        "classifications": set()
                    }
                
                pollutant_summary[pollutant]["areas"].append({
                    "area_name": area.area_name,
                    "state": area.state_name,
                    "status": area.current_status,
                    "classification": area.classification,
                    "design_value": area.design_value,
                    "design_value_units": area.design_value_units,
                    "meets_naaqs": area.meets_naaqs
                })
                pollutant_summary[pollutant]["statuses"].add(area.current_status)
                pollutant_summary[pollutant]["classifications"].add(area.classification)
            
            # Convert sets to lists for JSON serialization
            for pollutant in pollutant_summary:
                pollutant_summary[pollutant]["statuses"] = list(pollutant_summary[pollutant]["statuses"])
                pollutant_summary[pollutant]["classifications"] = list(pollutant_summary[pollutant]["classifications"])
            
            response.update({
                "violations_found": {
                    "pollutants_affected": list(pollutant_summary.keys()),
                    "pollutant_details": pollutant_summary,
                    "summary_statistics": summary.get("summary", {}),
                    "regulatory_implications": "Location is subject to Clean Air Act nonattainment area regulations"
                },
                "recommendations": summary.get("recommendations", [])
            })
        else:
            response.update({
                "clean_air_status": {
                    "message": "Location meets all National Ambient Air Quality Standards",
                    "regulatory_status": "No additional Clean Air Act requirements",
                    "air_quality_compliance": "Compliant"
                }
            })
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in nonattainment analysis: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "location": {"longitude": longitude, "latitude": latitude},
            "analysis_timestamp": datetime.now().isoformat()
        })

@tool
def generate_nonattainment_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    buffer_miles: float = 25.0,
    base_map: str = "World_Topo_Map",
    include_legend: bool = True,
    include_revoked: bool = False,
    pollutants: Optional[List[str]] = None
) -> str:
    """
    Generate a professional PDF map showing EPA nonattainment areas around a location.
    
    This tool creates high-quality maps displaying:
    - All EPA nonattainment areas within the specified radius
    - Color-coded pollutant layers with proper symbology
    - Professional legend and scale information
    - Location marker and geographic context
    - Regulatory compliance information
    
    Use this tool when you need:
    - Visual representation of air quality violations
    - Professional maps for regulatory submissions
    - Site analysis documentation
    - Environmental impact assessment visuals
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        location_name: Optional location name for map title
        buffer_miles: Buffer radius in miles for map extent (default: 25.0)
        base_map: Base map style (World_Topo_Map, World_Street_Map, World_Imagery)
        include_legend: Whether to include legend on map
        include_revoked: Whether to show revoked air quality standards
        pollutants: Specific pollutants to show on map (None for all active)
        
    Returns:
        JSON string with map generation results and file path
    """
    
    if location_name is None:
        location_name = f"Air Quality Analysis at {latitude:.4f}, {longitude:.4f}"
    
    print(f"🗺️ Generating nonattainment map for {location_name}")
    
    try:
        # Initialize map generator
        generator = NonAttainmentMapGenerator()
        
        # Generate map
        pdf_path = generator.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            include_legend=include_legend,
            include_revoked=include_revoked,
            pollutants=pollutants
        )
        
        if pdf_path:
            response = {
                "success": True,
                "map_generated": True,
                "file_path": pdf_path,
                "location": location_name,
                "coordinates": {"longitude": longitude, "latitude": latitude},
                "map_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "include_legend": include_legend,
                    "include_revoked": include_revoked,
                    "pollutants_shown": pollutants or "all_active"
                },
                "generation_timestamp": datetime.now().isoformat(),
                "file_type": "PDF" if pdf_path.endswith('.pdf') else "HTML"
            }
        else:
            response = {
                "success": False,
                "map_generated": False,
                "error": "Map generation failed",
                "location": location_name,
                "coordinates": {"longitude": longitude, "latitude": latitude}
            }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating nonattainment map: {e}")
        return json.dumps({
            "success": False,
            "map_generated": False,
            "error": str(e),
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude}
        })

@tool
def generate_adaptive_nonattainment_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None
) -> str:
    """
    Generate an intelligent adaptive nonattainment map that automatically adjusts
    settings based on the air quality analysis results.
    
    This tool:
    1. First analyzes the location for nonattainment areas
    2. Automatically determines optimal map settings based on findings:
       - If violations found: detailed 15-mile view with affected pollutants
       - If clean air: regional 50-mile overview for context
    3. Generates a professional map with appropriate styling
    
    Perfect for automated environmental screening where you want the system
    to intelligently choose the best map representation.
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        location_name: Optional location name for map title
        
    Returns:
        JSON string with analysis results and adaptive map generation details
    """
    
    if location_name is None:
        location_name = f"Adaptive Air Quality Analysis at {latitude:.4f}, {longitude:.4f}"
    
    print(f"🎯 Generating adaptive nonattainment map for {location_name}")
    
    try:
        # Step 1: Analyze location first
        client = NonAttainmentAreasClient()
        analysis_result = client.analyze_location(longitude, latitude)
        
        if not analysis_result.query_success:
            return json.dumps({
                "success": False,
                "error": f"Analysis failed: {analysis_result.error_message}",
                "location": location_name
            })
        
        # Step 2: Generate adaptive map
        generator = NonAttainmentMapGenerator()
        pdf_path = generator.generate_adaptive_nonattainment_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            analysis_result=analysis_result
        )
        
        # Step 3: Compile results
        summary = client.get_area_summary(analysis_result)
        
        response = {
            "success": True,
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "analysis_results": {
                "has_violations": analysis_result.has_nonattainment_areas,
                "total_areas": analysis_result.area_count,
                "status": summary["status"]
            },
            "adaptive_settings": {
                "reasoning": "Found violations - using detailed view" if analysis_result.has_nonattainment_areas else "Clean air - using regional overview",
                "buffer_miles": 15.0 if analysis_result.has_nonattainment_areas else 50.0,
                "map_focus": "detailed_violations" if analysis_result.has_nonattainment_areas else "regional_context"
            },
            "map_generation": {
                "file_path": pdf_path,
                "generated": pdf_path is not None,
                "file_type": "PDF" if pdf_path and pdf_path.endswith('.pdf') else "HTML"
            },
            "generation_timestamp": datetime.now().isoformat()
        }
        
        if analysis_result.has_nonattainment_areas:
            pollutants = list(set(area.pollutant_name for area in analysis_result.nonattainment_areas))
            response["analysis_results"]["pollutants_affected"] = pollutants
            response["analysis_results"]["recommendations"] = summary.get("recommendations", [])
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error generating adaptive nonattainment map: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude}
        })

@tool
def search_pollutant_areas(
    pollutant: str,
    include_revoked: bool = False
) -> str:
    """
    Search for all EPA nonattainment areas for a specific pollutant nationwide.
    
    This tool queries EPA data to find all areas that violate standards for
    a specific pollutant, providing comprehensive information about:
    - Geographic distribution of violations
    - Status classifications (Nonattainment vs Maintenance)
    - Severity levels (Extreme, Serious, Moderate, etc.)
    - State and regional patterns
    
    Use this tool for:
    - National pollutant trend analysis
    - Regional air quality comparisons
    - Regulatory compliance research
    - Environmental policy analysis
    
    Args:
        pollutant: Pollutant name (Ozone, PM2.5, PM10, Lead, Sulfur Dioxide, Carbon Monoxide, Nitrogen Dioxide)
        include_revoked: Whether to include areas with revoked standards
        
    Returns:
        JSON string with nationwide pollutant area information
    """
    
    print(f"🔍 Searching for {pollutant} nonattainment areas nationwide")
    
    try:
        # Initialize client
        client = NonAttainmentAreasClient()
        
        # Search for pollutant areas
        areas = client.get_pollutant_areas(pollutant, include_revoked)
        
        if not areas:
            return json.dumps({
                "success": True,
                "pollutant": pollutant,
                "areas_found": 0,
                "message": f"No nonattainment areas found for {pollutant}",
                "include_revoked": include_revoked,
                "search_timestamp": datetime.now().isoformat()
            })
        
        # Analyze results
        states = list(set(area.state_abbreviation for area in areas))
        statuses = list(set(area.current_status for area in areas))
        classifications = list(set(area.classification for area in areas if area.classification != 'Unknown'))
        
        # Group by state
        state_summary = {}
        for area in areas:
            state = area.state_abbreviation
            if state not in state_summary:
                state_summary[state] = {
                    "state_name": area.state_name,
                    "area_count": 0,
                    "areas": []
                }
            state_summary[state]["area_count"] += 1
            state_summary[state]["areas"].append({
                "area_name": area.area_name,
                "status": area.current_status,
                "classification": area.classification,
                "design_value": area.design_value,
                "design_value_units": area.design_value_units
            })
        
        response = {
            "success": True,
            "pollutant": pollutant,
            "search_parameters": {
                "include_revoked": include_revoked,
                "search_timestamp": datetime.now().isoformat()
            },
            "summary": {
                "total_areas": len(areas),
                "states_affected": len(states),
                "status_types": statuses,
                "classification_levels": classifications
            },
            "geographic_distribution": {
                "states": states,
                "state_details": state_summary
            },
            "sample_areas": [
                {
                    "area_name": area.area_name,
                    "state": area.state_abbreviation,
                    "status": area.current_status,
                    "classification": area.classification,
                    "epa_region": area.epa_region
                } for area in areas[:10]  # First 10 as examples
            ]
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching pollutant areas: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "pollutant": pollutant,
            "search_timestamp": datetime.now().isoformat()
        })

@tool
def analyze_location_with_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None,
    buffer_miles: float = 25.0,
    include_revoked: bool = False
) -> str:
    """
    Comprehensive nonattainment analysis tool that combines data analysis and map generation.
    
    This tool performs a complete air quality assessment:
    1. Analyzes location for nonattainment area intersections
    2. Provides detailed pollutant and regulatory information
    3. Generates a professional map showing violations
    4. Delivers actionable recommendations
    
    Perfect for environmental due diligence, site assessment, and regulatory compliance.
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        location_name: Optional location name for analysis
        buffer_miles: Buffer radius in miles for map generation
        include_revoked: Whether to include revoked air quality standards
        
    Returns:
        JSON string with complete analysis and map generation results
    """
    
    if location_name is None:
        location_name = f"Air Quality Assessment at {latitude:.4f}, {longitude:.4f}"
    
    print(f"🌫️ Comprehensive nonattainment analysis for {location_name}")
    
    try:
        # Step 1: Analyze location
        client = NonAttainmentAreasClient()
        analysis_result = client.analyze_location(
            longitude=longitude,
            latitude=latitude,
            include_revoked=include_revoked
        )
        
        if not analysis_result.query_success:
            return json.dumps({
                "success": False,
                "error": f"Analysis failed: {analysis_result.error_message}",
                "location": location_name
            })
        
        # Step 2: Generate map
        generator = NonAttainmentMapGenerator()
        pdf_path = generator.generate_nonattainment_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            include_revoked=include_revoked
        )
        
        # Step 3: Get detailed summary
        summary = client.get_area_summary(analysis_result)
        
        # Step 4: Compile comprehensive results
        response = {
            "success": True,
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "analysis_timestamp": analysis_result.analysis_timestamp,
            "air_quality_analysis": {
                "has_violations": analysis_result.has_nonattainment_areas,
                "total_areas": analysis_result.area_count,
                "status": summary["status"],
                "regulatory_compliance": "Non-compliant" if analysis_result.has_nonattainment_areas else "Compliant"
            },
            "map_generation": {
                "map_created": pdf_path is not None,
                "file_path": pdf_path,
                "buffer_miles": buffer_miles,
                "file_type": "PDF" if pdf_path and pdf_path.endswith('.pdf') else "HTML"
            }
        }
        
        if analysis_result.has_nonattainment_areas:
            # Extract detailed violation information
            violations = []
            for area in analysis_result.nonattainment_areas:
                violations.append({
                    "pollutant": area.pollutant_name,
                    "area_name": area.area_name,
                    "state": area.state_name,
                    "status": area.current_status,
                    "classification": area.classification,
                    "design_value": area.design_value,
                    "design_value_units": area.design_value_units,
                    "meets_naaqs": area.meets_naaqs
                })
            
            response["violations_details"] = violations
            response["recommendations"] = summary.get("recommendations", [])
            response["regulatory_implications"] = "Location is subject to Clean Air Act nonattainment area regulations"
        else:
            response["clean_air_status"] = {
                "message": "Location meets all National Ambient Air Quality Standards",
                "regulatory_status": "No additional Clean Air Act requirements"
            }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in comprehensive nonattainment analysis: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude}
        })

# Export tools list for easy import
NONATTAINMENT_TOOLS = [
    analyze_nonattainment_areas,
    generate_nonattainment_map,
    generate_adaptive_nonattainment_map,
    search_pollutant_areas,
    analyze_location_with_map
]

def get_nonattainment_tool_descriptions() -> Dict[str, str]:
    """Get descriptions of all available nonattainment tools"""
    return {
        "analyze_nonattainment_areas": "Analyze location for EPA nonattainment areas - provides detailed air quality violation information and regulatory compliance status",
        "generate_nonattainment_map": "Generate professional PDF map showing nonattainment areas - customizable with pollutant filters, base maps, and styling options",
        "generate_adaptive_nonattainment_map": "Generate intelligent adaptive map - automatically adjusts settings based on air quality analysis results for optimal visualization",
        "search_pollutant_areas": "Search nationwide for specific pollutant nonattainment areas - provides geographic distribution and regulatory status information",
        "analyze_location_with_map": "Comprehensive analysis combining data retrieval and map generation - complete air quality assessment with professional documentation"
    } 