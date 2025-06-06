#!/usr/bin/env python3
"""
Comprehensive Environmental Screening Agent using LangGraph

This agent provides complete environmental screening by combining:
- Property/Cadastral Analysis: Retrieves property data, land use classification, zoning, and development potential
- FEMA Flood Analysis: Generates all three FEMA reports (FIRMette, Preliminary Comparison, ABFE)
- Wetland Analysis: Comprehensive wetland assessment with adaptive mapping
- Critical Habitat Analysis: USFWS critical habitat assessment for threatened and endangered species
- Air Quality Analysis: EPA nonattainment areas assessment for Clean Air Act compliance
- Karst Analysis: PRAPEC karst area assessment and regulatory compliance
- Comprehensive Report Generation: Creates professional multi-format reports with embedded maps and 11-section schema
- Detailed environmental information extraction and risk assessment
- Integrated regulatory compliance guidance and recommendations
- Custom Output Directory Management: Organizes all files for each screening into dedicated project directories

The agent can understand natural language requests and automatically
perform complete environmental screening with property, flood, wetland, critical habitat, and karst analysis tools.
It integrates property characteristics with environmental constraints to provide
comprehensive development guidance and regulatory compliance recommendations.
The agent automatically generates comprehensive professional reports (JSON, Markdown, PDF) containing all findings
with embedded maps and supporting documentation suitable for regulatory submission.

All files for each screening are organized into custom project directories with
subdirectories for reports, maps, logs, and data files.
"""

import os
import sys
from typing import Annotated, List, Dict, Any, Optional, Union
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from comprehensive_flood_tool import COMPREHENSIVE_FLOOD_TOOLS, get_comprehensive_tool_description
from wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL
from cadastral.cadastral_data_tool import CADASTRAL_DATA_TOOLS
from comprehensive_screening_report_tool import COMPREHENSIVE_SCREENING_TOOLS
from output_directory_manager import get_output_manager, create_screening_directory, PROJECT_DIRECTORY_TOOLS

# Add karst tools
sys.path.append(os.path.join(os.path.dirname(__file__), 'karst'))
from karst_tools import KARST_TOOLS

# Add habitat tools
sys.path.append(os.path.join(os.path.dirname(__file__), 'HabitatINFO'))
from HabitatINFO.tools import habitat_tools

# Add comprehensive nonattainment analysis tool
from legacy.tools.ruined.nonattainment_analysis_tool import COMPREHENSIVE_NONATTAINMENT_TOOL

from langgraph.checkpoint.memory import MemorySaver

# Pydantic imports for structured output
from pydantic import BaseModel, Field

# =============================================================================
# STRUCTURED OUTPUT MODELS
# =============================================================================

class PropertyAnalysisOutput(BaseModel):
    cadastral_number: Optional[str] = Field(None, description="Primary cadastral number used for the analysis.")
    area_acres: Optional[float] = Field(None, description="Property area in acres.")
    area_sq_meters: Optional[float] = Field(None, description="Property area in square meters.")
    land_use: Optional[str] = Field(None, description="Current land use classification.")
    zoning: Optional[str] = Field(None, description="Official zoning designation.")
    development_potential: Optional[str] = Field(None, description="Assessed development potential (e.g., High, Moderate, Low).")

class KarstAnalysisOutput(BaseModel):
    within_karst_area: Optional[bool] = Field(None, description="Is the property within a PRAPEC designated karst area?")
    nearby_karst_features: Optional[bool] = Field(None, description="Are there known karst features nearby?")
    distance_to_nearest_feature_miles: Optional[float] = Field(None, description="Distance to the nearest known karst feature in miles.")
    regulatory_impact: Optional[str] = Field(None, description="Summary of regulatory impact related to karst findings.")

class FloodAnalysisOutput(BaseModel):
    flood_zone_code: Optional[str] = Field(None, description="FEMA flood zone designation (e.g., X, AE, VE).")
    panel_id: Optional[str] = Field(None, description="FEMA Flood Insurance Rate Map (FIRM) panel ID.")
    panel_date: Optional[str] = Field(None, description="Date of the FEMA FIRM panel (e.g., YYYY-MM-DD).")
    base_flood_elevation_ft: Optional[float] = Field(None, description="Base Flood Elevation (BFE) in feet, if applicable.")
    flood_risk_category: Optional[str] = Field(None, description="Overall flood risk category (e.g., Minimal, Low, Moderate, High).")
    insurance_requirements: Optional[str] = Field(None, description="Summary of flood insurance requirements (e.g., 'Mandatory', 'Recommended', 'Not Required').")
    firme_map_path: Optional[str] = Field(None, description="Relative path to the generated FIRMette PDF map.")
    comprehensive_flood_report_path: Optional[str] = Field(None, description="Relative path to the main comprehensive flood analysis report PDF, if generated.")
    additional_flood_report_paths: Optional[List[str]] = Field(None, description="List of relative paths to other supporting flood reports like preliminary comparisons or ABFE maps.")

