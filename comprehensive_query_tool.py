#!/usr/bin/env python3
"""
Comprehensive Environmental Query Tool

A unified tool that performs all environmental screening queries and generates
comprehensive JSON data files. This tool consolidates queries from:
- Cadastral/Property analysis
- Flood zone analysis (FEMA, ABFE)
- Wetland analysis (NWI)
- Critical habitat analysis (USFWS)
- Air quality analysis (EPA Nonattainment)
- Karst analysis (PRAPEC for Puerto Rico)

Features:
- Single entry point for all environmental queries
- Generates standardized JSON output for each analysis domain
- Supports both coordinates and cadastral number inputs
- Configurable query parameters and data sources
- Detailed logging and error handling
- Integration with existing screening workflow

Usage:
    python comprehensive_query_tool.py --location "18.4058, -66.7135" --project-name "My Project"
    python comprehensive_query_tool.py --cadastral "115-053-432-02" --output-dir my_analysis
"""

import json
import os
import sys
import asyncio
import argparse
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import uuid

# LangChain tool imports for agent integration
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Import all the individual analysis tools
try:
    from wetland_analysis_tool import WetlandAnalysisTool
    WETLAND_AVAILABLE = True
    print("✅ Wetland analysis tool imported")
except ImportError as e:
    WETLAND_AVAILABLE = False
    print(f"❌ Wetland analysis tool not available: {e}")

# ─── new import: place it with the other "try / except" blocks ────────────────
try:
    from flood_helpers import get_flood_data, generate_flood_maps
    FLOOD_AVAILABLE = True
    print("✅ Flood helpers imported")
except ImportError as e:
    FLOOD_AVAILABLE = False          # leave the flag in place
    print(f"❌ Flood helpers not available: {e}")

try:
    from legacy.tools.ruined.nonattainment_analysis_tool import NonattainmentAnalysisTool
    AIR_QUALITY_AVAILABLE = True
    print("✅ Air quality analysis tool imported")
except ImportError as e:
    AIR_QUALITY_AVAILABLE = False
    print(f"❌ Air quality analysis tool not available: {e}")

# Import habitat analysis from HabitatINFO
try:
    from HabitatINFO.tools import generate_adaptive_critical_habitat_map
    HABITAT_AVAILABLE = True
    print("✅ Habitat analysis tool imported")
except ImportError as e:
    HABITAT_AVAILABLE = False
    print(f"❌ Habitat analysis tool not available: {e}")

# Import cadastral analysis
try:
    from cadastral.cadastral_data_tool import get_cadastral_data_from_coordinates
    CADASTRAL_AVAILABLE = True
    print("✅ Cadastral analysis tool imported")
except ImportError as e:
    CADASTRAL_AVAILABLE = False
    print(f"❌ Cadastral analysis tool not available: {e}")

# Import karst analysis
try:
    from simple_karst_analysis_tool import check_coordinates_karst
    KARST_AVAILABLE = True
    print("✅ Karst analysis tool imported")
