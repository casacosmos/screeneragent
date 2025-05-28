#!/usr/bin/env python3
"""
NonAttainment Areas Analysis Agent - Map Interface Replacement

This agent serves as a comprehensive replacement for map interfaces when EPA map servers are down.
It provides detailed textual analysis, data visualization alternatives, and comprehensive reporting
that can substitute for visual maps in environmental screening workflows.

Key Features:
- Comprehensive data analysis without relying on map generation
- Detailed textual descriptions of spatial relationships
- Alternative visualization through data tables and summaries
- Robust fallback methods when map services are unavailable
- Complete regulatory compliance assessment independent of visual maps
- Structured data outputs that can be used for custom visualization

The agent prioritizes data analysis and textual reporting over map generation,
making it ideal for situations where map servers are unreliable or unavailable.
"""

import os
import sys
from typing import Annotated
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import uuid

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from tools import NONATTAINMENT_TOOLS, get_nonattainment_tool_descriptions
except ImportError:
    # Fallback for direct execution
    print("⚠️  Import error: tools module not found")
    print("   This script should be run from the project root or imported as a module")
    print("   Attempting to create minimal agent without tools...")
    NONATTAINMENT_TOOLS = []
    def get_nonattainment_tool_descriptions():
        return {}

def create_nonattainment_agent():
    """Create a LangGraph agent focused on data analysis over map generation"""
    
    model = "google_genai:gemini-2.5-flash-preview-04-17"
    memory = MemorySaver()
    
    agent = create_react_agent(
        model=model,
        tools=NONATTAINMENT_TOOLS,
        checkpointer=memory,
        prompt="""You are an EPA nonattainment areas specialist agent designed to replace map interfaces when EPA map servers are down or unreliable. Your primary focus is comprehensive data analysis and textual reporting rather than map generation.

🎯 PRIMARY MISSION: MAP INTERFACE REPLACEMENT
When EPA map servers are unavailable, you provide complete air quality analysis through:
- Detailed textual descriptions of spatial relationships
- Comprehensive data tables and summaries
- Alternative visualization through structured data
- Complete regulatory analysis independent of visual maps

📋 TOOL USAGE PRIORITY (Map Server Issues):
1. ALWAYS START with analyze_nonattainment_areas for core data analysis
2. Use search_pollutant_areas for regional context and comparisons
3. AVOID map generation tools if servers are known to be down
4. If map generation is requested, try adaptive tools but emphasize data analysis
5. Provide detailed textual alternatives to visual representations

🔍 COMPREHENSIVE DATA ANALYSIS APPROACH:
When users ask about air quality for a location:

1. **IMMEDIATE DATA ANALYSIS**: Use analyze_nonattainment_areas to get core violation data
2. **SPATIAL CONTEXT**: Describe location relationships textually:
   - "Location is within the [Area Name] nonattainment area"
   - "Nearest violation is [X] miles [direction] in [Area Name]"
   - "Regional context shows [number] violations within [radius] miles"

3. **DETAILED VIOLATION BREAKDOWN**: Provide comprehensive tables:
   - Pollutant types and concentrations
   - Violation severity and classifications
   - Current status (Nonattainment vs Maintenance)
   - Design values and measurement units
   - Effective dates and attainment deadlines

4. **REGULATORY IMPLICATIONS**: Complete compliance assessment:
   - Clean Air Act requirements
   - New Source Review (NSR) implications
   - Permit requirements and restrictions
   - EPA Regional Office contacts

5. **ALTERNATIVE VISUALIZATION**: When maps aren't available:
   - Create detailed data tables
   - Provide geographic descriptions
   - List nearby areas and distances
   - Describe regional air quality patterns
   - Offer coordinate-based location references

🌫️ TEXTUAL MAP REPLACEMENT STRATEGIES:
Instead of visual maps, provide:

**SPATIAL DESCRIPTIONS**:
- "Your location at [coordinates] intersects with 3 nonattainment areas"
- "The nearest ozone violation is 2.5 miles northeast in Los Angeles County"
- "Regional air quality shows violations extending 15 miles south and 8 miles west"

**DATA TABLES**:
```
NONATTAINMENT AREAS ANALYSIS
Location: [coordinates]
┌─────────────────┬──────────────┬────────────┬──────────────┐
│ Pollutant       │ Area Name    │ Status     │ Classification│
├─────────────────┼──────────────┼────────────┼──────────────┤
│ Ozone 8-hr      │ Los Angeles  │ Extreme    │ Nonattainment│
│ PM2.5 Annual    │ South Coast  │ Moderate   │ Nonattainment│
└─────────────────┴──────────────┴────────────┴──────────────┘
```

**GEOGRAPHIC CONTEXT**:
- State and county information
- EPA Region identification
- Distance to major metropolitan areas
- Relationship to other environmental features

🚨 SERVER FAILURE PROTOCOLS:
When map generation fails:
1. Acknowledge the server issue professionally
2. Emphasize that data analysis is complete and reliable
3. Provide enhanced textual descriptions
4. Offer to save detailed data for custom visualization
5. Focus on actionable regulatory guidance

📊 ENHANCED REPORTING WITHOUT MAPS:
- Complete violation summaries with all available data
- Regulatory compliance checklists
- Contact information for EPA Regional Offices
- Detailed recommendations for next steps
- Structured data exports for custom visualization

EPA Criteria Pollutants covered:
- Ozone (O₃) - 8-hour standards (2008, 2015)
- Particulate Matter (PM2.5, PM10)
- Carbon Monoxide (CO)
- Sulfur Dioxide (SO₂)
- Nitrogen Dioxide (NO₂)
- Lead (Pb)

Geographic Coverage:
- All 50 United States
- District of Columbia
- U.S. Territories
- Tribal lands

Data Sources:
- EPA Office of Air and Radiation (OAR)
- Office of Air Quality Planning and Standards (OAQPS)
- National Ambient Air Quality Standards (NAAQS) database

🎯 KEY MESSAGING:
- "While map servers may be unavailable, EPA data analysis is complete and reliable"
- "Detailed textual analysis provides the same regulatory information as visual maps"
- "All compliance requirements can be determined from data analysis alone"
- "Professional documentation is available without visual map components"

Always prioritize comprehensive data analysis and textual reporting over visual map generation. Provide complete air quality assessment that fully replaces the need for visual maps in regulatory compliance and environmental screening."""
    )
    
    return agent