class WetlandAnalysisOutput(BaseModel):
    wetlands_on_property: Optional[bool] = Field(None, description="Are there NWI classified wetlands directly on the property?")
    wetland_types_present: Optional[List[str]] = Field(None, description="List of NWI wetland classification codes found (e.g., PFO1A, PEM1C).")
    nearby_wetlands_identified: Optional[bool] = Field(None, description="Are there NWI classified wetlands identified nearby the property?")
    distance_to_nearest_wetland_miles: Optional[float] = Field(None, description="Distance to the nearest NWI wetland in miles.")
    regulatory_complexity_assessment: Optional[str] = Field(None, description="Assessed regulatory complexity concerning wetlands (e.g., Low, Medium, High).")
    nwi_map_path: Optional[str] = Field(None, description="Relative path to the generated NWI wetlands map PDF.")

class HabitatAnalysisOutput(BaseModel):
    within_designated_critical_habitat: Optional[bool] = Field(None, description="Is the property within a designated critical habitat area?")
    critical_habitat_designation_name: Optional[str] = Field(None, description="Name or identifier of the critical habitat designation, if applicable.")
    threatened_or_endangered_species_potentially_affected: Optional[List[str]] = Field(None, description="List of threatened or endangered species whose habitat may be affected.")
    esa_consultation_potentially_required: Optional[bool] = Field(None, description="Is consultation under the Endangered Species Act potentially required?")
    critical_habitat_map_path: Optional[str] = Field(None, description="Relative path to the generated critical habitat map PDF.")

class AirQualityAnalysisOutput(BaseModel):
    nonattainment_area_status: Optional[str] = Field(None, description="EPA nonattainment status (e.g., Attainment, Nonattainment for specific pollutants, Maintenance).")
    designated_nonattainment_pollutants: Optional[List[str]] = Field(None, description="List of pollutants for which the area is designated nonattainment, if applicable.")
    meets_naaqs_standards: Optional[bool] = Field(None, description="Does the area generally meet National Ambient Air Quality Standards?")
    air_quality_compliance_summary: Optional[str] = Field(None, description="Summary of air quality compliance status and potential implications.")
    nonattainment_map_path: Optional[str] = Field(None, description="Relative path to the generated nonattainment area map PDF.")

class ComprehensiveReportPathsOutput(BaseModel):
    json_report: Optional[str] = Field(None, description="Relative path to the comprehensive JSON report.")
    markdown: Optional[str] = Field(None, description="Relative path to the comprehensive Markdown report.")
    pdf: Optional[str] = Field(None, description="Relative path to the comprehensive PDF report.")

