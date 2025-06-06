#!/usr/bin/env python3
"""
Environmental Screening Templates

This module provides templates for:
1. Frontend Integration - API and UI templates for integrating environmental screening
2. Agent Prompting - Command templates for instructing the agent
3. Response Processing - Templates for handling agent responses

Templates support the complete workflow from initial screening through comprehensive report generation.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

# =============================================================================
# FRONTEND INTEGRATION TEMPLATES
# =============================================================================

@dataclass
class ScreeningRequest:
    """Template for environmental screening API requests"""
    
    # Project Information
    project_name: str
    project_description: str  # e.g., "Commercial Development Environmental Assessment"
    location_name: Optional[str] = None  # e.g., "Toa Baja, Puerto Rico"
    
    # Location Specification (one required)
    cadastral_number: Optional[str] = None  # Preferred: "060-000-009-58"
    coordinates: Optional[List[float]] = None  # [longitude, latitude] e.g., [-66.2097, 18.4154]
    
    # Analysis Options
    analyses_requested: List[str] = None  # ["property", "karst", "flood", "wetland", "habitat", "air_quality"]
    include_comprehensive_report: bool = True
    include_pdf: bool = True
    use_llm_enhancement: bool = True
    
    def __post_init__(self):
        if self.analyses_requested is None:
            self.analyses_requested = ["property", "karst", "flood", "wetland", "habitat", "air_quality"]

@dataclass 
class ScreeningResponse:
    """Template for environmental screening API responses"""
    
    success: bool
    project_directory: str
    project_name: str
    
    # Analysis Results
    property_analysis: Optional[Dict[str, Any]] = None
    karst_analysis: Optional[Dict[str, Any]] = None
    flood_analysis: Optional[Dict[str, Any]] = None
    wetland_analysis: Optional[Dict[str, Any]] = None
    habitat_analysis: Optional[Dict[str, Any]] = None
    air_quality_analysis: Optional[Dict[str, Any]] = None
    
    # Generated Files
    comprehensive_reports: Optional[Dict[str, str]] = None  # {"json": "path", "markdown": "path", "pdf": "path"}
    maps_generated: Optional[List[str]] = None
    individual_reports: Optional[List[str]] = None
    
    # Summary Information
    environmental_constraints: Optional[List[str]] = None
    risk_level: Optional[str] = None
    regulatory_requirements: Optional[List[str]] = None
    
    # Error Information (if success=False)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

# Frontend API Templates
class EnvironmentalScreeningAPI:
    """Template class for environmental screening API implementation"""
    
    @staticmethod
    def create_screening_request_template():
        """Template for creating a screening request"""
        return {
            "endpoint": "/api/environmental-screening",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer <your_api_key>"
            },
            "body": {
                "project_name": "Cytoimmune Toa BAJA",
                "project_description": "Industrial Development Environmental Assessment", 
                "location_name": "Toa Baja, Puerto Rico",
                "cadastral_number": "060-000-009-58",
                "analyses_requested": ["property", "karst", "flood", "wetland", "habitat", "air_quality"],
                "include_comprehensive_report": True,
                "include_pdf": True,
                "use_llm_enhancement": True
            }
        }
    
    @staticmethod
    def get_screening_status_template():
        """Template for checking screening status"""
        return {
            "endpoint": "/api/environmental-screening/{screening_id}/status",
            "method": "GET",
            "headers": {
                "Authorization": "Bearer <your_api_key>"
            },
            "response": {
                "screening_id": "cytoimmune_toa_baja_screening",
                "status": "completed",  # "pending", "in_progress", "completed", "failed"
                "progress": 100,
                "current_step": "comprehensive_report_generation",
                "estimated_completion": "2025-05-28T10:10:51Z",
                "files_generated": 15,
                "project_directory": "output/Cytoimmune_Toa_BAJA_Environmental_Screening_2025-05-28_at_10.08.15"
            }
        }
    
    @staticmethod
    def get_screening_results_template():
        """Template for retrieving screening results"""
        return {
            "endpoint": "/api/environmental-screening/{screening_id}/results",
            "method": "GET", 
            "headers": {
                "Authorization": "Bearer <your_api_key>"
            },
            "response": {
                "success": True,
                "project_directory": "output/Cytoimmune_Toa_BAJA_Environmental_Screening_2025-05-28_at_10.08.15",
                "project_name": "Cytoimmune Toa BAJA",
                "analysis_summary": {
                    "property": {
                        "cadastral": "060-000-009-58",
                        "municipality": "Toa Baja",
                        "area_acres": 4.99,
                        "land_use": "Industrial Liviano",
                        "development_potential": "High"
                    },
                    "karst": {
                        "within_karst_area": False,
                        "nearby_karst": True,
                        "distance_miles": 0.3,
                        "regulatory_impact": "Moderate"
                    },
                    "flood": {
                        "flood_zone": "X",
                        "flood_risk": "Minimal",
                        "insurance_required": False
                    },
                    "wetland": {
                        "directly_on_property": False,
                        "nearby_wetlands": True,
                        "nearest_distance_miles": 0.4,
                        "regulatory_complexity": "Medium"
                    },
                    "habitat": {
                        "within_critical_habitat": False,
                        "nearby_habitat": True,
                        "affected_species": ["Llanero Coqui"],
                        "consultation_required": True
                    },
                    "air_quality": {
                        "meets_naaqs": True,
                        "nonattainment_status": False,
                        "compliance_status": "Compliant"
                    }
                },
                "comprehensive_reports": {
                    "json": "reports/comprehensive_screening_report_*.json",
                    "markdown": "reports/comprehensive_screening_report_*.md", 
                    "pdf": "reports/comprehensive_screening_report_*.pdf"
                },
                "maps_generated": [
                    "maps/wetland_map_*.pdf",
                    "maps/critical_habitat_map_*.pdf",
                    "maps/nonattainment_map_*.pdf"
                ],
                "environmental_constraints": [
                    "Nearby karst areas require special permits",
                    "Wetlands within 0.5 miles - delineation recommended",
                    "Critical habitat proximity - impact assessment needed"
                ],
                "risk_level": "Moderate",
                "regulatory_requirements": [
                    "Municipal industrial development permits",
                    "PRAPEC karst assessment due to proximity",
                    "Wetland delineation study recommended",
                    "ESA consultation with USFWS recommended"
                ]
            }
        }

# Frontend UI Component Templates
class UIComponentTemplates:
    """Templates for frontend UI components"""
    
    @staticmethod
    def screening_form_template():
        """Template for environmental screening form"""
        return {
            "form_fields": [
                {
                    "name": "project_name",
                    "label": "Project Name",
                    "type": "text",
                    "required": True,
                    "placeholder": "e.g., Cytoimmune Toa BAJA"
                },
                {
                    "name": "project_description", 
                    "label": "Project Description",
                    "type": "select",
                    "required": True,
                    "options": [
                        "Industrial Development Environmental Assessment",
                        "Residential Development Environmental Assessment", 
                        "Commercial Development Environmental Assessment",
                        "Marina Construction Environmental Screening",
                        "Property Environmental Due Diligence",
                        "Environmental Compliance Assessment",
                        "Custom Environmental Screening"
                    ]
                },
                {
                    "name": "location_input_type",
                    "label": "Location Input Method",
                    "type": "radio",
                    "options": [
                        {"value": "cadastral", "label": "Cadastral Number (Preferred)"},
                        {"value": "coordinates", "label": "Coordinates"},
                        {"value": "address", "label": "Address/Location Name"}
                    ]
                },
                {
                    "name": "cadastral_number",
                    "label": "Cadastral Number",
                    "type": "text",
                    "conditional": "location_input_type === 'cadastral'",
                    "placeholder": "e.g., 060-000-009-58"
                },
                {
                    "name": "coordinates",
                    "label": "Coordinates (Longitude, Latitude)",
                    "type": "coordinates",
                    "conditional": "location_input_type === 'coordinates'",
                    "placeholder": "e.g., -66.2097, 18.4154"
                },
                {
                    "name": "location_name",
                    "label": "Location Name",
                    "type": "text",
                    "placeholder": "e.g., Toa Baja, Puerto Rico"
                },
                {
                    "name": "analyses_requested",
                    "label": "Environmental Analyses",
                    "type": "checkbox_group",
                    "default_all_checked": True,
                    "options": [
                        {"value": "property", "label": "Property/Cadastral Analysis"},
                        {"value": "karst", "label": "Karst Analysis (Puerto Rico)"},
                        {"value": "flood", "label": "FEMA Flood Analysis"},
                        {"value": "wetland", "label": "Wetland Analysis"},
                        {"value": "habitat", "label": "Critical Habitat Analysis"},
                        {"value": "air_quality", "label": "Air Quality Analysis"}
                    ]
                },
                {
                    "name": "include_comprehensive_report",
                    "label": "Generate Comprehensive Report",
                    "type": "checkbox",
                    "default": True,
                    "description": "Includes JSON, Markdown, and PDF formats with embedded maps"
                },
                {
                    "name": "use_llm_enhancement",
                    "label": "Use AI Enhancement",
                    "type": "checkbox",
                    "default": True,
                    "description": "Enhanced analysis with AI-powered insights and recommendations"
                }
            ],
            "validation_rules": {
                "project_name": {"required": True, "min_length": 3},
                "project_description": {"required": True},
                "location_validation": {
                    "rule": "at_least_one_required",
                    "fields": ["cadastral_number", "coordinates", "location_name"]
                }
            }
        }
    
    @staticmethod
    def results_display_template():
        """Template for displaying screening results"""
        return {
            "sections": [
                {
                    "title": "Project Overview",
                    "fields": ["project_name", "location", "analysis_date", "project_directory"]
                },
                {
                    "title": "Property Information",
                    "fields": ["cadastral_number", "municipality", "area", "land_use", "zoning"]
                },
                {
                    "title": "Environmental Constraints",
                    "type": "constraint_cards",
                    "show_risk_indicators": True
                },
                {
                    "title": "Risk Assessment",
                    "type": "risk_gauge",
                    "fields": ["risk_level", "complexity_score", "development_feasibility"]
                },
                {
                    "title": "Regulatory Requirements",
                    "type": "requirement_checklist",
                    "priority_indicators": True
                },
                {
                    "title": "Generated Reports",
                    "type": "file_downloads",
                    "categories": ["comprehensive", "maps", "individual_reports"]
                },
                {
                    "title": "Recommendations",
                    "type": "recommendation_list",
                    "priority_sorting": True
                }
            ],
            "map_integration": {
                "show_interactive_map": True,
                "overlay_constraints": True,
                "download_static_maps": True
            }
        }

# =============================================================================
# AGENT PROMPTING TEMPLATES
# =============================================================================

class AgentPromptTemplates:
    """Templates for instructing the environmental screening agent"""
    
    @staticmethod
    def comprehensive_screening_command():
        """Template for comprehensive environmental screening command"""
        return """Generate a comprehensive environmental screening report for {project_name} with cadastral {cadastral_number} in {location}. I need complete property information, karst analysis, critical habitat analysis, air quality analysis, flood and wetland analysis with all reports, maps, and regulatory assessments."""
    
    @staticmethod
    def specific_analysis_commands():
        """Templates for specific analysis types"""
        return {
            "property_only": "Analyze property data for cadastral {cadastral_number} including land use, zoning, and development potential.",
            
            "flood_only": "Perform comprehensive flood analysis for {project_name} at coordinates {coordinates}. Generate FIRMette, preliminary comparison, and ABFE reports.",
            
            "wetland_only": "Conduct comprehensive wetland analysis for {project_name} at {location}. Include adaptive mapping and regulatory assessment.",
            
            "habitat_only": "Generate critical habitat analysis for {project_name} at coordinates {coordinates}. Include species identification and consultation requirements.",
            
            "air_quality_only": "Analyze air quality compliance for {project_name} at {location}. Check nonattainment status and regulatory requirements.",
            
            "karst_only": "Perform PRAPEC karst analysis for cadastral {cadastral_number} in Puerto Rico. Include regulatory compliance assessment.",
            
            "multi_cadastral": "Analyze multiple cadastrals {cadastral_list} for {project_name}. Include karst analysis and comprehensive environmental screening.",
            
            "coordinates_based": "Perform comprehensive environmental screening for {project_name} at coordinates {coordinates}. Include all applicable analyses and generate comprehensive reports."
        }
    
    @staticmethod
    def report_generation_commands():
        """Templates for report generation commands"""
        return {
            "auto_comprehensive": "Find the latest screening directory and generate comprehensive reports with embedded maps.",
            
            "specific_directory": "Generate comprehensive screening report for directory {project_directory} with PDF including embedded maps.",
            
            "custom_filename": "Generate comprehensive reports for latest screening with custom filename '{custom_name}'.",
            
            "format_specific": "Generate comprehensive reports in {format} format for latest screening directory.",
            
            "batch_processing": "Auto-discover all screening directories and generate comprehensive reports for each project."
        }
    
    @staticmethod
    def trigger_phrases():
        """Phrases that should trigger specific agent behaviors"""
        return {
            "comprehensive_screening": [
                "comprehensive environmental screening",
                "environmental assessment",
                "environmental screening report",
                "complete environmental analysis"
            ],
            "auto_report_generation": [
                "generate comprehensive report",
                "create PDF report", 
                "generate screening report",
                "comprehensive report with maps"
            ],
            "specific_analyses": {
                "flood": ["flood analysis", "FEMA analysis", "floodplain assessment"],
                "wetland": ["wetland analysis", "wetland assessment", "NWI analysis"],
                "habitat": ["critical habitat", "habitat analysis", "ESA consultation"], 
                "air_quality": ["air quality", "nonattainment", "EPA analysis"],
                "karst": ["karst analysis", "PRAPEC", "geological assessment"],
                "property": ["property analysis", "cadastral analysis", "land use"]
            }
        }

# =============================================================================
# COMMAND TEMPLATES FOR COMMON SCENARIOS
# =============================================================================

class CommandTemplates:
    """Pre-built command templates for common environmental screening scenarios"""
    
    @staticmethod
    def industrial_development_screening():
        """Template for industrial development projects"""
        template = """Generate a comprehensive environmental screening report for {project_name} industrial development project with cadastral {cadastral_number} in {location}. 

