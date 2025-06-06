#!/usr/bin/env python3
"""
Comprehensive Environmental Screening Agent

This module creates a LangGraph agent that provides comprehensive environmental screening
including flood analysis, wetland analysis, critical habitat assessment, karst geology,
air quality (nonattainment areas), and cadastral data lookup.

The agent automatically:
1. Creates intelligent project directories
2. Performs all environmental analyses 
3. Generates maps and reports
4. Provides comprehensive risk assessment
5. Outputs structured results for regulatory compliance

Key Features:
- Automatic map generation for all analysis types
- Structured JSON output conforming to regulatory schemas
- Comprehensive report generation (PDF, HTML, Markdown)
- Project-based file organization
- Concurrent analysis execution for efficiency
"""

import os
import sys
from typing import Dict, Any, List, Optional, Union, Tuple, Annotated
from datetime import datetime
import json
import asyncio
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

# Pydantic for output schemas
from pydantic import BaseModel, Field

# Import all our comprehensive environmental tools
from comprehensive_flood_tool import COMPREHENSIVE_FLOOD_TOOLS
from WetlandsINFO.wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL
from nonattainment_analysis_tool import COMPREHENSIVE_NONATTAINMENT_TOOL
from HabitatINFO.tools import habitat_tools
from karst.karst_tools import KARST_TOOLS
from comprehensive_screening_report_tool import COMPREHENSIVE_SCREENING_TOOLS
from output_directory_manager import PROJECT_DIRECTORY_TOOLS

# Import async environmental tools for advanced workflows
try:
    from async_environmental_tools import (
        ASYNC_ENVIRONMENTAL_TOOLS,
        EnvironmentalState,
        analyze_wetlands_async,
        analyze_nonattainment_async,
        analyze_flood_risk_async,
        analyze_critical_habitat_async,
        analyze_karst_async,
        comprehensive_environmental_analysis_async
    )
    ASYNC_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Async environmental tools not available: {e}")
    ASYNC_TOOLS_AVAILABLE = False
    ASYNC_ENVIRONMENTAL_TOOLS = []

# Import cadastral data tools
try:
    from cadastral.comprehensive_property_analysis_tool import CADASTRAL_DATA_TOOLS
except ImportError:
    print("⚠️  Cadastral data tools not available - continuing without cadastral analysis")
    CADASTRAL_DATA_TOOLS = []

# Structured output schemas for regulatory compliance
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
    firmette_map_path: Optional[str] = Field(None, description="Relative path to the generated FIRMette PDF map.")
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

# Enhanced agent state with proper LangGraph patterns
class ComprehensiveEnvironmentalState(MessagesState):
    """Enhanced state for comprehensive environmental analysis following LangGraph best practices"""
    # Project metadata
    project_name: Optional[str] = None
    project_directory: Optional[str] = None
    project_description: Optional[str] = None
    
    # Location information (simplified to avoid Gemini API issues)
    analysis_location: Optional[List[float]] = None  # [longitude, latitude] instead of Tuple
    location_name: Optional[str] = None
    cadastral_number: Optional[str] = None
    
    # Analysis control flags
    analysis_requested: Dict[str, bool] = {}
    analysis_completed: Dict[str, bool] = {}
    analysis_results: Dict[str, Any] = {}
    
    # Generated files tracking
    maps_generated: List[str] = []
    reports_generated: List[str] = []
    data_files: List[str] = []
    
    # Error tracking
    errors: List[str] = []
    
    # User context
    user_id: Optional[str] = None
    
    # Required by create_react_agent - tracks remaining iterations
    remaining_steps: Optional[int] = 25