class StructuredScreeningOutput(BaseModel):
    success: bool = Field(..., description="True if the screening process completed successfully by the agent, False if the agent encountered an unrecoverable internal error during its operation.")
    project_name: str = Field(..., description="The name of the project as understood or assigned by the agent.")
    project_directory: str = Field(..., description="The main output directory path for all files related to this screening project (e.g., 'output/Project_Name_YYYYMMDD_HHMMSS'). All subsequent file paths are relative to this directory.")
    project_input_location_description: Optional[str] = Field(None, description="Description of the input location (e.g., 'Cadastral XXX-XX', 'Coordinates Y, X', 'Address...').")
    project_input_coordinates_lng_lat: Optional[List[float]] = Field(None, description="Input coordinates if provided, in [longitude, latitude] format (e.g., [-66.2097, 18.4154]).")
    screening_datetime_utc: Optional[str] = Field(None, description="Timestamp (ISO 8601 format) of when the screening analysis was initiated or completed by the agent.")

    cadastral_analysis: Optional[PropertyAnalysisOutput] = Field(None, description="Detailed findings from property/cadastral data analysis.")
    karst_analysis: Optional[KarstAnalysisOutput] = Field(None, description="Detailed findings from karst geological analysis (especially for Puerto Rico).")
    flood_analysis: Optional[FloodAnalysisOutput] = Field(None, description="Detailed findings from FEMA flood zone and risk analysis.")
    wetland_analysis: Optional[WetlandAnalysisOutput] = Field(None, description="Detailed findings from NWI wetland classification and proximity analysis.")
    critical_habitat_analysis: Optional[HabitatAnalysisOutput] = Field(None, description="Detailed findings from critical habitat and endangered species analysis.")
    air_quality_analysis: Optional[AirQualityAnalysisOutput] = Field(None, description="Detailed findings from EPA air quality nonattainment area analysis.")

    comprehensive_reports: Optional[ComprehensiveReportPathsOutput] = Field(None, description="Relative paths to the main multi-format comprehensive screening reports.")
    maps_generated_other: Optional[List[str]] = Field(None, description="List of relative paths to additional general maps generated, not already linked within specific analysis sections.")
    individual_analysis_reports_other: Optional[List[str]] = Field(None, description="List of relative paths to any standalone specific analysis reports not part of the main comprehensive report or already linked (e.g., detailed raw tool outputs).")
    data_files_supporting: Optional[List[str]] = Field(None, description="List of relative paths to supporting data files (e.g., 'cadastral_search.json', 'panel_info.json', raw tool outputs).")

    environmental_constraints_summary: Optional[List[str]] = Field(None, description="A bulleted list of key environmental constraints identified directly from tool outputs (e.g., 'Property intersects AE flood zone', 'NWI wetlands PFO1A identified on parcel').")
    overall_risk_level_assessment: Optional[str] = Field(None, description="Agent's overall environmental risk assessment for development (e.g., Low, Moderate, High, Significant Concerns). This is an analytical field.")
    key_regulatory_requirements_identified: Optional[List[str]] = Field(None, description="A bulleted list of key regulatory requirements, permits, or consultations likely needed based on factual findings (e.g., 'FEMA LOMR application', 'USACE Section 404 permit', 'ESA Section 7 consultation').")
    agent_recommendations: Optional[List[str]] = Field(None, description="Actionable recommendations provided by the agent based on the overall findings. This is an analytical field.")
    
    narrative_summary_of_findings: Optional[str] = Field(None, description="A concise textual summary (1-3 paragraphs) of the overall findings, key constraints, risks, and primary recommendations. This is an analytical field.")

    error_message: Optional[str] = Field(None, description="Brief error message if the agent's process failed internally.")
    error_details: Optional[Union[Dict[str, Any], str]] = Field(None, description="More detailed error information from the agent if success is False.")

# =============================================================================
# FORMATTING PROMPT TEMPLATE
# =============================================================================

