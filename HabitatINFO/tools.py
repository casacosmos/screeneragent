#!/usr/bin/env python3
"""
Critical Habitat Analysis Tools

This module provides LangChain-compatible tools for analyzing critical habitat areas
and determining if locations intersect with protected species habitats.
"""

from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Type
import json
import logging
from datetime import datetime

from .habitat_client import CriticalHabitatClient, HabitatAnalysisResult
from .map_tools import generate_adaptive_critical_habitat_map

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CriticalHabitatAnalysisInput(BaseModel):
    """Input schema for critical habitat analysis"""
    longitude: float = Field(description="Longitude coordinate (decimal degrees)")
    latitude: float = Field(description="Latitude coordinate (decimal degrees)")
    include_proposed: bool = Field(
        default=True, 
        description="Whether to include proposed critical habitat designations"
    )
    buffer_meters: float = Field(
        default=0, 
        description="Buffer distance around point in meters (0 for exact point)"
    )


@tool
def analyze_critical_habitat(
    longitude: float,
    latitude: float,
    include_proposed: bool = True,
    buffer_meters: float = 0
) -> str:
    """
    Analyze a geographic location to determine if it intersects with critical habitat areas 
    designated for threatened and endangered species under the Endangered Species Act.
    
    This tool queries USFWS critical habitat data and provides:
    - Whether the location has critical habitat designations
    - Details about affected species
    - Final vs proposed habitat status
    - Regulatory recommendations
    
    Use this tool when you need to:
    - Check if a location has critical habitat
    - Identify protected species at a location
    - Assess regulatory requirements for development
    - Understand conservation implications
    
    Args:
        longitude: Longitude coordinate (decimal degrees)
        latitude: Latitude coordinate (decimal degrees)
        include_proposed: Whether to include proposed critical habitat designations
        buffer_meters: Buffer distance around point in meters (0 for exact point)
        
    Returns:
        JSON string with detailed habitat analysis results
    """
    
    try:
        logger.info(f"Analyzing critical habitat for location: {longitude}, {latitude}")
        
        # Create client for this request
        client = CriticalHabitatClient()
        
        # Perform habitat analysis
        result = client.analyze_location(
            longitude=longitude,
            latitude=latitude,
            include_proposed=include_proposed,
            buffer_meters=buffer_meters
        )
        
        # Generate summary
        summary = client.get_habitat_summary(result)
        
        # Format response
        response = _format_analysis_response(summary, result)
        
        logger.info(f"Critical habitat analysis completed for {longitude}, {latitude}")
        return response
        
    except Exception as e:
        error_msg = f"Error analyzing critical habitat: {str(e)}"
        logger.error(error_msg)
        return json.dumps({
            "status": "error",
            "message": error_msg,
            "location": [longitude, latitude],
            "timestamp": datetime.now().isoformat()
        }, indent=2)


def _format_analysis_response(summary: Dict[str, Any], result) -> str:
    """Format the analysis response for display"""
    
    if summary["status"] == "error":
        return json.dumps({
            "critical_habitat_analysis": {
                "status": "error",
                "location": summary["location"],
                "error": summary["message"]
            }
        }, indent=2)
    
    if summary["status"] == "no_habitat":
        return json.dumps({
            "critical_habitat_analysis": {
                "status": "no_critical_habitat",
                "location": summary["location"],
                "message": "No critical habitat areas found at this location",
                "analysis_timestamp": summary["analysis_timestamp"],
                "regulatory_status": "No ESA critical habitat restrictions apply"
            }
        }, indent=2)
    
    # Format detailed habitat information
    response_data = {
        "critical_habitat_analysis": {
            "status": "critical_habitat_found",
            "location": summary["location"],
            "analysis_timestamp": summary["analysis_timestamp"],
            "summary": summary["summary"],
            "regulatory_implications": {
                "esa_consultation_required": True,
                "final_designations": summary["summary"]["final_designations"],
                "proposed_designations": summary["summary"]["proposed_designations"],
                "total_species_affected": summary["summary"]["unique_species"]
            },
            "affected_species": _format_species_details(summary["species_details"]),
            "recommendations": summary["recommendations"],
            "next_steps": [
                "Contact USFWS for formal consultation",
                "Review project impacts on critical habitat",
                "Consider alternative locations if possible",
                "Develop mitigation measures if needed"
            ]
        }
    }
    
    return json.dumps(response_data, indent=2)


def _format_species_details(species_list: List[Dict]) -> List[Dict]:
    """Format species details for display"""
    
    formatted_species = []
    
    # Group by species to avoid duplicates
    species_groups = {}
    for species in species_list:
        key = species["common_name"]
        if key not in species_groups:
            species_groups[key] = {
                "common_name": species["common_name"],
                "scientific_name": species["scientific_name"],
                "habitat_units": [],
                "designation_types": set(),
                "geometry_types": set()
            }
        
        species_groups[key]["habitat_units"].append(species["unit_name"])
        species_groups[key]["designation_types"].add(species["habitat_type"])
        species_groups[key]["geometry_types"].add(species["geometry_type"])
    
    # Format grouped species
    for species_data in species_groups.values():
        formatted_species.append({
            "common_name": species_data["common_name"],
            "scientific_name": species_data["scientific_name"],
            "habitat_units": list(set(species_data["habitat_units"])),
            "designation_types": list(species_data["designation_types"]),
            "geometry_types": list(species_data["geometry_types"]),
            "unit_count": len(set(species_data["habitat_units"]))
        })
    
    return formatted_species