# Agent instruction prompt based on LangGraph documentation patterns
COMPREHENSIVE_AGENT_INSTRUCTIONS = """You are a comprehensive environmental screening specialist agent. Your mission is to perform complete environmental analysis for any location using powerful comprehensive tools and generate professional screening reports.

🎯 PRIMARY OBJECTIVE
Provide thorough environmental screening that integrates property characteristics with environmental constraints, then AUTOMATICALLY generate comprehensive reports with maps and supporting documentation suitable for regulatory submission.

�� ANALYSIS WORKFLOW

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
     ✅ NEW: "output/Marina_Construction_Environmental_Screening_2024-12-19_at_14.30.15/"

2️⃣ COMPREHENSIVE ENVIRONMENTAL ANALYSIS
   Use these tools with map generation enabled:
   
   🌊 FLOOD ANALYSIS (comprehensive_flood_analysis)
   • Generates FIRMette, Preliminary Comparison, ABFE maps
   • Extracts flood zone, base flood elevation, FIRM panel data
   • Provides flood insurance requirements
   
   🌿 WETLAND ANALYSIS (analyze_wetland_location_with_map)  
   • Uses NWI data to identify wetlands on/near property
   • Generates detailed wetland maps with regulatory overlays
   • Assesses regulatory complexity and permitting needs
   
   🦎 CRITICAL HABITAT ANALYSIS (analyze_critical_habitat_comprehensive)
   • Identifies endangered species critical habitat
   • Generates critical habitat maps
   • Assesses ESA Section 7 consultation requirements
   
   🏔️ KARST ANALYSIS (check_coordinates_karst)
   • Identifies karst geology and regulated areas (Puerto Rico focus)
   • Generates karst hazard maps
   • Assesses regulatory buffers and restrictions
   
   🌫️ AIR QUALITY ANALYSIS (analyze_nonattainment_with_map)
   • Identifies EPA nonattainment areas
   • Generates air quality status maps  
   • Assesses NAAQS compliance and permitting impacts
   
   🏠 CADASTRAL ANALYSIS (if available)
   • Property boundaries and ownership data
   • Zoning and land use information

3️⃣ FINAL REPORT GENERATION
   • Use generate_comprehensive_screening_report for final deliverable
   • Creates professional PDF, HTML, and Markdown reports
   • Includes executive summary, findings, recommendations
   • Suitable for regulatory submission

🔧 TOOL USAGE PATTERNS

FOR COORDINATES: Always use longitude first, then latitude (e.g., -66.150906, 18.434059)

FOR TOOL CALLS: Include map generation in all analysis tools:
```
analyze_wetland_location_with_map(longitude=-66.150906, latitude=18.434059, location_name="Bayamón Marina Site")
comprehensive_flood_analysis(longitude=-66.150906, latitude=18.434059, location_name="Bayamón Marina Site", generate_reports=True)
```

FOR SMART DIRECTORY NAMING: Use create_intelligent_project_directory at start:
```
create_intelligent_project_directory(
    project_description="Marina Construction Environmental Assessment",
    location_name="Bayamón, Puerto Rico", 
    coordinates=[-66.150906, 18.434059]
)
```

⚖️ REGULATORY FOCUS
Your analysis must identify specific regulatory requirements:
• Section 404 Clean Water Act permits (wetlands)
• FEMA compliance and flood insurance requirements  
• ESA Section 7 consultation needs (critical habitat)
• NAAQS compliance for air quality
• Local karst protection regulations
• Zoning and land use compliance

🎯 FINAL OUTPUT
Always conclude with structured JSON using the exact StructuredScreeningOutput schema format. Populate ALL relevant fields with specific data extracted from tool results:
   • For `flood_analysis`, ensure fields like `flood_zone_code`, `panel_id`, `panel_date`, `base_flood_elevation_ft`, `insurance_requirements`, and paths to `firmette_map_path` and `comprehensive_flood_report_path` are populated from tool results.
   • For `wetland_analysis`, populate `wetlands_on_property`, `wetland_types_present`, `distance_to_nearest_wetland_miles`, and `nwi_map_path` directly.
   • Similarly for `karst_analysis`, `critical_habitat_analysis`, and `air_quality_analysis`, fill with the direct data points and map paths from tools.

Your final response for this step must be ONLY the populated JSON object as a valid JSON string, conforming to the schema. Do not add any explanatory text before or after the JSON string itself."""

