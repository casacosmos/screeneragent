#!/usr/bin/env python3
"""
PDF Comprehensive Environmental Screening Report Generator

Generates professional PDF reports that combine:
- Analysis from JSON data files in the data folder
- Maps and reports from the screening directory
- Organized according to the 11-section environmental screening schema
- Appends pages from associated PDF maps and reports into a single flat file.

Requirements:
    pip install reportlab pillow PyPDF2
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import glob
import io # For in-memory PDF generation

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
        PageBreak, KeepTogether, NextPageTemplate, PageTemplate
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: ReportLab not available. Install with: pip install reportlab pillow")
    REPORTLAB_AVAILABLE = False

# PDF Merging imports
try:
    from PyPDF2 import PdfWriter, PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: PyPDF2 not available. Install with: pip install PyPDF2")
    PYPDF2_AVAILABLE = False

# Import our report generators
try:
    from llm_enhanced_report_generator import EnhancedComprehensiveReportGenerator
    from comprehensive_report_generator import ComprehensiveReportGenerator, ComprehensiveReport
    LLM_AVAILABLE = True
except ImportError:
    from comprehensive_report_generator import ComprehensiveReportGenerator, ComprehensiveReport
    LLM_AVAILABLE = False


class ScreeningPDFGenerator:
    """Professional PDF generator for comprehensive environmental screening reports"""
    
    def __init__(self, output_directory: str, use_llm: bool = True, model_name: str = "gpt-4o-mini"):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab pillow")
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 is required for PDF merging. Install with: pip install PyPDF2")
        
        self.output_directory = Path(output_directory).resolve()
        self.data_directory = self.output_directory / "data"
        self.maps_directory = self.output_directory / "maps"
        self.reports_directory = self.output_directory / "reports"
        self.use_llm = use_llm and LLM_AVAILABLE
        
        self._initialize_data_generator(model_name)
        self._setup_pdf_styles()
        self._collect_files()
    
    def _initialize_data_generator(self, model_name: str):
        """Initialize the appropriate data generator"""
        data_dir_str = str(self.data_directory)
        
        if self.use_llm and LLM_AVAILABLE:
            try:
                self.data_generator = EnhancedComprehensiveReportGenerator(
                    data_directory=data_dir_str,
                    model_name=model_name,
                    use_llm=True
                )
                print("✅ Using LLM-enhanced data analysis")
            except Exception as e:
                print(f"⚠️ LLM initialization failed: {e}, using standard generator")
                self.data_generator = ComprehensiveReportGenerator(data_dir_str)
                self.use_llm = False
        else:
            self.data_generator = ComprehensiveReportGenerator(data_dir_str)
    
    def _setup_pdf_styles(self):
        """Set up PDF styles and formatting"""
        self.styles = getSampleStyleSheet()
        
        style_names = [style.name for style in self.styles.byName.values()]
        
        if 'CustomTitle' not in style_names:
            self.styles.add(ParagraphStyle(
                name='CustomTitle', parent=self.styles['Title'], fontSize=24,
                textColor=colors.darkblue, spaceAfter=30, alignment=TA_CENTER
            ))
        if 'SectionHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SectionHeader', parent=self.styles['Heading1'], fontSize=16,
                textColor=colors.darkblue, spaceAfter=12, spaceBefore=20,
                borderWidth=1, borderColor=colors.darkblue, borderPadding=5,
                backColor=colors.lightblue
            ))
        if 'SubSectionHeader' not in style_names:
            self.styles.add(ParagraphStyle(
                name='SubSectionHeader', parent=self.styles['Heading2'], fontSize=14,
                textColor=colors.darkgreen, spaceAfter=10, spaceBefore=15
            ))
        if 'BodyText' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BodyText', parent=self.styles['Normal'], fontSize=11,
                spaceAfter=6, alignment=TA_JUSTIFY
            ))
        if 'BulletList' not in style_names:
            self.styles.add(ParagraphStyle(
                name='BulletList', parent=self.styles['Normal'], fontSize=10,
                spaceAfter=3, leftIndent=20, bulletIndent=10
            ))
        if 'Caption' not in style_names:
            self.styles.add(ParagraphStyle(
                name='Caption', parent=self.styles['Normal'], fontSize=9,
                textColor=colors.grey, alignment=TA_CENTER, spaceAfter=10
            ))
    
    def _collect_files(self):
        """Collect and categorize all files from the screening directory"""
        self.file_inventory = {
            'maps': {}, 'reports': {}, 'data': {}, 'logs': {}
        }
        
        # Maps directory
        if self.maps_directory.exists():
            for map_file in self.maps_directory.glob("*"):
                if map_file.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                    category = self._categorize_map_file(map_file.name)
                    self.file_inventory['maps'].setdefault(category, []).append(map_file)
        
        # Reports directory
        if self.reports_directory.exists():
            # First, check if comprehensive flood report exists
            comprehensive_flood_exists = any(
                "comprehensive_flood_report" in report_file.name.lower()
                for report_file in self.reports_directory.glob("*.pdf")
            )
            
            for report_file in self.reports_directory.glob("*.pdf"):
                # Avoid re-adding the main report if it's already generated by a previous run
                if "comprehensive_environmental_screening_report" not in report_file.name:
                    # Skip individual flood reports if comprehensive flood report exists
                    if comprehensive_flood_exists and self._is_individual_flood_report(report_file.name):
                        print(f"  ⚠️ Skipping individual flood report {report_file.name} (included in comprehensive flood report)")
                        continue
                    
                    category = self._categorize_report_file(report_file.name)
                    self.file_inventory['reports'].setdefault(category, []).append(report_file)

        # Data directory (JSON files)
        if self.data_directory.exists():
            for data_file in self.data_directory.glob("*.json"):
                category = self._categorize_data_file(data_file.name)
                self.file_inventory['data'].setdefault(category, []).append(data_file)

    def _categorize_map_file(self, filename: str) -> str:
        filename_lower = filename.lower()
        if 'flood' in filename_lower or 'fema' in filename_lower or 'firm' in filename_lower: return 'flood'
        if 'wetland' in filename_lower or 'nwi' in filename_lower: return 'wetland'
        if 'habitat' in filename_lower or 'critical' in filename_lower or 'species' in filename_lower: return 'habitat'
        if 'nonattainment' in filename_lower or 'air' in filename_lower: return 'air_quality'
        if 'karst' in filename_lower or 'geology' in filename_lower: return 'karst'
        if 'cadastral' in filename_lower or 'property' in filename_lower: return 'cadastral'
        return 'general'

    _categorize_report_file = _categorize_map_file
    _categorize_data_file = _categorize_map_file

    def _is_individual_flood_report(self, filename: str) -> bool:
        """Check if a file is an individual flood report that would be included in comprehensive flood report"""
        filename_lower = filename.lower()
        individual_flood_patterns = [
            'firmette_', 'preliminary_comparison_', 'abfe_map_'
        ]
        return any(pattern in filename_lower for pattern in individual_flood_patterns)

    def generate_pdf_report(self, output_filename: str = None) -> str:
        """Generate the comprehensive PDF report, merging other PDFs."""
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = self.output_directory.name
            output_filename = f"comprehensive_environmental_screening_report_{project_id}_{timestamp}.pdf"
        
        # Save PDF directly to the reports directory
        pdf_output_dir = self.output_directory / "reports"
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        final_pdf_path = pdf_output_dir / output_filename
        
        print(f"🔄 Generating comprehensive PDF report (will merge attachments): {final_pdf_path}")
        
        if hasattr(self.data_generator, 'generate_enhanced_comprehensive_report') and self.use_llm:
            self.report_data = self.data_generator.generate_enhanced_comprehensive_report()
        else:
            self.report_data = self.data_generator.generate_comprehensive_report()

        # Generate main report content in memory
        main_report_buffer = io.BytesIO()
        doc = SimpleDocTemplate(main_report_buffer, pagesize=A4,
                                rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = self._build_main_report_story()
        
        try:
            doc.build(story)
            print("✅ Main report content generated in memory.")
        except Exception as e:
            print(f"❌ Error building main report content: {e}")
            raise
        
        main_report_buffer.seek(0) # Reset buffer position to the beginning

        # Start merging PDFs
        pdf_writer = PdfWriter()
        
        # Add main report content
        try:
            main_report_reader = PdfReader(main_report_buffer)
            for page in main_report_reader.pages:
                pdf_writer.add_page(page)
            print(f"📄 Added {len(main_report_reader.pages)} pages from main report.")
        except Exception as e:
            print(f"❌ Error reading main report from buffer for merging: {e}")
            # Continue to try and save attachments if main report fails to add
            # This part might need more robust error handling or decision logic
            pass # Or `raise` if main content is critical

        # Append categorized maps (PDFs only)
        appended_map_files = self._append_pdf_files_from_category(pdf_writer, 'maps', "Maps")

        # Append categorized reports
        appended_report_files = self._append_pdf_files_from_category(pdf_writer, 'reports', "Supporting Reports")
        
        # Save the final merged PDF
        try:
            with open(final_pdf_path, "wb") as f_out:
                pdf_writer.write(f_out)
            print(f"✅ Merged PDF report saved: {final_pdf_path}")
            print(f"   Includes main content + {appended_map_files} map PDF(s) + {appended_report_files} supporting report PDF(s).")

        except Exception as e:
            print(f"❌ Error saving merged PDF: {e}")
            raise
            
        return str(final_pdf_path)

    def _append_pdf_files_from_category(self, pdf_writer: PdfWriter, category_key: str, log_category_name: str) -> int:
        """Helper to append PDF files from a category in file_inventory to the writer."""
        count = 0
        if category_key in self.file_inventory:
            for domain, files in self.file_inventory[category_key].items():
                for file_path in files:
                    if file_path.suffix.lower() == '.pdf':
                        try:
                            reader = PdfReader(open(file_path, "rb"))
                            for page in reader.pages:
                                pdf_writer.add_page(page)
                            print(f"  + Appended {file_path.name} ({len(reader.pages)} pages) from {log_category_name}/{domain}")
                            count +=1
                        except Exception as e:
                            print(f"  ⚠️ Could not append PDF {file_path.name}: {e}")
        return count

    def _build_main_report_story(self) -> List:
        """Builds the story for the main part of the report (before merging others)."""
        story = []
        story.extend(self._build_title_page())
        story.append(PageBreak())
        story.extend(self._build_table_of_contents())
        story.append(Paragraph("<i>Note: Page numbers in this Table of Contents refer to the main report sections. Appended maps and supporting documents follow this main report.</i>", self.styles['Caption']))
        story.append(PageBreak())
        story.extend(self._build_project_information())
        story.extend(self._build_executive_summary())
        story.append(PageBreak())
        story.extend(self._build_cadastral_analysis())
        story.extend(self._build_karst_analysis())
        story.extend(self._build_flood_analysis())
        story.extend(self._build_wetland_analysis())
        story.extend(self._build_habitat_analysis())
        story.extend(self._build_air_quality_analysis())
        story.extend(self._build_risk_assessment())
        story.extend(self._build_recommendations())
        story.extend(self._build_appendices_references()) # Modified to list references
        return story

    def _build_title_page(self) -> List:
        story = []
        story.append(Paragraph("Comprehensive Environmental Screening Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<b>Project:</b> {self.report_data.project_info.project_name}", self.styles['BodyText']))
        story.append(Spacer(1, 10))
        if self.report_data.project_info.cadastral_numbers:
            story.append(Paragraph(f"<b>Cadastral Number(s):</b> {', '.join(self.report_data.project_info.cadastral_numbers)}", self.styles['BodyText']))
            story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Location:</b> {self.report_data.project_info.latitude:.6f}, {self.report_data.project_info.longitude:.6f}", self.styles['BodyText']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Analysis Date:</b> {self.report_data.project_info.analysis_date_time}", self.styles['BodyText']))
        story.append(Spacer(1, 30))
        if self.use_llm and self.report_data.cumulative_risk_assessment.get('enhanced_assessment'):
            story.append(Paragraph("🤖 <i>This report includes AI-enhanced environmental analysis</i>", self.styles['Caption']))
        return story
    
    def _build_table_of_contents(self) -> List:
        story = []
        story.append(Paragraph("Table of Contents", self.styles['SectionHeader']))
        story.append(Spacer(1, 20))
        toc_items = [
            "1. Project Information", "2. Executive Summary", "3. Property & Cadastral Analysis",
            "4. Karst Analysis", "5. Flood Analysis", "6. Wetland Analysis",
            "7. Critical Habitat Analysis", "8. Air Quality Analysis",
            "9. Cumulative Environmental Risk Assessment", "10. Recommendations & Compliance Guidance",
            "11. References to Appended Supporting Documents" # Updated TOC item
        ]
        for item in toc_items:
            story.append(Paragraph(f"• {item}", self.styles['BulletList']))
        return story
    
    def _build_project_information(self) -> List:
        story = []
        story.append(Paragraph("1. Project Information", self.styles['SectionHeader']))
        proj_info = self.report_data.project_info
        data = [
            ['Project Name', proj_info.project_name],
            ['Analysis Date & Time', proj_info.analysis_date_time],
            ['Coordinates', f"{proj_info.latitude:.6f}, {proj_info.longitude:.6f}"],
            ['Cadastral Numbers', ", ".join(proj_info.cadastral_numbers) if proj_info.cadastral_numbers else 'N/A'],
            ['Location Name', proj_info.location_name],
            ['Project Directory', proj_info.project_directory]
        ]
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey), ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10), ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        return story

    def _build_executive_summary(self) -> List:
        story = []
        story.append(Paragraph("2. Executive Summary", self.styles['SectionHeader']))
        exec_summary = self.report_data.executive_summary
        story.append(Paragraph("Property Overview", self.styles['SubSectionHeader']))
        story.append(Paragraph(exec_summary.property_overview, self.styles['BodyText']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Key Environmental Constraints", self.styles['SubSectionHeader']))
        for constraint in exec_summary.key_environmental_constraints:
            story.append(Paragraph(f"• {constraint}", self.styles['BulletList']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Regulatory Highlights", self.styles['SubSectionHeader']))
        for highlight in exec_summary.regulatory_highlights:
            story.append(Paragraph(f"• {highlight}", self.styles['BulletList']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Risk Assessment", self.styles['SubSectionHeader']))
        story.append(Paragraph(exec_summary.risk_assessment, self.styles['BodyText']))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Primary Recommendations", self.styles['SubSectionHeader']))
        for rec in exec_summary.primary_recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['BulletList']))
        return story

    def _build_cadastral_analysis(self) -> List:
        story = []
        story.append(Paragraph("3. Property & Cadastral Analysis", self.styles['SectionHeader']))
        if self.report_data.cadastral_analysis:
            ca = self.report_data.cadastral_analysis
            data = [
                ['Cadastral Numbers', ", ".join(ca.cadastral_numbers)], ['Municipality', ca.municipality],
                ['Neighborhood', ca.neighborhood], ['Region', ca.region],
                ['Land Use Classification', ca.land_use_classification], ['Zoning Designation', ca.zoning_designation],
                ['Total Area', f"{ca.area_acres:.2f} acres ({ca.area_hectares:.2f} hectares)"],
                ['Regulatory Status', ca.regulatory_status]
            ]
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 20))
        story.extend(self._add_maps_for_section('cadastral', "Cadastral Maps (Appended Separately if PDF)"))
        return story

    def _build_karst_analysis(self) -> List:
        story = []
        story.append(Paragraph("4. Karst Analysis (Applicable to Puerto Rico)", self.styles['SectionHeader']))
        if self.report_data.karst_analysis:
            story.append(Paragraph("Karst analysis data available", self.styles['BodyText'])) # Placeholder
        else:
            story.append(Paragraph("Karst analysis not available in current dataset.", self.styles['BodyText']))
        story.extend(self._add_maps_for_section('karst', "Karst Maps (Appended Separately if PDF)"))
        return story

    def _build_flood_analysis(self) -> List:
        story = []
        story.append(Paragraph("5. Flood Analysis", self.styles['SectionHeader']))
        if self.report_data.flood_analysis:
            fa = self.report_data.flood_analysis
            data = [
                ['FEMA Flood Zone', fa.fema_flood_zone],
                ['Base Flood Elevation (BFE)', f"{fa.base_flood_elevation} feet" if fa.base_flood_elevation else "N/A"],
                ['FIRM Panel', fa.firm_panel], ['Effective Date', fa.effective_date], ['Community', fa.community_name],
                ['Preliminary vs. Effective', fa.preliminary_vs_effective],
                ['ABFE Data Available', 'Yes' if fa.abfe_data_available else 'No']
            ]
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 15))
            story.append(Paragraph("Regulatory Requirements", self.styles['SubSectionHeader']))
            for req in fa.regulatory_requirements: story.append(Paragraph(f"• {req}", self.styles['BulletList']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Flood Risk Assessment", self.styles['SubSectionHeader']))
            story.append(Paragraph(fa.flood_risk_assessment, self.styles['BodyText']))
        story.extend(self._add_maps_for_section('flood', "Flood Maps (Appended Separately if PDF)"))
        return story

    def _build_wetland_analysis(self) -> List:
        story = []
        story.append(Paragraph("6. Wetland Analysis", self.styles['SectionHeader']))
        if self.report_data.wetland_analysis:
            wa = self.report_data.wetland_analysis
            data = [
                ['Directly on Property', 'Yes' if wa.directly_on_property else 'No'],
                ['Within Search Radius', 'Yes' if wa.within_search_radius else 'No'],
                ['Distance to Nearest', f"{wa.distance_to_nearest} miles" if wa.distance_to_nearest else 'N/A']
            ]
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 15))
            if wa.wetland_classifications:
                story.append(Paragraph("Wetland Classifications", self.styles['SubSectionHeader']))
                for c in wa.wetland_classifications: story.append(Paragraph(f"• {c}", self.styles['BulletList']))
                story.append(Spacer(1, 10))
            story.append(Paragraph("Regulatory Significance", self.styles['SubSectionHeader']))
            for sig in wa.regulatory_significance: story.append(Paragraph(f"• {sig}", self.styles['BulletList']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Development Guidance", self.styles['SubSectionHeader']))
            for g in wa.development_guidance: story.append(Paragraph(f"• {g}", self.styles['BulletList']))
        story.extend(self._add_maps_for_section('wetland', "Wetland Maps (Appended Separately if PDF)"))
        return story

    def _build_habitat_analysis(self) -> List:
        story = []
        story.append(Paragraph("7. Critical Habitat Analysis", self.styles['SectionHeader']))
        if self.report_data.critical_habitat_analysis:
            cha = self.report_data.critical_habitat_analysis
            data = [
                ['Within Designated Critical Habitat', 'Yes' if cha.within_designated_habitat else 'No'],
                ['Within Proposed Critical Habitat', 'Yes' if cha.within_proposed_habitat else 'No'],
                ['Distance to Nearest Habitat', f"{cha.distance_to_nearest:.2f} miles" if cha.distance_to_nearest else 'N/A']
            ]
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 15))
            if cha.affected_species:
                story.append(Paragraph("Affected Species", self.styles['SubSectionHeader']))
                for s in cha.affected_species: story.append(Paragraph(f"• {s}", self.styles['BulletList']))
                story.append(Spacer(1, 10))
            story.append(Paragraph("Regulatory Implications", self.styles['SubSectionHeader']))
            for imp in cha.regulatory_implications: story.append(Paragraph(f"• {imp}", self.styles['BulletList']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Development Constraints", self.styles['SubSectionHeader']))
            for con in cha.development_constraints: story.append(Paragraph(f"• {con}", self.styles['BulletList']))
        story.extend(self._add_maps_for_section('habitat', "Critical Habitat Maps (Appended Separately if PDF)"))
        return story

    def _build_air_quality_analysis(self) -> List:
        story = []
        story.append(Paragraph("8. Air Quality (Nonattainment) Analysis", self.styles['SectionHeader']))
        if self.report_data.air_quality_analysis:
            aqa = self.report_data.air_quality_analysis
            data = [
                ['Nonattainment Status', 'Yes' if aqa.nonattainment_status else 'No'],
                ['Area Classification', aqa.area_classification]
            ]
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(self._get_standard_table_style())
            story.append(table)
            story.append(Spacer(1, 15))
            story.append(Paragraph("Affected Pollutants", self.styles['SubSectionHeader']))
            for p in aqa.affected_pollutants: story.append(Paragraph(f"• {p}", self.styles['BulletList']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("Regulatory Implications", self.styles['SubSectionHeader']))
            for imp in aqa.regulatory_implications: story.append(Paragraph(f"• {imp}", self.styles['BulletList']))
        story.extend(self._add_maps_for_section('air_quality', "Air Quality Maps (Appended Separately if PDF)"))
        return story

    def _build_risk_assessment(self) -> List:
        story = []
        story.append(Paragraph("9. Cumulative Environmental Risk & Development Implications", self.styles['SectionHeader']))
        cra = self.report_data.cumulative_risk_assessment
        data = [
            ['Overall Risk Profile', cra.get('overall_risk_profile', 'N/A')],
            ['Development Feasibility', cra.get('development_feasibility', 'N/A')],
            ['Complexity Score', str(cra.get('complexity_score', 'N/A'))],
            ['Enhanced Assessment', 'Yes (AI)' if cra.get('enhanced_assessment') else 'No']
        ]
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(self._get_standard_table_style())
        story.append(table)
        story.append(Spacer(1, 15))
        if cra.get('risk_factors'):
            story.append(Paragraph("Identified Risk Factors", self.styles['SubSectionHeader']))
            for factor in cra['risk_factors']: story.append(Paragraph(f"• {factor}", self.styles['BulletList']))
            story.append(Spacer(1, 10))
        if self.use_llm and cra.get('llm_reasoning'):
            story.append(Paragraph("AI-Enhanced Risk Analysis", self.styles['SubSectionHeader']))
            story.append(Paragraph(cra['llm_reasoning'], self.styles['BodyText']))
        return story

    def _build_recommendations(self) -> List:
        story = []
        story.append(Paragraph("10. Recommendations & Compliance Guidance", self.styles['SectionHeader']))
        for i, rec in enumerate(self.report_data.recommendations, 1):
            story.append(Paragraph(f"{i}. {rec}", self.styles['BulletList']))
        return story

    def _build_appendices_references(self) -> List: # Renamed for clarity
        """Build appendices section listing references to files that will be merged."""
        story = []
        story.append(Paragraph("11. References to Appended Supporting Documents", self.styles['SectionHeader']))
        story.append(Paragraph(
            "The following maps and supporting reports are appended to this document in sequence. "
            "Their original filenames are listed below for reference.", self.styles['BodyText']
        ))
        story.append(Spacer(1, 15))

        # List PDF maps to be appended
        story.append(Paragraph("Appended Maps:", self.styles['SubSectionHeader']))
        maps_appended_count = 0
        if 'maps' in self.file_inventory:
            for domain, files in self.file_inventory['maps'].items():
                for map_file in files:
                    if map_file.suffix.lower() == '.pdf':
                        story.append(Paragraph(f"• {map_file.name} (from maps/{domain}/)", self.styles['BulletList']))
                        maps_appended_count +=1
        if maps_appended_count == 0:
            story.append(Paragraph("No PDF maps were found to append.", self.styles['BulletList']))
        story.append(Spacer(1, 10))

        # List PDF reports to be appended
        story.append(Paragraph("Appended Supporting Reports:", self.styles['SubSectionHeader']))
        reports_appended_count = 0
        if 'reports' in self.file_inventory:
            for domain, files in self.file_inventory['reports'].items():
                for report_file in files:
                    story.append(Paragraph(f"• {report_file.name} (from reports/{domain}/)", self.styles['BulletList']))
                    reports_appended_count += 1
        if reports_appended_count == 0:
            story.append(Paragraph("No supporting PDF reports were found to append.", self.styles['BulletList']))
        
        return story
    
    def _add_maps_for_section(self, section: str, title: str) -> List:
        """Add image maps for a specific section, or note that PDF maps are appended."""
        story = []
        has_content = False
        
        if section in self.file_inventory['maps']:
            maps = self.file_inventory['maps'][section]
            if maps:
                image_maps_added = False
                pdf_maps_referenced = False

                # Separate images and PDFs
                image_files = [mf for mf in maps if mf.suffix.lower() in ['.png', '.jpg', '.jpeg']]
                pdf_files = [mf for mf in maps if mf.suffix.lower() == '.pdf']

                if image_files:
                    story.append(Paragraph(title.replace("(Appended Separately if PDF)","(Embedded Images)"), self.styles['SubSectionHeader']))
                    has_content = True
                    for map_file in image_files:
                        try:
                            img = Image(str(map_file), width=6*inch, height=4*inch, kind='bound') # ensure image fits
                            story.append(img)
                            story.append(Paragraph(f"Map: {map_file.name}", self.styles['Caption']))
                            story.append(Spacer(1, 10))
                            image_maps_added = True
                        except Exception as e:
                            story.append(Paragraph(f"Image file reference: {map_file.name} (could not embed: {e})", self.styles['BulletList']))
                
                if pdf_files:
                    if not image_maps_added : # If only PDF maps, add a subsection header
                         story.append(Paragraph(title.replace("(Appended Separately if PDF)","(PDF Maps Referenced)"), self.styles['SubSectionHeader']))
                         has_content = True
                    story.append(Paragraph("The following PDF maps are appended to this report:", self.styles['BodyText']))
                    for map_file in pdf_files:
                        story.append(Paragraph(f"• {map_file.name}", self.styles['BulletList']))
                    pdf_maps_referenced = True
                
                if image_maps_added or pdf_maps_referenced:
                     story.append(Spacer(1, 15))

        if not has_content: # If no maps at all for this section
            story.append(Paragraph(title.replace("(Appended Separately if PDF)",""), self.styles['SubSectionHeader']))
            story.append(Paragraph("No maps available for this section.", self.styles['BodyText']))
            story.append(Spacer(1,15))
            
        return story
    
    def _get_standard_table_style(self) -> TableStyle:
        return TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey), ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10), ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.lightgrey]) # Alternating row colors
        ])

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate comprehensive PDF screening report with merged attachments.')
    parser.add_argument('output_directory', help='Screening output directory')
    parser.add_argument('--output', help='Custom PDF filename')
    parser.add_argument('--no-llm', action='store_true', help='Disable LLM enhancement')
    
    args = parser.parse_args()
    
    if not REPORTLAB_AVAILABLE or not PYPDF2_AVAILABLE:
        print("❌ Error: ReportLab, Pillow, and PyPDF2 are required.")
        print("Install with: pip install reportlab pillow PyPDF2")
        return 1
    
    try:
        generator = ScreeningPDFGenerator(output_directory=args.output_directory, use_llm=not args.no_llm)
        pdf_file = generator.generate_pdf_report(args.output)
        print(f"✅ Final merged PDF report generated successfully: {pdf_file}")
    except Exception as e:
        print(f"❌ Error generating PDF report: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 