formatting_prompt_template = """Your primary objective is to meticulously populate the provided JSON schema. Use information gathered throughout the entire conversation, including all user inputs, tool calls, and their direct results. Emphasize the factual data retrieved by the tools when filling each field.

JSON Schema to populate:
{schema_description}

Key Instructions for Populating the Schema:

1.  **Prioritize Retrieved Data**:
    *   For data fields (e.g., `cadastral_analysis.zoning`, `flood_analysis.flood_zone_code`, `wetland_analysis.wetland_types_present`, file paths in `comprehensive_reports`), you MUST use the specific data points, values, or lists directly retrieved or generated by the relevant tools.
    *   Example: If a tool reported `flood_zone` as "AE", the `flood_analysis.flood_zone_code` field must be "AE".
    *   Numerical data (like `cadastral_analysis.area_acres` or `wetland_analysis.distance_to_nearest_wetland_miles`) should be the direct numerical outputs.
    *   Boolean fields (like `karst_analysis.within_karst_area` or `critical_habitat_analysis.within_designated_critical_habitat`) should reflect the direct findings (true/false).

2.  **File Paths are Critical**:
    *   All file paths (in `comprehensive_reports`, `maps_generated_other`, `individual_analysis_reports_other`, `data_files_supporting`, and paths within specific analysis outputs like `flood_analysis.firme_map_path` or `wetland_analysis.nwi_map_path`) MUST be accurate and relative to the main `project_directory` value.
    *   For `comprehensive_reports`, ensure you provide paths for `json_report`, `markdown`, and `pdf` if they were generated.

3.  **Completeness and Accuracy**:
    *   Attempt to populate every applicable field in the schema.
    *   If a specific piece of data was not found, a tool was not run for a particular analysis, or an attribute is not applicable, use `null` for Optional fields. For lists where no items were found, use an empty list `[]`.
    *   The `success` field indicates the operational success of your (the agent's) screening process. It should be `false` only if you encountered an unrecoverable error that prevented you from completing the analysis or generating outputs. Environmental risks found do not make `success` false.
    *   `project_input_location_description` should reflect how the user specified the location (e.g. "Cadastral 060-000-009-58" or "Coordinates -66.2097, 18.4154").
    *   `project_input_coordinates_lng_lat` should be in [longitude, latitude] format if coordinates were the input.

4.  **Error Handling**:
    *   If any errors occurred during the process, set `success` to `false` and populate `error_message` with a brief description.
    *   For `error_details`, provide either a dictionary with structured error information or a string with additional details. Do not leave this as a non-dict/non-string value.
    *   If there were minor issues but the overall process succeeded, keep `success` as `true` and you can note issues in the analysis sections or recommendations.

5.  **Distinguish Data from Analysis in Designated Fields**:
    *   **`environmental_constraints_summary`**: List factual constraints derived directly from tool outputs (e.g., "Property intersects Flood Zone AE", "NWI wetland type PFO1A identified on parcel", "Area is nonattainment for Ozone").
    *   **`overall_risk_level_assessment`**: This is your analytical summary of risk (e.g., Low, Moderate, High).
    *   **`key_regulatory_requirements_identified`**: List specific regulatory actions identified (e.g., "FEMA LOMR likely required", "USACE Clean Water Act Section 404 permit needed for wetland impacts").
    *   **`agent_recommendations`**: Your analytical recommendations based on all findings.
    *   **`narrative_summary_of_findings`**: A concise (1-3 paragraphs) textual overview. This is where you synthesize and explain the key findings, constraints, and your overall assessment in prose.

6.  **Specific Analysis Sections (`cadastral_analysis`, `flood_analysis`, etc.)**:
    *   These nested objects should contain the direct, factual outputs from the corresponding analysis tools.
    *   For `flood_analysis`, ensure fields like `flood_zone_code`, `panel_id`, `panel_date`, `base_flood_elevation_ft`, `insurance_requirements`, and paths to `firme_map_path` and `comprehensive_flood_report_path` are populated from tool results.
    *   For `wetland_analysis`, populate `wetlands_on_property`, `wetland_types_present`, `distance_to_nearest_wetland_miles`, and `nwi_map_path` directly.
    *   Similarly for `karst_analysis`, `critical_habitat_analysis`, and `air_quality_analysis`, fill with the direct data points and map paths from tools.

Your final response for this step must be ONLY the populated JSON object as a valid JSON string, conforming to the schema. Do not add any explanatory text before or after the JSON string itself.
"""