def create_comprehensive_environmental_agent(use_async_tools: bool = False):
    """
    Create a LangGraph agent with comprehensive environmental screening tools
    
    Args:
        use_async_tools: Whether to use async environmental tools for better performance (default: False due to API compatibility)
        
    Returns:
        Compiled LangGraph agent
    """
    
    # Use Google Gemini which supports tool calling
    # Make sure to set your API key: export GOOGLE_API_KEY="your-key-here"
    # You can also use other supported models:
    # - "openai:gpt-4o-mini" (export OPENAI_API_KEY="sk-...")
    # - "anthropic:claude-3-5-haiku-latest" (export ANTHROPIC_API_KEY="sk-...")
    
    model = "google_genai:gemini-2.5-flash-preview-04-17"
    memory = MemorySaver()
    
    # Combine all comprehensive tools including new async tools if available
    base_tools = (
        COMPREHENSIVE_FLOOD_TOOLS + 
        COMPREHENSIVE_WETLAND_TOOL + 
        CADASTRAL_DATA_TOOLS + 
        KARST_TOOLS + 
        habitat_tools + 
        [COMPREHENSIVE_NONATTAINMENT_TOOL] + 
        COMPREHENSIVE_SCREENING_TOOLS + 
        PROJECT_DIRECTORY_TOOLS
    )
    
    # Add async tools if available and requested
    if use_async_tools and ASYNC_TOOLS_AVAILABLE:
        all_tools = base_tools + ASYNC_ENVIRONMENTAL_TOOLS
        print(f"✅ Using {len(all_tools)} tools including {len(ASYNC_ENVIRONMENTAL_TOOLS)} async environmental tools")
    else:
        all_tools = base_tools
        print(f"📊 Using {len(all_tools)} standard environmental tools")
    
    # Create a prompt function as required by create_react_agent
    def create_prompt_function(state: ComprehensiveEnvironmentalState, config: RunnableConfig = None):
        """Create dynamic prompt with system instructions"""
        from langchain_core.messages import SystemMessage
        
        # Add system message with our comprehensive instructions
        system_message = SystemMessage(content=COMPREHENSIVE_AGENT_INSTRUCTIONS)
        
        # Return system message plus existing messages
        return [system_message] + state.get("messages", [])
    
    # Create agent using LangGraph best practices from documentation
    try:
        agent = create_react_agent(
            model=model,
            tools=all_tools,
            state_schema=ComprehensiveEnvironmentalState,
            checkpointer=memory,
            # Pass prompt function instead of string
            prompt=create_prompt_function
        )
        
        print(f"✅ Created comprehensive environmental agent with {len(all_tools)} tools")
        return agent
        
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        # Fallback to basic StateGraph implementation
        return create_fallback_agent(all_tools, model, memory)

def create_fallback_agent(tools, model, memory):
    """Create a fallback agent using basic StateGraph if create_react_agent fails"""
    print("🔄 Creating fallback agent using StateGraph...")
    
    from langchain.chat_models import init_chat_model
    
    # Initialize the model
    llm = init_chat_model(model=model)
    llm_with_tools = llm.bind_tools(tools)
    
    # Create tool node
    tool_node = ToolNode(tools)
    
    def call_model(state: ComprehensiveEnvironmentalState, config: RunnableConfig):
        """Node that calls the LLM with tools"""
        messages = state["messages"]
        
        # Add system message with instructions
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            system_msg = SystemMessage(content=COMPREHENSIVE_AGENT_INSTRUCTIONS)
            messages = [system_msg] + messages
        
        response = llm_with_tools.invoke(messages, config)
        return {"messages": [response]}
    
    def should_continue(state: ComprehensiveEnvironmentalState):
        """Decide whether to continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tools"
        return END
    
    # Build the graph
    builder = StateGraph(ComprehensiveEnvironmentalState)
    
    # Add nodes
    builder.add_node("agent", call_model)
    builder.add_node("tools", tool_node)
    
    # Add edges
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")
    
    # Compile with checkpointer
    graph = builder.compile(checkpointer=memory)
    
    print("✅ Fallback agent created successfully")
    return graph

def main():
    """Example usage of the comprehensive environmental agent"""
    
    print("🌍 Comprehensive Environmental Screening Agent")
    print("=" * 60)
    
    # Create the agent (use standard tools to avoid Gemini API issues)
    try:
        agent = create_comprehensive_environmental_agent(use_async_tools=False)
    except Exception as e:
        print(f"⚠️  Agent creation failed: {e}")
        print("🔄 This shouldn't happen with standard tools...")
        return None
    
    # Example coordinates (Bayamón, Puerto Rico - potential marina development)
    longitude = -66.150906
    latitude = 18.434059
    location_name = "Bayamón Marina Development Site"
    project_description = "Marina Construction Environmental Assessment"
    
    print(f"\n🗺️ Running comprehensive environmental screening:")
    print(f"   Location: {location_name}")
    print(f"   Coordinates: {latitude}°N, {longitude}°W")
    print(f"   Project: {project_description}")
    
    # Create the user request
    user_message = f"""Please perform a comprehensive environmental screening for a {project_description.lower()} at {location_name} (coordinates: {longitude}, {latitude}).