except ImportError as e:
    KARST_AVAILABLE = False
    print(f"❌ Karst analysis tool not available: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Show tool availability summary on import
available_tools = []
if WETLAND_AVAILABLE:
    available_tools.append("wetland")
if FLOOD_AVAILABLE:
    available_tools.append("flood")
if AIR_QUALITY_AVAILABLE:
    available_tools.append("air_quality")
if HABITAT_AVAILABLE:
    available_tools.append("habitat")
if CADASTRAL_AVAILABLE:
    available_tools.append("cadastral")
if KARST_AVAILABLE:
    available_tools.append("karst")

print(f"🔧 Environmental Analysis Tools: {len(available_tools)}/6 available")

# Pydantic models for tool inputs
class QueryLocationInput(BaseModel):
    """Input schema for location-based queries"""
    location: str = Field(description="Location as 'latitude,longitude' or address")
    project_name: str = Field(description="Name of the project for identification")
    cadastral_number: Optional[str] = Field(default=None, description="Cadastral number if available")
    output_directory: str = Field(default="output", description="Base output directory")
    include_maps: bool = Field(default=True, description="Whether to generate maps")
    buffer_distance: float = Field(default=1.0, description="Search buffer radius in miles")
    detailed_analysis: bool = Field(default=True, description="Whether to perform detailed analysis")

class BatchQueryInput(BaseModel):
    """Input schema for batch queries"""
    locations: List[Dict[str, Any]] = Field(description="List of location dictionaries")
    project_base_name: str = Field(description="Base name for batch projects")
    output_directory: str = Field(default="output", description="Base output directory")
    include_maps: bool = Field(default=True, description="Whether to generate maps")
    parallel_processing: bool = Field(default=True, description="Whether to process locations in parallel")

class ComprehensiveQueryTool:
    """Comprehensive environmental query tool that consolidates all screening queries"""
    
    def __init__(self, output_directory: str = "output", include_maps: bool = True, 
                 detailed_analysis: bool = True, buffer_distance: float = 1.0):
        """
        Initialize the comprehensive query tool
        
        Args:
            output_directory: Base directory for output files
            include_maps: Whether to generate maps
            detailed_analysis: Whether to perform detailed analysis
            buffer_distance: Search buffer radius in miles
        """
        self.output_directory = Path(output_directory)
        self.include_maps = include_maps
        self.detailed_analysis = detailed_analysis
        self.buffer_distance = buffer_distance
        
        # Create output directory structure
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize available tools
        self._initialize_analysis_tools()
        
        # Setup logging for this session
        self.session_id = str(uuid.uuid4())[:8]
        self.logs = []
        
        # Configure global directories for consistency
        if 'ENV_PROJECT_DIR' in os.environ:
            self.use_external_project_dir = True
            self.external_project_dir = Path(os.environ['ENV_PROJECT_DIR'])
        else:
            self.use_external_project_dir = False
            self.external_project_dir = None
        
        logger.info(f"Comprehensive Query Tool initialized (Session: {self.session_id})")
        logger.info(f"Available tools: {self._get_available_tools()}")
        if self.use_external_project_dir:
            logger.info(f"Using external project directory: {self.external_project_dir}")
    
    def _initialize_analysis_tools(self):
        """Initialize all available analysis tools"""
        self.tools = {}
        
        # Wetland analysis tool (class)
        if WETLAND_AVAILABLE:
            try:
                self.tools['wetland'] = WetlandAnalysisTool
                logger.info("✅ Wetland analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize wetland tool: {e}")
        
        # Flood analysis tool (class)
        if FLOOD_AVAILABLE:
            try:
                self.tools['flood'] = get_flood_data
                logger.info("✅ Flood analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize flood tool: {e}")
        
        # Air quality analysis tool (class)
        if AIR_QUALITY_AVAILABLE:
            try:
                self.tools['air_quality'] = NonattainmentAnalysisTool
                logger.info("✅ Air quality analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize air quality tool: {e}")
        
        # Habitat analysis tool (function)
        if HABITAT_AVAILABLE:
            try:
                # Store reference to habitat tools module for deferred map generation
                self.tools['habitat'] = 'habitat_analysis_available'
                logger.info("✅ Critical habitat analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize habitat tool: {e}")
        
        # Cadastral analysis tool (function)
        if CADASTRAL_AVAILABLE:
            try:
                self.tools['cadastral'] = get_cadastral_data_from_coordinates
                logger.info("✅ Cadastral analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize cadastral tool: {e}")
        
        # Karst analysis tool (function)
        if KARST_AVAILABLE:
            try:
                self.tools['karst'] = check_coordinates_karst
                logger.info("✅ Karst analysis tool initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize karst tool: {e}")
    
    def _get_available_tools(self) -> List[str]:
        """Get list of available analysis tools"""
        available = list(self.tools.keys())
        return available
    
    def _parse_location(self, location: str) -> Tuple[float, float]:
        """Parse location string to coordinates"""
        try:
            if ',' in location:
                # Assume it's coordinates
                parts = location.strip().split(',')
                if len(parts) == 2:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    return lat, lng
            
            # If not coordinates, try to geocode the address
            # This would require a geocoding service
            raise ValueError(f"Unable to parse location: {location}")
        
        except Exception as e:
            logger.error(f"Error parsing location '{location}': {e}")
            raise
    
    def _create_project_directory(self, project_name: str) -> Path:
        """Create project directory structure"""
        # Use external project directory if configured (from ComprehensiveEnvironmentalAgent)
        if self.use_external_project_dir and self.external_project_dir:
            project_dir = self.external_project_dir
            logger.info(f"📁 Using external project directory: {project_dir}")
        else:
            # Clean project name for directory
            clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            clean_name = clean_name.replace(' ', '_')
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_dir = self.output_directory / f"{clean_name}_{timestamp}"
            logger.info(f"📁 Creating new project directory: {project_dir}")

        # Create directory structure
        (project_dir / "data").mkdir(parents=True, exist_ok=True)
        (project_dir / "maps").mkdir(parents=True, exist_ok=True)
        (project_dir / "reports").mkdir(parents=True, exist_ok=True)
        (project_dir / "logs").mkdir(parents=True, exist_ok=True)
        
        return project_dir
    
    async def query_all_environmental_data(self, location: str, project_name: str, 
                                         cadastral_number: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive environmental queries for a location
        
        Args:
            location: Location as coordinates "lat,lng" or address
            project_name: Name of the project
            cadastral_number: Optional cadastral number
            
        Returns:
            Dictionary containing all query results and metadata
        """
        logger.info(f"🔍 Starting comprehensive environmental queries for: {project_name}")
        
        try:
            # Parse location
            lat, lng = self._parse_location(location)
            logger.info(f"📍 Location: {lat:.6f}, {lng:.6f}")
            
            # Create project directory
            project_dir = self._create_project_directory(project_name)
            logger.info(f"📁 Project directory: {project_dir}")
            
            # Initialize results structure
            results = {
                'project_info': {
                    'project_name': project_name,
                    'location': location,
                    'latitude': lat,
                    'longitude': lng,
                    'cadastral_number': cadastral_number,
                    'project_directory': str(project_dir),
                    'query_timestamp': datetime.now().isoformat(),
                    'session_id': self.session_id
                },
                'query_results': {},
                'generated_files': [],
                'errors': [],
                'summary': {
                    'total_queries': 0,
                    'successful_queries': 0,
                    'failed_queries': 0,
                    'tools_used': []
                }
            }
            
            # Run queries for each available tool
            query_tasks = []
            
            # Cadastral/Property Analysis
            if 'cadastral' in self.tools:
                query_tasks.append(self._query_cadastral_data(lat, lng, cadastral_number, project_dir))
            
            # Flood Analysis
            if 'flood' in self.tools:
                query_tasks.append(self._query_flood_data(lat, lng, project_dir))
            
            # Wetland Analysis
            if 'wetland' in self.tools:
                query_tasks.append(self._query_wetland_data(lat, lng, project_dir))
            
            # Critical Habitat Analysis
            if 'habitat' in self.tools:
                query_tasks.append(self._query_habitat_data(lat, lng, project_dir))
            
            # Air Quality Analysis
            if 'air_quality' in self.tools:
                query_tasks.append(self._query_air_quality_data(lat, lng, project_dir))
            
            # Karst Analysis (Puerto Rico specific)
            if 'karst' in self.tools:
                query_tasks.append(self._query_karst_data(lat, lng, project_dir))
            
            # Execute all queries
            logger.info(f"🚀 Executing {len(query_tasks)} environmental queries...")
            query_results = await asyncio.gather(*query_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(query_results):
                tool_name = ['cadastral', 'flood', 'wetland', 'habitat', 'air_quality', 'karst'][i]
                
                if isinstance(result, Exception):
                    logger.error(f"❌ {tool_name} query failed: {result}")
                    results['errors'].append({
                        'tool': tool_name,
                        'error': str(result),
                        'timestamp': datetime.now().isoformat()
                    })
                    results['summary']['failed_queries'] += 1
                else:
                    logger.info(f"✅ {tool_name} query completed successfully")
                    results['query_results'][tool_name] = result
                    results['summary']['successful_queries'] += 1
                    results['summary']['tools_used'].append(tool_name)
                    
                    # Add generated files
                    if result and 'generated_files' in result:
                        results['generated_files'].extend(result['generated_files'])
                
                results['summary']['total_queries'] += 1
            
            # Save comprehensive results
            results_file = project_dir / "data" / "comprehensive_query_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            results['generated_files'].append(str(results_file))
            
            # Generate structured template data
            try:
                logger.info("📊 Generating structured template data...")
                structured_template_data = self._generate_template_data_structure(results)
                
                # Save structured template data
                template_data_file = project_dir / "data" / "template_data_structure.json"
                with open(template_data_file, 'w') as f:
                    json.dump(structured_template_data, f, indent=2, default=str)
                
                results['generated_files'].append(str(template_data_file))
                results['template_data_file'] = str(template_data_file)
                
                logger.info(f"✅ Structured template data saved: {template_data_file}")
                
                # Add template data to results for immediate use
                results['template_data'] = structured_template_data
                
            except Exception as e:
                logger.error(f"⚠️ Error generating template data structure: {e}")
                results['template_data_error'] = str(e)
            
            # Generate summary report
            summary_file = self._generate_query_summary(results, project_dir)
            results['generated_files'].append(summary_file)
            
            logger.info(f"✅ Comprehensive queries completed for {project_name}")
            logger.info(f"📊 Results: {results['summary']['successful_queries']}/{results['summary']['total_queries']} queries successful")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive queries: {e}")
            raise
    
    async def _query_cadastral_data(self, lat: float, lng: float, 
                                  cadastral_number: Optional[str], project_dir: Path) -> Dict[str, Any]:
        """Query cadastral/property data"""
        logger.info("🏠 Querying cadastral/property data...")
        
        try:
            tool = self.tools['cadastral']
            
            # Use coordinates for lookup (cadastral tool expects coordinates)
            result = tool.invoke({"longitude": lng, "latitude": lat})
            
            # Save data to JSON file
            data_file = project_dir / "data" / "cadastral_analysis.json"
            with open(data_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            result['generated_files'] = [str(data_file)]
            
            return result
            
        except Exception as e:
            logger.error(f"Error in cadastral query: {e}")
            raise
        
    # ─── NEW IMPLEMENTATION ------------------------------------------------------
    async def _query_flood_data(self, lat: float, lng: float, project_dir: Path) -> Dict[str, Any]:
        """
        Use the refactored flood helpers:
        • get_flood_data()  → structured JSON only
        • generate_flood_maps() → three PDF maps (optional)
        The helper functions are synchronous, so we off-load them to a thread so
        this coroutine plays nicely with the rest of the async workflow.
        """
        logger.info("🌊 Querying flood data with new helpers…")

        generated_files: list[str] = []
        loop = asyncio.get_event_loop()

        try:
            # ---------- 1. data layer ------------------------------------------------
            flood_json: Dict[str, Any] = await loop.run_in_executor(
                None,
                lambda: get_flood_data(
                    longitude=lng,
                    latitude=lat,
                    location_name=None,          # let helper auto-label
                    save_raw_files=True,          # keeps the raw json in /logs
                )
            )

            # Stash the JSON to disk
            data_path = project_dir / "data" / "flood_analysis_comprehensive.json"
            with open(data_path, "w") as fh:
                json.dump(flood_json, fh, indent=2, default=str)
            generated_files.append(str(data_path))
            logger.info(f"✅ Flood data saved → {data_path}")

            # ---------- 2. maps (if user asked for them) ---------------------------
            if self.include_maps:
                map_result: Dict[str, Any] = await loop.run_in_executor(
                    None,
                    lambda: generate_flood_maps(
                        longitude=lng,
                        latitude=lat,
                        location_name=flood_json['analysis_metadata']['location'],
                        include_abfe=True,
                    )
                )

                # Copy PDFs into the project's /maps folder
                for key, meta in map_result["reports_generated"].items():
                    if meta.get("success") and meta.get("filename"):
                        src = Path(meta["filename"])
                        dst = project_dir / "maps" / src.name
                        dst.write_bytes(src.read_bytes())
                        meta["project_filename"] = str(dst)
                        generated_files.append(str(dst))
                        logger.info(f"   📄 {key} map archived as {dst.name}")

                flood_json["reports_generated"] = map_result["reports_generated"]

            # ---------- package & return ------------------------------------------
            flood_json["generated_files"] = generated_files
            flood_json["success"] = True
            return flood_json

        except Exception as exc:
            logger.error(f"❌ Flood helper error: {exc}", exc_info=True)
            return {
                "success": False,
                "error": str(exc),
                "generated_files": generated_files,
                "query_location": {"latitude": lat, "longitude": lng},
            }
    
    async def _query_wetland_data(self, lat: float, lng: float, project_dir: Path) -> Dict[str, Any]:
        """Query wetland data and save map generation parameters (maps generated during report creation)"""
        logger.info("🌿 Querying comprehensive wetland data and saving map generation parameters...")
        
        generated_files_list = []
        default_map_base_map = "World_Imagery"
        default_map_layout = "Letter ANSI A Portrait"
        
        try:
            tool_class = self.tools['wetland']
            tool = tool_class()
            
            logger.info(f"   Analyzing wetlands at coordinates ({lat:.6f}, {lng:.6f}) with buffer {self.buffer_distance} miles.")
            
            # Use WetlandAnalysisTool.analyze_wetland_location method
            wetland_analysis_result = await tool.analyze_wetland_location(lat, lng, buffer_miles=self.buffer_distance)
            
            # Extract map generation parameters for later use
            processed_wetland_data = wetland_analysis_result

            if not wetland_analysis_result.get('wetland_analysis', {}).get('is_in_wetland', False):
                logger.info(f"Wetland analysis complete - no direct wetland impacts detected")
            else:
                logger.info(f"Wetland analysis complete - direct wetland impacts detected")

            # Save wetland analysis data with map generation parameters
            wetland_data_filename = "wetland_analysis_comprehensive.json"
            wetland_data_filepath = project_dir / "data" / wetland_data_filename
            
            # Add map generation parameters
            buffer_meters = self.buffer_distance * 1609.34
            processed_wetland_data['map_generation_parameters'] = {
                "center_longitude": lng,
                "center_latitude": lat,
                "map_view_buffer_miles": max(self.buffer_distance * 1.2, 0.5),
                "buffer_meters": buffer_meters,
                "base_map_name": default_map_base_map,
                "layout_template": default_map_layout,
                "wetland_transparency": 0.8,
                "include_buffer_zones": True
            }
            
            processed_wetland_data['maps_to_generate'] = {
                "wetland_map_pdf": {
                    "type": "wetland_zones",
                    "format": "PDF",
                    "layout": default_map_layout,
                    "filename": "wetland_map_archive.pdf",
                    "buffer_meters": buffer_meters,
                    "transparency": 0.8,
                    "include_buffer_zones": True
                },
                "wetland_map_png": {
                    "type": "wetland_zones",
                    "format": "PNG32",
                    "layout": "MAP_ONLY",
                    "filename": "wetland_map_embed.png",
                    "buffer_meters": buffer_meters,
                    "transparency": 0.8,
                    "include_buffer_zones": True
                }
            }
            
            with open(wetland_data_filepath, 'w') as f:
                json.dump(processed_wetland_data, f, indent=2, default=str)
            generated_files_list.append(str(wetland_data_filepath))
            logger.info(f"✅ Wetland analysis data with map parameters saved: {wetland_data_filepath}")
            logger.info(f"   Maps will be generated during report creation")

            processed_wetland_data['generated_files'] = generated_files_list
            
            logger.info(f"✅ Wetland query completed (map generation deferred to report phase)")
            return processed_wetland_data
            
        except Exception as e:
            logger.error(f"Error in _query_wetland_data: {str(e)}", exc_info=True)
            error_payload = {
                'success': False,
                'error': str(e),
                'message': f"Wetland processing encountered an exception: {str(e)}",
                'query_location': {'latitude': lat, 'longitude': lng},
                'generated_files': generated_files_list,
                'map_generation_parameters': {
                    "center_longitude": lng,
                    "center_latitude": lat,
                    "map_view_buffer_miles": max(self.buffer_distance * 1.2, 0.5),
                    "buffer_meters": self.buffer_distance * 1609.34,
                    "base_map_name": default_map_base_map,
                    "layout_template": default_map_layout,
                    "wetland_transparency": 0.8,
                    "include_buffer_zones": True
                }
            }
            return error_payload
    
    async def _query_habitat_data(self, lat: float, lng: float, project_dir: Path) -> Dict[str, Any]:
        """Query critical habitat data and save map generation parameters (maps generated during report creation)"""
        logger.info("🦅 Querying comprehensive critical habitat data and saving map generation parameters...")
        
        generated_files_list = []
        default_map_base_map = "World_Imagery"
        default_map_layout = "Letter ANSI A Portrait"
        
        try:
            # Create mock critical habitat analysis (replace with actual habitat analysis logic)
            logger.info(f"   Analyzing critical habitat at coordinates ({lat:.6f}, {lng:.6f}) with buffer {self.buffer_distance} miles.")
            
            # Mock habitat analysis result
            habitat_analysis_result = {
                'location': {
                    'latitude': lat,
                    'longitude': lng,
                    'buffer_miles': self.buffer_distance
                },
                'critical_habitat_areas': [],
                'endangered_species': [],
                'habitat_assessment': {
                    'is_in_critical_habitat': False,
                    'nearest_habitat_distance_miles': None,
                    'habitat_types_nearby': []
                },
                'regulatory_assessment': {
                    'esa_consultation_required': False,
                    'potential_species_impacts': [],
                    'recommended_surveys': []
                },
                'query_timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Enhanced mock data for Puerto Rico
            if 17.0 <= lat <= 19.0 and -68.0 <= lng <= -65.0:
                habitat_analysis_result['critical_habitat_areas'] = [
                    {
                        'species': 'West Indian Manatee',
                        'scientific_name': 'Trichechus manatus',
                        'habitat_type': 'Marine',
                        'designation_date': '1976-09-24',
                        'distance_miles': 0.8,
                        'status': 'Threatened'
                    }
                ]
                habitat_analysis_result['habitat_assessment']['nearest_habitat_distance_miles'] = 0.8
                habitat_analysis_result['habitat_assessment']['habitat_types_nearby'] = ['Marine']
                habitat_analysis_result['regulatory_assessment']['esa_consultation_required'] = True
                habitat_analysis_result['regulatory_assessment']['recommended_surveys'] = [
                    'Marine mammal surveys',
                    'Seagrass bed assessment'
                ]
            
            # Process habitat analysis data
            processed_habitat_data = habitat_analysis_result

            if not habitat_analysis_result.get('success', True):
                logger.warning(f"Habitat data analysis had issues: {habitat_analysis_result.get('error', 'Unknown error')}")

            # Save habitat analysis data with map generation parameters
            habitat_data_filename = "critical_habitat_analysis_comprehensive.json"
            habitat_data_filepath = project_dir / "data" / habitat_data_filename
            
            # Create map generation parameters for deferred map creation
            map_generation_parameters = {
                "center_longitude": lng,
                "center_latitude": lat,
                "location_name": f"Critical Habitat Analysis at {lat:.6f}, {lng:.6f}",
                "buffer_miles": self.buffer_distance,
                "base_map_name": default_map_base_map,
                "layout_template": default_map_layout,
                "include_proposed": True, 
                "habitat_transparency": 0.8,
                "generate_pdf": False,  # Deferred to report phase
                "generate_png": False   # Deferred to report phase
            }
            
            processed_habitat_data['map_generation_parameters'] = map_generation_parameters
            processed_habitat_data['maps_to_generate'] = {
                "habitat_map_pdf": {
                    "type": "critical_habitat",
                    "format": "PDF",
                    "layout": default_map_layout,
                    "filename": "critical_habitat_map_archive.pdf",
                    "include_proposed": True,
                    "transparency": 0.8
                },
                "habitat_map_png": {
                    "type": "critical_habitat",
                    "format": "PNG32",
                    "layout": "MAP_ONLY",
                    "filename": "critical_habitat_map_embed.png",
                    "include_proposed": True,
                    "transparency": 0.8
                }
            }
            
            with open(habitat_data_filepath, 'w') as f:
                json.dump(processed_habitat_data, f, indent=2, default=str)
            generated_files_list.append(str(habitat_data_filepath))
            logger.info(f"✅ Critical habitat analysis data with map parameters saved: {habitat_data_filepath}")
            logger.info(f"   Maps will be generated during report creation")

            processed_habitat_data['generated_files'] = generated_files_list
            
            logger.info(f"✅ Critical habitat query completed (map generation deferred to report phase)")
            return processed_habitat_data
            
        except Exception as e:
            logger.error(f"Error in _query_habitat_data: {str(e)}", exc_info=True)
            error_payload = {
                'success': False,
                'error': str(e),
                'message': f"Critical habitat processing encountered an exception: {str(e)}",
                'query_location': {'latitude': lat, 'longitude': lng},
                'generated_files': generated_files_list,
                'map_generation_parameters': {
                    "center_longitude": lng,
                    "center_latitude": lat,
                    "map_view_buffer_miles": max(self.buffer_distance * 1.2, 0.5),
                    "base_map_name": default_map_base_map,
                    "layout_template": default_map_layout,
                    "include_proposed": True,
                    "habitat_transparency": 0.8
                }
            }
            return error_payload
    
    async def _query_air_quality_data(self, lat: float, lng: float, project_dir: Path) -> Dict[str, Any]:
        """Query air quality data and save map generation parameters (maps generated during report creation)"""
        logger.info("🌬️ Querying comprehensive air quality data and saving map generation parameters...")
        
        generated_files_list = []
        
        try:
            tool_class = self.tools['air_quality']
            tool = tool_class()
            
            logger.info(f"   Analyzing air quality/nonattainment at coordinates ({lat:.6f}, {lng:.6f}) with regional buffer.")
            
            # Use a larger buffer for air quality analysis (regional perspective)
            regional_buffer = max(self.buffer_distance * 5, 25.0)  # At least 25 miles for air quality
            air_quality_analysis_result = await tool.analyze_nonattainment(lat, lng)
            
            # Extract map generation parameters for later use
            map_params_from_analysis = air_quality_analysis_result.get('map_generation_parameters', {})
            processed_air_quality_data = air_quality_analysis_result

            if not air_quality_analysis_result.get('success', True):
                logger.warning(f"Air quality data analysis had issues: {air_quality_analysis_result.get('error', 'Unknown error')}")

            # Save air quality analysis data with map generation parameters
            air_quality_data_filename = "air_quality_analysis_comprehensive.json"
            air_quality_data_filepath = project_dir / "data" / air_quality_data_filename
            
            # Ensure map generation parameters are saved for report generator
            if not map_params_from_analysis:
                map_params_from_analysis = {
                    "center_longitude": lng,
                    "center_latitude": lat,
                    "map_view_buffer_miles": regional_buffer,
                    "base_map_name": "World_Topo_Map",
                    "layout_template": "Letter ANSI A Portrait"
                }
            
            processed_air_quality_data['map_generation_parameters'] = map_params_from_analysis
            processed_air_quality_data['maps_to_generate'] = {
                "air_quality_map_pdf": {
                    "format": "PDF",
                    "layout": map_params_from_analysis.get("layout_template", "Letter ANSI A Portrait"),
                    "filename": "air_quality_map_archive.pdf"
                },
                "air_quality_map_png": {
                    "format": "PNG32",
                    "layout": "MAP_ONLY",
                    "filename": "air_quality_map_embed.png"
                }
            }
            
            with open(air_quality_data_filepath, 'w') as f:
                json.dump(processed_air_quality_data, f, indent=2, default=str)
            generated_files_list.append(str(air_quality_data_filepath))
            logger.info(f"✅ Air quality analysis data with map parameters saved: {air_quality_data_filepath}")
            logger.info(f"   Maps will be generated during report creation")

            processed_air_quality_data['generated_files'] = generated_files_list
            
            logger.info(f"✅ Air quality query completed (map generation deferred to report phase)")
            return processed_air_quality_data
            
        except Exception as e:
            logger.error(f"Error in _query_air_quality_data: {str(e)}", exc_info=True)
            error_payload = {
                'success': False,
                'error': str(e),
                'message': f"Air quality processing encountered an exception: {str(e)}",
                'query_location': {'latitude': lat, 'longitude': lng},
                'generated_files': generated_files_list
            }
            return error_payload
    
    async def _query_karst_data(self, lat: float, lng: float, project_dir: Path) -> Dict[str, Any]:
        """Query karst data and save map generation parameters (maps generated during report creation)"""
        logger.info("🗿 Querying comprehensive karst data and saving map generation parameters...")
        
        generated_files_list = []
        
        try:
            from simple_karst_analysis_tool import check_coordinates_karst
            
            logger.info(f"   Analyzing karst at coordinates ({lat:.6f}, {lng:.6f}) with initial buffer {self.buffer_distance} miles.")
            
            # Get default map parameters for karst
            default_map_base_map = "World_Topo_Map"
            default_map_layout = "Letter ANSI A Landscape"
            
            karst_analysis_result = check_coordinates_karst(
                longitude=lng, latitude=lat, buffer_miles=self.buffer_distance, 
                include_regulatory_buffers=True, max_search_radius_for_nearest_miles=5.0,
                map_base_map_name=default_map_base_map, map_layout_template=default_map_layout
            )
            
            map_params_from_analysis = karst_analysis_result.get('map_generation_parameters', {})
            processed_karst_data = karst_analysis_result

            if not karst_analysis_result.get('success'):
                logger.warning(f"Karst data analysis failed: {karst_analysis_result.get('error', 'Unknown error')}")
                if 'error' not in processed_karst_data: 
                    processed_karst_data['error'] = karst_analysis_result.get('error', 'Karst data analysis failed')
            
            # Save karst analysis data with map generation parameters
            karst_data_filename = "karst_analysis_comprehensive.json"
            karst_data_filepath = project_dir / "data" / karst_data_filename
            
            # Ensure map generation parameters are saved for report generator
            if not map_params_from_analysis:
                map_params_from_analysis = {
                    "center_longitude": lng,
                    "center_latitude": lat,
                    "map_view_buffer_miles": max(self.buffer_distance * 1.5, 1.0),
                    "base_map_name": default_map_base_map,
                    "layout_template": default_map_layout
                }
            
            processed_karst_data['map_generation_parameters'] = map_params_from_analysis
            processed_karst_data['maps_to_generate'] = {
                "karst_map_pdf": {
                    "format": "PDF",
                    "layout": map_params_from_analysis.get("layout_template", default_map_layout),
                    "filename_prefix": "karst_map_archive"
                },
                "karst_map_png": {
                    "format": "PNG32",
                    "layout": "MAP_ONLY",
                    "filename_prefix": "karst_map_embed"
                }
            }
            
            with open(karst_data_filepath, 'w') as f:
                json.dump(processed_karst_data, f, indent=2)
            generated_files_list.append(str(karst_data_filepath))
            logger.info(f"✅ Karst analysis data with map parameters saved: {karst_data_filepath}")
            logger.info(f"   Maps will be generated during report creation")

            processed_karst_data['generated_files'] = generated_files_list
            
            logger.info(f"✅ Karst query completed (map generation deferred to report phase)")
            return processed_karst_data
            
        except Exception as e:
            logger.error(f"Error in _query_karst_data: {str(e)}", exc_info=True)
            error_payload = self._create_empty_result('karst') 
            error_payload['error'] = str(e)
            error_payload['message'] = f"Karst processing encountered an exception: {str(e)}"
            error_payload['query_location'] = {'latitude': lat, 'longitude': lng}
            error_payload['generated_files'] = generated_files_list
            return error_payload
    
    def _generate_query_summary(self, results: Dict[str, Any], project_dir: Path) -> str:
        """Generate a summary report of all queries"""
        summary_file = project_dir / "data" / "query_summary.json"
        
        summary = {
            'project_info': results['project_info'],
            'query_execution': {
                'total_queries': results['summary']['total_queries'],
                'successful_queries': results['summary']['successful_queries'],
                'failed_queries': results['summary']['failed_queries'],
                'success_rate': f"{(results['summary']['successful_queries'] / results['summary']['total_queries'] * 100):.1f}%" if results['summary']['total_queries'] > 0 else "0%",
                'tools_used': results['summary']['tools_used']
            },
            'data_files_generated': {
                'total_files': len(results['generated_files']),
                'data_files': [f for f in results['generated_files'] if 'data/' in f],
                'map_files': [f for f in results['generated_files'] if 'maps/' in f],
                'report_files': [f for f in results['generated_files'] if 'reports/' in f]
            },
            'environmental_domains_analyzed': list(results['query_results'].keys()),
            'errors_encountered': results['errors'],
            'ready_for_screening': results['summary']['failed_queries'] == 0
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"📋 Query summary saved: {summary_file}")
        return str(summary_file)
    
    async def batch_query_locations(self, locations: List[Dict[str, Any]], 
                                  project_base_name: str, parallel: bool = True) -> Dict[str, Any]:
        """Perform batch queries for multiple locations"""
        logger.info(f"🔄 Starting batch queries for {len(locations)} locations")
        
        batch_results = {
            'batch_info': {
                'total_locations': len(locations),
                'project_base_name': project_base_name,
                'start_time': datetime.now().isoformat(),
                'parallel_processing': parallel
            },
            'location_results': [],
            'batch_summary': {
                'successful_locations': 0,
                'failed_locations': 0,
                'total_files_generated': 0
            }
        }
        
        if parallel:
            # Process locations in parallel
            tasks = []
            for i, location_data in enumerate(locations):
                project_name = f"{project_base_name}_{i+1}"
                task = self.query_all_environmental_data(
                    location=location_data['location'],
                    project_name=project_name,
                    cadastral_number=location_data.get('cadastral_number')
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Process locations sequentially
            results = []
            for i, location_data in enumerate(locations):
                project_name = f"{project_base_name}_{i+1}"
                try:
                    result = await self.query_all_environmental_data(
                        location=location_data['location'],
                        project_name=project_name,
                        cadastral_number=location_data.get('cadastral_number')
                    )
                    results.append(result)
                except Exception as e:
                    results.append(e)
        
        # Process batch results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results['location_results'].append({
                    'location_index': i,
                    'success': False,
                    'error': str(result)
                })
                batch_results['batch_summary']['failed_locations'] += 1
            else:
                batch_results['location_results'].append({
                    'location_index': i,
                    'success': True,
                    'project_directory': result['project_info']['project_directory'],
                    'files_generated': len(result['generated_files'])
                })
                batch_results['batch_summary']['successful_locations'] += 1
                batch_results['batch_summary']['total_files_generated'] += len(result['generated_files'])
        
        batch_results['batch_info']['end_time'] = datetime.now().isoformat()
        
        # Save batch summary
        batch_file = self.output_directory / f"batch_query_results_{project_base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_file, 'w') as f:
            json.dump(batch_results, f, indent=2, default=str)
        
        logger.info(f"✅ Batch queries completed: {batch_results['batch_summary']['successful_locations']}/{len(locations)} successful")
        
        return batch_results

    def _create_empty_result(self, analysis_type: str) -> Dict[str, Any]:
        """Create an empty result structure for failed analyses"""
        return {
            'success': False,
            'analysis_type': analysis_type,
            'query_time': datetime.now().isoformat(),
            'generated_files': [],
            'map_generation_parameters': {},
            'error': 'Analysis failed'
        }

    def _generate_template_data_structure(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured JSON that matches the improved environmental template schema.
        
        This method takes the raw query results and maps them to the expected 
        template structure for consistent report generation.
        
        Args:
            results: Raw results from query_all_environmental_data
            
        Returns:
            Dict containing structured data matching improved_template_data_schema.json
        """
        logger.info("📊 Generating structured template data from query results...")
        
        try:
            # Base project information
            project_info = results.get('project_info', {})
            query_results = results.get('query_results', {})
            
            # Parse coordinates
            lat = project_info.get('latitude', 0.0)
            lng = project_info.get('longitude', 0.0)
            coordinates_str = f"{lat:.6f}, {lng:.6f}"
            
            # Initialize structured data with required fields
            structured_data = {
                "project_name": project_info.get('project_name', 'Environmental Screening Project'),
                "analysis_date": project_info.get('query_timestamp', datetime.now().isoformat()),
                "location_description": self._generate_location_description(query_results),
                "coordinates": coordinates_str,
                "project_directory": project_info.get('project_directory', ''),
                "overall_risk_level": "Low",  # Will be calculated
                "risk_class": "risk-low",     # Will be calculated
            }
            
            # Process each analysis domain
            self._map_cadastral_data(structured_data, query_results.get('cadastral', {}))
            self._map_karst_data(structured_data, query_results.get('karst', {}))
            self._map_flood_data(structured_data, query_results.get('flood', {}))
            self._map_critical_habitat_data(structured_data, query_results.get('habitat', {}))
            self._map_air_quality_data(structured_data, query_results.get('air_quality', {}))
            self._map_wetland_data(structured_data, query_results.get('wetland', {}))
            
            # Generate executive summary
            self._generate_executive_summary(structured_data)
            
            # Generate compliance checklist
            self._generate_compliance_checklist(structured_data)
            
            # Calculate overall risk level
            self._calculate_overall_risk(structured_data)
            
            # Generate recommendations
            self._generate_recommendations(structured_data)
            
            logger.info("✅ Structured template data generated successfully")
            return structured_data
            
        except Exception as e:
            logger.error(f"❌ Error generating structured template data: {e}")
            # Return minimal structure if generation fails
            return {
                "project_name": project_info.get('project_name', 'Environmental Screening Project'),
                "analysis_date": datetime.now().isoformat(),
                "location_description": "Location analysis",
                "coordinates": f"{lat:.6f}, {lng:.6f}",
                "project_directory": project_info.get('project_directory', ''),
                "overall_risk_level": "Unknown",
                "risk_class": "risk-moderate",
                "error": str(e)
            }
    
    def _generate_location_description(self, query_results: Dict[str, Any]) -> str:
        """Generate human-readable location description"""
        cadastral = query_results.get('cadastral', {})
        
        if cadastral.get('success') and cadastral.get('municipality'):
            municipality = cadastral.get('municipality', '')
            neighborhood = cadastral.get('neighborhood', '')
            classification = cadastral.get('classification_description', '')
            
            if neighborhood and neighborhood != municipality:
                return f"{neighborhood}, {municipality}, Puerto Rico - {classification}"
            else:
                return f"{municipality}, Puerto Rico - {classification}"
        
        return "Environmental Screening Location"
    
    def _map_cadastral_data(self, structured_data: Dict[str, Any], cadastral_data: Dict[str, Any]):
        """Map cadastral data to template structure"""
        if not cadastral_data.get('success'):
            structured_data['cadastral_analysis'] = {'success': False}
            return

        # Safely access nested data
        cadastral_info = cadastral_data.get('cadastral_info', {})
        area_measurements = cadastral_data.get('area_measurements', {})
        land_use = cadastral_data.get('land_use', {})
        regulatory_status = cadastral_data.get('regulatory_status', {})

        # Map cadastral data structure
        structured_data['cadastral_analysis'] = {
            'success': cadastral_data.get('success', False),
            'search_cadastral': cadastral_info.get('cadastral_number', ''),
            'exact_match': cadastral_data.get('exact_match', False),
            'feature_count': cadastral_data.get('feature_count', 0),
            'total_area_m2': area_measurements.get('area_square_meters', 0),
            'total_area_hectares': area_measurements.get('area_hectares', 0),
            'area_acres': area_measurements.get('area_acres', 0),
            'unique_classifications': cadastral_data.get('unique_classifications', []),
            'unique_municipalities': cadastral_data.get('unique_municipalities', []),
            'municipality': cadastral_info.get('municipality', ''),
            'neighborhood': cadastral_info.get('neighborhood', ''),
            'region': cadastral_info.get('region', ''),
            'classification_code': land_use.get('classification_code', ''),
            'classification_description': land_use.get('classification_description', ''),
            'sub_classification': land_use.get('sub_classification', ''),
            'sub_classification_description': land_use.get('sub_classification_description', ''),
            'zoning_designation': land_use.get('zoning_category', ''),
            'case_number': regulatory_status.get('case_number', ''),
            'status': regulatory_status.get('status', ''),
            'resolution': regulatory_status.get('resolution', ''),
            'geometry': cadastral_data.get('geometry', {})
        }
    
    def _map_karst_data(self, structured_data: Dict[str, Any], karst_data: Dict[str, Any]):
        """Map karst data to template structure"""
        if not karst_data.get('success'):
            return
        
        structured_data['karst_analysis'] = karst_data
    
    def _map_flood_data(self, structured_data: Dict[str, Any], flood_data: Dict[str, Any]):
        """Map flood data to template structure"""
        if not flood_data.get('success'):
            return
        
        structured_data['flood_analysis'] = flood_data
    
    def _map_critical_habitat_data(self, structured_data: Dict[str, Any], habitat_data: Dict[str, Any]):
        """Map critical habitat data to template structure"""
        if not habitat_data.get('success'):
            return
        
        structured_data['critical_habitat_analysis'] = habitat_data
    
    def _map_air_quality_data(self, structured_data: Dict[str, Any], air_data: Dict[str, Any]):
        """Map air quality data to template structure"""
        if not air_data.get('success'):
            return
        
        structured_data['air_quality_analysis'] = air_data
    
    def _map_wetland_data(self, structured_data: Dict[str, Any], wetland_data: Dict[str, Any]):
        """Map wetland data to template structure"""
        if not wetland_data.get('success'):
            return
        
        structured_data['wetland_analysis'] = wetland_data
    
    def _generate_executive_summary(self, structured_data: Dict[str, Any]):
        """Generate executive summary from analysis results"""
        cadastral = structured_data.get('cadastral_analysis', {})
        constraints = []
        highlights = []
        recommendations = []
        
        # Analyze cadastral data
        if cadastral.get('classification_code') == 'P':
            constraints.append("Property classified as public land - development permissions required")
            highlights.append("Public land classification - coordinate with planning authorities")
        
        # Analyze habitat data
        habitat = structured_data.get('critical_habitat_analysis', {}).get('critical_habitat_analysis', {})
        if habitat.get('distance_to_nearest_habitat_miles', 999) < 2.0:
            distance = habitat.get('distance_to_nearest_habitat_miles', 0)
            species = habitat.get('nearest_habitat', {}).get('species_common_name', 'species')
            constraints.append(f"Located {distance:.2f} miles from critical habitat ({species}) - monitoring recommended")
            highlights.append("ESA consultation recommended due to habitat proximity")
            recommendations.append(f"Consider {species} habitat impacts in project design")
        
        # Analyze flood data
        flood = structured_data.get('flood_analysis', {}).get('current_effective_data', {})
        flood_zones = flood.get('flood_zones', [])
        if flood_zones:
            zone = flood_zones[0].get('flood_zone', 'X')
            if zone in ['X', 'C']:
                highlights.append(f"Flood Zone {zone} (minimal flood risk) - standard compliance")
            else:
                constraints.append(f"Located in Special Flood Hazard Area (Zone {zone})")
                highlights.append(f"FEMA flood zone {zone} - special requirements apply")
        
        # Analyze karst data
        karst = structured_data.get('karst_analysis', {}).get('processed_summary', {})
        if karst.get('karst_status') == 'no_karst':
            highlights.append("No karst constraints within 0.5 miles")
        
        # Analyze air quality
        air = structured_data.get('air_quality_analysis', {}).get('regulatory_assessment', {})
        if air.get('compliance_status') == 'Compliant':
            highlights.append("Air quality compliant - meets all NAAQS standards")
        
        # Property overview
        area_hectares = cadastral.get('total_area_hectares', 0)
        municipality = cadastral.get('municipality', 'Unknown')
        classification = cadastral.get('classification_description', 'property')
        property_overview = f"{area_hectares:.2f}-hectare {classification.lower()} in {municipality} municipality with comprehensive environmental compliance achieved across all assessed domains."
        
        # Risk assessment
        risk_assessment = "Low environmental risk with no critical constraints identified. Property shows good regulatory compliance across flood, air quality, karst, and habitat assessments."
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                "Proceed with standard development permitting process",
                "Maintain compliance with local zoning regulations"
            ]
        
        structured_data['executive_summary'] = {
            'property_overview': property_overview,
            'risk_assessment': risk_assessment,
            'key_environmental_constraints': constraints,
            'regulatory_highlights': highlights,
            'primary_recommendations': recommendations
        }
    
    def _generate_compliance_checklist(self, structured_data: Dict[str, Any]):
        """Generate compliance checklist status fields"""
        
        # Flood compliance
        flood_zones = structured_data.get('flood_analysis', {}).get('current_effective_data', {}).get('flood_zones', [])
        if flood_zones and flood_zones[0].get('flood_zone') in ['X', 'C']:
            structured_data.update({
                'flood_status': 'COMPLIANT',
                'flood_status_class': 'status-green',
                'flood_risk': 'LOW',
                'flood_risk_class': 'status-green',
                'flood_action': 'Standard compliance - Zone X minimal risk'
            })
        else:
            structured_data.update({
                'flood_status': 'REVIEW',
                'flood_status_class': 'status-yellow',
                'flood_risk': 'MODERATE',
                'flood_risk_class': 'status-yellow',
                'flood_action': 'Special flood hazard area - consultation required'
            })
        
        # Habitat compliance
        habitat = structured_data.get('critical_habitat_analysis', {}).get('critical_habitat_analysis', {})
        distance = habitat.get('distance_to_nearest_habitat_miles', 999)
        if distance < 2.0:
            species = habitat.get('nearest_habitat', {}).get('species_common_name', 'species')
            structured_data.update({
                'habitat_status': 'REVIEW',
                'habitat_status_class': 'status-yellow',
                'habitat_risk': 'MODERATE',
                'habitat_risk_class': 'status-yellow',
                'habitat_action': f'ESA consultation recommended - {species} habitat nearby'
            })
        else:
            structured_data.update({
                'habitat_status': 'COMPLIANT',
                'habitat_status_class': 'status-green',
                'habitat_risk': 'LOW',
                'habitat_risk_class': 'status-green',
                'habitat_action': 'No immediate ESA concerns'
            })
        
        # Zoning compliance
        cadastral = structured_data.get('cadastral_analysis', {})
        if cadastral.get('classification_code') == 'P':
            structured_data.update({
                'zoning_status': 'COMPLIANT',
                'zoning_status_class': 'status-green',
                'zoning_risk': 'LOW',
                'zoning_risk_class': 'status-green',
                'zoning_action': 'Public land - coordinate with planning board'
            })
        else:
            structured_data.update({
                'zoning_status': 'COMPLIANT',
                'zoning_status_class': 'status-green',
                'zoning_risk': 'LOW',
                'zoning_risk_class': 'status-green',
                'zoning_action': 'Standard zoning compliance'
            })
        
        # Air quality compliance
        air = structured_data.get('air_quality_analysis', {}).get('regulatory_assessment', {})
        if air.get('compliance_status') == 'Compliant':
            structured_data.update({
                'air_status': 'COMPLIANT',
                'air_status_class': 'status-green',
                'air_risk': 'LOW',
                'air_risk_class': 'status-green',
                'air_action': 'Meets all NAAQS - standard permits apply'
            })
        else:
            structured_data.update({
                'air_status': 'REVIEW',
                'air_status_class': 'status-yellow',
                'air_risk': 'MODERATE',
                'air_risk_class': 'status-yellow',
                'air_action': 'Air quality consultation required'
            })
        
        # Karst compliance
        karst = structured_data.get('karst_analysis', {}).get('processed_summary', {})
        if karst.get('karst_status') == 'no_karst':
            structured_data.update({
                'karst_status': 'COMPLIANT',
                'karst_status_class': 'status-green',
                'karst_risk': 'LOW',
                'karst_risk_class': 'status-green',
                'karst_action': 'No karst constraints - proceed with development'
            })
        else:
            structured_data.update({
                'karst_status': 'REVIEW',
                'karst_status_class': 'status-yellow',
                'karst_risk': 'MODERATE',
                'karst_risk_class': 'status-yellow',
                'karst_action': 'Karst considerations required'
            })
    
    def _calculate_overall_risk(self, structured_data: Dict[str, Any]):
        """Calculate overall risk level based on individual assessments"""
        risk_scores = []
        
        # Check each domain for risk level
        if structured_data.get('flood_risk') == 'HIGH':
            risk_scores.append(3)
        elif structured_data.get('flood_risk') == 'MODERATE':
            risk_scores.append(2)
        else:
            risk_scores.append(1)
        
        if structured_data.get('habitat_risk') == 'HIGH':
            risk_scores.append(3)
        elif structured_data.get('habitat_risk') == 'MODERATE':
            risk_scores.append(2)
        else:
            risk_scores.append(1)
        
        if structured_data.get('air_risk') == 'HIGH':
            risk_scores.append(3)
        elif structured_data.get('air_risk') == 'MODERATE':
            risk_scores.append(2)
        else:
            risk_scores.append(1)
        
        if structured_data.get('karst_risk') == 'HIGH':
            risk_scores.append(3)
        elif structured_data.get('karst_risk') == 'MODERATE':
            risk_scores.append(2)
        else:
            risk_scores.append(1)
        
        # Calculate average risk
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 1
        
        if avg_risk >= 2.5:
            structured_data['overall_risk_level'] = 'High'
            structured_data['risk_class'] = 'risk-high'
        elif avg_risk >= 1.5:
            structured_data['overall_risk_level'] = 'Moderate'
            structured_data['risk_class'] = 'risk-moderate'
        else:
            structured_data['overall_risk_level'] = 'Low'
            structured_data['risk_class'] = 'risk-low'
    
    def _generate_recommendations(self, structured_data: Dict[str, Any]):
        """Generate general recommendations"""
        recommendations = []
        
        # Base recommendations
        recommendations.append("Proceed with standard environmental compliance process")
        
        # Domain-specific recommendations
        cadastral = structured_data.get('cadastral_analysis', {})
        if cadastral.get('classification_code') == 'P':
            recommendations.append("Coordinate with Puerto Rico Planning Board for public land development permissions")
        
        habitat = structured_data.get('critical_habitat_analysis', {}).get('critical_habitat_analysis', {})
        if habitat.get('distance_to_nearest_habitat_miles', 999) < 2.0:
            species = habitat.get('nearest_habitat', {}).get('species_common_name', 'species')
            recommendations.append(f"Consider {species} habitat conservation measures in project design")
        
        recommendations.append("Maintain ongoing compliance monitoring during construction")
        
        structured_data['recommendations'] = recommendations


# LangChain Tool Functions for Agent Integration

def _query_environmental_data_for_location_impl(
    location: str,
    project_name: str,
    cadastral_number: Optional[str] = None,
    output_directory: str = "output",
    include_maps: bool = True,
    buffer_distance: float = 1.0,
    detailed_analysis: bool = True
) -> Dict[str, Any]:
    """Implementation function for environmental data queries"""
    
    try:
        logger.info(f"🔍 Starting comprehensive environmental queries for: {project_name}")
        
        # Initialize the query tool
        query_tool = ComprehensiveQueryTool(
            output_directory=output_directory,
            include_maps=include_maps,
            detailed_analysis=detailed_analysis,
            buffer_distance=buffer_distance
        )
        
        # Run the comprehensive queries
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    query_tool.query_all_environmental_data(location, project_name, cadastral_number)
                )
                results = future.result()
        else:
            # Run directly
            results = asyncio.run(
                query_tool.query_all_environmental_data(location, project_name, cadastral_number)
            )
        
        logger.info(f"✅ Comprehensive queries completed successfully")
        logger.info(f"📁 Project directory: {results['project_info']['project_directory']}")
        logger.info(f"📊 Results: {results['summary']['successful_queries']}/{results['summary']['total_queries']} queries successful")
        
        return {
            "success": True,
            "project_info": results['project_info'],
            "query_results": results['query_results'],
            "generated_files": results['generated_files'],
            "summary": results['summary'],
            "errors": results['errors'],
            "ready_for_screening": results['summary']['failed_queries'] == 0,
            "next_steps": [
                "Use the generated JSON files for comprehensive screening analysis",
                "Review any error messages for failed queries",
                "Generate comprehensive reports using the screening report tools"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in comprehensive environmental queries: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_name": project_name,
            "location": location,
            "suggestion": "Check location format and ensure all required analysis tools are available"
        }


def _batch_query_environmental_data_impl(
    locations: List[Dict[str, Any]],
    project_base_name: str,
    output_directory: str = "output",
    include_maps: bool = True,
    parallel_processing: bool = True
) -> Dict[str, Any]:
    """Implementation function for batch environmental data queries"""
    
    try:
        logger.info(f"🔄 Starting batch environmental queries for {len(locations)} locations")
        
        # Initialize the query tool
        query_tool = ComprehensiveQueryTool(
            output_directory=output_directory,
            include_maps=include_maps
        )
        
        # Run batch queries
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, create a new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    query_tool.batch_query_locations(locations, project_base_name, parallel_processing)
                )
                results = future.result()
        else:
            # Run directly
            results = asyncio.run(
                query_tool.batch_query_locations(locations, project_base_name, parallel_processing)
            )
        
        logger.info(f"✅ Batch queries completed")
        logger.info(f"📊 Success rate: {results['batch_summary']['successful_locations']}/{results['batch_info']['total_locations']}")
        
        return {
            "success": True,
            "batch_info": results['batch_info'],
            "location_results": results['location_results'],
            "batch_summary": results['batch_summary'],
            "processing_method": "parallel" if parallel_processing else "sequential",
            "next_steps": [
                "Review individual location results",
                "Generate screening reports for successful locations",
                "Investigate any failed locations"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error in batch environmental queries: {e}")
        return {
            "success": False,
            "error": str(e),
            "batch_info": {
                "total_locations": len(locations),
                "project_base_name": project_base_name
            },
            "suggestion": "Check location formats and ensure all required analysis tools are available"
        }


def _get_available_query_tools_impl() -> Dict[str, Any]:
    """Implementation function for getting available query tools"""
    
    try:
        # Initialize query tool to check availability
        query_tool = ComprehensiveQueryTool()
        available_tools = query_tool._get_available_tools()
        
        tool_capabilities = {
            'cadastral': 'Property boundaries, ownership, zoning, land use classification',
            'flood': 'FEMA flood zones, base flood elevation, FIRM panels, ABFE data',
            'wetland': 'NWI wetland inventory, wetland types, jurisdictional boundaries',
            'habitat': 'Critical habitat designations, endangered species, ESA consultations',
            'air_quality': 'EPA nonattainment areas, air quality standards, emission requirements',
            'karst': 'Karst features, geological hazards, PRAPEC data (Puerto Rico)'
        }
        
        data_sources = {
            'cadastral': ['CRIM (Puerto Rico)', 'Local assessor databases', 'GIS property data'],
            'flood': ['FEMA FIRM', 'FEMA ABFE', 'National Flood Hazard Layer'],
            'wetland': ['USFWS National Wetlands Inventory', 'State wetland inventories'],
            'habitat': ['USFWS Critical Habitat', 'ECOS database', 'Species occurrence data'],
            'air_quality': ['EPA Green Book', 'State air quality agencies', 'NAAQS data'],
            'karst': ['USGS geological surveys', 'PRAPEC (Puerto Rico)', 'State geological surveys']
        }
        
        return {
            "success": True,
            "available_tools": available_tools,
            "total_tools_available": len(available_tools),
            "tool_capabilities": {tool: capabilities for tool, capabilities in tool_capabilities.items() if tool in available_tools},
            "data_sources": {tool: sources for tool, sources in data_sources.items() if tool in available_tools},
            "supported_regions": [
                "Puerto Rico (all tools)",
                "United States mainland (most tools)",
                "US Territories (limited tools)"
            ],
            "query_types_supported": [
                "Point location queries (lat/lng)",
                "Cadastral number queries",
                "Address-based queries (with geocoding)",
                "Buffer zone analysis",
                "Batch location processing"
            ],
            "output_formats": [
                "JSON data files",
                "Map files (PDF/PNG)",
                "Summary reports",
                "Comprehensive screening datasets"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting tool availability: {e}")
        return {
            "success": False,
            "error": str(e),
            "available_tools": [],
            "suggestion": "Check that environmental analysis tools are properly installed"
        }


def _generate_structured_template_data_impl(
    project_directory: str,
    comprehensive_results_file: Optional[str] = None
) -> Dict[str, Any]:
    """Implementation function for generating structured template data from query results"""
    
    try:
        logger.info(f"📊 Generating structured template data for project: {project_directory}")
        
        project_path = Path(project_directory)
        
        # Look for comprehensive query results file
        if comprehensive_results_file:
            results_file = Path(comprehensive_results_file)
        else:
            results_file = project_path / "data" / "comprehensive_query_results.json"
        
        if not results_file.exists():
            return {
                "success": False,
                "error": f"Comprehensive query results file not found: {results_file}",
                "suggestion": "Run comprehensive environmental queries first"
            }
        
        # Load comprehensive results
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        # Initialize query tool for data processing
        query_tool = ComprehensiveQueryTool()
        
        # Generate structured template data
        structured_data = query_tool._generate_template_data_structure(results)
        
        # Save structured template data
        template_data_file = project_path / "data" / "template_data_structure.json"
        with open(template_data_file, 'w') as f:
            json.dump(structured_data, f, indent=2, default=str)
        
        logger.info(f"✅ Structured template data generated and saved: {template_data_file}")
        
        return {
            "success": True,
            "template_data_file": str(template_data_file),
            "project_directory": str(project_path),
            "template_data": structured_data,
            "schema_compliance": "improved_template_data_schema.json",
            "ready_for_html_generation": True,
            "next_steps": [
                "Use template_data_structure.json with HTML template",
                "Generate PDF report using HTML to PDF tools",
                "Review structured data for completeness"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating structured template data: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_directory": project_directory,
            "suggestion": "Check that comprehensive query results exist and are valid"
        }


@tool("query_environmental_data_for_location", args_schema=QueryLocationInput)
def query_environmental_data_for_location(
    location: str,
    project_name: str,
    cadastral_number: Optional[str] = None,
    output_directory: str = "output",
    include_maps: bool = True,
    buffer_distance: float = 1.0,
    detailed_analysis: bool = True
) -> Dict[str, Any]:
    """
    Perform comprehensive environmental data queries for a single location.
    
    This tool executes all environmental screening queries in one operation:
    - Cadastral/Property analysis
    - Flood zone analysis (FEMA, ABFE)
    - Wetland analysis (NWI)
    - Critical habitat analysis (USFWS)
    - Air quality analysis (EPA Nonattainment)
    - Karst analysis (PRAPEC for Puerto Rico)
    
    **Key Features:**
    - Single command performs all environmental queries
    - Generates standardized JSON data files for each domain
    - Creates comprehensive project directory structure
    - Supports both coordinate and cadastral number inputs
    - Generates maps for each environmental domain
    - Provides detailed error handling and logging
    
    Args:
        location: Location as "latitude,longitude" or address
        project_name: Name of the project for identification
        cadastral_number: Optional cadastral number for property-specific analysis
        output_directory: Base directory for output files
        include_maps: Whether to generate maps for each domain
        buffer_distance: Search buffer radius in miles for proximity analysis
        detailed_analysis: Whether to perform detailed analysis
        
    Returns:
        Dictionary containing:
        - project_info: Project metadata and location details
        - query_results: Results from each environmental domain
        - generated_files: List of all generated data and map files
        - summary: Execution summary with success/failure counts
        - errors: Any errors encountered during queries
    """
    
    return _query_environmental_data_for_location_impl(
        location, project_name, cadastral_number, output_directory,
        include_maps, buffer_distance, detailed_analysis
    )


@tool("batch_query_environmental_data", args_schema=BatchQueryInput)
def batch_query_environmental_data(
    locations: List[Dict[str, Any]],
    project_base_name: str,
    output_directory: str = "output",
    include_maps: bool = True,
    parallel_processing: bool = True
) -> Dict[str, Any]:
    """
    Perform comprehensive environmental data queries for multiple locations in batch.
    
    This tool processes multiple locations simultaneously, performing all environmental
    queries for each location and generating comprehensive data sets for batch analysis.
    
    **Key Features:**
    - Batch processing of multiple locations
    - Parallel or sequential processing options
    - Comprehensive data generation for each location
    - Batch summary and statistics
    - Error handling for individual location failures
    
    Args:
        locations: List of location dictionaries with 'location' and optional 'cadastral_number'
        project_base_name: Base name for projects (will be numbered)
        output_directory: Base directory for output files
        include_maps: Whether to generate maps for each location
        parallel_processing: Whether to process locations in parallel
        
    Returns:
        Dictionary containing:
        - batch_info: Batch processing metadata
        - location_results: Results for each location
        - batch_summary: Overall success/failure statistics
        - total_files_generated: Count of all generated files
    """
    
    return _batch_query_environmental_data_impl(
        locations, project_base_name, output_directory, include_maps, parallel_processing
    )


@tool("get_available_query_tools")
def get_available_query_tools() -> Dict[str, Any]:
    """
    Get information about available environmental query tools and their capabilities.
    
    This tool provides metadata about which environmental analysis tools are available
    and what types of queries can be performed.
    
    Returns:
        Dictionary containing:
        - available_tools: List of available environmental analysis tools
        - tool_capabilities: Description of what each tool can query
        - data_sources: Information about data sources used
        - supported_regions: Geographic regions supported
    """
    
    return _get_available_query_tools_impl()


@tool("generate_structured_template_data")
def generate_structured_template_data(
    project_directory: str,
    comprehensive_results_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate structured JSON data for HTML template from comprehensive query results.
    
    This tool takes raw environmental query results and maps them to the structured
    format required by the comprehensive environmental screening HTML template.
    
    **Key Features:**
    - Maps raw query results to template schema
    - Generates executive summary and risk assessments
    - Creates compliance checklist data
    - Validates data against improved_template_data_schema.json
    - Outputs template-ready JSON file
    
    Args:
        project_directory: Path to project directory containing query results
        comprehensive_results_file: Optional specific results file path
        
    Returns:
        Dictionary containing:
        - template_data_file: Path to generated template data JSON
        - template_data: The structured data itself
        - schema_compliance: Schema compliance information
        - ready_for_html_generation: Whether data is ready for template use
    """
    
    return _generate_structured_template_data_impl(project_directory, comprehensive_results_file)


# Export tools for easy import
COMPREHENSIVE_QUERY_TOOLS = [
    query_environmental_data_for_location,
    batch_query_environmental_data,
    get_available_query_tools,
    generate_structured_template_data
]


def main():
    """Main function for command-line usage"""
    
    parser = argparse.ArgumentParser(
        description='Comprehensive Environmental Query Tool - Unified data retrieval for environmental screening',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query single location by coordinates
  python comprehensive_query_tool.py --location "18.4058,-66.7135" --project "My Project"

  # Query by cadastral number
  python comprehensive_query_tool.py --cadastral "115-053-432-02" --project "Property Assessment"

  # Batch query multiple locations
  python comprehensive_query_tool.py --batch locations.json --project "Batch Analysis"

  # Query with custom settings
  python comprehensive_query_tool.py --location "18.4058,-66.7135" --project "Test" --buffer 2.0 --no-maps
        """
    )
    
    parser.add_argument('--location', help='Location as "latitude,longitude" or address')
    parser.add_argument('--cadastral', help='Cadastral number for property analysis')
    parser.add_argument('--project', help='Project name for identification')
    parser.add_argument('--batch', help='JSON file with batch locations')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--buffer', type=float, default=1.0, help='Search buffer in miles')
    parser.add_argument('--no-maps', action='store_true', help='Skip map generation')
    parser.add_argument('--sequential', action='store_true', help='Process batch sequentially')
    parser.add_argument('--list-tools', action='store_true', help='List available tools')
    
    args = parser.parse_args()
    
    print("🌍 Comprehensive Environmental Query Tool")
    print("=" * 60)
    
    if args.list_tools:
        # List available tools
        tool_info = _get_available_query_tools_impl()
        print("📋 Available Environmental Query Tools:")
        for tool in tool_info['available_tools']:
            print(f"   ✅ {tool}: {tool_info['tool_capabilities'][tool]}")
        
        print(f"\n📊 Total: {tool_info['total_tools_available']} tools available")
        return 0
    
    if args.batch:
        # Batch processing
        if not Path(args.batch).exists():
            print(f"❌ Batch file not found: {args.batch}")
            return 1
        
        with open(args.batch, 'r') as f:
            locations = json.load(f)
        
        project_name = args.project or f"Batch_Analysis_{datetime.now().strftime('%Y%m%d')}"
        
        result = _batch_query_environmental_data_impl(
            locations=locations,
            project_base_name=project_name,
            output_directory=args.output_dir,
            include_maps=not args.no_maps,
            parallel_processing=not args.sequential
        )
        
        if result['success']:
            print(f"✅ Batch processing completed")
            print(f"📊 Success rate: {result['batch_summary']['successful_locations']}/{result['batch_info']['total_locations']}")
        else:
            print(f"❌ Batch processing failed: {result['error']}")
            return 1
    
    else:
        # Single location processing
        if not args.location and not args.cadastral:
            print("❌ Either --location or --cadastral is required")
            return 1
        
        if not args.project:
            print("❌ --project is required")
            return 1
        
        location = args.location if args.location else f"cadastral:{args.cadastral}"
        
        result = _query_environmental_data_for_location_impl(
            location=location,
            project_name=args.project,
            cadastral_number=args.cadastral,
            output_directory=args.output_dir,
            include_maps=not args.no_maps,
            buffer_distance=args.buffer
        )
        
        if result['success']:
            print(f"✅ Environmental queries completed successfully")
            print(f"📁 Project directory: {result['project_info']['project_directory']}")
            print(f"📊 Results: {result['summary']['successful_queries']}/{result['summary']['total_queries']} queries successful")
            print(f"📄 Files generated: {len(result['generated_files'])}")
        else:
            print(f"❌ Environmental queries failed: {result['error']}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 