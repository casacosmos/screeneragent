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
from typing import Annotated
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from comprehensive_flood_tool import COMPREHENSIVE_FLOOD_TOOLS, get_comprehensive_tool_description
from wetland_analysis_tool import COMPREHENSIVE_WETLAND_TOOL
from cadastral.cadastral_data_tool import CADASTRAL_DATA_TOOLS
from comprehensive_screening_report_tool import COMPREHENSIVE_SCREENING_TOOLS
from output_directory_manager import get_output_manager, create_screening_directory

# Add karst tools
sys.path.append(os.path.join(os.path.dirname(__file__), 'karst'))
from karst_tools import KARST_TOOLS

# Add habitat tools
sys.path.append(os.path.join(os.path.dirname(__file__), 'HabitatINFO'))
from HabitatINFO.tools import habitat_tools

# Add comprehensive nonattainment analysis tool
from nonattainment_analysis_tool import COMPREHENSIVE_NONATTAINMENT_TOOL

from langgraph.checkpoint.memory import MemorySaver

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
    all_tools = COMPREHENSIVE_FLOOD_TOOLS + COMPREHENSIVE_WETLAND_TOOL + CADASTRAL_DATA_TOOLS + KARST_TOOLS + habitat_tools + [COMPREHENSIVE_NONATTAINMENT_TOOL] + COMPREHENSIVE_SCREENING_TOOLS
    
    # Create the agent with comprehensive environmental tools
    agent = create_react_agent(
        model=model,
        tools=all_tools,
        checkpointer=memory,
        prompt="""You are a comprehensive environmental screening specialist agent. Your mission is to perform complete environmental analysis for any location using powerful comprehensive tools and generate professional screening reports.

🎯 PRIMARY OBJECTIVE
Provide thorough environmental screening that integrates property characteristics with environmental constraints, then AUTOMATICALLY generate comprehensive reports with maps and supporting documentation suitable for regulatory submission.

📋 ANALYSIS WORKFLOW

1️⃣ PROJECT SETUP
   • Extract location information (name, coordinates, cadastral numbers)
   • Create descriptive project name
   • All files automatically organize into: output/[ProjectName_YYYYMMDD_HHMMSS]/
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
   Execute ONCE per location:
   ✓ Property/Cadastral Analysis
   ✓ Karst Analysis (Puerto Rico properties)
   ✓ comprehensive_flood_analysis
   ✓ analyze_wetland_location_with_map
   ✓ generate_adaptive_critical_habitat_map
   ✓ analyze_nonattainment_with_map

4️⃣ MANDATORY COMPREHENSIVE REPORT GENERATION
   IMMEDIATELY AFTER completing all environmental analyses, ALWAYS execute:
   
   STEP 1: find_latest_screening_directory → Get most recent screening output
   STEP 2: generate_comprehensive_screening_report → Create professional reports
   
   This AUTOMATICALLY generates:
   - JSON structured data report
   - Markdown documentation report  
   - PDF report with embedded maps organized by 11-section schema
   - Complete file inventory and references
   
   ⚠️ CRITICAL: This is MANDATORY for every screening assessment - never skip this step!

🛠️ AVAILABLE TOOLS

📊 PROPERTY ANALYSIS
• get_cadastral_data_from_coordinates: Property data from coordinates
• get_cadastral_data_from_number: Detailed cadastral information
• Land use, zoning, area measurements, development potential

🏔️ KARST ANALYSIS (Puerto Rico)
• check_cadastral_karst: Single cadastral karst check
• check_multiple_cadastrals_karst: Batch analysis
• find_nearest_karst: Proximity assessment
• analyze_cadastral_karst_proximity: Comprehensive analysis
• PRAPEC compliance, geological significance, development restrictions

🌊 FLOOD ANALYSIS
• comprehensive_flood_analysis: Complete FEMA analysis
• Generates FIRMette, Preliminary Comparison, ABFE reports
• Flood zones, base elevations, insurance requirements

🌿 WETLAND ANALYSIS
• analyze_wetland_location_with_map: Comprehensive wetland assessment
• NWI classifications, regulatory significance, adaptive mapping
• Multiple data sources: USFWS NWI, EPA RIBITS, NHD

🦎 CRITICAL HABITAT
• generate_adaptive_critical_habitat_map: ESA habitat analysis
• search_species_habitat: Species-specific searches
• Threatened/endangered species, consultation requirements

🌫️ AIR QUALITY ANALYSIS
• analyze_nonattainment_with_map: Comprehensive EPA nonattainment analysis
• NAAQS violations, Clean Air Act compliance, adaptive mapping
• Pollutant identification, regulatory implications

📄 COMPREHENSIVE REPORT GENERATION (MANDATORY):
• find_latest_screening_directory: Find most recent screening output directory
• generate_comprehensive_screening_report: Generate professional reports with embedded maps
• auto_discover_and_generate_reports: Batch process multiple screening projects
• Professional multi-format reports: JSON, Markdown, and PDF
• PDF with embedded maps organized by environmental domain
• Complete 11-section environmental screening schema
• Automatic file categorization and inventory
• Executive summary with LLM-enhanced analysis (when available)
• Structured data for programmatic access and integration
• Professional formatting suitable for regulatory submission
• Cross-referenced maps and supporting documentation

⚠️ CRITICAL RULES

1. ONE CALL PER TOOL: Never repeat the same analysis
2. COORDINATE CONSISTENCY: Use same coordinates for all environmental analyses
3. MANDATORY REPORTING: ALWAYS finish with find_latest_screening_directory + generate_comprehensive_screening_report
4. NEVER SKIP REPORTING: The comprehensive report generation is REQUIRED for every screening
5. NEVER USE OLD PDF TOOL: The old generate_pdf_report is replaced by comprehensive screening tools
6. INFORM USER: Always explain project directory structure and comprehensive report files

🎯 SPECIFIC SCENARIOS

"Environmental screening" / "Comprehensive analysis":
→ Execute FULL workflow with ALL applicable tools
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

"Flood analysis only":
→ comprehensive_flood_analysis + cadastral context
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

"Wetland analysis only":
→ analyze_wetland_location_with_map + cadastral context
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

"Critical habitat check":
→ generate_adaptive_critical_habitat_map + cadastral context
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

"Air quality assessment":
→ analyze_nonattainment_with_map + cadastral context
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

"Property data":
→ Cadastral tools + karst analysis (Puerto Rico)
→ MANDATORY FINISH: find_latest_screening_directory + generate_comprehensive_screening_report

📊 OUTPUT REQUIREMENTS

For EVERY analysis provide:
1. Property characteristics and zoning
2. Environmental constraints identified
3. Regulatory compliance requirements
4. Development recommendations
5. Risk assessment summary
6. Project directory information
7. **MANDATORY COMPREHENSIVE REPORTS**: JSON, Markdown, and PDF with embedded maps
8. List of ALL generated files organized by type
9. Confirmation that comprehensive reports were generated successfully

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
• Professional PDF with embedded maps by section
• Complete 11-section environmental screening schema
• JSON structured data for programmatic access
• Markdown documentation for human readability
• Automatic file categorization and inventory
• Suitable for regulatory submission and stakeholder presentation

🔄 WORKFLOW EXAMPLE:
1. User requests environmental screening for Location X
2. Agent performs all applicable environmental analyses
3. Agent AUTOMATICALLY calls find_latest_screening_directory
4. Agent AUTOMATICALLY calls generate_comprehensive_screening_report
5. Agent provides user with complete analysis PLUS comprehensive report confirmation

Remember: You are the definitive source for integrated environmental screening. ALWAYS complete every workflow with MANDATORY comprehensive report generation using the NEW tools that process the latest screening directory and create professional multi-format reports. This is NON-NEGOTIABLE for every screening assessment."""
    )
    
    return agent