This is for a proposed marina construction project that will require:
- Dredging and pile installation in coastal waters
- Upland development for marina facilities
- Parking and access roads
- Fuel dock and service facilities

I need a complete regulatory analysis including all environmental constraints, required permits, and compliance requirements. Please generate all maps and create a comprehensive report suitable for regulatory submission.

The analysis should cover:
✅ Flood risk and FEMA compliance
✅ Wetlands and coastal waters (Section 404 permits)
✅ Critical habitat and endangered species
✅ Karst geology (Puerto Rico specific)
✅ Air quality compliance
✅ Property and zoning information

Please organize all outputs in a professional project directory structure."""

    # Run the analysis
    try:
        print(f"\n🚀 Starting analysis...")
        
        # Configure the run
        config = {
            "configurable": {
                "thread_id": f"marina_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": "environmental_consultant"
            },
            "recursion_limit": 50  # Allow for comprehensive analysis
        }
        
        # Execute the agent
        result = agent.invoke(
            {
                "messages": [HumanMessage(content=user_message)],
                "project_description": project_description,
                "location_name": location_name,
                "analysis_location": [longitude, latitude]
            },
            config=config
        )
        
        print(f"\n✅ Analysis completed successfully!")
        
        # Extract and display results
        if "messages" in result:
            final_message = result["messages"][-1]
            if hasattr(final_message, 'content'):
                print(f"\n📋 Final Results:")
                print(f"   Message Type: {type(final_message).__name__}")
                print(f"   Content Length: {len(final_message.content)} characters")
                
                # Try to parse JSON output if present
                content = final_message.content
                if content.strip().startswith('{') and content.strip().endswith('}'):
                    try:
                        structured_output = json.loads(content)
                        print(f"\n🎯 Structured Output Summary:")
                        print(f"   Success: {structured_output.get('success', 'Unknown')}")
                        print(f"   Project: {structured_output.get('project_name', 'Unknown')}")
                        print(f"   Directory: {structured_output.get('project_directory', 'Unknown')}")
                        
                        # Show key findings
                        if 'environmental_constraints_summary' in structured_output:
                            constraints = structured_output['environmental_constraints_summary']
                            if constraints:
                                print(f"\n🚨 Key Environmental Constraints:")
                                for constraint in constraints[:5]:  # Show first 5
                                    print(f"     • {constraint}")
                        
                        if 'overall_risk_level_assessment' in structured_output:
                            risk = structured_output['overall_risk_level_assessment']
                            print(f"\n⚖️  Overall Risk Level: {risk}")
                        
                    except json.JSONDecodeError:
                        print(f"\n📄 Final response (first 500 chars):")
                        print(f"   {content[:500]}...")
                else:
                    print(f"\n📄 Final response (first 500 chars):")
                    print(f"   {content[:500]}...")
        
        # Show project directory info if available
        if "project_directory" in result:
            print(f"\n📁 Project Directory: {result['project_directory']}")
        
        print(f"\n🎉 Comprehensive environmental screening completed!")
        return result
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_example_analysis():
    """Run a quick example analysis for testing"""
    
    print("🧪 Running Example Environmental Analysis")
    print("-" * 50)
    
    # Create agent
    agent = create_comprehensive_environmental_agent(use_async_tools=False)
    
    # Simple coordinates test (Cataño, Puerto Rico)
    longitude = -66.1689712
    latitude = 18.4282314
    
    user_message = f"""Please perform environmental screening for coordinates {longitude}, {latitude} in Cataño, Puerto Rico. 

This is for a residential development project. Please:
1. Create an appropriate project directory
2. Analyze flood risk with FEMA data
3. Check for wetlands 
4. Generate basic maps
5. Provide a summary of findings

Keep it concise but thorough."""

    try:
        config = {
            "configurable": {
                "thread_id": f"test_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            },
            "recursion_limit": 25
        }
        
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config=config
        )
        
        print("✅ Example analysis completed!")
        
        # Show final message
        if "messages" in result:
            final_msg = result["messages"][-1]
            print(f"\n📄 Final Response (first 300 chars):")
            print(f"{final_msg.content[:300]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Example analysis failed: {e}")
        return None

if __name__ == "__main__":
    # Check if we're doing a quick test or full demo
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_example_analysis()
    else:
        main() 