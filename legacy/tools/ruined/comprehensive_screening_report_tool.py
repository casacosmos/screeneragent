#!/usr/bin/env python3
"""
Comprehensive Screening Report Tool

A streamlined tool that automatically generates comprehensive environmental screening reports
from data folders in screening output directories. Designed to work seamlessly with the
environmental screening workflow.

Usage:
    python comprehensive_screening_report_tool.py <output_directory>
    python comprehensive_screening_report_tool.py output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# LangChain tool imports
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Import the enhanced generator
try:
    from llm_enhanced_report_generator import EnhancedComprehensiveReportGenerator
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    # Will warn only when actually trying to use LLM features

# Always import the base generator
from comprehensive_report_generator import ComprehensiveReportGenerator

# Import PDF generator
try:
    from pdf_report_generator import ScreeningPDFGenerator, StructuredPDFGenerator, STRUCTURED_OUTPUT_AVAILABLE
    PDF_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: PDF generation not available - install reportlab pillow")
    PDF_AVAILABLE = False
    STRUCTURED_OUTPUT_AVAILABLE = False

# Import HTML-based PDF generator
try:
    from html_pdf_generator import HTMLEnvironmentalPDFGenerator
    HTML_PDF_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: HTML PDF generation not available - install jinja2 weasyprint")
    HTML_PDF_AVAILABLE = False

# Pydantic input models for LangChain tools
class ScreeningReportInput(BaseModel):
    """Input schema for comprehensive screening report generation"""
    output_directory: str = Field(description="Screening output directory path (e.g., 'output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17')")
    output_format: str = Field(default="both", description="Output format: 'json', 'markdown', 'both'")
    custom_filename: Optional[str] = Field(default=None, description="Custom filename for reports (without extension)")
    include_pdf: bool = Field(default=True, description="Whether to generate PDF report with embedded maps")
    use_professional_html_pdf: bool = Field(default=True, description="Use professional HTML-based PDF generator with compliance checklist")
    use_llm: bool = Field(default=True, description="Whether to use LLM enhancement for analysis")
    model_name: str = Field(default="grok-3-mini-fast", description="LLM model to use for enhanced analysis")

class AutoDiscoveryInput(BaseModel):
    """Input schema for auto-discovery batch processing"""
    base_output_dir: str = Field(default="output", description="Base directory to search for screening projects")
    output_format: str = Field(default="both", description="Output format: 'json', 'markdown', 'both'")
    include_pdf: bool = Field(default=True, description="Whether to generate PDF reports with embedded maps")
    use_llm: bool = Field(default=True, description="Whether to use LLM enhancement for analysis")
    model_name: str = Field(default="grok-3-mini-fast", description="LLM model to use for enhancement")

class ScreeningReportTool:
    """Tool for generating comprehensive reports from screening output directories"""
    
    @staticmethod
    def configure_for_png_output():
        """Configure environmental analysis tools to prefer PNG output for better HTML embedding"""
        try:
            # Configure map generation tools to prefer PNG format
            import os
            
            # Set environment variables for map generation
            os.environ['SCREENING_MAP_FORMAT'] = 'PNG'
            os.environ['PREFER_PNG_MAPS'] = 'TRUE'
            
            print("🛠️ Configured environmental tools for PNG map output")
            print("   • Wetland maps will generate as PNG when possible")
            print("   • Critical habitat maps will generate as PNG when possible") 
            print("   • ABFE maps will generate as PNG when possible")
            print("   • Karst maps will generate embeddable PNG versions")
            
            return True
        except Exception as e:
            print(f"⚠️ Could not configure PNG output: {e}")
            return False
    
    def __init__(self, output_directory: str, output_format: str = "both", 
                 custom_filename: Optional[str] = None, include_pdf: bool = True,
                 use_professional_html_pdf: bool = True, use_llm: bool = True, 
                 model_name: str = "grok-3-mini-fast"):
        """
        Initialize the comprehensive screening report generator.
        
        Args:
            output_directory: Path to the screening output directory
            output_format: Format to generate ('json', 'markdown', 'both')
            custom_filename: Custom filename for reports (optional)
            include_pdf: Whether to generate PDF with embedded maps (ALWAYS FORCED TO TRUE)
            use_professional_html_pdf: Use professional HTML-based PDF generator with compliance checklist
            use_llm: Whether to use LLM enhancement for analysis
            model_name: LLM model to use for enhancement
        """
        self.output_directory = Path(output_directory).resolve()
        self.output_format = output_format
        self.custom_filename = custom_filename
        self.include_pdf = True  # ALWAYS TRUE - PDF generation is mandatory
        self.use_professional_html_pdf = use_professional_html_pdf
        self.use_llm = use_llm
        self.model_name = model_name
        
        # Configure for PNG output if using professional HTML PDF
        if self.use_professional_html_pdf:
            self.configure_for_png_output()
        
        # Initialize the data directory and report generator
        self.data_directory = self.output_directory / "data"
        if not self.data_directory.exists():
            raise ValueError(f"Data directory not found: {self.data_directory}")
        
        # Initialize the appropriate report generator
        self._initialize_generator()
    
    def _validate_directory_structure(self):
        """Validate the screening output directory structure"""
        
        if not self.output_directory.exists():
            raise FileNotFoundError(f"Output directory not found: {self.output_directory}")
        
        if not self.data_directory.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_directory}")
        
        # Check for JSON files
        json_files = list(self.data_directory.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in data directory: {self.data_directory}")
        
        print(f"✅ Found {len(json_files)} JSON data files in {self.data_directory}")
        
        # List the JSON files found
        for json_file in json_files:
            print(f"   📄 {json_file.name}")
    
    def _initialize_generator(self):
        """Initialize the appropriate report generator"""
        
        data_dir_str = str(self.data_directory)
        
        if self.use_llm and LLM_AVAILABLE:
            print(f"🤖 Initializing LLM-enhanced generator with model: {self.model_name}")
            try:
                self.generator = EnhancedComprehensiveReportGenerator(
                    data_directory=data_dir_str,
                    model_name=self.model_name,
                    use_llm=True
                )
                print("✅ LLM-enhanced generator initialized successfully")
            except Exception as e:
                print(f"⚠️ LLM initialization failed: {e}")
                print("Falling back to standard generator")
                self.generator = ComprehensiveReportGenerator(data_dir_str)
                self.use_llm = False
        else:
            print("📋 Using standard report generator")
            self.generator = ComprehensiveReportGenerator(data_dir_str)
    
    def generate_reports(self, output_format: str = "both", custom_filename: str = None, include_pdf: bool = True) -> Dict[str, str]:
        """Generate comprehensive screening reports"""
        
        print(f"\n🔄 Generating comprehensive screening reports...")
        print(f"📄 PDF Generation: {'ENABLED (MANDATORY)' if include_pdf else 'DISABLED'}")
        
        # Force PDF generation to True - it should always be enabled
        if not include_pdf:
            print("⚠️ WARNING: PDF generation was disabled but is MANDATORY - forcing enable")
            include_pdf = True
        
        # Determine output directory (reports folder)
        reports_dir = self.output_directory / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Generate base filename if not provided
        if custom_filename is None:
            # Extract project identifier from directory name
            project_id = self.output_directory.name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            custom_filename = f"comprehensive_screening_report_{project_id}_{timestamp}"
        
        output_files = {}
        
        try:
            if output_format in ["json", "both"]:
                json_filename = f"{custom_filename}.json"
                json_path = reports_dir / json_filename
                
                if hasattr(self.generator, 'export_enhanced_report_to_json') and self.use_llm:
                    json_file = self.generator.export_enhanced_report_to_json(str(json_path))
                else:
                    json_file = self.generator.export_to_json(str(json_path))
                
                output_files['json'] = json_file
                print(f"✅ JSON report generated: {json_file}")
            
            if output_format in ["markdown", "both"]:
                md_filename = f"{custom_filename}.md"
                md_path = reports_dir / md_filename
                
                if hasattr(self.generator, 'export_enhanced_report_to_markdown') and self.use_llm:
                    md_file = self.generator.export_enhanced_report_to_markdown(str(md_path))
                else:
                    md_file = self.generator.export_to_markdown(str(md_path))
                
                output_files['markdown'] = md_file
                print(f"✅ Markdown report generated: {md_file}")
            
            # MANDATORY PDF GENERATION - Always attempt to generate PDF
            pdf_generation_attempted = False
            if include_pdf:
                # Try Professional HTML-based PDF generation first (if enabled)
                if self.use_professional_html_pdf and HTML_PDF_AVAILABLE and 'json' in output_files:
                    try:
                        print(f"📄 Generating professional HTML-based PDF report...")
                        
                        # Ensure JSON file exists and is saved before using it
                        json_file = output_files.get('json')
                        if not json_file or not Path(json_file).exists():
                            print("⚠️ JSON file not found, creating it first...")
                            json_filename = f"{custom_filename}.json"
                            json_path = reports_dir / json_filename
                            
                            if hasattr(self.generator, 'export_enhanced_report_to_json') and self.use_llm:
                                json_file = self.generator.export_enhanced_report_to_json(str(json_path))
                            else:
                                json_file = self.generator.export_to_json(str(json_path))
                            
                            output_files['json'] = json_file
                        
                        html_pdf_generator = HTMLEnvironmentalPDFGenerator(
                            json_report_path=str(json_file),
                            project_directory=str(self.output_directory),
                            prefer_png_maps=True  # Prefer PNG for better HTML embedding
                        )
                        
                        # Generate professional PDF with compliance checklist
                        professional_pdf_path = html_pdf_generator.generate_pdf_report()
                        print(f"✅ Professional PDF with compliance checklist generated: {professional_pdf_path}")
                        
                        output_files['pdf'] = professional_pdf_path
                        pdf_generation_attempted = True
                        
                    except Exception as e:
                        print(f"⚠️ Professional HTML PDF generation failed: {e}")
                        print("Falling back to standard PDF generation...")
                
                # Fallback to standard PDF generation
                if not pdf_generation_attempted and PDF_AVAILABLE:
                    try:
                        print(f"📄 Generating standard PDF report...")
                        
                        # Check if we can use structured PDF generation
                        # Try to use structured PDF generation if we have enhanced data
                        structured_pdf_generated = False
                        if (STRUCTURED_OUTPUT_AVAILABLE and 
                            hasattr(self.generator, 'extract_with_llm_enhancement') and 
                            self.use_llm):
                            
                            try:
                                # Try structured approach if available
                                enhanced_data = self.generator.extract_with_llm_enhancement()
                                if enhanced_data:
                                    structured_generator = StructuredPDFGenerator(
                                        structured_data=enhanced_data.__dict__ if hasattr(enhanced_data, '__dict__') else enhanced_data,
                                        project_directory=str(self.output_directory),
                                        use_llm=self.use_llm
                                    )
                                    structured_pdf_path = structured_generator.generate_sophisticated_pdf_report()
                                    output_files['pdf'] = structured_pdf_path
                                    structured_pdf_generated = True
                                    print(f"✅ Structured PDF generated: {structured_pdf_path}")
                            except Exception as e:
                                print(f"⚠️ Structured PDF generation failed: {e}, using standard approach")
                        
                        # Standard PDF generation if structured failed
                        if not structured_pdf_generated:
                            pdf_generator = ScreeningPDFGenerator(
                                output_directory=str(self.output_directory),
                                use_llm=self.use_llm,
                                model_name=self.model_name
                            )
                            standard_pdf_path = pdf_generator.generate_pdf_report()
                            output_files['pdf'] = standard_pdf_path
                            print(f"✅ Standard PDF generated: {standard_pdf_path}")
                        
                        pdf_generation_attempted = True
                        
                    except Exception as e:
                        print(f"⚠️ Standard PDF generation failed: {e}")
                
                # Final fallback message
                if not pdf_generation_attempted:
                    print("❌ All PDF generation methods failed")
                    print("📄 Comprehensive JSON and Markdown reports are available")
                    if not PDF_AVAILABLE and not HTML_PDF_AVAILABLE:
                        print("💡 To enable PDF generation, install:")
                        print("   Standard PDF: pip install reportlab pillow PyPDF2")
                        print("   Professional PDF: pip install jinja2 weasyprint")
                else:
                    print(f"📄 PDF generation completed successfully")
            else:
                print("📄 PDF generation skipped (include_pdf=False)")
            
            # Ensure at least one report format was generated
            if not json_file and not md_file and 'pdf' not in output_files:
                raise Exception("No reports were generated successfully")
            
            return output_files
            
        except Exception as e:
            print(f"❌ Error generating reports: {e}")
            raise
    
    def _create_structured_data_for_pdf(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured data dictionary for sophisticated PDF generation"""
        
        # Helper function to safely convert dataclass to dict
        def safe_to_dict(obj):
            if obj is None:
                return None
            if hasattr(obj, '__dict__'):
                return {k: v for k, v in obj.__dict__.items()}
            return obj
        
        structured_data = {
            'success': True,
            'project_name': getattr(enhanced_data.get('project_info'), 'project_name', 'Environmental Screening Project'),
            'project_directory': str(self.output_directory),
            'screening_datetime_utc': datetime.now().isoformat(),
        }
        
        # Extract project information
        project_info = enhanced_data.get('project_info')
        if project_info:
            structured_data.update({
                'project_input_location_description': f"Cadastral {', '.join(project_info.cadastral_numbers)}" if hasattr(project_info, 'cadastral_numbers') and project_info.cadastral_numbers else "Location analysis",
                'project_input_coordinates_lng_lat': [project_info.longitude, project_info.latitude] if hasattr(project_info, 'longitude') and hasattr(project_info, 'latitude') else None
            })
        
        # Convert analysis sections to structured format
        analysis_sections = ['cadastral_analysis', 'flood_analysis', 'wetland_analysis', 'critical_habitat_analysis', 'air_quality_analysis', 'karst_analysis']
        
        for section in analysis_sections:
            section_data = enhanced_data.get(section)
            if section_data:
                structured_data[section] = safe_to_dict(section_data)
        
        # Add comprehensive report paths if available
        comprehensive_reports = {}
        reports_dir = self.output_directory / "reports"
        
        # Look for generated comprehensive reports
        for report_file in reports_dir.glob("comprehensive_screening_report_*.json"):
            comprehensive_reports['json_report'] = f"reports/{report_file.name}"
            break
            
        for report_file in reports_dir.glob("comprehensive_screening_report_*.md"):
            comprehensive_reports['markdown'] = f"reports/{report_file.name}"
            break
        
        if comprehensive_reports:
            structured_data['comprehensive_reports'] = comprehensive_reports
        
        # Extract maps from the directories
        maps_other = []
        maps_dir = self.output_directory / "maps"
        if maps_dir.exists():
            for map_file in maps_dir.glob("*.pdf"):
                maps_other.append(f"maps/{map_file.name}")
        
        if maps_other:
            structured_data['maps_generated_other'] = maps_other
        
        # Extract executive summary components if available
        if enhanced_data.get('executive_summary'):
            exec_summary = enhanced_data['executive_summary']
            if hasattr(exec_summary, 'key_environmental_constraints'):
                structured_data['environmental_constraints_summary'] = exec_summary.key_environmental_constraints
            if hasattr(exec_summary, 'primary_recommendations'):
                structured_data['agent_recommendations'] = exec_summary.primary_recommendations
        
        # Extract risk assessment if available
        if enhanced_data.get('enhanced_risk'):
            risk = enhanced_data['enhanced_risk']
            structured_data['overall_risk_level_assessment'] = getattr(risk, 'risk_level', 'Not assessed')
            structured_data['key_regulatory_requirements_identified'] = getattr(risk, 'regulatory_concerns', [])
            structured_data['narrative_summary_of_findings'] = getattr(risk, 'reasoning', '')
        
        return structured_data
    
    def display_summary(self):
        """Display a summary of the screening analysis"""
        
        try:
            # Generate report object for summary
            if hasattr(self.generator, 'generate_enhanced_comprehensive_report') and self.use_llm:
                report = self.generator.generate_enhanced_comprehensive_report()
            else:
                report = self.generator.generate_comprehensive_report()
            
            print(f"\n📊 SCREENING ANALYSIS SUMMARY")
            print("=" * 60)
            
            # Project Information
            print(f"🏠 Project: {report.project_info.project_name}")
            print(f"📍 Location: {report.project_info.latitude:.6f}, {report.project_info.longitude:.6f}")
            print(f"📅 Analysis Date: {report.project_info.analysis_date_time}")
            
            if report.project_info.cadastral_numbers:
                print(f"🗺️  Cadastral: {', '.join(report.project_info.cadastral_numbers)}")
            
            # Property Details
            if report.cadastral_analysis:
                ca = report.cadastral_analysis
                print(f"🏘️  Municipality: {ca.municipality}")
                print(f"📐 Area: {ca.area_acres:.2f} acres ({ca.area_hectares:.2f} hectares)")
                print(f"🏗️  Land Use: {ca.land_use_classification}")
            
            # Environmental Constraints
            print(f"\n⚠️  ENVIRONMENTAL CONSTRAINTS:")
            for i, constraint in enumerate(report.executive_summary.key_environmental_constraints, 1):
                print(f"   {i}. {constraint}")
            
            # Risk Assessment
            risk_info = report.cumulative_risk_assessment
            print(f"\n📊 RISK ASSESSMENT:")
            print(f"   Overall Risk: {risk_info.get('overall_risk_profile', 'Not assessed')}")
            print(f"   Development Feasibility: {risk_info.get('development_feasibility', 'Not assessed')}")
            print(f"   Complexity Score: {risk_info.get('complexity_score', 'N/A')}")
            
            if self.use_llm and risk_info.get('enhanced_assessment'):
                print("   🤖 Enhanced with AI analysis")
            
            # Key Recommendations
            print(f"\n💡 PRIMARY RECOMMENDATIONS:")
            for i, rec in enumerate(report.recommendations[:5], 1):  # Top 5
                print(f"   {i}. {rec}")
            
            # Generated Files
            print(f"\n📁 GENERATED FILES ({len(report.generated_files)}):")
            file_categories = {'maps': [], 'reports': [], 'logs': [], 'other': []}
            
            for file in report.generated_files:
                if file.startswith('maps/'):
                    file_categories['maps'].append(file)
                elif file.startswith('reports/'):
                    file_categories['reports'].append(file)
                elif file.startswith('logs/'):
                    file_categories['logs'].append(file)
                else:
                    file_categories['other'].append(file)
            
            for category, files in file_categories.items():
                if files:
                    print(f"   {category.title()}: {len(files)} files")
                    for file in files[:3]:  # Show first 3
                        print(f"     - {file}")
                    if len(files) > 3:
                        print(f"     ... and {len(files) - 3} more")
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
    
    def get_analysis_data(self) -> Dict[str, Any]:
        """Get the raw analysis data for programmatic access"""
        
        if hasattr(self.generator, 'extract_with_llm_enhancement') and self.use_llm:
            return self.generator.extract_with_llm_enhancement()
        else:
            return {
                'project_info': self.generator.extract_project_info(),
                'cadastral': self.generator.extract_cadastral_analysis(),
                'flood': self.generator.extract_flood_analysis(),
                'wetland': self.generator.extract_wetland_analysis(),
                'habitat': self.generator.extract_critical_habitat_analysis(),
                'air_quality': self.generator.extract_air_quality_analysis(),
            }