def create_comprehensive_environmental_agent():
    """Create a LangGraph agent with comprehensive environmental screening tools (flood + wetland + habitat + karst + air quality analysis)"""
    
    # Use Google Gemini which supports tool calling
    # Make sure to set your API key: export GOOGLE_API_KEY="your-key-here"
    # You can also use other supported models:
    # - "openai:gpt-4o-mini" (export OPENAI_API_KEY="sk-...")
    # - "anthropic:claude-3-5-haiku-latest" (export ANTHROPIC_API_KEY="sk-...")
    
    model = "google_genai:gemini-2.5-flash-preview-04-17"
    memory = MemorySaver()
    # Combine all comprehensive tools including cadastral data tools, karst tools, habitat tools, nonattainment analysis, and PDF generation
    all_tools = COMPREHENSIVE_FLOOD_TOOLS + COMPREHENSIVE_WETLAND_TOOL + CADASTRAL_DATA_TOOLS + KARST_TOOLS + habitat_tools + [COMPREHENSIVE_NONATTAINMENT_TOOL] + COMPREHENSIVE_SCREENING_TOOLS + PROJECT_DIRECTORY_TOOLS
    
    # Main agent prompt guides the overall analysis workflow
    main_agent_prompt = """You are a comprehensive environmental screening specialist agent. Your mission is to perform complete environmental analysis for any location using powerful comprehensive tools and generate professional screening reports.

🎯 PRIMARY OBJECTIVE
Provide thorough environmental screening that integrates property characteristics with environmental constraints, then AUTOMATICALLY generate comprehensive reports with maps and supporting documentation suitable for regulatory submission.

📋 ANALYSIS WORKFLOW

1️⃣ PROJECT SETUP & INTELLIGENT NAMING
   • CRITICAL: Extract meaningful project context from user requests for directory naming
   • Analyze user query for project type/purpose: 
     - "residential development" → "Residential Development Environmental Assessment"
     - "commercial project" → "Commercial Development Environmental Assessment"  
     - "marina construction" → "Marina Construction Environmental Screening"
     - "property assessment" → "Property Environmental Assessment"
     - "due diligence" → "Environmental Due Diligence Assessment"
   • When tools create directories, they now use DESCRIPTIVE PROJECT NAMES instead of generic coordinates
   • Example outputs:
     ❌ OLD: "output/Coordinates_-66.150906_18.434059_2024-12-19_at_14.30.15/"
     ✅ NEW: "output/Residential_Development_Environmental_Assessment_Catano_Puerto_Rico_2024-12-19_at_14.30.15/"
     ✅ NEW: "output/Commercial_Property_Assessment_Miami_Beach_Florida_2024-12-19_at_14.30.15/"
   • Extract location information (name, coordinates, cadastral numbers)
   • All files automatically organize into: output/[DESCRIPTIVE_PROJECT_NAME_YYYYMMDD_HHMMSS]/
     ├── reports/  (PDF reports, comprehensive documents)
     ├── maps/     (Generated maps and visualizations)  
     ├── logs/     (Analysis logs and raw data)
     └── data/     (Structured JSON data exports)

2️⃣ ANALYSIS PRIORITY
   
   🏗️ CADASTRAL-BASED (PREFERRED):
   Single Cadastral:
   • get_cadastral_data_from_number → property details
   • check_cadastral_karst → karst analysis (Puerto Rico)
   • Extract center point → use for all environmental analyses
   
   Multiple Cadastrals:
   • check_multiple_cadastrals_karst → comprehensive karst analysis
   • Get LARGEST cadastral → extract center point
   • Use largest cadastral's coordinates for all analyses
   
   📍 COORDINATE-BASED (FALLBACK):
   • get_cadastral_data_from_coordinates → identify property
   • If cadastral found → proceed with cadastral-based
   • If not → continue with coordinate-based analysis

3️⃣ COMPREHENSIVE SCREENING SEQUENCE
   🔥 STEP 0 (MANDATORY FIRST): create_intelligent_project_directory
   • Extract project context from user query (development type, assessment purpose, etc.)
   • Call create_intelligent_project_directory with optional project_description
   • This establishes the project directory BEFORE running analysis tools
   • Example calls:
     - create_intelligent_project_directory(project_description="Residential Development Environmental Assessment", location_name="Cataño, Puerto Rico")
     - create_intelligent_project_directory(location_name="Miami Beach, Florida", coordinates=[-80.1918, 25.7617])
     - create_intelligent_project_directory(cadastral_number="227-052-007-20")
     - create_intelligent_project_directory(project_description="Marina Construction Screening", location_name="Dorado, Puerto Rico")
   
   Then execute ONCE per location:
   ✓ Property/Cadastral Analysis
   ✓ Karst Analysis (Puerto Rico properties)
   ✓ comprehensive_flood_analysis (ONCE ONLY - generates comprehensive report with all flood components)
   ✓ analyze_wetland_location_with_map
   ✓ generate_adaptive_critical_habitat_map
   ✓ analyze_nonattainment_with_map

4️⃣ MANDATORY COMPREHENSIVE REPORT GENERATION
   IMMEDIATELY AFTER completing all environmental analyses, ALWAYS execute:
   
   STEP 1: find_latest_screening_directory → Get most recent screening output
   STEP 2: generate_comprehensive_screening_report → Create professional reports
   
   ⚠️ CRITICAL: PDF GENERATION IS MANDATORY AND ALWAYS ENABLED
   This AUTOMATICALLY generates:
   - JSON structured data report
   - Markdown documentation report  
   - **PDF report with embedded maps organized by 11-section schema (MANDATORY)**
   - Complete file inventory and references
   
   📄 PDF REPORT REQUIREMENTS:
   • PDF generation is ALWAYS enabled (include_pdf=True by default)
   • PDF contains embedded maps organized by environmental domain
   • Professional formatting suitable for regulatory submission
   • Complete 11-section environmental screening schema
   • NEVER disable PDF generation - it is a core requirement
   
   ⚠️ CRITICAL: This is MANDATORY for every screening assessment - never skip this step!

🌍 COORDINATE FORMAT
Always use (longitude, latitude)
Puerto Rico example: (-66.150906, 18.434059)

💡 KEY INTEGRATIONS
• Property zoning ↔ Environmental constraints
• Land use classification → Compliance requirements
• Multiple regulations → Cumulative impact assessment
• All findings → MANDATORY comprehensive multi-format reports with 11-section schema
• Maps embedded by environmental domain (flood, wetland, habitat, air quality, etc.)

🚀 COMPREHENSIVE REPORTING FEATURES (MANDATORY)
• **Professional PDF with embedded maps by section (ALWAYS GENERATED)**
• Complete 11-section environmental screening schema
• JSON structured data for programmatic access
• Markdown documentation for human readability
• Automatic file categorization and inventory
• Suitable for regulatory submission and stakeholder presentation
• **PDF generation is NEVER optional - always enabled by default**

🔄 WORKFLOW EXAMPLE:
1. User requests environmental screening for Location X
2. Agent extracts project context from user query (development type, purpose, etc.) - OPTIONAL
3. Agent calls create_intelligent_project_directory with optional project_description
4. Agent performs all applicable environmental analyses (using existing project directory)
5. Agent AUTOMATICALLY calls find_latest_screening_directory
6. Agent AUTOMATICALLY calls generate_comprehensive_screening_report
7. Agent provides user with complete analysis PLUS comprehensive report confirmation

📁 DIRECTORY NAMING EXAMPLES:
• User: "Environmental assessment for residential development in Cataño, Puerto Rico"
  → Directory: "Residential_Development_Environmental_Assessment_Catano_Puerto_Rico_2024-12-19_at_14.30.15"

• User: "Property screening for marina construction project"
  → Directory: "Marina_Construction_Property_Screening_2024-12-19_at_14.30.15"

• User: "Due diligence analysis for commercial property in Miami Beach"  
  → Directory: "Commercial_Property_Due_Diligence_Analysis_Miami_Beach_2024-12-19_at_14.30.15"

Remember: You are the definitive source for integrated environmental screening. ALWAYS complete every workflow with MANDATORY comprehensive report generation using the NEW tools that process the latest screening directory and create professional multi-format reports. EXTRACT MEANINGFUL PROJECT CONTEXT from user queries to create descriptive, professional directory names that reflect the actual purpose and scope of the environmental assessment. This is NON-NEGOTIABLE for every screening assessment.

FINAL INSTRUCTION: Once all analyses are complete and all necessary files are generated by the tools, prepare to provide a complete, structured JSON representation of all findings, file paths, and summaries when prompted by the system for the final formatted output. The system will guide you through the final formatting step to ensure all data is properly structured."""

    # Create the agent with comprehensive environmental tools and structured output
    agent = create_react_agent(
        model=model,
        tools=all_tools,
        checkpointer=memory,
        prompt=main_agent_prompt,
        # Use response_format to ensure structured JSON output
        response_format=(formatting_prompt_template, StructuredScreeningOutput)
    )
    
    return agent