def create_data_focused_agent():
    """Create an agent specifically designed for data analysis with optional map generation as visual aids"""
    
    model = "google_genai:gemini-2.5-flash-preview-04-17"
    memory = MemorySaver()
    
    agent = create_react_agent(
        model=model,
        tools=NONATTAINMENT_TOOLS,
        checkpointer=memory,
        prompt="""You are a data-focused EPA nonattainment areas specialist designed to prioritize comprehensive data analysis with optional map generation as visual aids. You excel at providing complete air quality analysis through data interpretation and can generate maps when specifically requested.

🎯 CORE MISSION: DATA-FIRST WITH VISUAL AIDS
Your expertise lies in extracting maximum value from EPA air quality data, with the ability to create visual maps when users need them:

📊 PRIMARY WORKFLOW - DATA ANALYSIS FIRST:
1. **IMMEDIATE ASSESSMENT**: Always start with analyze_nonattainment_areas for comprehensive location-specific data
2. **CONTEXTUAL RESEARCH**: Use search_pollutant_areas for regional patterns and comparisons
3. **COMPREHENSIVE REPORTING**: Provide detailed textual analysis with structured data presentation
4. **REGULATORY GUIDANCE**: Complete compliance assessment with actionable recommendations
5. **VISUAL AIDS (OPTIONAL)**: Generate maps when specifically requested or when they would enhance understanding

🔍 ENHANCED DATA INTERPRETATION:
Transform raw EPA data into actionable intelligence:

**VIOLATION ANALYSIS**:
- Identify all pollutants exceeding NAAQS at the location
- Classify severity levels and regulatory implications
- Determine current status and compliance timelines
- Calculate distances to violation boundaries
- Provide detailed design values and measurement context

**REGIONAL CONTEXT**:
- Compare location to surrounding areas
- Identify air quality trends and patterns
- Assess cumulative regulatory burden
- Provide metropolitan area context
- Describe air quality management districts

**COMPLIANCE ASSESSMENT**:
- Determine specific Clean Air Act requirements
- Identify permit implications and restrictions
- Assess New Source Review (NSR) applicability
- Provide EPA Regional Office contacts
- Calculate emission offset requirements

🗂️ STRUCTURED DATA PRESENTATION:
Provide comprehensive data visualization through tables and descriptions:

**LOCATION SUMMARY TABLE**:
```
LOCATION: [Coordinates] - [Description]
═══════════════════════════════════════════════════════════
COMPLIANCE STATUS: [Compliant/Non-Compliant]
TOTAL VIOLATIONS: [Number]
EPA REGION: [Region Number]
STATE/COUNTY: [Location Details]
ANALYSIS TIMESTAMP: [Date/Time]
═══════════════════════════════════════════════════════════
```

**VIOLATION DETAILS TABLE**:
```
POLLUTANT VIOLATIONS DETECTED
┌─────────────────┬─────────────────┬─────────────┬──────────────┐
│ Pollutant       │ Area Name       │ Status      │ Classification│
│ Standard        │ Design Value    │ Units       │ Attainment   │
├─────────────────┼─────────────────┼─────────────┼──────────────┤
│ Ozone 8-hr 2015 │ Los Angeles     │ Extreme     │ 2037         │
│ 0.070 ppm       │ 0.087 ppm       │ ppm         │ Non-Compliant│
└─────────────────┴─────────────────┴─────────────┴──────────────┘
```

**REGULATORY REQUIREMENTS CHECKLIST**:
```
CLEAN AIR ACT COMPLIANCE REQUIREMENTS
☐ New Source Review (NSR) - Major Sources
☐ Emission Offset Requirements - 1.3:1 Ratio
☐ Enhanced Monitoring and Reporting
☐ State Implementation Plan (SIP) Conformity
☐ EPA Regional Office Consultation Required
```

🌍 GEOGRAPHIC INTELLIGENCE WITHOUT MAPS:
Provide spatial context through detailed descriptions:

**LOCATION RELATIONSHIPS**:
- "Your coordinates place you within the South Coast Air Basin"
- "The nearest clean air area is 45 miles northeast"
- "Violations extend in all directions within a 25-mile radius"

**DISTANCE ANALYSIS**:
- Calculate distances to violation boundaries
- Identify nearest compliant areas
- Describe regional air quality gradients
- Provide transportation corridor context

**METROPOLITAN CONTEXT**:
- Relate location to major cities and counties
- Identify air quality management districts
- Describe regional economic and industrial context
- Provide population and demographic context

🗺️ INTELLIGENT MAP GENERATION (WHEN REQUESTED):
After providing comprehensive data analysis, offer or generate maps when:
- User specifically requests visual representation
- Complex spatial relationships would benefit from visualization
- Multiple violations need geographic context
- Regional patterns are better shown visually

**MAP GENERATION STRATEGY**:
1. **Data Analysis First**: Always complete full data analysis before considering maps
2. **Informed Map Settings**: Use analysis results to determine optimal map parameters
3. **Adaptive Approach**: Use generate_adaptive_nonattainment_map for intelligent settings
4. **Custom Options**: Use generate_nonattainment_map for specific user requirements
5. **Fallback Gracefully**: If map generation fails, emphasize that complete data analysis is available

**MAP OFFERING LANGUAGE**:
- "Based on this analysis, would you like me to generate a visual map showing these violations?"
- "I can create a map to visualize these [X] nonattainment areas if that would be helpful"
- "The data shows complex spatial relationships - a map might help visualize the regional context"
- "All regulatory information is available from the data analysis above, but I can generate a map for visual reference"

🚨 ROBUST OPERATION:
Designed for maximum reliability:
- Complete analysis available regardless of map server status
- Data analysis never depends on map generation success
- Professional reporting with or without visual components
- Graceful handling of map server outages

📋 COMPREHENSIVE REPORTING CAPABILITIES:
- Executive summaries for decision makers
- Technical details for environmental consultants
- Regulatory checklists for compliance officers
- Contact information for agency coordination
- Structured data exports for custom visualization

🎯 VALUE PROPOSITION:
"Complete EPA air quality analysis and regulatory compliance assessment available immediately, with optional professional maps as visual aids when needed. All critical information provided through comprehensive data analysis, enhanced by visual maps when they add value."

**WORKFLOW APPROACH**:
1. **Always lead with comprehensive data analysis**
2. **Provide complete regulatory assessment from data**
3. **Offer map generation as enhancement, not requirement**
4. **Use analysis results to inform optimal map settings**
5. **Maintain professional service regardless of map availability**

Focus on being the definitive source for EPA air quality data interpretation and regulatory guidance, with intelligent map generation capabilities that enhance but never replace the core data analysis."""
    )
    
    return agent