This is for an industrial facility requiring complete environmental due diligence including:
- Property/cadastral analysis with zoning verification
- PRAPEC karst analysis (Puerto Rico properties)
- FEMA flood analysis with insurance requirements
- Wetland analysis with regulatory compliance
- Critical habitat analysis with ESA consultation requirements
- Air quality analysis for industrial emissions compliance
- Comprehensive PDF report with all maps and regulatory assessments

Please organize all files in a descriptive project directory and generate professional reports suitable for permitting and regulatory submission."""
        
        return template
    
    @staticmethod
    def residential_development_screening():
        """Template for residential development projects"""
        template = """Generate a comprehensive environmental screening report for {project_name} residential development project with cadastral {cadastral_number} in {location}.

This is for a residential subdivision/development requiring:
- Property analysis with residential zoning verification
- Flood analysis for insurance and construction requirements
- Wetland analysis with setback requirements
- Critical habitat analysis for development restrictions
- Air quality compliance for residential standards
- Karst analysis if in Puerto Rico
- Complete reports package with maps for planning and permitting

Please create a descriptive project directory and generate comprehensive reports with embedded maps."""
        
        return template
    
    @staticmethod
    def commercial_development_screening():
        """Template for commercial development projects"""
        template = """Generate a comprehensive environmental screening report for {project_name} commercial development project with cadastral {cadastral_number} in {location}.

