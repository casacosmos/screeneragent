#!/usr/bin/env python3
"""
Comprehensive Wetland Analysis Tool

This module provides a single comprehensive tool that combines wetland data querying
and adaptive map generation for a given coordinate point.

The tool:
1. Analyzes if the coordinate point is within a wetland
2. If not in wetland, identifies wetlands within 0.5-mile radius
3. Provides detailed wetland information and classifications
4. Generates an adaptive wetland map based on the analysis
5. Returns comprehensive results including both data and map

Tool:
- analyze_wetland_location_with_map: Complete wetland analysis with adaptive map generation
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import math

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_core.tools import tool
from query_wetland_location import WetlandLocationAnalyzer, save_results_to_file
from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

class WetlandAnalysisInput(BaseModel):
    """Input schema for comprehensive wetland analysis"""
    longitude: float = Field(description="Longitude coordinate (e.g., -66.199399 for Puerto Rico)")
    latitude: float = Field(description="Latitude coordinate (e.g., 18.408303 for Puerto Rico)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location (e.g., 'Bayamón, Puerto Rico')")

@tool("analyze_wetland_location_with_map", args_schema=WetlandAnalysisInput)
def analyze_wetland_location_with_map(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive wetland analysis tool that combines data querying and adaptive map generation.
    
    This tool performs a complete wetland assessment:
    
    1. **Point Analysis**: Determines if the coordinate point is within a wetland
    2. **Radius Search**: If not in wetland, searches for wetlands within 0.5-mile radius
    3. **Wetland Details**: Provides comprehensive information about identified wetlands including:
       - NWI classifications and codes
       - Wetland types and characteristics
       - Areas and distances
       - Regulatory implications
    4. **Adaptive Map**: Generates an intelligent map with optimal settings based on analysis:
       - Automatic buffer sizing based on wetland proximity
       - Appropriate base map selection
       - Optimal transparency settings
       - Professional legend and scale
    
    Data Sources:
    - USFWS National Wetlands Inventory (NWI)
    - EPA RIBITS (Regulatory In-lieu fee and Bank Information Tracking System)
    - EPA National Hydrography Dataset (NHD)
    - USFWS Riparian Mapping
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere)
        latitude: Latitude coordinate (positive for northern hemisphere)
        location_name: Optional descriptive name for the location
        
    Returns:
        Dictionary containing:
        - location_analysis: Complete wetland data analysis
        - wetlands_in_radius: Detailed information about wetlands within 0.5-mile radius
        - map_generation: Results of adaptive map generation
        - regulatory_assessment: Environmental and regulatory implications
        - recommendations: Actionable recommendations based on findings
    """
    
    if location_name is None:
        location_name = f"Wetland Analysis at ({longitude}, {latitude})"
    
    print(f"🌿 Starting comprehensive wetland analysis for {location_name}")
    
    try:
        # Initialize components
        analyzer = WetlandLocationAnalyzer()
        map_generator = WetlandMapGeneratorV3()
        
        # Step 1: Perform wetland data analysis
        print(f"🔍 Step 1: Analyzing wetland data...")
        wetland_results = analyzer.analyze_location(longitude, latitude, location_name)
        
        # Auto-save detailed results
        save_results_to_file(wetland_results)
        
        # Step 2: Process wetland information for 0.5-mile radius focus
        print(f"📏 Step 2: Processing wetlands within 0.5-mile radius...")
        wetlands_in_radius = []
        
        # Check if point is in wetland
        is_in_wetland = wetland_results['is_in_wetland']
        
        if is_in_wetland:
            # Add wetlands at exact location
            for wetland in wetland_results.get('wetlands_at_location', []):
                wetland_info = _extract_wetland_info(wetland, 0.0, "At location")
                wetlands_in_radius.append(wetland_info)
        
        # Add nearby wetlands within 0.5 miles
        for nearby in wetland_results.get('nearest_wetlands', []):
            if nearby['distance_miles'] <= 0.5:
                wetland_info = _extract_wetland_info(
                    nearby['wetland'], 
                    nearby['distance_miles'], 
                    nearby['bearing']
                )
                wetlands_in_radius.append(wetland_info)
        
        # Step 3: Generate adaptive map
        print(f"🗺️  Step 3: Generating adaptive wetland map...")
        map_result = _generate_adaptive_map(
            longitude, latitude, location_name, 
            wetland_results, analyzer, map_generator
        )
        
        # Step 4: Create regulatory assessment
        print(f"⚖️  Step 4: Creating regulatory assessment...")
        regulatory_assessment = _create_regulatory_assessment(
            is_in_wetland, wetlands_in_radius, wetland_results
        )
        
        # Step 5: Generate recommendations
        print(f"💡 Step 5: Generating recommendations...")
        recommendations = _generate_recommendations(
            is_in_wetland, wetlands_in_radius, regulatory_assessment
        )
        
        # Compile comprehensive results
        results = {
            "location_analysis": {
                "location": location_name,
                "coordinates": (longitude, latitude),
                "query_time": wetland_results['query_time'],
                "is_in_wetland": is_in_wetland,
                "total_wetlands_found": len(wetlands_in_radius),
                "search_radius_used": wetland_results['search_summary']['search_radius_used'],
                "data_sources": [
                    "USFWS National Wetlands Inventory (NWI)",
                    "EPA RIBITS",
                    "EPA National Hydrography Dataset (NHD)",
                    "USFWS Riparian Mapping"
                ]
            },
            "wetlands_in_radius": {
                "radius_miles": 0.5,
                "radius_area_sq_miles": round(math.pi * (0.5 ** 2), 2),
                "wetlands_count": len(wetlands_in_radius),
                "wetlands": wetlands_in_radius
            },
            "map_generation": map_result,
            "regulatory_assessment": regulatory_assessment,
            "recommendations": recommendations,
            "analysis_summary": {
                "environmental_significance": wetland_results['analysis']['environmental_significance'],
                "key_wetland_types": list(set([w['wetland_type'] for w in wetlands_in_radius])),
                "regulatory_complexity": _assess_regulatory_complexity(wetlands_in_radius),
                "next_steps": "Review recommendations and consider professional consultation if permits may be required"
            }
        }
        
        print(f"✅ Comprehensive wetland analysis completed successfully")
        return results
        
    except Exception as e:
        error_result = {
            "location_analysis": {
                "location": location_name,
                "coordinates": (longitude, latitude),
                "error": f"Analysis failed: {str(e)}"
            },
            "wetlands_in_radius": {"error": "Could not analyze wetlands"},
            "map_generation": {"success": False, "error": str(e)},
            "regulatory_assessment": {"status": "Could not assess due to analysis error"},
            "recommendations": ["Verify coordinates are valid and try again"],
            "analysis_summary": {
                "status": "Failed",
                "error": str(e)
            }
        }
        print(f"❌ Error during comprehensive analysis: {str(e)}")
        return error_result