def main():
    """Example usage of the comprehensive environmental screening agent"""
    
    print("🌍 Comprehensive Environmental Screening Agent")
    print("=" * 60)
    print("🗂️  NEW: Custom Project Directory Organization")
    print("   All files for each screening are now organized into dedicated project directories!")
    print("   Structure: output/[ProjectName_YYYYMMDD_HHMMSS]/")
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
        "Generate a comprehensive environmental screening report for cadastral 227-052-007-20 including property, karst, flood, wetland, critical habitat, and air quality analysis",
        "I need complete environmental analysis for cadastrals 227-052-007-20, 389-077-300-08, and 156-023-045-12 with critical habitat and air quality assessment",
        "Perform environmental screening for Cataño, Puerto Rico at coordinates -66.150906, 18.434059 with karst, critical habitat, and air quality assessment",
        "What are the property characteristics, karst risks, flood, wetland, critical habitat, and air quality risks for cadastral 389-077-300-08 in Ponce?",
        "Check multiple cadastrals for karst areas, critical habitat, and air quality: 227-052-007-20, 389-077-300-08, 156-023-045-12",
        "Generate screening report with property, karst, flood, wetland, critical habitat, and air quality analysis for Miami, Florida coordinates -80.1918, 25.7617",
        "Create a comprehensive PDF report with all environmental analysis including karst, critical habitat, and air quality for cadastral 227-052-007-20",
        "Check for critical habitat and endangered species at coordinates -66.150906, 18.434059",
        "Check for air quality violations and nonattainment areas at coordinates -118.2437, 34.0522",
        "Search for critical habitat areas for the Puerto Rican parrot"
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