This is for commercial development requiring:
- Property/cadastral analysis with commercial zoning verification
- Comprehensive flood analysis for construction and insurance
- Wetland analysis with commercial development implications
- Critical habitat analysis with mitigation requirements
- Air quality analysis for commercial operations
- Complete regulatory compliance assessment
- Professional reports suitable for investor due diligence

Please organize in descriptive project directory and generate comprehensive PDF report with all environmental maps."""
        
        return template
    
    @staticmethod
    def marina_construction_screening():
        """Template for marina/waterfront projects"""
        template = """Generate a comprehensive environmental screening report for {project_name} marina construction project at coordinates {coordinates} in {location}.

This is for waterfront/marina development requiring specialized analysis:
- Comprehensive flood analysis with coastal considerations
- Detailed wetland analysis with aquatic impacts assessment
- Critical habitat analysis for marine/aquatic species
- Water quality and air quality compliance
- Property analysis for waterfront zoning
- Complete regulatory framework for marine construction

Please generate comprehensive reports with adaptive mapping focused on aquatic environmental factors."""
        
        return template
    
    @staticmethod
    def due_diligence_screening():
        """Template for environmental due diligence"""
        template = """Generate a comprehensive environmental screening report for {project_name} environmental due diligence assessment with cadastral {cadastral_number} in {location}.

