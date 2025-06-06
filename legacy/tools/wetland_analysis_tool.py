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

All files are organized into a custom project directory structure.

Tool:
- analyze_wetland_location_with_map: Complete wetland analysis with adaptive map generation
"""

import sys
import os
import math
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic.v1 import BaseModel, Field

# Add WetlandsINFO directory to path
wetlands_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'WetlandsINFO')
sys.path.append(wetlands_dir)

from langchain_core.tools import tool
from query_wetland_location import WetlandLocationAnalyzer, save_results_to_file
from generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3
from output_directory_manager import get_output_manager


class WetlandAnalysisInput(BaseModel):
    """Input schema for comprehensive wetland analysis"""
    longitude: float = Field(..., description="Longitude coordinate (e.g., -66.199399 for Puerto Rico)")
    latitude: float = Field(..., description="Latitude coordinate (e.g., 18.408303 for Puerto Rico)")
    location_name: Optional[str] = Field(
        default=None,
        description="Optional descriptive name for the location (e.g., 'Bayamón, Puerto Rico')"
    )


@tool("analyze_wetland_location_with_map", args_schema=WetlandAnalysisInput)
def analyze_wetland_location_with_map(
    longitude: float,
    latitude: float,
    location_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive wetland analysis tool that combines data querying and adaptive map generation.
    """
    if location_name is None:
        location_name = f"Wetland Analysis at ({longitude}, {latitude})"

    print(f"🌿 Starting comprehensive wetland analysis for {location_name}")

    # Get or create project directory
    output_manager = get_output_manager()
    if not output_manager.current_project_dir:
        project_dir = output_manager.create_project_directory(
            location_name=location_name,
            coordinates=(longitude, latitude)
        )
        print(f"📁 Created project directory: {project_dir}")
    else:
        project_dir = output_manager.current_project_dir
        print(f"📁 Using existing project directory: {project_dir}")

    try:
        # Step 1: Perform wetland data analysis
        print("🔍 Step 1: Analyzing wetland data...")
        analyzer = WetlandLocationAnalyzer()
        wetland_results = analyzer.analyze_location(longitude, latitude, location_name)
        # (wetland_results must include keys: is_in_wetland, wetlands_at_location, nearest_wetlands,
        #  query_time, search_summary, analysis)

        # Save detailed results to logs
        logs_dir = output_manager.get_subdirectory("logs")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{longitude}_{latitude}".replace('-', 'neg').replace('.', 'p')
        wetland_data_file = os.path.join(logs_dir, f"wetland_analysis_{coords}_{timestamp}.json")
        with open(wetland_data_file, 'w') as f:
            json.dump(wetland_results, f, indent=2, default=str)
        print(f"💾 Wetland analysis data saved to: {wetland_data_file}")

        # Step 2: Process wetlands within 0.5-mile radius
        print("📏 Step 2: Processing wetlands within 0.5-mile radius...")
        wetlands_in_radius: List[Dict[str, Any]] = []
        is_in_wetland = wetland_results.get('is_in_wetland', False)

        if is_in_wetland:
            for wet in wetland_results.get('wetlands_at_location', []):
                wetlands_in_radius.append(_extract_wetland_info(wet, 0.0, "At location"))

        for nearby in wetland_results.get('nearest_wetlands', []):
            if nearby.get('distance_miles', float('inf')) <= 0.5:
                wetlands_in_radius.append(
                    _extract_wetland_info(
                        nearby.get('wetland', {}),
                        nearby['distance_miles'],
                        nearby.get('bearing', 'Unknown')
                    )
                )

        # Step 3: Generate adaptive map
        print("🗺️  Step 3: Generating adaptive wetland map...")
        map_generator = WetlandMapGeneratorV3()
        map_result = _generate_adaptive_map(
            longitude, latitude, location_name,
            wetland_results, analyzer, map_generator, output_manager
        )

        # Step 4: Create regulatory assessment
        print("⚖️  Step 4: Creating regulatory assessment...")
        regulatory_assessment = _create_regulatory_assessment(
            is_in_wetland, wetlands_in_radius, wetland_results
        )

        # Step 5: Generate recommendations
        print("💡 Step 5: Generating recommendations...")
        recommendations = _generate_recommendations(
            is_in_wetland, wetlands_in_radius, regulatory_assessment
        )

        # Save summary JSON
        data_dir = output_manager.get_subdirectory("data")
        summary_data = {
            "location_analysis": {
                "location": location_name,
                "coordinates": (longitude, latitude),
                "query_time": wetland_results.get('query_time'),
                "is_in_wetland": is_in_wetland,
                "total_wetlands_found": len(wetlands_in_radius)
            },
            "wetlands_in_radius": wetlands_in_radius,
            "regulatory_assessment": regulatory_assessment,
            "recommendations": recommendations
        }
        summary_file = os.path.join(data_dir, f"wetland_summary_{coords}_{timestamp}.json")
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        print(f"📋 Wetland summary saved to: {summary_file}")

        # Compile full results
        results = {
            "location_analysis": {
                "location": location_name,
                "coordinates": (longitude, latitude),
                "query_time": wetland_results.get('query_time'),
                "is_in_wetland": is_in_wetland,
                "total_wetlands_found": len(wetlands_in_radius),
                "search_radius_used": wetland_results.get('search_summary', {}).get('search_radius_used'),
                "data_sources": [
                    "USFWS NWI",
                    "EPA RIBITS",
                    "EPA NHD",
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
                "environmental_significance": wetland_results.get('analysis', {}).get('environmental_significance'),
                "key_wetland_types": list({w["wetland_type"] for w in wetlands_in_radius}),
                "regulatory_complexity": _assess_regulatory_complexity(wetlands_in_radius),
                "next_steps": "Review recommendations and consider professional consultation"
            },
            "project_directory": output_manager.get_project_info(),
            "files_generated": {
                "wetland_data_file": wetland_data_file,
                "summary_file": summary_file,
                "map_file": map_result.get("filename")
            }
        }

        print("✅ Comprehensive wetland analysis completed successfully")
        print(f"📁 All files saved to project directory: {project_dir}")
        return results

    except Exception as e:
        error = str(e)
        print(f"❌ Error during comprehensive analysis: {error}")
        return {
            "location_analysis": {"error": error},
            "wetlands_in_radius": {"error": error},
            "map_generation": {"success": False, "error": error},
            "regulatory_assessment": {"status": "failed"},
            "recommendations": ["Verify coordinates and try again"],
            "analysis_summary": {"status": "Failed", "error": error},
            "project_directory": output_manager.get_project_info() if output_manager.current_project_dir else {"error": "No project directory"}
        }


def _extract_wetland_info(wetland: Any, distance_miles: float, bearing: str) -> Dict[str, Any]:
    """Extract standardized wetland information"""
    if isinstance(wetland, dict):
        info = {
            "wetland_type": wetland.get('wetland_type', 'Unknown'),
            "nwi_code": wetland.get('nwi_code', 'Unknown'),
            "area_acres": wetland.get('area_acres', 0.0),
        }
    else:
        info = {
            "wetland_type": getattr(wetland, 'wetland_type', 'Unknown'),
            "nwi_code": getattr(wetland, 'nwi_code', 'Unknown'),
            "area_acres": getattr(wetland, 'area_acres', 0.0),
        }
    info.update({
        "distance_miles": distance_miles,
        "bearing": bearing,
        "regulatory_significance": _assess_wetland_regulatory_significance(
            info["nwi_code"], info["area_acres"]
        ),
        "source": "NWI"
    })
    return info


def _assess_wetland_regulatory_significance(nwi_code: str, area_acres: float) -> str:
    """Assess regulatory significance of a wetland"""
    if "PUB" in nwi_code or "POW" in nwi_code:
        return "High - Open water/pond, likely jurisdictional"
    if "PEM" in nwi_code:
        return "High - Emergent wetland"
    if "PSS" in nwi_code:
        return "High - Scrub-shrub wetland"
    if "PFO" in nwi_code:
        return "High - Forested wetland"
    if area_acres > 1.0:
        return "Medium-High - Large wetland"
    if area_acres > 0.1:
        return "Medium - Moderate wetland"
    return "Low-Medium - Small wetland"


def _generate_adaptive_map(
    longitude: float,
    latitude: float,
    location_name: str,
    wetland_results: Dict[str, Any],
    analyzer: WetlandLocationAnalyzer,
    map_generator: WetlandMapGeneratorV3,
    output_manager
) -> Dict[str, Any]:
    """Generate adaptive map based on wetland analysis"""
    try:
        if wetland_results.get('is_in_wetland'):
            buffer_miles = 0.5
            transparency = 0.75
            base_map = "World_Imagery"
            reasoning = "Wetlands at exact location → detailed 0.5-mi buffer"
        else:
            search_radius = wetland_results.get('search_summary', {}).get('search_radius_used', 2.0)
            nearest = wetland_results.get('nearest_wetlands', [])
            if nearest:
                dist = nearest[0].get('distance_miles', search_radius)
                if dist <= 0.5:
                    buffer_miles = 1.0
                    reasoning = f"Wetlands within 0.5 mi → 1.0-mi buffer"
                else:
                    buffer_miles = min(dist + 1.0, 3.0)
                    reasoning = f"Nearest wetland at {dist} mi → {buffer_miles}-mi buffer"
            else:
                buffer_miles = 2.0
                reasoning = f"No wetlands within {search_radius} mi → 2.0-mi regional view"
            transparency = 0.8
            base_map = "World_Imagery" if nearest else "World_Topo_Map"

        # Build output path
        maps_dir = output_manager.get_subdirectory("maps")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = location_name.replace(' ', '_').replace(',', '')
        filename = f"wetland_map_{safe}_{ts}.png"
        out_path = os.path.join(maps_dir, filename)

        print(f"🎨 Map: buffer={buffer_miles} mi, base={base_map}, trans={transparency}")
        generated = map_generator.generate_wetland_map_pdf(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=buffer_miles,
            base_map=base_map,
            dpi=300,
            output_size=(1224, 792),
            include_legend=True,
            wetland_transparency=transparency,
            output_format="PNG",
            output_filename=filename
        )

        if generated and generated != out_path:
            try:
                shutil.move(generated, out_path)
            except:
                out_path = generated

        if out_path:
            area = round(math.pi * buffer_miles**2, 2)
            return {
                "success": True,
                "filename": out_path,
                "adaptive_settings": {
                    "buffer_miles": buffer_miles,
                    "base_map": base_map,
                    "wetland_transparency": transparency,
                    "reasoning": reasoning,
                    "coverage_area_sq_miles": area
                }
            }

        return {"success": False, "message": "No map generated"}

    except Exception as e:
        return {"success": False, "message": f"Map generation error: {e}"}


def _create_regulatory_assessment(
    is_in_wetland: bool,
    wetlands_in_radius: List[Dict[str, Any]],
    wetland_results: Dict[str, Any]
) -> Dict[str, Any]:
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
        assessment["permit_requirements"] = [
            "Section 404 CWA permit likely required",
            "State wetland permits may be required"
        ]
        assessment["regulatory_agencies"] = [
            "US Army Corps of Engineers", "EPA", "State Environmental Agency"
        ]
        assessment["compliance_notes"].append("Direct wetland impacts expected")
    elif wetlands_in_radius:
        d = min(w["distance_miles"] for w in wetlands_in_radius)
        if d <= 0.1:
            assessment["buffer_considerations"].append("Wetlands within 500 ft")
            assessment["immediate_impact_risk"] = "High"
        elif d <= 0.5:
            assessment["buffer_considerations"].append("Wetlands within 0.5 mi")
            assessment["immediate_impact_risk"] = "Medium"
        assessment["permit_requirements"].append("Proximity to jurisdictional wetlands")
        assessment["regulatory_agencies"].append("USACE")
        assessment["compliance_notes"].append(f"{len(wetlands_in_radius)} wetland(s) nearby")
    else:
        assessment["compliance_notes"].append("No wetlands within 0.5 mi")

    return assessment


def _generate_recommendations(
    is_in_wetland: bool,
    wetlands_in_radius: List[Dict[str, Any]],
    regulatory_assessment: Dict[str, Any]
) -> List[str]:
    """Generate actionable recommendations based on analysis"""
    recs: List[str] = []
    if is_in_wetland:
        recs += [
            "🚨 Immediate action required: site within wetland",
            "📋 Professional wetland delineation study",
            "⚖️ Consult USACE for Section 404 pre-application",
        ]
    elif wetlands_in_radius:
        recs.append("📋 Conduct wetland buffer assessment")
    else:
        recs.append("✅ No immediate wetland concerns")

    recs += [
        "💾 Detailed logs saved",
        "🗺️ Map generated for documentation",
        "📞 Consult environmental professionals"
    ]
    return recs


def _assess_regulatory_complexity(wetlands_in_radius: List[Dict[str, Any]]) -> str:
    """Assess overall regulatory complexity"""
    if not wetlands_in_radius:
        return "Low - No nearby wetlands"
    high = sum(1 for w in wetlands_in_radius if "High" in w.get("regulatory_significance", ""))
    closest = min(w["distance_miles"] for w in wetlands_in_radius)
    if high >= 3 or closest <= 0.1:
        return "High"
    if high >= 1 or closest <= 0.5:
        return "Medium"
    return "Low-Medium"


# Export the tool
COMPREHENSIVE_WETLAND_TOOL = [analyze_wetland_location_with_map]


if __name__ == "__main__":
    print("🌿 Comprehensive Wetland Analysis Tool")
    print("=" * 60)
    print("Usage example:")
    print("  from wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL")
    print("  # Call using your LangGraph agent or interactively")
    print("=" * 60)
