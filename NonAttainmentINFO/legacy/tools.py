#!/usr/bin/env python3
"""
Nonattainment Areas Analysis Tools

This module provides LangChain-compatible tools for analyzing nonattainment areas
and determining if locations intersect with areas that violate air quality standards.
Includes comprehensive map generation capabilities.
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Type
import json
import logging
from datetime import datetime
import os
import sys

from .nonattainment_client import NonAttainmentAreasClient, NonAttainmentAnalysisResult
from .map_generator import NonAttainmentMapGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NonAttainmentAnalysisInput(BaseModel):
    """Input schema for nonattainment area analysis"""
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
        description="List of specific pollutants to check (e.g., ['Ozone', 'PM2.5']). None for all pollutants."
    )

class NonAttainmentAnalysisWithMapInput(BaseModel):
    """Input schema for comprehensive nonattainment analysis with map generation"""
    longitude: float = Field(description="Longitude coordinate (decimal degrees)")
    latitude: float = Field(description="Latitude coordinate (decimal degrees)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location")
    include_revoked: bool = Field(
        default=False, 
        description="Whether to include revoked air quality standards"
    )
    pollutants: Optional[List[str]] = Field(
        default=None,
        description="List of specific pollutants to check (e.g., ['Ozone', 'PM2.5']). None for all pollutants."
    )

class PollutantAreasSearchInput(BaseModel):
    """Input schema for pollutant areas search"""
    pollutant: str = Field(description="Name of the pollutant to search for (e.g., 'Ozone', 'PM2.5', 'Lead')")
    include_revoked: bool = Field(
        default=False, 
        description="Whether to include revoked air quality standards"
    )

class NonAttainmentAnalysisTool(BaseTool):
    """Tool for analyzing nonattainment areas at a specific location"""
    
    name: str = "analyze_nonattainment_areas"
    description: str = """
    Analyze a geographic location to determine if it intersects with nonattainment areas 
    designated under the Clean Air Act for National Ambient Air Quality Standards (NAAQS).
    
    This tool queries EPA nonattainment areas data and provides:
    - Whether the location has nonattainment area designations
    - Details about affected pollutants and air quality standards
    - Current status (Nonattainment vs Maintenance)
    - Regulatory recommendations and compliance requirements
    
    Use this tool when you need to:
    - Check if a location has air quality violations
    - Identify pollutants that exceed NAAQS at a location
    - Assess Clean Air Act regulatory requirements for development
    - Understand air quality compliance implications
    """
    args_schema: Type[BaseModel] = NonAttainmentAnalysisInput
    
    def _run(self, longitude: float, latitude: float, 
             include_revoked: bool = False, buffer_meters: float = 0,
             pollutants: Optional[List[str]] = None) -> str:
        """Execute nonattainment area analysis"""
        
        try:
            logger.info(f"Analyzing nonattainment areas for location: {longitude}, {latitude}")
            
            # Create client for this request
            client = NonAttainmentAreasClient()
            
            # Perform nonattainment analysis
            result = client.analyze_location(
                longitude=longitude,
                latitude=latitude,
                include_revoked=include_revoked,
                buffer_meters=buffer_meters,
                pollutants=pollutants
            )
            
            # Generate summary
            summary = client.get_area_summary(result)
            
            # Format response
            response = self._format_analysis_response(summary, result)
            
            logger.info(f"Nonattainment area analysis completed for {longitude}, {latitude}")
            return response
            
        except Exception as e:
            error_msg = f"Error analyzing nonattainment areas: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "location": [longitude, latitude],
                "timestamp": datetime.now().isoformat()
            }, indent=2)
    
    def _format_analysis_response(self, summary: Dict[str, Any], 
                                 result: NonAttainmentAnalysisResult) -> str:
        """Format the analysis response for display"""
        
        if summary["status"] == "error":
            return json.dumps({
                "nonattainment_analysis": {
                    "status": "error",
                    "location": summary["location"],
                    "error": summary["message"]
                }
            }, indent=2)
        
        if summary["status"] == "no_nonattainment":
            return json.dumps({
                "nonattainment_analysis": {
                    "status": "no_nonattainment_areas",
                    "location": summary["location"],
                    "message": "No nonattainment areas found at this location",
                    "analysis_timestamp": summary["analysis_timestamp"],
                    "regulatory_status": "Location meets all National Ambient Air Quality Standards (NAAQS)",
                    "air_quality_compliance": "No additional Clean Air Act restrictions apply"
                }
            }, indent=2)
        
        # Format detailed nonattainment information
        response_data = {
            "nonattainment_analysis": {
                "status": "nonattainment_areas_found",
                "location": summary["location"],
                "analysis_timestamp": summary["analysis_timestamp"],
                "summary": summary["summary"],
                "regulatory_implications": {
                    "clean_air_act_restrictions": True,
                    "nonattainment_areas": summary["summary"]["nonattainment_areas"],
                    "maintenance_areas": summary["summary"]["maintenance_areas"],
                    "total_pollutants_affected": summary["summary"]["unique_pollutants"],
                    "pollutants_list": summary["summary"]["pollutants_affected"]
                },
                "affected_areas": self._format_areas_details(summary["areas_details"]),
                "recommendations": summary["recommendations"],
                "next_steps": [
                    "Contact EPA Regional Office for air quality consultation",
                    "Review Clean Air Act permit requirements",
                    "Assess potential emission sources and controls",
                    "Consider air quality impact analysis for new projects"
                ]
            }
        }
        
        return json.dumps(response_data, indent=2)
    
    def _format_areas_details(self, areas_list: List[Dict]) -> List[Dict]:
        """Format areas details for display"""
        
        formatted_areas = []
        
        # Group by pollutant to avoid duplicates
        pollutant_groups = {}
        for area in areas_list:
            pollutant = area["pollutant_name"]
            if pollutant not in pollutant_groups:
                pollutant_groups[pollutant] = {
                    "pollutant_name": pollutant,
                    "areas": [],
                    "statuses": set(),
                    "classifications": set()
                }
            
            pollutant_groups[pollutant]["areas"].append({
                "area_name": area["area_name"],
                "state_name": area["state_name"],
                "current_status": area["current_status"],
                "classification": area["classification"],
                "design_value": area["design_value"],
                "design_value_units": area["design_value_units"],
                "meets_naaqs": area["meets_naaqs"]
            })
            pollutant_groups[pollutant]["statuses"].add(area["current_status"])
            pollutant_groups[pollutant]["classifications"].add(area["classification"])
        
        # Format grouped pollutants
        for pollutant_data in pollutant_groups.values():
            formatted_areas.append({
                "pollutant_name": pollutant_data["pollutant_name"],
                "affected_areas": pollutant_data["areas"],
                "area_count": len(pollutant_data["areas"]),
                "statuses": list(pollutant_data["statuses"]),
                "classifications": list(pollutant_data["classifications"]),
                "regulatory_significance": self._assess_pollutant_significance(pollutant_data["pollutant_name"])
            })
        
        return formatted_areas
    
    def _assess_pollutant_significance(self, pollutant: str) -> str:
        """Assess regulatory significance of a pollutant"""
        
        significance_map = {
            "Ozone": "Major air quality concern - affects respiratory health and vegetation",
            "PM2.5": "Fine particulate matter - serious health impacts, especially cardiovascular and respiratory",
            "PM10": "Coarse particulate matter - respiratory health concerns",
            "Lead": "Toxic heavy metal - serious neurological health impacts, especially in children",
            "Sulfur Dioxide": "Respiratory irritant - contributes to acid rain and particulate formation",
            "Carbon Monoxide": "Toxic gas - reduces oxygen delivery in blood",
            "Nitrogen Dioxide": "Respiratory irritant - contributes to ozone and particulate formation"
        }
        
        return significance_map.get(pollutant, "Regulated air pollutant under Clean Air Act")

class NonAttainmentAnalysisWithMapTool(BaseTool):
    """Tool for comprehensive nonattainment analysis with adaptive map generation"""
    
    name: str = "analyze_nonattainment_areas_with_map"
    description: str = """
    Comprehensive nonattainment areas analysis tool that combines data querying and adaptive map generation.
    
    This tool performs a complete air quality assessment:
    
    1. **Location Analysis**: Determines if the coordinate point intersects with nonattainment areas
    2. **Regional Assessment**: Analyzes air quality violations in the surrounding region
    3. **Pollutant Details**: Provides comprehensive information about affected pollutants including:
       - NAAQS standards and violations
       - Area classifications and status
       - Design values and compliance metrics
       - Regulatory implications
    4. **Adaptive Map**: Generates an intelligent map with optimal settings based on analysis:
       - Automatic buffer sizing based on nonattainment area presence
       - Appropriate base map selection for air quality visualization
       - Optimal transparency settings for multiple pollutant layers
       - Professional legend and regulatory context
    
    All files are organized into a custom project directory structure.
    
    Data Sources:
    - EPA Nonattainment Areas Database
    - National Ambient Air Quality Standards (NAAQS)
    - Clean Air Act regulatory framework
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere)
        latitude: Latitude coordinate (positive for northern hemisphere)
        location_name: Optional descriptive name for the location
        include_revoked: Whether to include revoked air quality standards
        pollutants: List of specific pollutants to analyze (None for all)
        
    Returns:
        Dictionary containing:
        - location_analysis: Complete air quality data analysis
        - nonattainment_areas: Detailed information about violations in the region
        - map_generation: Results of adaptive map generation
        - regulatory_assessment: Clean Air Act compliance implications
        - recommendations: Actionable recommendations based on findings
        - project_directory: Information about the custom output directory
    """
    args_schema: Type[BaseModel] = NonAttainmentAnalysisWithMapInput
    
    def _run(self, longitude: float, latitude: float, 
             location_name: Optional[str] = None,
             include_revoked: bool = False,
             pollutants: Optional[List[str]] = None) -> str:
        """Execute comprehensive nonattainment analysis with map generation"""
        
        if location_name is None:
            location_name = f"Air Quality Analysis at ({longitude}, {latitude})"
        
        print(f"🌫️ Starting comprehensive nonattainment analysis for {location_name}")
        
        # Get or create project directory
        try:
            # Import output manager
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from output_directory_manager import get_output_manager
            
            output_manager = get_output_manager()
            if not output_manager.current_project_dir:
                # Create project directory if not already created
                project_dir = output_manager.create_project_directory(
                    location_name=location_name,
                    coordinates=(longitude, latitude)
                )
                print(f"📁 Created project directory: {project_dir}")
            else:
                project_dir = output_manager.current_project_dir
                print(f"📁 Using existing project directory: {project_dir}")
        except Exception as e:
            print(f"⚠️ Could not set up project directory: {e}")
            output_manager = None
            project_dir = "."
        
        try:
            # Initialize components
            client = NonAttainmentAreasClient()
            map_generator = NonAttainmentMapGenerator()
            
            # Step 1: Perform nonattainment data analysis
            print(f"🔍 Step 1: Analyzing nonattainment areas data...")
            result = client.analyze_location(
                longitude=longitude,
                latitude=latitude,
                include_revoked=include_revoked,
                buffer_meters=0,  # Point analysis
                pollutants=pollutants
            )
            
            # Generate summary
            summary = client.get_area_summary(result)
            
            # Save detailed results to project logs directory if available
            if output_manager:
                logs_dir = output_manager.get_subdirectory("logs")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                coords = f"{longitude}_{latitude}".replace('-', 'neg').replace('.', 'p')
                nonattainment_data_file = os.path.join(logs_dir, f"nonattainment_analysis_{coords}_{timestamp}.json")
                
                with open(nonattainment_data_file, 'w') as f:
                    json.dump({
                        "analysis_result": {
                            "location": result.location,
                            "has_nonattainment_areas": result.has_nonattainment_areas,
                            "area_count": result.area_count,
                            "query_success": result.query_success,
                            "analysis_timestamp": result.analysis_timestamp
                        },
                        "summary": summary
                    }, f, indent=2, default=str)
                print(f"💾 Nonattainment analysis data saved to: {nonattainment_data_file}")
            
            # Step 2: Generate adaptive map
            print(f"🗺️  Step 2: Generating adaptive nonattainment areas map...")
            map_result = self._generate_adaptive_map(
                longitude, latitude, location_name, result, map_generator, output_manager
            )
            
            # Step 3: Create regulatory assessment
            print(f"⚖️  Step 3: Creating regulatory assessment...")
            regulatory_assessment = self._create_regulatory_assessment(result, summary)
            
            # Step 4: Generate recommendations
            print(f"💡 Step 4: Generating recommendations...")
            recommendations = self._generate_recommendations(result, regulatory_assessment)
            
            # Save summary data to project data directory if available
            if output_manager:
                data_dir = output_manager.get_subdirectory("data")
                summary_data = {
                    "location_analysis": {
                        "location": location_name,
                        "coordinates": (longitude, latitude),
                        "analysis_timestamp": result.analysis_timestamp,
                        "has_nonattainment_areas": result.has_nonattainment_areas,
                        "total_areas_found": result.area_count
                    },
                    "nonattainment_areas": [
                        {
                            "pollutant_name": area.pollutant_name,
                            "area_name": area.area_name,
                            "state_name": area.state_name,
                            "current_status": area.current_status,
                            "classification": area.classification
                        } for area in result.nonattainment_areas
                    ],
                    "regulatory_assessment": regulatory_assessment,
                    "recommendations": recommendations
                }
                
                summary_file = os.path.join(data_dir, f"nonattainment_summary_{coords}_{timestamp}.json")
                with open(summary_file, 'w') as f:
                    json.dump(summary_data, f, indent=2, default=str)
                print(f"📋 Nonattainment summary saved to: {summary_file}")
            
            # Compile comprehensive results
            results = {
                "location_analysis": {
                    "location": location_name,
                    "coordinates": (longitude, latitude),
                    "analysis_timestamp": result.analysis_timestamp,
                    "has_nonattainment_areas": result.has_nonattainment_areas,
                    "total_areas_found": result.area_count,
                    "query_success": result.query_success,
                    "data_sources": [
                        "EPA Nonattainment Areas Database",
                        "National Ambient Air Quality Standards (NAAQS)",
                        "Clean Air Act regulatory framework"
                    ]
                },
                "nonattainment_areas": {
                    "areas_found": result.area_count,
                    "areas": [
                        {
                            "pollutant_name": area.pollutant_name,
                            "area_name": area.area_name,
                            "state_name": area.state_name,
                            "current_status": area.current_status,
                            "classification": area.classification,
                            "design_value": area.design_value,
                            "design_value_units": area.design_value_units,
                            "regulatory_significance": self._assess_pollutant_significance(area.pollutant_name)
                        } for area in result.nonattainment_areas
                    ]
                },
                "map_generation": map_result,
                "regulatory_assessment": regulatory_assessment,
                "recommendations": recommendations,
                "analysis_summary": {
                    "air_quality_status": "Nonattainment areas present" if result.has_nonattainment_areas else "Meets air quality standards",
                    "pollutants_affected": list(set(area.pollutant_name for area in result.nonattainment_areas)) if result.nonattainment_areas else [],
                    "regulatory_complexity": self._assess_regulatory_complexity(result),
                    "next_steps": "Review recommendations and consider air quality consultation if development is planned"
                },
                "project_directory": output_manager.get_project_info() if output_manager else {"note": "No project directory"},
                "files_generated": {
                    "nonattainment_data_file": nonattainment_data_file if output_manager else None,
                    "summary_file": summary_file if output_manager else None,
                    "map_file": map_result.get("filename") if map_result.get("success") else None
                }
            }
            
            print(f"✅ Comprehensive nonattainment analysis completed successfully")
            if output_manager:
                print(f"📁 All files saved to project directory: {project_dir}")
            
            return json.dumps(results, indent=2, default=str)
            
        except Exception as e:
            error_result = {
                "location_analysis": {
                    "location": location_name,
                    "coordinates": (longitude, latitude),
                    "error": f"Analysis failed: {str(e)}"
                },
                "nonattainment_areas": {"error": "Could not analyze nonattainment areas"},
                "map_generation": {"success": False, "error": str(e)},
                "regulatory_assessment": {"status": "Could not assess due to analysis error"},
                "recommendations": ["Verify coordinates are valid and try again"],
                "analysis_summary": {
                    "status": "Failed",
                    "error": str(e)
                },
                "project_directory": output_manager.get_project_info() if output_manager else {"error": "No project directory"}
            }
            print(f"❌ Error during comprehensive analysis: {str(e)}")
            return json.dumps(error_result, indent=2)
    
    def _generate_adaptive_map(self, longitude: float, latitude: float, location_name: str,
                              result: NonAttainmentAnalysisResult, map_generator: NonAttainmentMapGenerator,
                              output_manager) -> Dict[str, Any]:
        """Generate adaptive map based on nonattainment analysis"""
        
        try:
            # Determine optimal settings based on analysis results
            if result.has_nonattainment_areas:
                # Areas found - use detailed regional view
                buffer_miles = 25.0
                base_map = "World_Topo_Map"
                transparency = 0.7
                reasoning = f"Found {result.area_count} nonattainment areas - using detailed 25-mile regional view"
                
                # Extract pollutants from results
                pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
            else:
                # No areas found - use broader regional view to show clean air status
                buffer_miles = 50.0
                base_map = "World_Street_Map"
                transparency = 0.8
                reasoning = "No nonattainment areas found - using 50-mile regional view to confirm clean air status"
                pollutants = None
            
            # Generate filename for maps directory
            if output_manager:
                maps_dir = output_manager.get_subdirectory("maps")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
                map_filename = os.path.join(maps_dir, f"nonattainment_map_{safe_name}_{timestamp}.pdf")
                output_filename = os.path.basename(map_filename)
            else:
                output_filename = None
            
            # Generate the map with adaptive configuration
            map_path = map_generator.generate_nonattainment_map_pdf(
                longitude=longitude,
                latitude=latitude,
                location_name=f"{location_name} - Air Quality Analysis Map",
                buffer_miles=buffer_miles,
                base_map=base_map,
                pollutants=pollutants,
                nonattainment_transparency=transparency,
                include_legend=True,
                output_filename=output_filename
            )
            
            # Move the generated map to the correct location if needed
            if output_manager and map_path and map_path != map_filename:
                import shutil
                try:
                    shutil.move(map_path, map_filename)
                    map_path = map_filename
                except:
                    # If move fails, keep original path
                    pass
            
            if map_path:
                coverage_area = round(3.14159 * (buffer_miles ** 2), 2)
                
                return {
                    "success": True,
                    "message": "Adaptive nonattainment areas map successfully generated",
                    "filename": map_path,
                    "adaptive_settings": {
                        "buffer_miles": buffer_miles,
                        "base_map": base_map,
                        "nonattainment_transparency": transparency,
                        "reasoning": reasoning,
                        "resolution_dpi": 300,
                        "coverage_area_sq_miles": coverage_area,
                        "pollutants_shown": pollutants if pollutants else "All active standards"
                    },
                    "map_features": {
                        "includes_legend": True,
                        "includes_scale_bar": True,
                        "high_resolution": True,
                        "optimized_for_air_quality_analysis": True,
                        "shows_regulatory_boundaries": True
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to generate adaptive nonattainment areas map",
                    "reasoning": reasoning,
                    "suggested_buffer": buffer_miles
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during map generation: {str(e)}",
                "suggestion": "Map generation failed, but nonattainment data analysis was successful"
            }
    
    def _create_regulatory_assessment(self, result: NonAttainmentAnalysisResult, 
                                    summary: Dict[str, Any]) -> Dict[str, Any]:
        """Create regulatory assessment based on nonattainment findings"""
        
        assessment = {
            "clean_air_act_impact": "Low",
            "permit_requirements": [],
            "regulatory_agencies": [],
            "compliance_considerations": [],
            "development_implications": []
        }
        
        if result.has_nonattainment_areas:
            assessment["clean_air_act_impact"] = "High"
            assessment["permit_requirements"].extend([
                "New Source Review (NSR) requirements may apply",
                "Prevention of Significant Deterioration (PSD) permits may be required",
                "State Implementation Plan (SIP) compliance required"
            ])
            assessment["regulatory_agencies"].extend([
                "EPA Regional Office",
                "State Air Quality Agency",
                "Local Air Quality Management District"
            ])
            
            # Assess based on pollutants and status
            nonattainment_areas = [area for area in result.nonattainment_areas if area.current_status == 'Nonattainment']
            maintenance_areas = [area for area in result.nonattainment_areas if area.current_status == 'Maintenance']
            
            if nonattainment_areas:
                assessment["compliance_considerations"].append(
                    f"Location in {len(nonattainment_areas)} active nonattainment area(s) - strict emission controls apply"
                )
                assessment["development_implications"].append(
                    "New sources may require emission offsets"
                )
            
            if maintenance_areas:
                assessment["compliance_considerations"].append(
                    f"Location in {len(maintenance_areas)} maintenance area(s) - continued compliance monitoring required"
                )
            
            pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
            if len(pollutants) > 1:
                assessment["compliance_considerations"].append(
                    f"Multiple pollutants affected ({len(pollutants)}) - complex regulatory requirements"
                )
            
            assessment["development_implications"].extend([
                "Air quality impact analysis required for major sources",
                "Transportation conformity requirements may apply",
                "Enhanced monitoring and reporting obligations"
            ])
        else:
            assessment["clean_air_act_impact"] = "Low"
            assessment["compliance_considerations"].append("Location meets all National Ambient Air Quality Standards")
            assessment["development_implications"].append("Standard air quality permitting applies")
        
        return assessment
    
    def _generate_recommendations(self, result: NonAttainmentAnalysisResult, 
                                regulatory_assessment: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        if result.has_nonattainment_areas:
            recommendations.extend([
                "🚨 REGULATORY ALERT: Location is within nonattainment areas for air quality standards",
                "📋 Conduct air quality impact assessment for any development projects",
                "⚖️ Consult with EPA Regional Office and state air quality agency early in planning",
                "📞 Contact local Air Quality Management District for specific requirements"
            ])
            
            nonattainment_areas = [area for area in result.nonattainment_areas if area.current_status == 'Nonattainment']
            if nonattainment_areas:
                recommendations.extend([
                    f"⚠️ HIGH PRIORITY: {len(nonattainment_areas)} active nonattainment area(s) - enhanced controls required",
                    "💰 Budget for potential emission offset requirements",
                    "🔍 Consider alternative locations if air quality compliance is challenging"
                ])
            
            pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
            recommendations.extend([
                f"🌫️ Affected pollutants: {', '.join(pollutants)}",
                "📚 Review Clean Air Act New Source Review requirements",
                "🗺️ Use generated map for regulatory consultation and planning"
            ])
        else:
            recommendations.extend([
                "✅ GOOD NEWS: No nonattainment areas identified at this location",
                "📋 Standard air quality permitting requirements apply",
                "🔍 Verify findings with state air quality agency for large projects",
                "🗺️ Use generated regional map to confirm clean air status"
            ])
        
        recommendations.extend([
            "📄 Include this analysis in environmental compliance documentation",
            "🔄 Monitor EPA Green Book for changes in nonattainment designations"
        ])
        
        return recommendations
    
    def _assess_regulatory_complexity(self, result: NonAttainmentAnalysisResult) -> str:
        """Assess regulatory complexity based on nonattainment findings"""
        
        if not result.has_nonattainment_areas:
            return "Low - Standard air quality regulations apply"
        
        pollutants = list(set(area.pollutant_name for area in result.nonattainment_areas))
        nonattainment_count = len([area for area in result.nonattainment_areas if area.current_status == 'Nonattainment'])
        
        if len(pollutants) > 2 and nonattainment_count > 2:
            return "Very High - Multiple pollutants with active nonattainment status"
        elif len(pollutants) > 1 or nonattainment_count > 1:
            return "High - Multiple areas or pollutants affected"
        else:
            return "Medium - Single pollutant nonattainment area"
    
    def _assess_pollutant_significance(self, pollutant: str) -> str:
        """Assess regulatory significance of a pollutant"""
        
        significance_map = {
            "Ozone": "Major air quality concern - affects respiratory health and vegetation",
            "PM2.5": "Fine particulate matter - serious health impacts, especially cardiovascular and respiratory",
            "PM10": "Coarse particulate matter - respiratory health concerns",
            "Lead": "Toxic heavy metal - serious neurological health impacts, especially in children",
            "Sulfur Dioxide": "Respiratory irritant - contributes to acid rain and particulate formation",
            "Carbon Monoxide": "Toxic gas - reduces oxygen delivery in blood",
            "Nitrogen Dioxide": "Respiratory irritant - contributes to ozone and particulate formation"
        }
        
        return significance_map.get(pollutant, "Regulated air pollutant under Clean Air Act")

class PollutantAreasSearchTool(BaseTool):
    """Tool for searching nonattainment areas by pollutant type"""
    
    name: str = "search_pollutant_areas"
    description: str = """
    Search for all nonattainment areas designated for a specific air pollutant 
    under the National Ambient Air Quality Standards (NAAQS). This tool helps 
    identify where air quality violations exist for a particular pollutant 
    across the United States.
    
    Use this tool when you need to:
    - Find all nonattainment areas for a specific pollutant
    - Understand the geographic scope of air quality violations
    - Research pollutant-specific compliance requirements
    - Plan projects around known air quality problem areas
    """
    args_schema: Type[BaseModel] = PollutantAreasSearchInput
    
    def _run(self, pollutant: str, include_revoked: bool = False) -> str:
        """Execute pollutant areas search"""
        
        try:
            logger.info(f"Searching for nonattainment areas for pollutant: {pollutant}")
            
            # Create client for this request
            client = NonAttainmentAreasClient()
            
            # Search for pollutant areas
            areas = client.get_pollutant_areas(
                pollutant=pollutant,
                include_revoked=include_revoked
            )
            
            # Format response
            response = self._format_pollutant_search_response(pollutant, areas, include_revoked)
            
            logger.info(f"Found {len(areas)} nonattainment areas for {pollutant}")
            return response
            
        except Exception as e:
            error_msg = f"Error searching for pollutant areas: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "pollutant_searched": pollutant,
                "timestamp": datetime.now().isoformat()
            }, indent=2)
    
    def _format_pollutant_search_response(self, pollutant: str, 
                                         areas: List, include_revoked: bool) -> str:
        """Format the pollutant search response"""
        
        if not areas:
            return json.dumps({
                "pollutant_areas_search": {
                    "status": "no_areas_found",
                    "pollutant_searched": pollutant,
                    "include_revoked": include_revoked,
                    "message": f"No nonattainment areas found for '{pollutant}'",
                    "suggestions": [
                        "Check spelling of pollutant name",
                        "Try common pollutant names: Ozone, PM2.5, PM10, Lead, SO2, CO, NO2",
                        "Pollutant may not have current nonattainment areas",
                        "Try including revoked standards if searching historical data"
                    ]
                }
            }, indent=2)
        
        # Analyze areas data
        nonattainment_areas = [area for area in areas if area.current_status == 'Nonattainment']
        maintenance_areas = [area for area in areas if area.current_status == 'Maintenance']
        unique_states = list(set(area.state_name for area in areas))
        unique_regions = list(set(area.epa_region for area in areas if area.epa_region))
        
        # Group by state
        states_data = {}
        for area in areas:
            state = area.state_name
            if state not in states_data:
                states_data[state] = {
                    "state_name": state,
                    "state_abbreviation": area.state_abbreviation,
                    "areas": [],
                    "nonattainment_count": 0,
                    "maintenance_count": 0
                }
            
            states_data[state]["areas"].append({
                "area_name": area.area_name,
                "current_status": area.current_status,
                "classification": area.classification,
                "design_value": area.design_value,
                "design_value_units": area.design_value_units
            })
            
            if area.current_status == 'Nonattainment':
                states_data[state]["nonattainment_count"] += 1
            elif area.current_status == 'Maintenance':
                states_data[state]["maintenance_count"] += 1
        
        # Format state information
        states_summary = []
        for state_data in states_data.values():
            states_summary.append({
                "state_name": state_data["state_name"],
                "state_abbreviation": state_data["state_abbreviation"],
                "total_areas": len(state_data["areas"]),
                "nonattainment_areas": state_data["nonattainment_count"],
                "maintenance_areas": state_data["maintenance_count"],
                "areas_details": state_data["areas"][:10]  # Limit to first 10 areas per state
            })
        
        response_data = {
            "pollutant_areas_search": {
                "status": "areas_found",
                "pollutant_searched": pollutant,
                "include_revoked": include_revoked,
                "analysis_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_areas": len(areas),
                    "states_affected": len(unique_states),
                    "epa_regions_affected": len(unique_regions),
                    "nonattainment_areas": len(nonattainment_areas),
                    "maintenance_areas": len(maintenance_areas)
                },
                "states_summary": states_summary,
                "epa_regions_affected": sorted(unique_regions),
                "pollutant_info": {
                    "pollutant_name": pollutant,
                    "regulatory_significance": self._get_pollutant_info(pollutant),
                    "health_impacts": self._get_health_impacts(pollutant)
                },
                "regulatory_context": {
                    "clean_air_act_regulated": True,
                    "naaqs_standards_apply": True,
                    "state_implementation_plans_required": True
                }
            }
        }
        
        if len(areas) > 100:
            response_data["pollutant_areas_search"]["note"] = f"Large dataset - showing summary for {len(areas)} areas"
        
        return json.dumps(response_data, indent=2)
    
    def _get_pollutant_info(self, pollutant: str) -> str:
        """Get regulatory information about a pollutant"""
        
        info_map = {
            "Ozone": "Ground-level ozone is a criteria pollutant formed by chemical reactions between NOx and VOCs in sunlight",
            "PM2.5": "Fine particulate matter with diameter ≤2.5 micrometers - penetrates deep into lungs and bloodstream",
            "PM10": "Coarse particulate matter with diameter ≤10 micrometers - includes dust, pollen, and mold",
            "Lead": "Toxic heavy metal that accumulates in the body - primarily from industrial sources",
            "Sulfur Dioxide": "SO2 gas primarily from fossil fuel combustion - forms sulfuric acid in atmosphere",
            "Carbon Monoxide": "Colorless, odorless toxic gas from incomplete combustion",
            "Nitrogen Dioxide": "NO2 gas from high-temperature combustion - precursor to ozone and PM formation"
        }
        
        return info_map.get(pollutant, f"Criteria pollutant regulated under National Ambient Air Quality Standards")
    
    def _get_health_impacts(self, pollutant: str) -> str:
        """Get health impact information about a pollutant"""
        
        health_map = {
            "Ozone": "Respiratory irritation, asthma exacerbation, reduced lung function",
            "PM2.5": "Cardiovascular disease, respiratory disease, premature death",
            "PM10": "Respiratory irritation, aggravated asthma, reduced lung function",
            "Lead": "Neurological damage, developmental delays in children, cardiovascular effects",
            "Sulfur Dioxide": "Respiratory irritation, bronchoconstriction, aggravated asthma",
            "Carbon Monoxide": "Reduced oxygen delivery, cardiovascular stress, neurological effects",
            "Nitrogen Dioxide": "Respiratory irritation, increased susceptibility to respiratory infections"
        }
        
        return health_map.get(pollutant, "Various health impacts depending on exposure level and duration")

# Create tool instances
analyze_nonattainment_areas = NonAttainmentAnalysisTool()
analyze_nonattainment_areas_with_map = NonAttainmentAnalysisWithMapTool()
search_pollutant_areas = PollutantAreasSearchTool()

# Export tools list
nonattainment_tools = [
    analyze_nonattainment_areas,
    analyze_nonattainment_areas_with_map,
    search_pollutant_areas
] 