This is for property acquisition due diligence requiring:
- Complete property/cadastral analysis with development constraints
- All applicable environmental analyses (flood, wetland, habitat, air quality, karst)
- Risk assessment with development feasibility analysis
- Regulatory compliance summary with permit requirements
- Professional reports suitable for real estate transactions
- Executive summary with key findings and recommendations

Please create comprehensive documentation package with all maps and supporting reports for stakeholder review."""
        
        return template

# =============================================================================
# EXAMPLE USAGE FUNCTIONS
# =============================================================================

class ExampleUsage:
    """Example implementations using the templates"""
    
    @staticmethod
    def run_cytoimmune_example():
        """Example: Run the Cytoimmune Toa BAJA screening"""
        
        # Using command template
        command_template = CommandTemplates.industrial_development_screening()
        command = command_template.format(
            project_name="Cytoimmune Toa BAJA",
            cadastral_number="060-000-009-58",
            location="Toa Baja, Puerto Rico"
        )
        
        print("🔄 Example Command:")
        print(command)
        
        # Expected response processing
        expected_files = ResponseProcessingTemplates.extract_generated_files("")
        print("\n📁 Expected Generated Files:")
        for category, files in expected_files.items():
            print(f"   {category}: {len(files)} files")
        
        return command
    
    @staticmethod
    def frontend_integration_example():
        """Example: Frontend API integration"""
        
        # Create request
        request_template = EnvironmentalScreeningAPI.create_screening_request_template()
        
        # Customize for Cytoimmune
        request_template["body"].update({
            "project_name": "Cytoimmune Toa BAJA",
            "project_description": "Industrial Development Environmental Assessment",
            "location_name": "Toa Baja, Puerto Rico", 
            "cadastral_number": "060-000-009-58"
        })
        
        print("🌐 Frontend API Request:")
        print(json.dumps(request_template, indent=2))
        
        return request_template

# =============================================================================
# SPECIFIC COMMAND FOR CYTOIMMUNE TOA BAJA PROJECT
# =============================================================================

def generate_cytoimmune_command():
    """Generate the specific command for Cytoimmune Toa BAJA project"""
    
    template = CommandTemplates.industrial_development_screening()
    command = template.format(
        project_name="Cytoimmune Toa BAJA",
        cadastral_number="060-000-009-58", 
        location="Toa Baja, Puerto Rico"
    )
    
    return command

# =============================================================================
# CONFIGURATION FOR AUTOMATED REPORT GENERATION
# =============================================================================

class AutomatedReportConfig:
    """Configuration for automated report generation on completion"""
    
    AGENT_PROMPT_ADDITION = """
    