def _extract_wetland_info(wetland, distance_miles: float, bearing: str) -> Dict[str, Any]:
    """Extract standardized wetland information"""
    
    if isinstance(wetland, dict):
        # Handle dictionary format
        wetland_info = {
            "wetland_type": wetland.get('type', 'Unknown'),
            "nwi_code": wetland.get('attribute', 'Unknown'),
            "area_acres": wetland.get('acres', 0),
            "distance_miles": distance_miles,
            "bearing": bearing,
            "classification": wetland.get('wetland_type', 'Unknown'),
            "source": "NWI"
        }
    else:
        # Handle object format
        wetland_info = {
            "wetland_type": getattr(wetland, 'wetland_type', 'Unknown'),
            "nwi_code": getattr(wetland, 'attribute', 'Unknown'),
            "area_acres": getattr(wetland, 'acres', 0),
            "distance_miles": distance_miles,
            "bearing": bearing,
            "classification": getattr(wetland, 'wetland_type', 'Unknown'),
            "source": "NWI"
        }
    
    # Add regulatory significance
    wetland_info["regulatory_significance"] = _assess_wetland_regulatory_significance(
        wetland_info["nwi_code"], wetland_info["area_acres"]
    )
    
    return wetland_info

def _assess_wetland_regulatory_significance(nwi_code: str, area_acres: float) -> str:
    """Assess regulatory significance of a wetland"""
    
    if "PUB" in nwi_code or "POW" in nwi_code:
        return "High - Open water/pond, likely jurisdictional"
    elif "PEM" in nwi_code:
        return "High - Emergent wetland, typically jurisdictional"
    elif "PSS" in nwi_code:
        return "High - Scrub-shrub wetland, typically jurisdictional"
    elif "PFO" in nwi_code:
        return "High - Forested wetland, typically jurisdictional"
    elif area_acres > 1.0:
        return "Medium-High - Large wetland area"
    elif area_acres > 0.1:
        return "Medium - Moderate wetland area"
    else:
        return "Low-Medium - Small wetland area"