class CriticalHabitatAnalysisTool(BaseTool):
    """Tool for analyzing critical habitat at a specific location"""
    
    name: str = "analyze_critical_habitat"
    description: str = """
    Analyze a geographic location to determine if it intersects with critical habitat areas 
    designated for threatened and endangered species under the Endangered Species Act.
    
    This tool queries USFWS critical habitat data and provides:
    - Whether the location has critical habitat designations
    - Details about affected species
    - Final vs proposed habitat status
    - Regulatory recommendations
    
    Use this tool when you need to:
    - Check if a location has critical habitat
    - Identify protected species at a location
    - Assess regulatory requirements for development
    - Understand conservation implications
    """
    args_schema: Type[BaseModel] = CriticalHabitatAnalysisInput
    
    def _run(self, longitude: float, latitude: float, 
             include_proposed: bool = True, buffer_meters: float = 0) -> str:
        """Execute critical habitat analysis"""
        
        try:
            logger.info(f"Analyzing critical habitat for location: {longitude}, {latitude}")
            
            # Create client for this request
            client = CriticalHabitatClient()
            
            # Perform habitat analysis
            result = client.analyze_location(
                longitude=longitude,
                latitude=latitude,
                include_proposed=include_proposed,
                buffer_meters=buffer_meters
            )
            
            # Generate summary
            summary = client.get_habitat_summary(result)
            
            # Format response
            response = self._format_analysis_response(summary, result)
            
            logger.info(f"Critical habitat analysis completed for {longitude}, {latitude}")
            return response
            
        except Exception as e:
            error_msg = f"Error analyzing critical habitat: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "location": [longitude, latitude],
                "timestamp": datetime.now().isoformat()
            }, indent=2)
    
    def _format_analysis_response(self, summary: Dict[str, Any], 
                                 result: HabitatAnalysisResult) -> str:
        """Format the analysis response for display"""
        
        if summary["status"] == "error":
            return json.dumps({
                "critical_habitat_analysis": {
                    "status": "error",
                    "location": summary["location"],
                    "error": summary["message"]
                }
            }, indent=2)
        
        if summary["status"] == "no_habitat":
            return json.dumps({
                "critical_habitat_analysis": {
                    "status": "no_critical_habitat",
                    "location": summary["location"],
                    "message": "No critical habitat areas found at this location",
                    "analysis_timestamp": summary["analysis_timestamp"],
                    "regulatory_status": "No ESA critical habitat restrictions apply"
                }
            }, indent=2)
        
        # Format detailed habitat information
        response_data = {
            "critical_habitat_analysis": {
                "status": "critical_habitat_found",
                "location": summary["location"],
                "analysis_timestamp": summary["analysis_timestamp"],
                "summary": summary["summary"],
                "regulatory_implications": {
                    "esa_consultation_required": True,
                    "final_designations": summary["summary"]["final_designations"],
                    "proposed_designations": summary["summary"]["proposed_designations"],
                    "total_species_affected": summary["summary"]["unique_species"]
                },
                "affected_species": self._format_species_details(summary["species_details"]),
                "recommendations": summary["recommendations"],
                "next_steps": [
                    "Contact USFWS for formal consultation",
                    "Review project impacts on critical habitat",
                    "Consider alternative locations if possible",
                    "Develop mitigation measures if needed"
                ]
            }
        }
        
        return json.dumps(response_data, indent=2)
    
    def _format_species_details(self, species_list: List[Dict]) -> List[Dict]:
        """Format species details for display"""
        
        formatted_species = []
        
        # Group by species to avoid duplicates
        species_groups = {}
        for species in species_list:
            key = species["common_name"]
            if key not in species_groups:
                species_groups[key] = {
                    "common_name": species["common_name"],
                    "scientific_name": species["scientific_name"],
                    "habitat_units": [],
                    "designation_types": set(),
                    "geometry_types": set()
                }
            
            species_groups[key]["habitat_units"].append(species["unit_name"])
            species_groups[key]["designation_types"].add(species["habitat_type"])
            species_groups[key]["geometry_types"].add(species["geometry_type"])
        
        # Format grouped species
        for species_data in species_groups.values():
            formatted_species.append({
                "common_name": species_data["common_name"],
                "scientific_name": species_data["scientific_name"],
                "habitat_units": list(set(species_data["habitat_units"])),
                "designation_types": list(species_data["designation_types"]),
                "geometry_types": list(species_data["geometry_types"]),
                "unit_count": len(set(species_data["habitat_units"]))
            })
        
        return formatted_species


# Export tools list - using @tool decorated functions
habitat_tools = [
    generate_adaptive_critical_habitat_map
] 