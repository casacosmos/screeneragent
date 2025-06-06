#!/usr/bin/env python3
"""
Async Environmental Analysis Tools

This module provides async tools for environmental analysis using LangGraph patterns.
These tools can be used with LangGraph agents for concurrent analysis operations.
"""

import asyncio
import json
import logging
from typing import Annotated, Dict, List, Any, Optional, Tuple
from datetime import datetime

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from langgraph.graph import MessagesState

# Import our environmental clients
from WetlandsINFO.wetlands_client import WetlandsClient, WetlandHabitatInfo
from WetlandsINFO.generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3
from NonAttainmentINFO.nonattainment_client import NonAttainmentAreasClient, NonAttainmentAnalysisResult
from NonAttainmentINFO.generate_nonattainment_map_pdf import NonAttainmentMapGenerator
from HabitatINFO.habitat_client import CriticalHabitatClient, HabitatAnalysisResult
from HabitatINFO.generate_critical_habitat_map_pdf import CriticalHabitatMapGenerator
from karst.comprehensive_karst_analysis import ComprehensiveKarstAnalyzer
from karst_map_generator import KarstMapGenerator
from FloodINFO.firmette_client import FEMAFIRMetteClient
from FloodINFO.preliminary_comparison_client import FEMAPreliminaryComparisonClient
from FloodINFO.abfe_client import FEMAABFEClient
from output_directory_manager import get_output_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentalState(MessagesState):
    """Extended state for environmental analysis"""
    project_name: Optional[str] = None
    analysis_location: Optional[List[float]] = None  # [longitude, latitude] - changed from Tuple for API compatibility
    analysis_results: Dict[str, Any] = {}
    user_id: Optional[str] = None