def find_screening_directories(base_path: str = "output") -> List[Path]:
    """Find all screening output directories"""
    
    base_path = Path(base_path)
    if not base_path.exists():
        return []
    
    screening_dirs = []
    for item in base_path.iterdir():
        if item.is_dir():
            data_dir = item / "data"
            if data_dir.exists() and list(data_dir.glob("*.json")):
                screening_dirs.append(item)
    
    return screening_dirs


def auto_discover_and_process(base_output_dir: str = "output", 
                             use_llm: bool = True, 
                             output_format: str = "both",
                             include_pdf: bool = True) -> Dict[str, List[str]]:
    """Auto-discover and process all screening directories"""
    
    print(f"🔍 Auto-discovering screening directories in: {base_output_dir}")
    
    # FORCE PDF generation to True - it is MANDATORY
    if not include_pdf:
        print("⚠️ PDF generation was disabled but is MANDATORY - forcing enable")
        include_pdf = True
    
    print(f"📄 PDF Generation: ENABLED (MANDATORY) for all discovered projects")
    
    screening_dirs = find_screening_directories(base_output_dir)
    
    if not screening_dirs:
        print(f"❌ No screening directories found in {base_output_dir}")
        return {}
    
    print(f"✅ Found {len(screening_dirs)} screening directories")
    
    results = {}
    
    for i, screening_dir in enumerate(screening_dirs, 1):
        print(f"\n📁 Processing {i}/{len(screening_dirs)}: {screening_dir.name}")
        
        try:
            tool = ScreeningReportTool(
                output_directory=str(screening_dir),
                use_llm=use_llm
            )
            
            output_files = tool.generate_reports(
                output_format=output_format,
                include_pdf=True  # Always force PDF generation
            )
            results[str(screening_dir)] = list(output_files.values())
            
            # Check if PDF was generated
            pdf_generated = any(f.endswith('.pdf') for f in output_files.values())
            if pdf_generated:
                print(f"✅ Successfully processed {screening_dir.name} (PDF included)")
            else:
                print(f"⚠️ Processed {screening_dir.name} but PDF generation may have failed")
            
        except Exception as e:
            print(f"❌ Error processing {screening_dir.name}: {e}")
            results[str(screening_dir)] = []
    
    return results