def _generate_adaptive_map(longitude: float, latitude: float, location_name: str,
                          wetland_results: Dict, analyzer: WetlandLocationAnalyzer,
                          map_generator: WetlandMapGeneratorV3) -> Dict[str, Any]:
    """Generate adaptive map based on wetland analysis"""
    
    try:
        # Determine optimal settings based on analysis results
        if wetland_results['is_in_wetland']:
            # If wetlands are present at exact location, use smaller buffer for detail
            buffer_miles = 0.5
            wetland_transparency = 0.75
            base_map = "World_Imagery"
            reasoning = "Wetlands at exact location - using detailed view with 0.5-mile buffer"
        else:
            # If no wetlands at exact location, use buffer based on search results
            search_radius = wetland_results['search_summary']['search_radius_used']
            wetlands_found = len(wetland_results.get('nearest_wetlands', []))
            
            if wetlands_found > 0:
                # Calculate buffer based on actual distance to nearest wetland
                nearest_wetland = wetland_results['nearest_wetlands'][0]
                nearest_distance = nearest_wetland['distance_miles']
                
                if nearest_distance <= 0.5:
                    # Wetlands within 0.5 miles - use 1.0 mile buffer to show context
                    buffer_miles = 1.0
                    reasoning = f"Wetlands within 0.5 miles (nearest at {nearest_distance} miles) - using 1.0-mile buffer"
                else:
                    # Add buffer to ensure wetlands are visible with context
                    buffer_miles = min(nearest_distance + 1.0, 3.0)
                    reasoning = f"Nearest wetland at {nearest_distance} miles - using {buffer_miles}-mile buffer"
                
                wetland_transparency = 0.8
                base_map = "World_Imagery"
            else:
                # No wetlands found even after expanded search
                buffer_miles = 2.0
                wetland_transparency = 0.8
                base_map = "World_Topo_Map"
                reasoning = f"No wetlands found within {search_radius} miles - using 2.0-mile regional view"
        
        # Generate the map with adaptive configuration
        map_path = map_generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=f"{location_name} - Adaptive Analysis Map",
            buffer_miles=buffer_miles,
            base_map=base_map,
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            wetland_transparency=wetland_transparency
        )
        
        if map_path:
            coverage_area = round(math.pi * (buffer_miles ** 2), 2)
            
            return {
                "success": True,
                "message": "Adaptive wetland map successfully generated",
                "filename": map_path,
                "adaptive_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "wetland_transparency": wetland_transparency,
                    "reasoning": reasoning,
                    "resolution_dpi": 300,
                    "coverage_area_sq_miles": coverage_area
                },
                "map_features": {
                    "includes_legend": True,
                    "includes_scale_bar": True,
                    "high_resolution": True,
                    "optimized_for_analysis": True
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate adaptive wetland map",
                "reasoning": reasoning,
                "suggested_buffer": buffer_miles
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during map generation: {str(e)}",
            "suggestion": "Map generation failed, but wetland data analysis was successful"
        }

def _create_regulatory_assessment(is_in_wetland: bool, wetlands_in_radius: List[Dict], 
                                wetland_results: Dict) -> Dict[str, Any]:
    """Create regulatory assessment based on wetland findings"""
    
    assessment = {
        "immediate_impact_risk": "Low",
        "permit_requirements": [],
        "regulatory_agencies": [],
        "buffer_considerations": [],
        "compliance_notes": []
    }
    
    if is_in_wetland:
        assessment["immediate_impact_risk"] = "High"
        assessment["permit_requirements"].append("Section 404 Clean Water Act permit likely required")
        assessment["permit_requirements"].append("State wetland permits may be required")
        assessment["regulatory_agencies"].extend(["US Army Corps of Engineers", "EPA", "State Environmental Agency"])
        assessment["compliance_notes"].append("Direct wetland impacts - comprehensive permitting process expected")
        
    elif wetlands_in_radius:
        # Assess based on proximity and wetland characteristics
        closest_distance = min([w['distance_miles'] for w in wetlands_in_radius])
        high_value_wetlands = [w for w in wetlands_in_radius if "High" in w['regulatory_significance']]
        
        if closest_distance <= 0.1:
            assessment["immediate_impact_risk"] = "High"
            assessment["buffer_considerations"].append("Wetlands within 500 feet - buffer requirements likely apply")
        elif closest_distance <= 0.25:
            assessment["immediate_impact_risk"] = "Medium-High"
            assessment["buffer_considerations"].append("Wetlands within 1,300 feet - buffer requirements may apply")
        elif closest_distance <= 0.5:
            assessment["immediate_impact_risk"] = "Medium"
            assessment["buffer_considerations"].append("Wetlands within 0.5 miles - consider buffer requirements")
        
        if high_value_wetlands:
            assessment["permit_requirements"].append("Proximity to jurisdictional wetlands - permits may be required")
            assessment["regulatory_agencies"].extend(["US Army Corps of Engineers", "State Environmental Agency"])
        
        assessment["compliance_notes"].append(f"Found {len(wetlands_in_radius)} wetlands within 0.5 miles")
        assessment["compliance_notes"].append("Recommend wetland delineation study for development projects")
    
    else:
        assessment["immediate_impact_risk"] = "Low"
        assessment["compliance_notes"].append("No wetlands identified within 0.5-mile radius")
        assessment["compliance_notes"].append("Standard environmental due diligence recommended")
    
    return assessment

