#!/usr/bin/env python3
"""
Comprehensive NonAttainment Areas Analysis Tool

This tool provides complete air quality analysis by combining:
- EPA nonattainment areas data retrieval and analysis
- Professional PDF map generation with adaptive settings
- Detailed regulatory compliance assessment
- Organized output directory management
- Comprehensive recommendations and next steps

The tool integrates with the project's output directory management system
and provides structured results for LangGraph agents.
"""

import sys
import os
import json
import math
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

# Add NonAttainmentINFO to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'NonAttainmentINFO'))

from langchain_core.tools import tool
from NonAttainmentINFO.nonattainment_client import NonAttainmentAreasClient
from NonAttainmentINFO.generate_nonattainment_map_pdf import NonAttainmentMapGenerator
from output_directory_manager import get_output_manager

class NonAttainmentAnalysisInput(BaseModel):
    """Input schema for comprehensive nonattainment analysis"""
    longitude: float = Field(description="Longitude coordinate (decimal degrees)")
    latitude: float = Field(description="Latitude coordinate (decimal degrees)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location")

@tool("analyze_nonattainment_with_map", args_schema=NonAttainmentAnalysisInput)
def analyze_nonattainment_with_map(longitude: float, latitude: float, location_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive EPA nonattainment areas analysis tool that combines data querying and adaptive map generation.
    
    This tool performs a complete air quality assessment:
    
    1. **Location Analysis**: Determines if the coordinate point intersects with EPA nonattainment areas
    2. **Pollutant Assessment**: Identifies all affected pollutants and their violation status
    3. **Regulatory Analysis**: Provides detailed information about:
       - Current status (Nonattainment vs Maintenance)
       - Classification levels (Extreme, Serious, Moderate, etc.)
       - Design values and air quality measurements
       - NAAQS compliance status
    4. **Adaptive Map Generation**: Creates professional maps with optimal settings:
       - Automatic buffer sizing based on violation findings
       - Appropriate base map selection for air quality visualization
       - Color-coded pollutant layers with proper symbology
       - Professional legend and regulatory information
    5. **Compliance Assessment**: Evaluates Clean Air Act regulatory requirements
    
    Data Sources:
    - EPA Office of Air and Radiation (OAR)
    - Office of Air Quality Planning and Standards (OAQPS)
    - National Ambient Air Quality Standards (NAAQS) database
    
    Covers all EPA criteria pollutants:
    - Ozone (O₃) - 8-hour standards (2008, 2015)
    - Particulate Matter (PM2.5, PM10)
    - Carbon Monoxide (CO)
    - Sulfur Dioxide (SO₂)
    - Nitrogen Dioxide (NO₂)
    - Lead (Pb)
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere)
        latitude: Latitude coordinate (positive for northern hemisphere)
        location_name: Optional descriptive name for the location
        
    Returns:
        Dictionary containing:
        - location_analysis: Complete air quality violation analysis
        - violations_in_area: Detailed information about nonattainment areas
        - map_generation: Results of adaptive map generation
        - regulatory_assessment: Clean Air Act compliance implications
        - recommendations: Actionable recommendations based on findings
        - project_directory: Output directory information for generated files
    """
    
    if location_name is None:
        location_name = f"Air Quality Analysis at {latitude:.4f}, {longitude:.4f}"
    
    print(f"🌫️ Comprehensive nonattainment analysis for {location_name}")
    
    # Get the global output directory manager instance
    output_manager = get_output_manager()
    
    # Check if there's already a project directory from the comprehensive screening
    if not output_manager.current_project_dir:
        # Only create a new project directory if one doesn't exist
        project_name = f"NonAttainment_{location_name.replace(' ', '_').replace(',', '')}"
        output_manager.create_project_directory(custom_name=project_name)
        print(f"📁 Created new project directory for nonattainment analysis")
    else:
        print(f"📁 Using existing project directory: {output_manager.current_project_dir}")
    
    try:
        # Step 1: Analyze location for nonattainment areas
        print(f"🔍 Step 1: Analyzing EPA nonattainment areas...")
        client = NonAttainmentAreasClient()
        
        # Perform comprehensive analysis (active standards)
        result = client.analyze_location(longitude, latitude, include_revoked=False)
        
        if not result.query_success:
            return {
                "success": False,
                "error": f"EPA data query failed: {result.error_message}",
                "location": location_name,
                "coordinates": (longitude, latitude),
                "analysis_timestamp": result.analysis_timestamp,
                "project_directory": output_manager.get_project_info()
            }
        
        # Step 2: Get detailed summary and recommendations
        print(f"📊 Step 2: Generating regulatory assessment...")
        summary = client.get_area_summary(result)
        
        # Step 3: Determine violations in analysis area
        violations_in_area = []
        if result.has_nonattainment_areas:
            for area in result.nonattainment_areas:
                violation_info = {
                    "pollutant_name": area.pollutant_name,
                    "area_name": area.area_name,
                    "state": area.state_name,
                    "state_abbreviation": area.state_abbreviation,
                    "epa_region": area.epa_region,
                    "current_status": area.current_status,
                    "classification": area.classification,
                    "design_value": area.design_value,
                    "design_value_units": area.design_value_units,
                    "meets_naaqs": area.meets_naaqs,
                    "population_2020": area.population_2020,
                    "designation_date": area.designation_effective_date,
                    "attainment_date": area.statutory_attainment_date
                }
                violations_in_area.append(violation_info)
        
        # Step 4: Generate adaptive map
        print(f"🗺️ Step 3: Generating adaptive nonattainment map...")
        generator = NonAttainmentMapGenerator()
        
        # Use adaptive map generation for optimal settings
        map_filename = f"nonattainment_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        map_path = generator.generate_adaptive_nonattainment_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            analysis_result=result
        )
        
        # Determine map result
        map_result = {
            "success": map_path is not None,
            "filename": os.path.basename(map_path) if map_path else None,
            "full_path": map_path,
            "file_type": "PDF" if map_path and map_path.endswith('.pdf') else "HTML",
            "adaptive_settings": {
                "buffer_miles": 15.0 if result.has_nonattainment_areas else 50.0,
                "reasoning": "Detailed view for violations found" if result.has_nonattainment_areas else "Regional overview for clean air area"
            }
        }
        
        if not map_result["success"]:
            map_result["error"] = "Map generation failed - check EPA service availability"
        
        # Step 5: Create regulatory assessment
        print(f"⚖️ Step 4: Assessing regulatory implications...")
        regulatory_assessment = _create_regulatory_assessment(
            result.has_nonattainment_areas, violations_in_area, summary
        )
        
        # Step 6: Generate recommendations
        print(f"💡 Step 5: Generating recommendations...")
        recommendations = _generate_recommendations(
            result.has_nonattainment_areas, violations_in_area, regulatory_assessment
        )
        
        # Step 7: Save detailed results to files
        print(f"💾 Step 6: Saving analysis results...")
        
        # Save nonattainment data
        nonattainment_data_filename = f"nonattainment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        nonattainment_data_file = output_manager.get_file_path(nonattainment_data_filename, "data")
        
        with open(nonattainment_data_file, 'w') as f:
            json.dump({
                "location": location_name,
                "coordinates": {"longitude": longitude, "latitude": latitude},
                "analysis_timestamp": result.analysis_timestamp,
                "has_violations": result.has_nonattainment_areas,
                "total_areas": result.area_count,
                "violations_details": violations_in_area,
                "epa_summary": summary,
                "query_parameters": {
                    "include_revoked": False,
                    "buffer_meters": 0,
                    "pollutants": None
                }
            }, f, indent=2)
        
        # Save summary report
        summary_filename = f"nonattainment_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_file = output_manager.get_file_path(summary_filename, "reports")
        
        with open(summary_file, 'w') as f:
            json.dump({
                "location_analysis": {
                    "location": location_name,
                    "coordinates": (longitude, latitude),
                    "analysis_timestamp": result.analysis_timestamp,
                    "has_violations": result.has_nonattainment_areas,
                    "total_violations": len(violations_in_area),
                    "epa_data_sources": [
                        "EPA Office of Air and Radiation (OAR)",
                        "Office of Air Quality Planning and Standards (OAQPS)",
                        "National Ambient Air Quality Standards (NAAQS)"
                    ]
                },
                "violations_summary": {
                    "violations_count": len(violations_in_area),
                    "violations": violations_in_area
                },
                "regulatory_assessment": regulatory_assessment,
                "recommendations": recommendations,
                "map_generation": map_result
            }, f, indent=2)
        
        # Compile comprehensive results
        results = {
            "location_analysis": {
                "location": location_name,
                "coordinates": (longitude, latitude),
                "analysis_timestamp": result.analysis_timestamp,
                "has_violations": result.has_nonattainment_areas,
                "total_violations": len(violations_in_area),
                "epa_data_sources": [
                    "EPA Office of Air and Radiation (OAR)",
                    "Office of Air Quality Planning and Standards (OAQPS)",
                    "National Ambient Air Quality Standards (NAAQS)"
                ]
            },
            "violations_in_area": {
                "violations_count": len(violations_in_area),
                "violations": violations_in_area
            },
            "map_generation": map_result,
            "regulatory_assessment": regulatory_assessment,
            "recommendations": recommendations,
            "analysis_summary": {
                "air_quality_status": "Non-compliant" if result.has_nonattainment_areas else "Compliant",
                "pollutants_affected": list(set([v["pollutant_name"] for v in violations_in_area])) if violations_in_area else [],
                "regulatory_complexity": _assess_regulatory_complexity(violations_in_area),
                "next_steps": "Review recommendations and consult with EPA Regional Office if violations are present"
            },
            "project_directory": output_manager.get_project_info(),
            "files_generated": {
                "nonattainment_data_file": nonattainment_data_filename,
                "summary_file": summary_filename,
                "map_file": map_result.get("filename") if map_result.get("success") else None
            }
        }
        
        print(f"✅ Comprehensive nonattainment analysis completed successfully")
        
        if result.has_nonattainment_areas:
            print(f"⚠️  Found {len(violations_in_area)} air quality violation(s)")
            pollutants = list(set([v["pollutant_name"] for v in violations_in_area]))
            print(f"🌫️ Affected pollutants: {', '.join(pollutants)}")
        else:
            print(f"✅ Location meets all National Ambient Air Quality Standards")
        
        return results
        
    except Exception as e:
        print(f"❌ Error in nonattainment analysis: {e}")
        
        # Save error information
        error_filename = f"nonattainment_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        error_file = output_manager.get_file_path(error_filename, "logs")
        
        with open(error_file, 'w') as f:
            json.dump({
                "error": str(e),
                "location": location_name,
                "coordinates": (longitude, latitude),
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "nonattainment_areas"
            }, f, indent=2)
        
        return {
            "success": False,
            "error": str(e),
            "location": location_name,
            "coordinates": (longitude, latitude),
            "analysis_timestamp": datetime.now().isoformat(),
            "project_directory": output_manager.get_project_info(),
            "error_file": error_filename
        }

def _create_regulatory_assessment(has_violations: bool, violations: List[Dict], summary: Dict) -> Dict[str, Any]:
    """Create regulatory assessment based on nonattainment findings"""
    
    if not has_violations:
        return {
            "compliance_status": "Compliant",
            "regulatory_requirements": "No additional Clean Air Act requirements",
            "air_quality_status": "Meets all National Ambient Air Quality Standards (NAAQS)",
            "development_implications": "No air quality restrictions for development",
            "permit_requirements": "Standard air quality permits may apply for certain activities",
            "monitoring_requirements": "No special air quality monitoring required"
        }
    
    # Analyze violation characteristics
    pollutants = list(set([v["pollutant_name"] for v in violations]))
    statuses = list(set([v["current_status"] for v in violations]))
    classifications = list(set([v["classification"] for v in violations if v["classification"] != "Unknown"]))
    
    # Determine severity
    severity = "Low"
    if any("Extreme" in c for c in classifications):
        severity = "Extreme"
    elif any("Serious" in c for c in classifications):
        severity = "High"
    elif any("Moderate" in c for c in classifications):
        severity = "Moderate"
    
    return {
        "compliance_status": "Non-compliant",
        "violation_severity": severity,
        "pollutants_affected": pollutants,
        "status_types": statuses,
        "classification_levels": classifications,
        "regulatory_requirements": [
            "Subject to Clean Air Act nonattainment area regulations",
            "New Source Review (NSR) requirements may apply",
            "Emission offset requirements for major sources",
            "Enhanced monitoring and reporting requirements",
            "Conformity determinations for federal actions"
        ],
        "development_implications": [
            "Additional air quality analysis required for development",
            "Potential emission offset requirements",
            "Enhanced environmental review processes",
            "Possible restrictions on certain industrial activities"
        ],
        "permit_requirements": [
            "Enhanced air quality permits required",
            "Emission offset banking may be required",
            "Additional modeling and monitoring requirements",
            "Conformity analysis for federal funding"
        ],
        "epa_consultation": "Required for major development projects"
    }

def _generate_recommendations(has_violations: bool, violations: List[Dict], regulatory_assessment: Dict) -> List[str]:
    """Generate actionable recommendations based on nonattainment analysis"""
    
    recommendations = []
    
    if not has_violations:
        recommendations.extend([
            "✅ Location meets all National Ambient Air Quality Standards - no air quality restrictions",
            "📋 Standard air quality permits may still be required for certain development activities",
            "🔍 Monitor EPA designations as standards may change over time",
            "📞 Consult with state air quality agency for project-specific guidance"
        ])
        return recommendations
    
    # Violation-specific recommendations
    recommendations.append(
        "⚠️ Location is within EPA nonattainment areas - additional regulatory requirements apply"
    )
    
    pollutants = list(set([v["pollutant_name"] for v in violations]))
    if len(pollutants) > 1:
        recommendations.append(
            f"🌫️ Multiple pollutants affected ({len(pollutants)}) - comprehensive air quality strategy needed"
        )
    
    # Status-based recommendations
    nonattainment_areas = [v for v in violations if v["current_status"] == "Nonattainment"]
    maintenance_areas = [v for v in violations if v["current_status"] == "Maintenance"]
    
    if nonattainment_areas:
        recommendations.append(
            f"🚫 {len(nonattainment_areas)} active nonattainment area(s) - stringent emission controls required"
        )
    
    if maintenance_areas:
        recommendations.append(
            f"🔧 {len(maintenance_areas)} maintenance area(s) - continued compliance monitoring required"
        )
    
    # Severity-based recommendations
    severity = regulatory_assessment.get("violation_severity", "Low")
    if severity == "Extreme":
        recommendations.append(
            "🔴 Extreme nonattainment classification - most stringent controls and offset requirements"
        )
    elif severity == "High":
        recommendations.append(
            "🟠 Serious nonattainment classification - enhanced controls and monitoring required"
        )
    
    # General regulatory recommendations
    recommendations.extend([
        "📞 Contact EPA Regional Office for project consultation and compliance guidance",
        "📋 Review Clean Air Act New Source Review (NSR) requirements",
        "💰 Investigate emission offset requirements and banking options",
        "📊 Conduct detailed air quality impact analysis for development projects",
        "⚖️ Ensure conformity with State Implementation Plan (SIP) requirements",
        "🔍 Monitor for changes in nonattainment designations and standards"
    ])
    
    return recommendations

def _assess_regulatory_complexity(violations: List[Dict]) -> str:
    """Assess the regulatory complexity based on violations"""
    
    if not violations:
        return "Low - No air quality violations"
    
    # Count factors that increase complexity
    complexity_factors = 0
    
    # Multiple pollutants
    pollutants = list(set([v["pollutant_name"] for v in violations]))
    if len(pollutants) > 2:
        complexity_factors += 2
    elif len(pollutants) > 1:
        complexity_factors += 1
    
    # Nonattainment vs maintenance status
    nonattainment_count = len([v for v in violations if v["current_status"] == "Nonattainment"])
    if nonattainment_count > 0:
        complexity_factors += 2
    
    # Classification severity
    classifications = [v["classification"] for v in violations if v["classification"] != "Unknown"]
    if any("Extreme" in c for c in classifications):
        complexity_factors += 3
    elif any("Serious" in c for c in classifications):
        complexity_factors += 2
    elif any("Moderate" in c for c in classifications):
        complexity_factors += 1
    
    # Determine overall complexity
    if complexity_factors >= 5:
        return "Very High - Multiple severe violations with complex regulatory requirements"
    elif complexity_factors >= 3:
        return "High - Significant air quality violations requiring enhanced compliance"
    elif complexity_factors >= 1:
        return "Moderate - Some air quality violations with additional requirements"
    else:
        return "Low - Minor air quality considerations"

# Export the tool for easy import
COMPREHENSIVE_NONATTAINMENT_TOOL = analyze_nonattainment_with_map

def get_comprehensive_tool_description() -> str:
    """Get description of the comprehensive nonattainment tool"""
    return "Comprehensive EPA nonattainment areas analysis with adaptive map generation - provides complete air quality violation assessment, regulatory compliance analysis, and professional documentation"

if __name__ == "__main__":
    # Example usage
    print("🌫️ NonAttainment Areas Analysis Tool")
    print("=" * 50)
    
    # Test location: Los Angeles, CA (known nonattainment area)
    result = analyze_nonattainment_with_map(
        longitude=-118.2437,
        latitude=34.0522,
        location_name="Los Angeles, CA"
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"   Location: {result['location_analysis']['location']}")
    print(f"   Has Violations: {result['location_analysis']['has_violations']}")
    if result['location_analysis']['has_violations']:
        print(f"   Total Violations: {result['location_analysis']['total_violations']}")
        print(f"   Pollutants: {', '.join(result['analysis_summary']['pollutants_affected'])}")
    print(f"   Regulatory Complexity: {result['analysis_summary']['regulatory_complexity']}")
    print(f"   Map Generated: {result['map_generation']['success']}") 