def main():
    """Main function for command-line usage"""
    
    parser = argparse.ArgumentParser(
        description='Generate comprehensive screening reports from environmental analysis data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific screening directory
  python comprehensive_screening_report_tool.py output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17

  # Auto-discover and process all screening directories
  python comprehensive_screening_report_tool.py --auto-discover

  # Generate only JSON format with custom filename
  python comprehensive_screening_report_tool.py output/MyProject --format json --output my_report

  # Use standard processing (no LLM)
  python comprehensive_screening_report_tool.py output/MyProject --no-llm
        """
    )
    
    parser.add_argument('output_directory', nargs='?', 
                       help='Screening output directory (e.g., output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17)')
    parser.add_argument('--auto-discover', action='store_true',
                       help='Auto-discover and process all screening directories in output/')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                       help='Output format (default: both)')
    parser.add_argument('--output', help='Custom output filename (without extension)')
    parser.add_argument('--model', default='grok-3-mini-fast',
                       help='LLM model to use for enhanced processing (default: grok-3-mini-fast)')
    parser.add_argument('--no-llm', action='store_true',
                       help='Disable LLM enhancement and use standard processing')
    parser.add_argument('--no-pdf', action='store_true',
                       help='Disable PDF generation (only generate JSON/Markdown)')
    parser.add_argument('--summary-only', action='store_true',
                       help='Display summary only, do not generate report files')
    parser.add_argument('--base-dir', default='output',
                       help='Base directory for auto-discovery (default: output)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.auto_discover and not args.output_directory:
        parser.error("Either provide an output_directory or use --auto-discover")
    
    print("🌍 Comprehensive Environmental Screening Report Tool")
    print("=" * 60)
    
    if args.auto_discover:
        # Auto-discover mode
        print(f"🔄 Auto-discovering screening directories...")
        
        results = auto_discover_and_process(
            base_output_dir=args.base_dir,
            use_llm=not args.no_llm,
            output_format=args.format,
            include_pdf=not args.no_pdf
        )
        
        # Summary
        print(f"\n📊 BATCH PROCESSING SUMMARY:")
        print(f"   Total directories processed: {len(results)}")
        print(f"   Successful: {sum(1 for files in results.values() if files)}")
        print(f"   Failed: {sum(1 for files in results.values() if not files)}")
        
        successful_reports = sum(len(files) for files in results.values())
        print(f"   Total reports generated: {successful_reports}")
        
    else:
        # Single directory mode
        try:
            tool = ScreeningReportTool(
                output_directory=args.output_directory,
                use_llm=not args.no_llm,
                model_name=args.model
            )
            
            # Display summary
            tool.display_summary()
            
            if not args.summary_only:
                # Generate reports
                output_files = tool.generate_reports(
                    output_format=args.format,
                    custom_filename=args.output,
                    include_pdf=not args.no_pdf
                )
                
                print(f"\n✅ Report generation complete!")
                print(f"📁 Reports saved to: {Path(args.output_directory) / 'reports'}")
                for format_type, file_path in output_files.items():
                    print(f"   {format_type.upper()}: {Path(file_path).name}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    print(f"\n{'🤖' if not args.no_llm and LLM_AVAILABLE else '📋'} Processing complete!")
    return 0


# LangChain Tool Functions for Agent Integration

@tool("generate_comprehensive_screening_report", args_schema=ScreeningReportInput)
def generate_comprehensive_screening_report(
    output_directory: str,
    output_format: str = "both",
    custom_filename: Optional[str] = None,
    include_pdf: bool = True,
    use_professional_html_pdf: bool = True,
    use_llm: bool = True,
    model_name: str = "grok-3-mini-fast"
) -> Dict[str, Any]:
    """
    Generate comprehensive environmental screening reports from screening output directory.
    
    This tool processes JSON data from the data folder of a screening output directory and
    generates professional reports in multiple formats (JSON, Markdown, PDF) with embedded
    maps and comprehensive analysis following the 11-section environmental screening schema.
    
    **CRITICAL: PDF GENERATION IS MANDATORY AND ALWAYS ENABLED**
    
    **Key Features:**
    - Processes JSON data from data/ folder
    - Embeds maps automatically in PDF by environmental domain
    - Generates all 11 schema sections (Project Info, Executive Summary, etc.)
    - Optional LLM enhancement for intelligent analysis
    - **Professional PDF output suitable for regulatory submission (MANDATORY)**
    
    Args:
        output_directory: Screening output directory path
        output_format: Output format ('json', 'markdown', 'both')
        custom_filename: Custom filename for reports (optional)
        include_pdf: Whether to generate PDF with embedded maps (ALWAYS FORCED TO TRUE)
        use_professional_html_pdf: Use professional HTML-based PDF generator with compliance checklist
        use_llm: Whether to use LLM enhancement for analysis
        model_name: LLM model to use for enhancement
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - output_files: List of generated report files
        - project_info: Project details extracted from data
        - summary: Analysis summary
        - file_counts: Count of maps, reports, data files processed
        - pdf_generated: Boolean confirming PDF was created
    """
    
    try:
        print(f"🔄 Generating comprehensive screening reports for: {output_directory}")
        
        # FORCE PDF generation to True - it is MANDATORY
        if not include_pdf:
            print("⚠️ PDF generation was disabled but is MANDATORY - forcing enable")
            include_pdf = True
        
        print(f"📄 PDF Generation: ENABLED (MANDATORY)")
        
        # Validate directory exists
        if not Path(output_directory).exists():
            return {
                "success": False,
                "error": f"Output directory not found: {output_directory}",
                "suggestion": "Ensure the screening directory exists and contains a data/ folder with JSON files"
            }
        
        # Initialize the screening report tool
        tool = ScreeningReportTool(
            output_directory=output_directory,
            use_llm=use_llm,
            model_name=model_name
        )
        
        # Generate reports (PDF is forced to True)
        output_files = tool.generate_reports(
            output_format=output_format,
            custom_filename=custom_filename,
            include_pdf=True  # Always force PDF generation
        )
        
        # Check if PDF was generated successfully
        pdf_generated = 'pdf' in output_files and output_files['pdf']
        pdf_error = output_files.get('pdf_error')
        
        # Get analysis data for summary
        analysis_data = tool.get_analysis_data()
        project_info = analysis_data.get('project_info')
        
        # Count processed files
        file_counts = {
            "json_data_files": len(tool.generator.json_files),
            "maps_found": len([f for f in Path(output_directory).glob("maps/*") if f.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']]),
            "reports_generated": len([f for f in output_files.values() if not f.startswith('PDF generation')])
        }
        
        # Create summary
        summary = f"Successfully processed {file_counts['json_data_files']} JSON data files"
        if project_info:
            if hasattr(project_info, 'cadastral_numbers') and project_info.cadastral_numbers:
                summary += f" for cadastral {', '.join(project_info.cadastral_numbers)}"
            if hasattr(project_info, 'project_name'):
                summary += f" ({project_info.project_name})"
        
        # Add PDF generation status to summary
        if pdf_generated:
            summary += f". PDF report successfully generated."
        elif pdf_error:
            summary += f". WARNING: PDF generation failed - {pdf_error}"
        
        print(f"✅ Generated {len(output_files)} report files successfully")
        if pdf_generated:
            print(f"📄 PDF report confirmed: {output_files['pdf']}")
        elif pdf_error:
            print(f"❌ PDF generation issue: {pdf_error}")
        
        return {
            "success": True,
            "output_files": list(output_files.values()),
            "output_formats": list(output_files.keys()),
            "pdf_generated": pdf_generated,
            "pdf_file": output_files.get('pdf', 'Not generated'),
            "pdf_error": pdf_error,
            "project_info": {
                "project_name": project_info.project_name if project_info else "Unknown",
                "cadastral_numbers": project_info.cadastral_numbers if project_info else [],
                "coordinates": f"{project_info.latitude:.6f}, {project_info.longitude:.6f}" if project_info else "Unknown",
                "analysis_date": project_info.analysis_date_time if project_info else datetime.now().isoformat()
            },
            "summary": summary,
            "file_counts": file_counts,
            "llm_enhanced": use_llm and LLM_AVAILABLE,
            "pdf_mandatory_status": "PDF generation is MANDATORY and was attempted",
            "output_directory": output_directory
        }
        
    except Exception as e:
        print(f"❌ Error generating comprehensive reports: {e}")
        return {
            "success": False,
            "error": str(e),
            "output_directory": output_directory,
            "pdf_generated": False,
            "pdf_error": f"Report generation failed: {str(e)}",
            "suggestion": "Check that the directory contains valid JSON data files and required dependencies are installed"
        }


@tool("auto_discover_and_generate_reports", args_schema=AutoDiscoveryInput)
def auto_discover_and_generate_reports(
    base_output_dir: str = "output",
    output_format: str = "both", 
    include_pdf: bool = True,
    use_llm: bool = True,
    model_name: str = "grok-3-mini-fast"
) -> Dict[str, Any]:
    """
    Auto-discover screening directories and generate comprehensive reports for all projects.
    
    This tool automatically finds all screening output directories in the base directory
    and generates comprehensive environmental reports for each project found. Perfect for
    batch processing multiple screening projects.
    
    **CRITICAL: PDF GENERATION IS MANDATORY AND ALWAYS ENABLED**
    
    **Features:**
    - Automatic discovery of screening directories with data/ folders
    - Batch processing of multiple projects
    - Comprehensive reports for each project
    - **PDF reports with embedded maps for all projects (MANDATORY)**
    - Summary statistics of processing results
    
    Args:
        base_output_dir: Base directory to search for screening projects
        output_format: Output format ('json', 'markdown', 'both')
        include_pdf: Whether to generate PDF reports with embedded maps (ALWAYS FORCED TO TRUE)
        use_llm: Whether to use LLM enhancement for analysis
        model_name: LLM model to use for enhancement
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating overall success
        - projects_processed: List of processed project details
        - summary_stats: Statistics about processing results
        - failed_projects: List of projects that failed processing
        - pdf_generation_summary: Summary of PDF generation results
    """
    
    try:
        print(f"🔍 Auto-discovering screening directories in: {base_output_dir}")
        
        # FORCE PDF generation to True - it is MANDATORY
        if not include_pdf:
            print("⚠️ PDF generation was disabled but is MANDATORY - forcing enable")
            include_pdf = True
        
        print(f"📄 PDF Generation: ENABLED (MANDATORY) for all projects")
        
        # Use existing auto-discovery function (with forced PDF generation)
        results = auto_discover_and_process(
            base_output_dir=base_output_dir,
            use_llm=use_llm,
            output_format=output_format,
            include_pdf=True  # Always force PDF generation
        )
        
        # Process results
        successful_projects = []
        failed_projects = []
        pdf_success_count = 0
        pdf_failure_count = 0
        
        for directory, files in results.items():
            project_name = Path(directory).name
            if files:
                # Check if PDF was generated
                pdf_files = [f for f in files if f.endswith('.pdf')]
                pdf_generated = len(pdf_files) > 0
                
                if pdf_generated:
                    pdf_success_count += 1
                else:
                    pdf_failure_count += 1
                
                successful_projects.append({
                    "project_name": project_name,
                    "directory": directory,
                    "reports_generated": len(files),
                    "output_files": files,
                    "pdf_generated": pdf_generated,
                    "pdf_files": pdf_files
                })
            else:
                failed_projects.append({
                    "project_name": project_name,
                    "directory": directory,
                    "error": "No reports generated",
                    "pdf_generated": False
                })
                pdf_failure_count += 1
        
        # Summary statistics
        total_projects = len(results)
        successful_count = len(successful_projects)
        failed_count = len(failed_projects)
        total_reports = sum(len(files) for files in results.values())
        
        summary_stats = {
            "total_projects_found": total_projects,
            "successful_projects": successful_count,
            "failed_projects": failed_count,
            "total_reports_generated": total_reports,
            "success_rate": f"{(successful_count/total_projects*100):.1f}%" if total_projects > 0 else "0%",
            "pdf_success_count": pdf_success_count,
            "pdf_failure_count": pdf_failure_count,
            "pdf_success_rate": f"{(pdf_success_count/total_projects*100):.1f}%" if total_projects > 0 else "0%"
        }
        
        pdf_generation_summary = {
            "total_projects": total_projects,
            "pdf_generated_successfully": pdf_success_count,
            "pdf_generation_failed": pdf_failure_count,
            "pdf_mandatory_status": "PDF generation is MANDATORY for all projects"
        }
        
        print(f"✅ Batch processing complete: {successful_count}/{total_projects} projects successful")
        print(f"📄 PDF Generation: {pdf_success_count}/{total_projects} PDFs generated successfully")
        
        return {
            "success": successful_count > 0,
            "projects_processed": successful_projects,
            "failed_projects": failed_projects,
            "summary_stats": summary_stats,
            "pdf_generation_summary": pdf_generation_summary,
            "base_directory": base_output_dir,
            "llm_enhanced": use_llm and LLM_AVAILABLE,
            "pdf_mandatory_status": "PDF generation is MANDATORY and was attempted for all projects"
        }
        
    except Exception as e:
        print(f"❌ Error in auto-discovery: {e}")
        return {
            "success": False,
            "error": str(e),
            "base_directory": base_output_dir,
            "pdf_generated": False,
            "pdf_error": f"Auto-discovery failed: {str(e)}",
            "suggestion": "Ensure the base directory exists and contains screening project directories"
        }


@tool("find_latest_screening_directory")
def find_latest_screening_directory(base_dir: str = "output") -> Dict[str, Any]:
    """
    Find the most recently created screening directory for report generation.
    
    This tool searches for screening output directories and returns the most recent one
    based on creation time or directory name timestamp. Useful for automatically 
    processing the latest screening results.
    
    Args:
        base_dir: Base directory to search for screening projects
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if a directory was found
        - latest_directory: Path to the most recent screening directory
        - project_name: Name of the latest project
        - creation_time: When the directory was created
        - available_directories: List of all found screening directories
    """
    
    try:
        print(f"🔍 Finding latest screening directory in: {base_dir}")
        
        # Find all screening directories
        screening_dirs = find_screening_directories(base_dir)
        
        if not screening_dirs:
            return {
                "success": False,
                "error": f"No screening directories found in {base_dir}",
                "suggestion": "Run environmental screening tools first to generate data"
            }
        
        # Sort by modification time (most recent first)
        screening_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_dir = screening_dirs[0]
        
        # Get directory info
        creation_time = datetime.fromtimestamp(latest_dir.stat().st_mtime)
        
        print(f"✅ Found latest screening directory: {latest_dir.name}")
        
        return {
            "success": True,
            "latest_directory": str(latest_dir),
            "project_name": latest_dir.name,
            "creation_time": creation_time.isoformat(),
            "available_directories": [str(d) for d in screening_dirs],
            "total_directories": len(screening_dirs)
        }
        
    except Exception as e:
        print(f"❌ Error finding latest directory: {e}")
        return {
            "success": False,
            "error": str(e),
            "base_directory": base_dir
        }


# Export tools for easy import
COMPREHENSIVE_SCREENING_TOOLS = [
    generate_comprehensive_screening_report,
    auto_discover_and_generate_reports, 
    find_latest_screening_directory
]


if __name__ == "__main__":
    exit(main()) 