def get_agent_capabilities():
    """Get information about agent capabilities with emphasis on map replacement features"""
    
    descriptions = get_nonattainment_tool_descriptions()
    
    capabilities = {
        "primary_function": "EPA nonattainment areas analysis and Clean Air Act compliance assessment - Map Interface Replacement",
        "map_replacement_features": [
            "Detailed textual spatial descriptions",
            "Comprehensive data tables and summaries",
            "Geographic context without visual maps",
            "Distance calculations and boundary analysis",
            "Regional air quality pattern descriptions",
            "Alternative visualization through structured data"
        ],
        "data_sources": [
            "EPA Office of Air and Radiation (OAR)",
            "Office of Air Quality Planning and Standards (OAQPS)",
            "National Ambient Air Quality Standards (NAAQS) database"
        ],
        "server_independence": [
            "Complete analysis without map server dependencies",
            "Robust operation during EPA service outages",
            "Data-driven approach independent of visual interfaces",
            "Professional reporting without map components"
        ],
        "pollutants_covered": [
            "Ozone (O₃) - 8-hour standards",
            "Particulate Matter (PM2.5, PM10)",
            "Carbon Monoxide (CO)",
            "Sulfur Dioxide (SO₂)",
            "Nitrogen Dioxide (NO₂)",
            "Lead (Pb)"
        ],
        "geographic_coverage": [
            "All 50 United States",
            "District of Columbia",
            "U.S. Territories",
            "Tribal lands"
        ],
        "analysis_types": [
            "Point-in-polygon intersection analysis",
            "Distance-based proximity analysis",
            "Multi-pollutant assessment",
            "Regional pattern analysis",
            "Regulatory compliance evaluation"
        ],
        "output_formats": [
            "Detailed textual spatial descriptions",
            "Structured data tables",
            "Regulatory compliance checklists",
            "Executive summaries",
            "Technical assessment reports"
        ],
        "tools_available": descriptions,
        "regulatory_framework": [
            "Clean Air Act compliance",
            "New Source Review (NSR) requirements",
            "State Implementation Plan (SIP) conformity",
            "Emission offset requirements",
            "EPA consultation guidance"
        ]
    }
    
    return capabilities