def _generate_recommendations(is_in_wetland: bool, wetlands_in_radius: List[Dict], 
                            regulatory_assessment: Dict) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    
    recommendations = []
    
    if is_in_wetland:
        recommendations.extend([
            "🚨 IMMEDIATE ACTION: Coordinate point is within a wetland - development restrictions apply",
            "📋 Conduct professional wetland delineation study before any development",
            "⚖️ Consult with environmental attorney or consultant regarding permit requirements",
            "📞 Contact US Army Corps of Engineers for pre-application consultation",
            "🔍 Consider alternative site locations to avoid wetland impacts"
        ])
    
    elif wetlands_in_radius:
        closest_distance = min([w['distance_miles'] for w in wetlands_in_radius])
        
        if closest_distance <= 0.25:
            recommendations.extend([
                "⚠️ HIGH PRIORITY: Wetlands very close to site - detailed assessment required",
                "📋 Conduct professional wetland delineation and buffer study",
                "📞 Early consultation with regulatory agencies recommended"
            ])
        else:
            recommendations.extend([
                "📋 Conduct wetland assessment as part of environmental due diligence",
                "🔍 Consider wetland buffers in site planning and design"
            ])
        
        recommendations.extend([
            f"📏 {len(wetlands_in_radius)} wetlands identified within 0.5-mile radius",
            "🗺️ Use generated map for preliminary site planning",
            "📚 Review local and state wetland regulations"
        ])
    
    else:
        recommendations.extend([
            "✅ No immediate wetland concerns identified",
            "📋 Standard environmental assessment recommended for development projects",
            "🔍 Verify findings with site-specific studies for large projects"
        ])
    
    # Add general recommendations
    recommendations.extend([
        "💾 Detailed analysis results saved to logs/ directory",
        "🗺️ High-resolution map generated for documentation",
        "📞 Consult qualified environmental professionals for project-specific guidance"
    ])
    
    return recommendations

def _assess_regulatory_complexity(wetlands_in_radius: List[Dict]) -> str:
    """Assess overall regulatory complexity"""
    
    if not wetlands_in_radius:
        return "Low - No wetlands in immediate area"
    
    high_significance_count = len([w for w in wetlands_in_radius if "High" in w['regulatory_significance']])
    total_wetlands = len(wetlands_in_radius)
    closest_distance = min([w['distance_miles'] for w in wetlands_in_radius])
    
    if high_significance_count >= 3 or closest_distance <= 0.1:
        return "High - Multiple high-value wetlands or very close proximity"
    elif high_significance_count >= 1 or closest_distance <= 0.25:
        return "Medium-High - Jurisdictional wetlands nearby"
    elif total_wetlands >= 3 or closest_distance <= 0.5:
        return "Medium - Multiple wetlands in area"
    else:
        return "Low-Medium - Limited wetland presence"

# Export the tool for easy import
COMPREHENSIVE_WETLAND_TOOL = [analyze_wetland_location_with_map]

if __name__ == "__main__":
    print("🌿 Comprehensive Wetland Analysis Tool")
    print("=" * 60)
    print("This module provides a single comprehensive tool that:")
    print("✓ Analyzes if coordinate point is within a wetland")
    print("✓ Identifies wetlands within 0.5-mile radius")
    print("✓ Provides detailed wetland information and classifications")
    print("✓ Generates adaptive wetland map based on analysis")
    print("✓ Creates regulatory assessment and recommendations")
    print()
    print("Usage:")
    print("  from wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL")
    print("  # Use with LangGraph agents or ToolNode")
    print("=" * 60) 