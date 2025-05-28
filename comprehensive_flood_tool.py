#!/usr/bin/env python3
"""
Comprehensive FEMA Flood Tool for LangGraph Agents

This module provides a single comprehensive tool that:
1. Generates all three FEMA reports (FIRMette, Preliminary Comparison, ABFE)
2. Automatically merges all generated PDFs into a single comprehensive report
3. Retrieves detailed flood information including:
   - Floodplain information
   - FIRM panel details
   - Flood zone designations
   - Base flood elevations
   - Effective dates
   - Political jurisdictions

This tool combines all flood data operations into a single comprehensive analysis.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic.v1 import BaseModel, Field
import asyncio
import concurrent.futures

# PDF merging imports
try:
    from PyPDF2 import PdfMerger, PdfReader
    PDF_MERGE_AVAILABLE = True
except ImportError:
    try:
        from pypdf import PdfMerger, PdfReader
        PDF_MERGE_AVAILABLE = True
    except ImportError:
        PDF_MERGE_AVAILABLE = False
        print("⚠️  PDF merging not available - install PyPDF2 or pypdf for PDF merging functionality")

# Add FloodINFO to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'FloodINFO'))

from langchain_core.tools import tool
from query_coordinates_data import query_coordinate_data, save_results_to_file, extract_panel_information
from firmette_client import FEMAFIRMetteClient
from preliminary_comparison_client import FEMAPreliminaryComparisonClient
from abfe_client import FEMAABFEClient
from output_directory_manager import get_output_manager

# Remove the old output directory creation
# os.makedirs('output', exist_ok=True)

class ComprehensiveFloodInput(BaseModel):
    """Input schema for comprehensive flood analysis"""
    longitude: float = Field(description="Longitude coordinate (e.g., -66.150906 for Puerto Rico)")
    latitude: float = Field(description="Latitude coordinate (e.g., 18.434059 for Puerto Rico)")
    location_name: Optional[str] = Field(default=None, description="Optional descriptive name for the location (e.g., 'Cataño, Puerto Rico')")
    generate_reports: bool = Field(default=True, description="Whether to generate PDF reports (FIRMette, Preliminary Comparison, ABFE)")
    include_abfe: bool = Field(default=True, description="Whether to include ABFE data (may not be available for all locations)")
    merge_pdfs: bool = Field(default=True, description="Whether to merge all generated PDFs into a single comprehensive report")

# FloodInformation class removed - not needed for tool definition

@tool("comprehensive_flood_analysis", args_schema=ComprehensiveFloodInput)
def comprehensive_flood_analysis(
    longitude: float, 
    latitude: float, 
    location_name: Optional[str] = None,
    generate_reports: bool = True,
    include_abfe: bool = True,
    merge_pdfs: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive FEMA flood analysis tool that generates all reports and extracts detailed flood information.
    
    This tool performs a complete flood analysis including:
    1. Querying comprehensive FEMA flood data
    2. Generating FIRMette (FIRM) report
    3. Generating Preliminary Comparison (pFIRM) report  
    4. Generating ABFE map (if data available)
    5. Merging all PDFs into a single comprehensive report
    6. Extracting structured flood information:
       - Floodplain information and identifiers
       - FIRM panel details and numbers
       - Flood zone designations (A, AE, X, VE, etc.)
       - Base flood elevations
       - Effective dates
       - Political jurisdictions and community information
    
    All files are organized into a custom project directory structure.
    
    Args:
        longitude: Longitude coordinate (negative for western hemisphere)
        latitude: Latitude coordinate (positive for northern hemisphere)
        location_name: Optional descriptive name for the location
        generate_reports: Whether to generate PDF reports (default: True)
        include_abfe: Whether to include ABFE analysis (default: True)
        merge_pdfs: Whether to merge all PDFs into a single comprehensive report (default: True)
        
    Returns:
        Dictionary containing:
        - flood_information: Structured flood data (floodplain, panel, zone, elevation, dates)
        - reports_generated: Status and files for each report type
        - raw_data_summary: Summary of all FEMA data found
        - analysis_metadata: Query details and timestamps
        - project_directory: Information about the custom output directory
    """
    
    if location_name is None:
        location_name = f"({longitude}, {latitude})"
    
    print(f"🌊 Starting comprehensive flood analysis for {location_name}")
    
    # Get or create project directory
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
    
    # Initialize result structure
    result = {
        "analysis_metadata": {
            "location": location_name,
            "coordinates": {"longitude": longitude, "latitude": latitude},
            "analysis_time": datetime.now().isoformat(),
            "reports_requested": generate_reports,
            "abfe_requested": include_abfe,
            "merge_pdfs_requested": merge_pdfs
        },
        "flood_information": {
            "current_effective": {},
            "preliminary": {},
            "summary": {}
        },
        "reports_generated": {
            "firmette": {"requested": generate_reports, "success": False},
            "preliminary_comparison": {"requested": generate_reports, "success": False},
            "abfe_map": {"requested": generate_reports and include_abfe, "success": False}
        },
        "raw_data_summary": {},
        "project_directory": output_manager.get_project_info(),
        "errors": []
    }
    
    try:
        # Step 1: Query comprehensive flood data
        print("📊 Step 1: Querying comprehensive FEMA flood data...")
        flood_data = query_coordinate_data(longitude, latitude, location_name)
        
        # Save flood data to project logs directory
        logs_dir = output_manager.get_subdirectory("logs")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        coords = f"{longitude}_{latitude}".replace('-', 'neg').replace('.', 'p')
        flood_data_file = os.path.join(logs_dir, f"flood_data_{coords}_{timestamp}.json")
        
        import json
        with open(flood_data_file, 'w') as f:
            json.dump(flood_data, f, indent=2, default=str)
        print(f"💾 Flood data saved to: {flood_data_file}")
        
        # Extract structured panel information
        panel_info = extract_panel_information(flood_data)
        
        # Save panel info to project data directory
        data_dir = output_manager.get_subdirectory("data")
        panel_info_file = os.path.join(data_dir, f"panel_info_{coords}_{timestamp}.json")
        with open(panel_info_file, 'w') as f:
            json.dump(panel_info, f, indent=2, default=str)
        print(f"📋 Panel information saved to: {panel_info_file}")
        
        # Store raw data summary
        result["raw_data_summary"] = {
            "services_with_data": flood_data["summary"]["services_with_data"],
            "total_features_found": flood_data["summary"]["total_features_found"],
            "puerto_rico_data_confirmed": flood_data["summary"]["puerto_rico_data_confirmed"],
            "panel_info_file_generated": True,
            "flood_data_file": flood_data_file,
            "panel_info_file": panel_info_file
        }
        
        # Step 2: Extract structured flood information
        print("🔍 Step 2: Extracting structured flood information...")
        extracted_info = _extract_flood_information(panel_info)
        result["flood_information"] = extracted_info
        
        # Step 3: Generate reports if requested
        if generate_reports:
            print("📄 Step 3: Generating flood reports...")
            
            # Use concurrent execution for faster report generation
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                
                # Submit FIRMette generation
                futures['firmette'] = executor.submit(_generate_firmette_safe, longitude, latitude, location_name, output_manager)
                
                # Submit Preliminary Comparison generation
                futures['preliminary_comparison'] = executor.submit(_generate_preliminary_safe, longitude, latitude, location_name, output_manager)
                
                # Submit ABFE generation if requested
                if include_abfe:
                    futures['abfe_map'] = executor.submit(_generate_abfe_safe, longitude, latitude, location_name, output_manager)
                
                # Collect results
                for report_type, future in futures.items():
                    try:
                        report_result = future.result(timeout=120)  # 2 minute timeout per report
                        result["reports_generated"][report_type].update(report_result)
                    except Exception as e:
                        result["reports_generated"][report_type]["error"] = str(e)
                        result["errors"].append(f"{report_type} generation failed: {str(e)}")
        
        # Step 4: Merge PDFs if requested and reports were generated
        if generate_reports and merge_pdfs:
            print("📄 Step 4: Merging generated PDFs...")
            merge_result = _merge_generated_pdfs(result, location_name, output_manager)
            result["pdf_merge"] = merge_result
        else:
            result["pdf_merge"] = {"requested": False, "success": False, "message": "PDF merging not requested"}
        
        # Step 5: Generate summary
        print("📋 Step 5: Generating analysis summary...")
        result["analysis_summary"] = _generate_analysis_summary(result)
        
        print("✅ Comprehensive flood analysis completed!")
        print(f"📁 All files saved to project directory: {project_dir}")
        return result
        
    except Exception as e:
        error_msg = f"Comprehensive flood analysis failed: {str(e)}"
        result["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        return result

def _extract_flood_information(panel_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured flood information from panel data"""
    
    extracted = {
        "current_effective": {
            "floodplain_data": [],
            "firm_panels": [],
            "flood_zones": [],
            "political_jurisdictions": [],
            "summary": {
                "primary_flood_zone": None,
                "primary_base_flood_elevation": None,
                "primary_firm_panel": None,
                "primary_effective_date": None,
                "primary_floodplain_id": None,
                "region": None,
                "dfirm_id": None,
                "community_id": None
            }
        },
        "preliminary": {
            "floodplain_data": [],
            "firm_panels": [],
            "flood_zones": [],
            "political_jurisdictions": [],
            "has_preliminary_data": False,
            "summary": {
                "changes_detected": False,
                "new_flood_zone": None,
                "new_base_flood_elevation": None,
                "new_firm_panel": None,
                "new_effective_date": None
            }
        },
        "overall_summary": {
            "data_available": False,
            "location_in_floodplain": False,
            "flood_insurance_required": False,
            "preliminary_changes_pending": False,
            "primary_identifiers": {}
        }
    }
    
    # Process current effective data
    current_data = panel_info.get("current_effective_data", {})
    
    # Extract floodplain information (from political jurisdictions and panel data)
    for jurisdiction in current_data.get("political_jurisdictions", []):
        floodplain_entry = {
            "floodplain_id": jurisdiction.get("political_area_id"),
            "floodplain_name": jurisdiction.get("jurisdiction_name_1") or jurisdiction.get("jurisdiction_name_2"),
            "region": jurisdiction.get("region"),
            "state_fips": jurisdiction.get("state_fips"),
            "community_id": jurisdiction.get("community_id"),
            "effective_date": jurisdiction.get("effective_date"),
            "dfirm_id": jurisdiction.get("dfirm_id")
        }
        extracted["current_effective"]["floodplain_data"].append(floodplain_entry)
    
    # Extract FIRM panel information
    for panel in current_data.get("panel_information", []):
        panel_entry = {
            "firm_panel": panel.get("firm_panel"),
            "panel_number": panel.get("panel_number"),
            "panel_suffix": panel.get("panel_suffix"),
            "panel_type": panel.get("panel_type"),
            "dfirm_id": panel.get("dfirm_id"),
            "effective_date": panel.get("effective_date"),
            "region": panel.get("region"),
            "state_fips": panel.get("state_fips"),
            "community_id": panel.get("community_id"),
            "floodplain_number": panel.get("floodplain_number")
        }
        extracted["current_effective"]["firm_panels"].append(panel_entry)
    
    # Extract flood zone information
    for zone in current_data.get("flood_zones", []):
        zone_entry = {
            "flood_zone": zone.get("flood_zone"),
            "base_flood_elevation": zone.get("base_flood_elevation"),
            "effective_date": zone.get("effective_date"),
            "region": zone.get("region"),
            "dfirm_id": zone.get("dfirm_id"),
            "firm_panel": zone.get("firm_panel"),
            "community_id": zone.get("community_id")
        }
        extracted["current_effective"]["flood_zones"].append(zone_entry)
    
    # Extract political jurisdictions
    extracted["current_effective"]["political_jurisdictions"] = current_data.get("political_jurisdictions", [])
    
    # Process preliminary data
    preliminary_data = panel_info.get("preliminary_data", {})
    extracted["preliminary"]["has_preliminary_data"] = preliminary_data.get("has_preliminary_data", False)
    
    if extracted["preliminary"]["has_preliminary_data"]:
        # Extract preliminary floodplain information
        for jurisdiction in preliminary_data.get("political_jurisdictions", []):
            floodplain_entry = {
                "floodplain_id": jurisdiction.get("political_area_id"),
                "floodplain_name": jurisdiction.get("jurisdiction_name_1") or jurisdiction.get("jurisdiction_name_2"),
                "region": jurisdiction.get("region"),
                "state_fips": jurisdiction.get("state_fips"),
                "community_id": jurisdiction.get("community_id"),
                "effective_date": jurisdiction.get("effective_date"),
                "dfirm_id": jurisdiction.get("dfirm_id")
            }
            extracted["preliminary"]["floodplain_data"].append(floodplain_entry)
        
        # Extract preliminary FIRM panels
        extracted["preliminary"]["firm_panels"] = preliminary_data.get("panel_information", [])
        
        # Extract preliminary flood zones
        extracted["preliminary"]["flood_zones"] = preliminary_data.get("flood_zones", [])
        
        # Extract preliminary political jurisdictions
        extracted["preliminary"]["political_jurisdictions"] = preliminary_data.get("political_jurisdictions", [])
    
    # Generate primary summaries
    _generate_primary_summaries(extracted)
    
    # Generate overall summary
    _generate_overall_summary(extracted)
    
    return extracted

def _generate_primary_summaries(extracted: Dict[str, Any]):
    """Generate primary summary information from extracted data"""
    
    current = extracted["current_effective"]
    
    # Find primary flood zone (first non-X zone, or first zone if all are X)
    primary_zone = None
    primary_bfe = None
    for zone in current["flood_zones"]:
        if zone["flood_zone"] and zone["flood_zone"] != "X":
            primary_zone = zone["flood_zone"]
            primary_bfe = zone["base_flood_elevation"]
            break
    
    if not primary_zone and current["flood_zones"]:
        # Use first zone if no non-X zones found
        first_zone = current["flood_zones"][0]
        primary_zone = first_zone["flood_zone"]
        primary_bfe = first_zone["base_flood_elevation"]
    
    # Find primary FIRM panel
    primary_panel = None
    if current["firm_panels"]:
        panel = current["firm_panels"][0]
        primary_panel = panel.get("firm_panel") or panel.get("panel_number")
    
    # Find primary effective date
    primary_date = None
    if current["flood_zones"]:
        primary_date = current["flood_zones"][0].get("effective_date")
    elif current["firm_panels"]:
        primary_date = current["firm_panels"][0].get("effective_date")
    
    # Find primary floodplain ID
    primary_floodplain = None
    if current["floodplain_data"]:
        primary_floodplain = current["floodplain_data"][0].get("floodplain_id")
    elif current["firm_panels"]:
        primary_floodplain = current["firm_panels"][0].get("floodplain_number")
    
    # Find region and identifiers
    region = None
    dfirm_id = None
    community_id = None
    
    for data_list in [current["flood_zones"], current["firm_panels"], current["floodplain_data"]]:
        if data_list:
            item = data_list[0]
            if not region:
                region = item.get("region")
            if not dfirm_id:
                dfirm_id = item.get("dfirm_id")
            if not community_id:
                community_id = item.get("community_id")
    
    # Update summary
    current["summary"].update({
        "primary_flood_zone": primary_zone,
        "primary_base_flood_elevation": primary_bfe,
        "primary_firm_panel": primary_panel,
        "primary_effective_date": primary_date,
        "primary_floodplain_id": primary_floodplain,
        "region": region,
        "dfirm_id": dfirm_id,
        "community_id": community_id
    })
    
    # Check for preliminary changes
    preliminary = extracted["preliminary"]
    if preliminary["has_preliminary_data"]:
        preliminary["summary"]["changes_detected"] = True
        
        # Find new flood zone
        if preliminary["flood_zones"]:
            new_zone = preliminary["flood_zones"][0]
            preliminary["summary"]["new_flood_zone"] = new_zone.get("flood_zone")
            preliminary["summary"]["new_base_flood_elevation"] = new_zone.get("base_flood_elevation")
            preliminary["summary"]["new_effective_date"] = new_zone.get("effective_date")
        
        # Find new FIRM panel
        if preliminary["firm_panels"]:
            new_panel = preliminary["firm_panels"][0]
            preliminary["summary"]["new_firm_panel"] = new_panel.get("firm_panel") or new_panel.get("panel_number")

def _generate_overall_summary(extracted: Dict[str, Any]):
    """Generate overall summary of flood information"""
    
    current = extracted["current_effective"]
    preliminary = extracted["preliminary"]
    
    # Check if data is available
    data_available = (len(current["flood_zones"]) > 0 or 
                     len(current["firm_panels"]) > 0 or 
                     len(current["floodplain_data"]) > 0)
    
    # Check if location is in floodplain
    in_floodplain = False
    insurance_required = False
    
    primary_zone = current["summary"]["primary_flood_zone"]
    if primary_zone:
        # Zones A, AE, AH, AO, AR, A99, V, VE require flood insurance
        high_risk_zones = ["A", "AE", "AH", "AO", "AR", "A99", "V", "VE"]
        if any(primary_zone.startswith(zone) for zone in high_risk_zones):
            in_floodplain = True
            insurance_required = True
    
    # Primary identifiers
    primary_identifiers = {
        "flood_zone": primary_zone,
        "base_flood_elevation": current["summary"]["primary_base_flood_elevation"],
        "firm_panel": current["summary"]["primary_firm_panel"],
        "effective_date": current["summary"]["primary_effective_date"],
        "floodplain_id": current["summary"]["primary_floodplain_id"],
        "region": current["summary"]["region"],
        "dfirm_id": current["summary"]["dfirm_id"],
        "community_id": current["summary"]["community_id"]
    }
    
    extracted["overall_summary"] = {
        "data_available": data_available,
        "location_in_floodplain": in_floodplain,
        "flood_insurance_required": insurance_required,
        "preliminary_changes_pending": preliminary["has_preliminary_data"],
        "primary_identifiers": primary_identifiers
    }

def _generate_firmette_safe(longitude: float, latitude: float, location_name: str, output_manager) -> Dict[str, Any]:
    """Safely generate FIRMette report with error handling"""
    try:
        client = FEMAFIRMetteClient()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = os.path.join(output_manager.get_subdirectory("reports"), f"firmette_{safe_name}_{timestamp}.pdf")
        
        success, result, job_id = client.generate_firmette_via_msc(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if success and client.download_firmette(result, filename):
            return {
                "success": True,
                "filename": filename,
                "url": result,
                "job_id": job_id,
                "message": "FIRMette successfully generated"
            }
        else:
            return {
                "success": False,
                "message": f"FIRMette generation failed: {result}",
                "url": result if success else None,
                "job_id": job_id if success else None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"FIRMette generation error: {str(e)}"
        }

def _generate_preliminary_safe(longitude: float, latitude: float, location_name: str, output_manager) -> Dict[str, Any]:
    """Safely generate Preliminary Comparison report with error handling"""
    try:
        client = FEMAPreliminaryComparisonClient()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = os.path.join(output_manager.get_subdirectory("reports"), f"preliminary_comparison_{safe_name}_{timestamp}.pdf")
        
        success, result, job_id = client.generate_comparison_report(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if success and client.download_comparison_report(result, filename):
            return {
                "success": True,
                "filename": filename,
                "url": result,
                "job_id": job_id,
                "message": "Preliminary Comparison report successfully generated"
            }
        else:
            return {
                "success": False,
                "message": f"Preliminary Comparison generation failed: {result}",
                "url": result if success else None,
                "job_id": job_id if success else None
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Preliminary Comparison generation error: {str(e)}"
        }

def _generate_abfe_safe(longitude: float, latitude: float, location_name: str, output_manager) -> Dict[str, Any]:
    """Safely generate ABFE map with error handling - always generates a map with point location"""
    try:
        client = FEMAABFEClient()
        
        # First check if ABFE data is available
        abfe_summary = client.get_abfe_summary(longitude, latitude, location_name)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        filename = os.path.join(output_manager.get_subdirectory("reports"), f"abfe_map_{safe_name}_{timestamp}.pdf")
        
        # Determine map parameters based on data availability
        if not abfe_summary['abfe_data_available']:
            # No ABFE data - generate larger area map with point marker
            buffer_miles = 2.0  # Larger radius for context
            map_title = f"ABFE Reference Map - {location_name}"
            map_message = "No ABFE data available for this location - showing regional context"
            print(f"🗺️  No ABFE data available - generating reference map with {buffer_miles}-mile radius")
        else:
            # ABFE data available - use standard parameters
            buffer_miles = 0.5  # Standard radius for ABFE data
            map_title = f"ABFE Map - {location_name}"
            map_message = "ABFE map successfully generated"
            print(f"🗺️  ABFE data available - generating detailed map with {buffer_miles}-mile radius")
        
        # Always generate a map with point marker
        success, result, job_id = client.generate_abfe_map(
            longitude=longitude,
            latitude=latitude,
            location_name=map_title,
            buffer_miles=buffer_miles,
            base_map="World_Imagery",
            map_format="PDF",
            dpi=250,
            output_size=(1224, 792),
            include_legend=True,
            show_point_marker=True,  # Always show the point
            show_attribution=True
        )
        
        if success and client.download_abfe_map(result, filename):
            return {
                "success": True,
                "filename": filename,
                "url": result,
                "job_id": job_id,
                "message": map_message,
                "data_available": abfe_summary['abfe_data_available'],
                "abfe_values": abfe_summary.get('abfe_values', []),
                "map_type": "ABFE data map" if abfe_summary['abfe_data_available'] else "ABFE reference map",
                "buffer_miles": buffer_miles,
                "note": "Map shows point location with regional context" if not abfe_summary['abfe_data_available'] else "Map shows ABFE data with point location"
            }
        else:
            # If map generation fails, try with different parameters
            print(f"⚠️  First attempt failed, trying with basic parameters...")
            
            # Fallback: try with simpler parameters
            success_fallback, result_fallback, job_id_fallback = client.generate_abfe_map(
                longitude=longitude,
                latitude=latitude,
                location_name=f"Location Map - {location_name}",
                buffer_miles=1.0,  # Medium radius
                base_map="World_Topo_Map",  # Different base map
                map_format="PDF",
                dpi=150,  # Lower DPI
                output_size=(792, 612),  # Smaller size
                include_legend=False,  # No legend for simplicity
                show_point_marker=True,
                show_attribution=True
            )
            
            if success_fallback and client.download_abfe_map(result_fallback, filename):
                return {
                    "success": True,
                    "filename": filename,
                    "url": result_fallback,
                    "job_id": job_id_fallback,
                    "message": f"Reference map generated (fallback mode) - {map_message}",
                    "data_available": abfe_summary['abfe_data_available'],
                    "abfe_values": abfe_summary.get('abfe_values', []),
                    "map_type": "Reference map (fallback)",
                    "buffer_miles": 1.0,
                    "note": "Generated with simplified parameters due to initial generation failure"
                }
            else:
                return {
                    "success": False,
                    "message": f"ABFE map generation failed: {result}. Fallback also failed: {result_fallback}",
                "url": result if success else None,
                "job_id": job_id if success else None,
                    "data_available": abfe_summary['abfe_data_available'],
                    "attempted_fallback": True
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"ABFE map generation error: {str(e)}",
            "data_available": False,
            "note": "Error occurred during map generation process"
        }

def _merge_generated_pdfs(result: Dict[str, Any], location_name: str, output_manager) -> Dict[str, Any]:
    """Merge all successfully generated PDFs into a single comprehensive report"""
    
    if not PDF_MERGE_AVAILABLE:
        return {
            "requested": True,
            "success": False,
            "message": "PDF merging not available - PyPDF2 or pypdf not installed",
            "merged_filename": None
        }
    
    try:
        # Collect all successfully generated PDF files
        pdf_files = []
        reports_info = []
        
        reports = result["reports_generated"]
        
        # Check FIRMette
        if reports["firmette"].get("success") and reports["firmette"].get("filename"):
            filename = reports["firmette"]["filename"]
            if os.path.exists(filename):
                pdf_files.append(filename)
                reports_info.append("FIRMette (FIRM) Report")
                print(f"   📄 Adding FIRMette: {os.path.basename(filename)}")
        
        # Check Preliminary Comparison
        if reports["preliminary_comparison"].get("success") and reports["preliminary_comparison"].get("filename"):
            filename = reports["preliminary_comparison"]["filename"]
            if os.path.exists(filename):
                pdf_files.append(filename)
                reports_info.append("Preliminary Comparison (pFIRM) Report")
                print(f"   📄 Adding Preliminary Comparison: {os.path.basename(filename)}")
        
        # Check ABFE Map
        if reports["abfe_map"].get("success") and reports["abfe_map"].get("filename"):
            filename = reports["abfe_map"]["filename"]
            if os.path.exists(filename):
                pdf_files.append(filename)
                if reports["abfe_map"].get("data_available", False):
                    reports_info.append("ABFE (Advisory Base Flood Elevation) Map")
                else:
                    reports_info.append("ABFE Reference Map (No ABFE data available)")
                print(f"   📄 Adding ABFE Map: {os.path.basename(filename)}")
        
        if not pdf_files:
            return {
                "requested": True,
                "success": False,
                "message": "No PDF files available to merge",
                "merged_filename": None,
                "files_attempted": 0
            }
        
        # Generate merged filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = location_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
        merged_filename = os.path.join(output_manager.get_subdirectory("reports"), f"comprehensive_flood_report_{safe_name}_{timestamp}.pdf")
        
        print(f"   📄 Merging {len(pdf_files)} PDF(s) into: {os.path.basename(merged_filename)}")
        
        # Create PDF merger
        merger = PdfMerger()
        
        # Add cover page information (as a simple text overlay would require additional libraries)
        # For now, we'll just merge the existing PDFs in order
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                print(f"   📄 Processing {os.path.basename(pdf_file)}...")
                with open(pdf_file, 'rb') as file:
                    merger.append(file)
            except Exception as e:
                print(f"   ⚠️  Warning: Could not add {os.path.basename(pdf_file)}: {str(e)}")
                continue
        
        # Write merged PDF
        with open(merged_filename, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        
        # Verify the merged file was created
        if os.path.exists(merged_filename):
            file_size = os.path.getsize(merged_filename)
            print(f"   ✅ Merged PDF created: {os.path.basename(merged_filename)} ({file_size:,} bytes)")
            
            return {
                "requested": True,
                "success": True,
                "message": f"Successfully merged {len(pdf_files)} PDF(s) into comprehensive report",
                "merged_filename": merged_filename,
                "files_merged": len(pdf_files),
                "reports_included": reports_info,
                "file_size_bytes": file_size,
                "individual_files": [os.path.basename(f) for f in pdf_files]
            }
        else:
            return {
                "requested": True,
                "success": False,
                "message": "Merged PDF file was not created successfully",
                "merged_filename": merged_filename,
                "files_attempted": len(pdf_files)
            }
    
    except Exception as e:
        return {
            "requested": True,
            "success": False,
            "message": f"Error during PDF merging: {str(e)}",
            "merged_filename": None,
            "error_details": str(e)
        }

def _generate_analysis_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a comprehensive analysis summary"""
    
    flood_info = result["flood_information"]
    reports = result["reports_generated"]
    
    # Count successful reports
    successful_reports = sum(1 for report in reports.values() if report.get("success", False))
    requested_reports = sum(1 for report in reports.values() if report.get("requested", False))
    
    # Extract key findings
    current_summary = flood_info["current_effective"]["summary"]
    overall_summary = flood_info["overall_summary"]
    
    summary = {
        "location_analysis": {
            "coordinates": result["analysis_metadata"]["coordinates"],
            "location_name": result["analysis_metadata"]["location"],
            "analysis_completed": datetime.now().isoformat()
        },
        "flood_risk_assessment": {
            "data_available": overall_summary["data_available"],
            "in_floodplain": overall_summary["location_in_floodplain"],
            "flood_insurance_required": overall_summary["flood_insurance_required"],
            "preliminary_changes_pending": overall_summary["preliminary_changes_pending"]
        },
        "key_identifiers": overall_summary["primary_identifiers"],
        "reports_summary": {
            "reports_requested": requested_reports,
            "reports_generated": successful_reports,
            "firmette_success": reports["firmette"].get("success", False),
            "preliminary_comparison_success": reports["preliminary_comparison"].get("success", False),
            "abfe_map_success": reports["abfe_map"].get("success", False),
            "pdf_merge_requested": result.get("pdf_merge", {}).get("requested", False),
            "pdf_merge_success": result.get("pdf_merge", {}).get("success", False),
            "merged_pdf_filename": result.get("pdf_merge", {}).get("merged_filename"),
            "files_merged": result.get("pdf_merge", {}).get("files_merged", 0)
        },
        "data_summary": {
            "current_flood_zones_found": len(flood_info["current_effective"]["flood_zones"]),
            "current_firm_panels_found": len(flood_info["current_effective"]["firm_panels"]),
            "current_floodplain_areas_found": len(flood_info["current_effective"]["floodplain_data"]),
            "preliminary_data_available": flood_info["preliminary"]["has_preliminary_data"],
            "preliminary_changes_detected": flood_info["preliminary"]["summary"].get("changes_detected", False)
        },
        "recommendations": _generate_recommendations(flood_info, reports, result)
    }
    
    return summary

def _generate_recommendations(flood_info: Dict[str, Any], reports: Dict[str, Any], result: Dict[str, Any] = None) -> List[str]:
    """Generate recommendations based on analysis results"""
    
    recommendations = []
    overall = flood_info["overall_summary"]
    current = flood_info["current_effective"]["summary"]
    preliminary = flood_info["preliminary"]
    
    # Data availability recommendations
    if not overall["data_available"]:
        recommendations.append("No FEMA flood data found for this location. This may indicate the area is not mapped or outside NFIP participating communities.")
    
    # Flood insurance recommendations
    if overall["flood_insurance_required"]:
        recommendations.append(f"Location is in flood zone {current['primary_flood_zone']} - flood insurance is required for federally backed mortgages.")
    elif overall["location_in_floodplain"]:
        recommendations.append("Location is in a mapped floodplain. Consider flood insurance even if not required.")
    else:
        recommendations.append("Location appears to be in minimal flood hazard area (Zone X). Flood insurance may still be advisable.")
    
    # Base flood elevation recommendations
    if current["primary_base_flood_elevation"]:
        recommendations.append(f"Base Flood Elevation is {current['primary_base_flood_elevation']} feet. Ensure structures are built above this elevation.")
    
    # Preliminary changes recommendations
    if preliminary["has_preliminary_data"]:
        recommendations.append("Preliminary flood map changes are pending. Review preliminary comparison report for upcoming changes.")
        if preliminary["summary"].get("new_flood_zone"):
            recommendations.append(f"Flood zone may change to {preliminary['summary']['new_flood_zone']} in future updates.")
    
    # Report recommendations
    if reports["firmette"]["success"]:
        recommendations.append("Use the generated FIRMette for official flood insurance determinations.")
    
    if reports["preliminary_comparison"]["success"]:
        recommendations.append("Review the preliminary comparison report to understand upcoming flood map changes.")
    
    if reports["abfe_map"]["success"]:
        recommendations.append("ABFE data provides advisory flood elevation guidance for planning purposes.")
    
    # PDF merge recommendations
    if result:
        pdf_merge = result.get("pdf_merge", {})
        if pdf_merge.get("success"):
            merged_filename = pdf_merge.get("merged_filename", "")
            files_merged = pdf_merge.get("files_merged", 0)
            recommendations.append(f"All {files_merged} flood reports have been merged into a single comprehensive PDF: {os.path.basename(merged_filename) if merged_filename else 'comprehensive report'}")
            recommendations.append("Use the merged PDF for complete flood documentation and regulatory submissions.")
        elif pdf_merge.get("requested") and not pdf_merge.get("success"):
            recommendations.append("PDF merging was attempted but failed - individual reports are available separately.")
    
    # General recommendations
    recommendations.append("Consult with local floodplain administrators for building and development requirements.")
    recommendations.append("Consider consulting with a licensed surveyor for precise elevation determinations.")
    
    return recommendations

# Tool list for easy import
COMPREHENSIVE_FLOOD_TOOLS = [comprehensive_flood_analysis]

def get_comprehensive_tool_description() -> str:
    """Get description of the comprehensive flood tool"""
    return "Comprehensive FEMA flood analysis - generates all reports (FIRM, pFIRM, ABFE), extracts detailed flood information including floodplain, panel, zone, elevation, and effective date data, and automatically merges all PDFs into a single comprehensive report"

if __name__ == "__main__":
    print("🌊 Comprehensive FEMA Flood Analysis Tool")
    print("=" * 60)
    print("This tool provides complete flood analysis including:")
    print("• All three FEMA reports (FIRMette, Preliminary Comparison, ABFE)")
    print("• Automatic PDF merging into single comprehensive report")
    print("• Detailed flood information extraction:")
    print("  - Floodplain information and identifiers")
    print("  - FIRM panel details and numbers")
    print("  - Flood zone designations")
    print("  - Base flood elevations")
    print("  - Effective dates")
    print("  - Political jurisdictions")
    print("• Risk assessment and recommendations")
    print("• Structured data export")
    print("\n💡 Usage:")
    print("   from comprehensive_flood_tool import COMPREHENSIVE_FLOOD_TOOLS")
    print("   # Use with LangGraph agents")
    print("=" * 60) 