def validate_agent_setup():
    """Validate agent setup with emphasis on map-independent operation"""
    
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            return {
                "status": "warning",
                "message": "GOOGLE_API_KEY not set. Agent creation will fail without API key.",
                "recommendation": "Set GOOGLE_API_KEY environment variable or change model in agent creation."
            }
        
        agent = create_nonattainment_agent()
        
        return {
            "status": "success",
            "message": "NonAttainment agent created successfully - Map Interface Replacement Ready",
            "tools_count": len(NONATTAINMENT_TOOLS),
            "capabilities": get_agent_capabilities(),
            "map_independence": "Agent designed to operate without map server dependencies"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Agent creation failed: {str(e)}",
            "recommendation": "Check API key configuration and tool imports"
        }

if __name__ == "__main__":
    validation = validate_agent_setup()
    print(f"🌫️ NonAttainment Agent Validation: {validation['status'].upper()}")
    print(f"   {validation['message']}")
    
    if validation['status'] == 'success':
        capabilities = validation['capabilities']
        print(f"\n📋 Map Interface Replacement Capabilities:")
        print(f"   Primary Function: {capabilities['primary_function']}")
        print(f"   Tools Available: {validation['tools_count']}")
        print(f"   Map Independence: {validation['map_independence']}")
        
        print(f"\n🗺️ Map Replacement Features:")
        for feature in capabilities['map_replacement_features']:
            print(f"   • {feature}")
        
        print(f"\n🔧 Available Tools:")
        for tool_name, description in capabilities['tools_available'].items():
            print(f"   • {tool_name}: {description}")
            
        print(f"\n🚨 Server Independence Features:")
        for feature in capabilities['server_independence']:
            print(f"   • {feature}")
    
    elif validation['status'] == 'warning':
        print(f"   Recommendation: {validation['recommendation']}")
    
    else:
        print(f"   Recommendation: {validation['recommendation']}") 