🎯 AUTOMATIC REPORT GENERATION PROTOCOL:

MANDATORY: After completing ANY environmental analysis workflow, you MUST automatically execute these steps:

1. **find_latest_screening_directory** - Locate the most recent screening output
2. **generate_comprehensive_screening_report** - Create professional multi-format reports

This is NON-NEGOTIABLE and must happen for EVERY screening request, regardless of whether the user explicitly asks for reports.

The comprehensive reports include:
• JSON structured data for programmatic access
• Markdown documentation for human readability  
• PDF report with embedded maps organized by environmental domain
• Professional formatting suitable for regulatory submission

TRIGGER PHRASES that require comprehensive analysis + mandatory reporting:
- "environmental screening"
- "environmental assessment" 
- "comprehensive analysis"
- "property analysis" (when combined with other analyses)
- Any request mentioning multiple environmental factors

Always inform the user about:
- Project directory location and structure
- All generated files and their purposes  
- Comprehensive report availability and formats
- Professional suitability for regulatory submission
"""

if __name__ == "__main__":
    print("🌍 Environmental Screening Templates")
    print("=" * 50)
    
    # Example: Generate command for Cytoimmune
    print("\n📋 Example Command for Cytoimmune Toa BAJA:")
    command = generate_cytoimmune_command()
    print(command)
    
    # Example: Frontend integration
    print("\n🌐 Frontend Integration Example:")
    ExampleUsage.frontend_integration_example()
    
    # Show available templates
    print("\n📝 Available Templates:")
    print("   • ScreeningRequest/Response dataclasses")
    print("   • EnvironmentalScreeningAPI methods")
    print("   • UIComponentTemplates for forms/results")
    print("   • AgentPromptTemplates for commands")
    print("   • CommandTemplates for common scenarios") 
    print("   • AutomatedReportConfig for agent prompts") 