@tool
async def analyze_wetlands_async(
    longitude: float,
    latitude: float,
    include_riparian: bool = True,
    include_watershed: bool = True,
    generate_map: bool = True,
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Asynchronously analyze wetland and habitat information at a specific location and optionally generate a map.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate  
        include_riparian: Whether to include riparian area data
        include_watershed: Whether to include watershed boundary data
        generate_map: Whether to generate a wetland map (default: True)
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with wetland analysis results
    """
    try:
        logger.info(f"Starting async wetland analysis at {longitude}, {latitude}")
        
        # Run the wetland analysis in an executor to make it async
        loop = asyncio.get_event_loop()
        client = WetlandsClient()
        
        wetland_data = await loop.run_in_executor(
            None,
            client.query_point_wetland_info,
            longitude,
            latitude,
            include_riparian,
            include_watershed
        )
        
        # Save data using output directory manager
        await loop.run_in_executor(
            None,
            client.save_wetland_data,
            wetland_data
        )
        
        # Generate map if requested
        map_path = None
        if generate_map:
            try:
                logger.info("Generating wetland map...")
                map_generator = WetlandMapGeneratorV3()
                
                # Get location name for map title
                location_name = f"Wetland Analysis ({latitude:.4f}°N, {abs(longitude):.4f}°W)"
                
                # Generate map using output directory manager
                output_manager = get_output_manager()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename = f"wetland_map_{timestamp}.pdf"
                map_output_path = output_manager.get_file_path(map_filename, "maps")
                
                map_path = await loop.run_in_executor(
                    None,
                    map_generator.generate_wetland_map_pdf,
                    longitude,
                    latitude,
                    location_name,
                    0.5,  # buffer_miles
                    "World_Imagery",  # base_map
                    300,  # dpi
                    (1224, 792),  # output_size
                    True,  # include_legend
                    "Letter ANSI A Portrait",  # layout_template
                    0.8,  # wetland_transparency
                    map_output_path  # output_filename
                )
                
                if map_path:
                    logger.info(f"Wetland map generated: {map_path}")
                else:
                    logger.warning("Failed to generate wetland map")
                    
            except Exception as e:
                logger.error(f"Error generating wetland map: {e}")
                map_path = None
        
        # Update state if available
        if state is not None:
            state.get("analysis_results", {})["wetlands"] = {
                "location": (longitude, latitude),
                "has_data": wetland_data.has_wetland_data,
                "wetland_count": len(wetland_data.wetlands),
                "riparian_count": len(wetland_data.riparian_areas),
                "watershed_count": len(wetland_data.watersheds),
                "map_generated": map_path is not None,
                "map_path": map_path
            }
        
        # Prepare response
        result = {
            "analysis_type": "wetlands",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "has_wetland_data": wetland_data.has_wetland_data,
                "has_riparian_data": wetland_data.has_riparian_data,
                "has_watershed_data": wetland_data.has_watershed_data,
                "total_wetlands": len(wetland_data.wetlands),
                "total_riparian_areas": len(wetland_data.riparian_areas),
                "total_watersheds": len(wetland_data.watersheds),
                "map_generated": map_path is not None,
                "map_path": map_path
            },
            "status": "success"
        }
        
        logger.info(f"Completed async wetland analysis: {result['summary']}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "wetlands",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Async wetland analysis failed: {e}")
        return json.dumps(error_result, indent=2)


@tool
async def analyze_nonattainment_async(
    longitude: float,
    latitude: float,
    include_revoked: bool = False,
    buffer_meters: float = 0,
    pollutants: Optional[List[str]] = None,
    generate_map: bool = True,
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Asynchronously analyze nonattainment areas at a specific location and optionally generate a map.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        include_revoked: Whether to include revoked standards
        buffer_meters: Buffer distance around point in meters
        pollutants: List of specific pollutants to check
        generate_map: Whether to generate a nonattainment map (default: True)
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with nonattainment analysis results
    """
    try:
        logger.info(f"Starting async nonattainment analysis at {longitude}, {latitude}")
        
        # Run the nonattainment analysis in an executor to make it async
        loop = asyncio.get_event_loop()
        client = NonAttainmentAreasClient()
        
        analysis_result = await loop.run_in_executor(
            None,
            client.analyze_location,
            longitude,
            latitude,
            include_revoked,
            buffer_meters,
            pollutants
        )
        
        # Save data using output directory manager
        await loop.run_in_executor(
            None,
            client.save_nonattainment_data,
            analysis_result
        )
        
        # Generate map if requested
        map_path = None
        if generate_map:
            try:
                logger.info("Generating nonattainment map...")
                map_generator = NonAttainmentMapGenerator()
                
                # Get location name for map title
                location_name = f"Nonattainment Analysis ({latitude:.4f}°N, {abs(longitude):.4f}°W)"
                
                # Generate map using output directory manager
                output_manager = get_output_manager()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename = f"nonattainment_map_{timestamp}.pdf"
                map_output_path = output_manager.get_file_path(map_filename, "maps")
                
                map_path = await loop.run_in_executor(
                    None,
                    map_generator.generate_nonattainment_map_pdf,
                    longitude,
                    latitude,
                    location_name,
                    0.5,  # buffer_miles
                    "World_Imagery",  # base_map
                    300,  # dpi
                    (1224, 792),  # output_size
                    True,  # include_legend
                    "Letter ANSI A Portrait",  # layout_template
                    include_revoked,  # include_revoked
                    0.8,  # layer_transparency
                    map_output_path  # output_filename
                )
                
                if map_path:
                    logger.info(f"Nonattainment map generated: {map_path}")
                else:
                    logger.warning("Failed to generate nonattainment map")
                    
            except Exception as e:
                logger.error(f"Error generating nonattainment map: {e}")
                map_path = None
        
        # Update state if available
        if state is not None:
            state.get("analysis_results", {})["nonattainment"] = {
                "location": (longitude, latitude),
                "has_areas": analysis_result.has_nonattainment_areas,
                "area_count": analysis_result.area_count,
                "query_success": analysis_result.query_success,
                "map_generated": map_path is not None,
                "map_path": map_path
            }
        
        # Prepare response
        result = {
            "analysis_type": "nonattainment",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": analysis_result.analysis_timestamp,
            "summary": {
                "has_nonattainment_areas": analysis_result.has_nonattainment_areas,
                "area_count": analysis_result.area_count,
                "query_success": analysis_result.query_success,
                "error_message": analysis_result.error_message,
                "map_generated": map_path is not None,
                "map_path": map_path
            },
            "status": "success" if analysis_result.query_success else "error"
        }
        
        logger.info(f"Completed async nonattainment analysis: {result['summary']}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "nonattainment",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Async nonattainment analysis failed: {e}")
        return json.dumps(error_result, indent=2)


@tool
async def analyze_flood_risk_async(
    longitude: float,
    latitude: float,
    include_firmette: bool = True,
    include_preliminary: bool = True,
    include_abfe: bool = True,
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Asynchronously analyze flood risk information at a specific location.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        include_firmette: Whether to generate FIRMette
        include_preliminary: Whether to check preliminary flood data
        include_abfe: Whether to check ABFE data
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with flood risk analysis results
    """
    try:
        logger.info(f"Starting async flood risk analysis at {longitude}, {latitude}")
        
        loop = asyncio.get_event_loop()
        results = {}
        
        # Run flood analyses concurrently
        tasks = []
        
        if include_firmette:
            firmette_client = FEMAFIRMetteClient()
            tasks.append(
                loop.run_in_executor(
                    None,
                    firmette_client.generate_firmette,
                    longitude,
                    latitude
                )
            )
        
        if include_preliminary:
            prelim_client = FEMAPreliminaryComparisonClient()
            tasks.append(
                loop.run_in_executor(
                    None,
                    prelim_client.generate_comparison,
                    longitude,
                    latitude
                )
            )
        
        if include_abfe:
            abfe_client = FEMAABFEClient()
            tasks.append(
                loop.run_in_executor(
                    None,
                    abfe_client.query_abfe_data,
                    longitude,
                    latitude
                )
            )
        
        # Wait for all tasks to complete
        if tasks:
            flood_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            result_types = []
            if include_firmette:
                result_types.append("firmette")
            if include_preliminary:
                result_types.append("preliminary")
            if include_abfe:
                result_types.append("abfe")
            
            for i, result in enumerate(flood_results):
                if isinstance(result, Exception):
                    results[result_types[i]] = {"status": "error", "error": str(result)}
                else:
                    results[result_types[i]] = {"status": "success", "data": result}
        
        # Update state if available
        if state is not None:
            state.get("analysis_results", {})["flood"] = {
                "location": (longitude, latitude),
                "components": list(results.keys()),
                "success_count": len([r for r in results.values() if r.get("status") == "success"])
            }
        
        # Prepare response
        response = {
            "analysis_type": "flood_risk",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "status": "success"
        }
        
        logger.info(f"Completed async flood risk analysis: {len(results)} components")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "flood_risk",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Async flood risk analysis failed: {e}")
        return json.dumps(error_result, indent=2)


@tool
async def analyze_critical_habitat_async(
    longitude: float,
    latitude: float,
    include_proposed: bool = True,
    buffer_meters: float = 0,
    generate_map: bool = True,
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Asynchronously analyze critical habitat information at a specific location and optionally generate a map.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        include_proposed: Whether to include proposed critical habitats
        buffer_meters: Buffer distance around point in meters
        generate_map: Whether to generate a critical habitat map (default: True)
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with critical habitat analysis results
    """
    try:
        logger.info(f"Starting async critical habitat analysis at {longitude}, {latitude}")
        
        # Run the habitat analysis in an executor to make it async
        loop = asyncio.get_event_loop()
        client = CriticalHabitatClient()
        
        analysis_result = await loop.run_in_executor(
            None,
            client.analyze_location,
            longitude,
            latitude,
            include_proposed,
            buffer_meters
        )
        
        # Save data using output directory manager
        await loop.run_in_executor(
            None,
            client.save_habitat_data,
            analysis_result
        )
        
        # Generate map if requested
        map_path = None
        if generate_map:
            try:
                logger.info("Generating critical habitat map...")
                map_generator = CriticalHabitatMapGenerator()
                
                # Get location name for map title
                location_name = f"Critical Habitat Analysis ({latitude:.4f}°N, {abs(longitude):.4f}°W)"
                
                # Generate map using output directory manager
                output_manager = get_output_manager()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename = f"critical_habitat_map_{timestamp}.pdf"
                map_output_path = output_manager.get_file_path(map_filename, "maps")
                
                map_path = await loop.run_in_executor(
                    None,
                    map_generator.generate_critical_habitat_map_pdf,
                    longitude,
                    latitude,
                    location_name,
                    0.5,  # buffer_miles
                    "World_Imagery",  # base_map
                    300,  # dpi
                    (1224, 792),  # output_size
                    True,  # include_legend
                    "Letter ANSI A Portrait",  # layout_template
                    include_proposed,  # include_proposed
                    0.8,  # habitat_transparency
                    map_output_path  # output_filename
                )
                
                if map_path:
                    logger.info(f"Critical habitat map generated: {map_path}")
                else:
                    logger.warning("Failed to generate critical habitat map")
                    
            except Exception as e:
                logger.error(f"Error generating critical habitat map: {e}")
                map_path = None
        
        # Update state if available
        if state is not None:
            state.get("analysis_results", {})["critical_habitat"] = {
                "location": (longitude, latitude),
                "has_habitat": analysis_result.has_critical_habitat,
                "habitat_count": analysis_result.habitat_count,
                "query_success": analysis_result.query_success,
                "map_generated": map_path is not None,
                "map_path": map_path
            }
        
        # Prepare response
        result = {
            "analysis_type": "critical_habitat",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": analysis_result.analysis_timestamp,
            "summary": {
                "has_critical_habitat": analysis_result.has_critical_habitat,
                "habitat_count": analysis_result.habitat_count,
                "query_success": analysis_result.query_success,
                "error_message": analysis_result.error_message,
                "species_count": len(set(h.species_common_name for h in analysis_result.critical_habitats)),
                "map_generated": map_path is not None,
                "map_path": map_path
            },
            "status": "success" if analysis_result.query_success else "error"
        }
        
        logger.info(f"Completed async critical habitat analysis: {result['summary']}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "critical_habitat",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Async critical habitat analysis failed: {e}")
        return json.dumps(error_result, indent=2)


@tool
async def analyze_karst_async(
    longitude: float,
    latitude: float,
    search_radius_miles: float = 2.0,
    generate_map: bool = True,
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Asynchronously analyze karst geology information at a specific location and optionally generate a map.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        search_radius_miles: Search radius in miles for karst features
        generate_map: Whether to generate a karst map (default: True)
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with karst analysis results
    """
    try:
        logger.info(f"Starting async karst analysis at {longitude}, {latitude}")
        
        # Run the karst analysis in an executor to make it async
        loop = asyncio.get_event_loop()
        analyzer = ComprehensiveKarstAnalyzer()
        
        analysis_result = await loop.run_in_executor(
            None,
            analyzer.analyze_comprehensive_karst,
            longitude,
            latitude,
            search_radius_miles
        )
        
        # Save data using output directory manager
        await loop.run_in_executor(
            None,
            analyzer.save_karst_data,
            analysis_result
        )
        
        # Generate map if requested
        map_path = None
        if generate_map:
            try:
                logger.info("Generating karst map...")
                
                # Get output directory for maps
                output_manager = get_output_manager()
                map_output_dir = output_manager.get_subdirectory("maps")
                
                # Create map generator with the correct interface
                map_generator = KarstMapGenerator(
                    longitude=longitude,
                    latitude=latitude,
                    output_directory=map_output_dir,
                    map_buffer_miles=search_radius_miles
                )
                
                # Generate map
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                map_filename_prefix = f"karst_analysis_{timestamp}"
                
                map_path = await loop.run_in_executor(
                    None,
                    map_generator.generate_karst_map,
                    map_filename_prefix
                )
                
                if map_path:
                    logger.info(f"Karst map generated: {map_path}")
                else:
                    logger.warning("Failed to generate karst map")
                    
            except Exception as e:
                logger.error(f"Error generating karst map: {e}")
                map_path = None
        
        # Update state if available
        if state is not None:
            prapec_found = analysis_result.get("prapec_analysis", {}).get("karst_found", False)
            buffer_found = analysis_result.get("buffer_zone_analysis", {}).get("buffer_zones_found", False)
            
            state.get("analysis_results", {})["karst"] = {
                "location": (longitude, latitude),
                "prapec_karst_found": prapec_found,
                "buffer_zones_found": buffer_found,
                "overall_impact": analysis_result.get("combined_assessment", {}).get("overall_karst_impact", "none"),
                "query_success": analysis_result.get("success", False),
                "map_generated": map_path is not None,
                "map_path": map_path
            }
        
        # Prepare response
        result = {
            "analysis_type": "karst",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": analysis_result.get("query_time", datetime.now().isoformat()),
            "summary": {
                "analysis_success": analysis_result.get("success", False),
                "prapec_karst_found": analysis_result.get("prapec_analysis", {}).get("karst_found", False),
                "buffer_zones_found": analysis_result.get("buffer_zone_analysis", {}).get("buffer_zones_found", False),
                "overall_karst_impact": analysis_result.get("combined_assessment", {}).get("overall_karst_impact", "none"),
                "regulatory_zones_count": len(analysis_result.get("combined_assessment", {}).get("regulatory_zones_identified", [])),
                "search_radius_miles": search_radius_miles,
                "map_generated": map_path is not None,
                "map_path": map_path
            },
            "status": "success" if analysis_result.get("success", False) else "error"
        }
        
        if not analysis_result.get("success", False):
            result["error_message"] = analysis_result.get("error", "Unknown error")
        
        logger.info(f"Completed async karst analysis: {result['summary']}")
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "karst",
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Async karst analysis failed: {e}")
        return json.dumps(error_result, indent=2)


@tool
async def comprehensive_environmental_analysis_async(
    longitude: float,
    latitude: float,
    project_name: str = "Environmental_Analysis",
    state: Annotated[EnvironmentalState, InjectedState] = None,
    config: RunnableConfig = None
) -> str:
    """
    Run a comprehensive environmental analysis combining all available data sources asynchronously.
    
    Args:
        longitude: Longitude coordinate
        latitude: Latitude coordinate
        project_name: Name for the analysis project
        state: Graph state (injected)
        config: Runtime configuration (injected)
        
    Returns:
        JSON string with comprehensive analysis results
    """
    try:
        logger.info(f"Starting comprehensive async environmental analysis for {project_name} at {longitude}, {latitude}")
        
        # Update state with project info
        if state is not None:
            state["project_name"] = project_name
            state["analysis_location"] = [longitude, latitude]
        
        # Run all analyses concurrently
        tasks = [
            analyze_wetlands_async(longitude, latitude, state=state, config=config),
            analyze_nonattainment_async(longitude, latitude, state=state, config=config),
            analyze_flood_risk_async(longitude, latitude, state=state, config=config),
            analyze_critical_habitat_async(longitude, latitude, state=state, config=config),
            analyze_karst_async(longitude, latitude, state=state, config=config)
        ]
        
        # Wait for all analyses to complete
        analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        results = {}
        for i, (analysis_type, result) in enumerate(zip(["wetlands", "nonattainment", "flood", "critical_habitat", "karst"], analysis_results)):
            if isinstance(result, Exception):
                results[analysis_type] = {"status": "error", "error": str(result)}
            else:
                try:
                    results[analysis_type] = json.loads(result)
                except json.JSONDecodeError:
                    results[analysis_type] = {"status": "error", "error": "Invalid JSON response"}
        
        # Generate comprehensive report
        success_count = len([r for r in results.values() if r.get("status") == "success"])
        
        comprehensive_result = {
            "analysis_type": "comprehensive",
            "project_name": project_name,
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_analyses": len(results),
                "successful_analyses": success_count,
                "failed_analyses": len(results) - success_count,
                "completion_rate": f"{(success_count / len(results)) * 100:.1f}%"
            },
            "results": results,
            "status": "success" if success_count > 0 else "error"
        }
        
        # Save comprehensive results
        output_manager = get_output_manager()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_analysis_{project_name}_{timestamp}.json"
        file_path = output_manager.get_file_path(filename, "reports")
        
        with open(file_path, 'w') as f:
            json.dump(comprehensive_result, f, indent=2)
        
        logger.info(f"Comprehensive analysis completed: {success_count}/{len(results)} successful")
        return json.dumps(comprehensive_result, indent=2)
        
    except Exception as e:
        error_result = {
            "analysis_type": "comprehensive", 
            "project_name": project_name,
            "location": {"longitude": longitude, "latitude": latitude},
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error_message": str(e)
        }
        logger.error(f"Comprehensive async analysis failed: {e}")
        return json.dumps(error_result, indent=2)


# List of all async environmental tools
ASYNC_ENVIRONMENTAL_TOOLS = [
    analyze_wetlands_async,
    analyze_nonattainment_async,
    analyze_flood_risk_async,
    analyze_critical_habitat_async,
    analyze_karst_async,
    comprehensive_environmental_analysis_async
] 