def main():
    """Example usage of the comprehensive environmental screening agent"""
    
    print("🌍 Comprehensive Environmental Screening Agent")
    print("=" * 60)
    print("🗂️  NEW: Intelligent Project Directory Naming")
    print("   Agent now creates meaningful directory names based on project context!")
    print("   📁 Example: 'Residential_Development_Environmental_Assessment_Catano_Puerto_Rico_2024-12-19_at_14.30.15'")
    print("   📁 Instead of: 'Coordinates_-66.150906_18.434059_2024-12-19_at_14.30.15'")
    print("   🤖 Agent extracts project context from your requests for professional naming")
    print("🗂️  Custom Project Directory Organization")
    print("   All files for each screening are organized into dedicated project directories!")
    print("   Structure: output/[DESCRIPTIVE_PROJECT_NAME_YYYYMMDD_HHMMSS]/")
    print("   ├── reports/     (PDF reports, comprehensive documents)")
    print("   ├── maps/        (Generated maps and visualizations)")
    print("   ├── logs/        (Analysis logs and raw data)")
    print("   └── data/        (Structured data exports)")
    print("🏔️  NEW: PRAPEC Karst Analysis")
    print("   Comprehensive karst assessment for Puerto Rico properties!")
    print("   • Direct karst intersection detection")
    print("   • Regulatory compliance assessment (Regulation 259)")
    print("   • Development restrictions and permit requirements")
    print("   • Risk assessment and mitigation strategies")
    print("🦎 NEW: Critical Habitat Analysis")
    print("   USFWS critical habitat assessment for threatened and endangered species!")
    print("   • Critical habitat intersection detection")
    print("   • Species identification and conservation status")
    print("   • ESA consultation requirements")
    print("   • Final vs proposed habitat designations")
    print("   • Regulatory compliance and mitigation recommendations")
    print("🌫️ NEW: Air Quality Analysis")
    print("   EPA nonattainment areas assessment for Clean Air Act compliance!")
    print("   • Nonattainment area intersection detection")
    print("   • Pollutant identification and NAAQS violations")
    print("   • Clean Air Act consultation requirements")
    print("   • Nonattainment vs maintenance area status")
    print("   • Adaptive air quality mapping and regulatory compliance")

    
    # Create the agent
    try:
        agent = create_comprehensive_environmental_agent()
        print("✅ Comprehensive environmental screening agent created successfully!")
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return
    
    # Example queries
    example_queries = [
        "Environmental assessment for residential development at cadastral 227-052-007-20 in Puerto Rico",
        "Commercial property due diligence screening for cadastrals 227-052-007-20, 389-077-300-08, and 156-023-045-12",
        "Marina construction environmental screening in Cataño, Puerto Rico at coordinates -66.150906, 18.434059",
        "Environmental screening for hotel development project at cadastral 389-077-300-08 in Ponce",
        "Property assessment for residential subdivision development - multiple cadastrals 227-052-007-20, 389-077-300-08, 156-023-045-12",
        "Environmental due diligence for commercial real estate acquisition in Miami, Florida at coordinates -80.1918, 25.7617",
        "Comprehensive environmental screening for waterfront development project at cadastral 227-052-007-20",
        "Environmental assessment for industrial facility development at coordinates -66.150906, 18.434059",
        "Marina expansion project environmental screening at coordinates -118.2437, 34.0522",
        "Environmental compliance assessment for pharmaceutical facility at cadastral 389-077-300-08"
    ]
    
    print(f"\n📋 Available Tools:")
    flood_description = get_comprehensive_tool_description()
    print(f"   • Property/Cadastral Analysis: Retrieve property data, land use classification, zoning, and development potential")
    print(f"   • Karst Analysis: PRAPEC karst area assessment and regulatory compliance (Puerto Rico)")
    print(f"   • Critical Habitat Analysis: USFWS critical habitat assessment for threatened and endangered species")
    print(f"   • Air Quality Analysis: EPA nonattainment areas assessment for Clean Air Act compliance")
    print(f"   • Flood Analysis: {flood_description}")
    print(f"   • Wetland Analysis: Complete wetland assessment with adaptive mapping and regulatory guidance")
    print(f"   • Comprehensive Report Generation: Professional multi-format reports with embedded maps and 11-section schema")
    print(f"   • Custom Directory Management: Organize all files into dedicated project directories")
    
    print(f"\n🎯 Example Queries:")
    for i, query in enumerate(example_queries, 1):
        print(f"   {i}. {query}")
    
    print(f"\n📊 What the comprehensive environmental screening provides:")
    print(f"   🗂️  PROJECT ORGANIZATION:")
    print(f"     • Custom project directory for each screening")
    print(f"     • Organized subdirectories for different file types")
    print(f"     • Easy file management and sharing")
    print(f"     • Project information file with directory structure")
    print(f"   🏗️  PROPERTY/CADASTRAL ANALYSIS:")
    print(f"     • Cadastral number and property identification")
    print(f"     • Land use classification and zoning category")
    print(f"     • Municipality, neighborhood, and regional location")
    print(f"     • Property area measurements (hectares, acres, sq meters, sq feet)")
    print(f"     • Development potential and regulatory status")
    print(f"     • Zoning implications and permitted uses")
    print(f"   🏔️  KARST ANALYSIS (Puerto Rico):")
    print(f"     • PRAPEC karst area intersection detection")
    print(f"     • Regulatory compliance assessment (Regulation 259)")
    print(f"     • Geological significance and environmental considerations")
    print(f"     • Development restrictions and permit requirements")
    print(f"     • Risk assessment and mitigation strategies")
    print(f"     • Batch analysis for multiple cadastrals")
    print(f"   🦎 CRITICAL HABITAT ANALYSIS:")
    print(f"     • Critical habitat intersection detection")
    print(f"     • Threatened and endangered species identification")
    print(f"     • Final vs proposed habitat designations")
    print(f"     • ESA Section 7 consultation requirements")
    print(f"     • Species-specific conservation recommendations")
    print(f"     • Federal regulatory compliance assessment")
    print(f"   🌫️ AIR QUALITY ANALYSIS:")
    print(f"     • Nonattainment area intersection detection")
    print(f"     • Pollutant identification and NAAQS violations")
    print(f"     • Current status (Nonattainment vs Maintenance)")
    print(f"     • Clean Air Act compliance requirements")
    print(f"     • Pollutant-specific health impacts and regulatory significance")
    print(f"     • Adaptive air quality mapping with regional context")
    print(f"   📋 INTEGRATED ASSESSMENT:")
    print(f"     • Property characteristics and development suitability")
    print(f"     • Overall environmental risk profile including karst, critical habitat, and air quality")
    print(f"     • Cumulative regulatory requirements from all sources (ESA, CWA, CAA, NFIP, local)")
    print(f"     • Development constraints considering property zoning, karst risks, flood risks, wetland factors, critical habitat requirements, and air quality compliance")
    print(f"     • Comprehensive recommendations for compliance and development planning")
    print(f"   📄 COMPREHENSIVE REPORT GENERATION:")
    print(f"     • Professional multi-format reports: JSON, Markdown, and PDF")
    print(f"     • PDF with embedded maps organized by environmental domain")
    print(f"     • Complete 11-section environmental screening schema")
    print(f"     • Automatic file categorization and inventory")
    print(f"     • Executive summary with LLM-enhanced analysis (when available)")
    print(f"     • Structured data for programmatic access and integration")
    print(f"     • Professional formatting suitable for regulatory submission")
    print(f"     • Cross-referenced maps and supporting documentation")
    
    # Interactive mode
    print(f"\n💬 Interactive Mode (type 'quit' to exit):")
    print(f"   Ask for comprehensive environmental screening for any location!")
    print(f"   🏗️  PREFERRED: Provide cadastral numbers for optimal analysis")
    print(f"   Example: 'Generate environmental screening for cadastral 227-052-007-20'")
    print(f"   Example: 'Analyze cadastrals 227-052-007-20, 389-077-300-08 for environmental risks'")
    print(f"   Example: 'Environmental assessment for coordinates -66.15, 18.43 with karst, critical habitat, and air quality analysis'")
    print(f"   For complete screening, use terms like 'screening report', 'environmental assessment', or 'comprehensive analysis'")
    print(f"   The agent will automatically generate a professional PDF report with all findings!")
    print(f"   🗂️  All files will be organized in a custom project directory for easy access!")
    
    while True:
        try:
            user_input = input(f"\n🤔 Your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 Agent is performing comprehensive environmental screening...")
            print(f"   This may take 2-5 minutes to generate all reports and maps...")
            print(f"   🗂️  Files will be organized in a custom project directory...")
            
            # Run the agent
            response = agent.invoke({
                "messages": [HumanMessage(content=user_input)]
            })
            
            # Print the agent's response
            last_message = response["messages"][-1]
            print(f"\n🌍 Comprehensive Environmental Screening Results:")
            print(f"{last_message.content}")
            
        except KeyboardInterrupt:
            print(f"\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"Please try again or type 'quit' to exit.")

def run_example_analysis():
    """Run a single example comprehensive environmental screening without interactive mode"""
    
    print("🌍 Running Example Comprehensive Environmental Screening")
    print("=" * 50)
    print("🗂️  Files will be organized in a custom project directory")
    print("🏔️  Including PRAPEC karst analysis")
    print("🦎 Including critical habitat analysis")
    
    try:
        agent = create_comprehensive_environmental_agent()
        
        # Example query with cadastral number
        query = "Generate a comprehensive environmental screening report for cadastral 227-052-007-20 in Puerto Rico. I need complete property information, karst analysis, critical habitat analysis, air quality analysis, flood and wetland analysis with all reports, maps, and regulatory assessments."
        print(f"Query: {query}")
        print(f"\n🤖 Comprehensive Environmental Screening Results:")
        print(f"   (This may take 2-5 minutes to generate all reports and maps...)")
        print(f"   🗂️  All files will be organized in a custom project directory...")
        
        response = agent.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        last_message = response["messages"][-1]
        print(last_message.content)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        run_example_analysis()
    else:
        main() 