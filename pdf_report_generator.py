#!/usr/bin/env python3
"""
PDF Comprehensive Environmental Screening Report Generator

Generates professional PDF reports that combine:
- Analysis from JSON data files in the data folder
- Maps generated on-demand from saved parameters
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
import asyncio
import logging

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

# Import map generators
try:
    from WetlandsINFO.generate_wetland_map_pdf_v3 import WetlandMapGeneratorV3
    WETLAND_MAP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Wetland map generator not available")
    WETLAND_MAP_AVAILABLE = False

try:
    from NonAttainmentINFO.generate_nonattainment_map_pdf import NonAttainmentMapGenerator
    NONATTAINMENT_MAP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: NonAttainment map generator not available")
    NONATTAINMENT_MAP_AVAILABLE = False

try:
    from HabitatINFO.generate_critical_habitat_map_pdf import CriticalHabitatMapGenerator
    HABITAT_MAP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Critical habitat map generator not available")
    HABITAT_MAP_AVAILABLE = False

try:
    from karst.karst_map_generator import KarstMapGenerator
    KARST_MAP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Karst map generator not available")
    KARST_MAP_AVAILABLE = False

# Import flood analysis tool for map generation
try:
    from comprehensive_flood_tool import comprehensive_flood_analysis
    FLOOD_MAP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Flood analysis tool not available for map generation")
    FLOOD_MAP_AVAILABLE = False

# Import our report generators
try:
    from llm_enhanced_report_generator import EnhancedComprehensiveReportGenerator
    from comprehensive_report_generator import ComprehensiveReportGenerator, ComprehensiveReport
    LLM_AVAILABLE = True
except ImportError:
    from comprehensive_report_generator import ComprehensiveReportGenerator, ComprehensiveReport
    LLM_AVAILABLE = False

# Import structured output model
try:
    from comprehensive_environmental_agent import StructuredScreeningOutput
    STRUCTURED_OUTPUT_AVAILABLE = True
except ImportError as e:
    STRUCTURED_OUTPUT_AVAILABLE = False
    # Only show this warning if the StructuredPDFGenerator is actually being used
    # We'll check this later and only warn if someone tries to use structured features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScreeningPDFGenerator:
    """Professional PDF generator for comprehensive environmental screening reports"""
    
    def __init__(self, output_directory: str, use_llm: bool = True, model_name: str = "grok-3-mini"):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab pillow")
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 is required for PDF merging. Install with: pip install PyPDF2")
        
        self.output_directory = Path(output_directory).resolve()
        self.data_directory = self.output_directory / "data"
        self.maps_directory = self.output_directory / "maps"
        self.reports_directory = self.output_directory / "reports"
        self.use_llm = use_llm and LLM_AVAILABLE
        
        # Initialize map generators
        self._initialize_map_generators()
        
        self._initialize_data_generator(model_name)
        self._setup_pdf_styles()
        self._collect_files()
    
    def _initialize_map_generators(self):
        """Initialize all available map generators"""
        self.map_generators = {}
        
        if WETLAND_MAP_AVAILABLE:
            self.map_generators['wetland'] = WetlandMapGeneratorV3()
            logger.info("✅ Wetland map generator initialized")
        
        if NONATTAINMENT_MAP_AVAILABLE:
            self.map_generators['air_quality'] = NonAttainmentMapGenerator()
            logger.info("✅ NonAttainment map generator initialized")
        
        if HABITAT_MAP_AVAILABLE:
            self.map_generators['habitat'] = CriticalHabitatMapGenerator()
            logger.info("✅ Critical habitat map generator initialized")
        
        if KARST_MAP_AVAILABLE:
            # Karst map generator needs output directory
            self.map_generators['karst'] = lambda: KarstMapGenerator(output_directory=str(self.maps_directory))
            logger.info("✅ Karst map generator initialized")
        
        if FLOOD_MAP_AVAILABLE:
            # Store the function for flood analysis instead of trying to instantiate a class
            self.map_generators['flood'] = comprehensive_flood_analysis
            logger.info("✅ Flood map generator initialized")
    
    def _generate_maps_from_parameters(self):
        """Generate all maps based on saved parameters in JSON data files"""
        logger.info("🗺️ Generating maps from saved parameters...")
        
        # Ensure maps directory exists
        self.maps_directory.mkdir(exist_ok=True)
        
        generated_maps = {
            'flood': [], 'wetland': [], 'habitat': [], 'air_quality': [], 'karst': []
        }
        
        # Load and process each analysis JSON file
        data_files = {
            'flood': self.data_directory / "flood_analysis_comprehensive.json",
            'wetland': self.data_directory / "wetland_analysis_comprehensive.json", 
            'habitat': self.data_directory / "critical_habitat_analysis_comprehensive.json",
            'air_quality': self.data_directory / "air_quality_analysis_comprehensive.json",
            'karst': self.data_directory / "karst_analysis_comprehensive.json"
        }
        
        # Generate flood maps
        if data_files['flood'].exists() and 'flood' in self.map_generators:
            logger.info("   Generating flood maps...")
            flood_maps = self._generate_flood_maps(data_files['flood'])
            generated_maps['flood'].extend(flood_maps)
        
        # Generate wetland maps
        if data_files['wetland'].exists() and 'wetland' in self.map_generators:
            logger.info("   Generating wetland maps...")
            wetland_maps = self._generate_wetland_maps(data_files['wetland'])
            generated_maps['wetland'].extend(wetland_maps)
        
        # Generate habitat maps
        if data_files['habitat'].exists() and 'habitat' in self.map_generators:
            logger.info("   Generating critical habitat maps...")
            habitat_maps = self._generate_habitat_maps(data_files['habitat'])
            generated_maps['habitat'].extend(habitat_maps)
        
        # Generate air quality maps
        if data_files['air_quality'].exists() and 'air_quality' in self.map_generators:
            logger.info("   Generating air quality maps...")
            air_maps = self._generate_air_quality_maps(data_files['air_quality'])
            generated_maps['air_quality'].extend(air_maps)
        
        # Generate karst maps
        if data_files['karst'].exists() and 'karst' in self.map_generators:
            logger.info("   Generating karst maps...")
            karst_maps = self._generate_karst_maps(data_files['karst'])
            generated_maps['karst'].extend(karst_maps)
        
        logger.info(f"✅ Map generation complete. Generated {sum(len(maps) for maps in generated_maps.values())} maps")
        return generated_maps
    
    def _generate_flood_maps(self, data_file: Path) -> List[Path]:
        """Generate flood maps from saved parameters"""
        generated_maps = []
        
        try:
            with open(data_file, 'r') as f:
                flood_data = json.load(f)
            
            map_params = flood_data.get('map_generation_parameters', {})
            maps_to_generate = flood_data.get('maps_to_generate', {})
            
            if not map_params:
                logger.warning("   No map generation parameters found for flood analysis")
                return generated_maps
            
            tool = self.map_generators['flood']
            
            # Extract parameters
            center_lon = map_params.get('center_longitude', 0)
            center_lat = map_params.get('center_latitude', 0)
            buffer_miles = map_params.get('map_view_buffer_miles', 1.0)
            base_map = map_params.get('base_map_name', 'World_Imagery')
            
            # Generate FIRM map (PDF)
            if maps_to_generate.get('firm_map_pdf', {}).get('type') == 'FIRM':
                firm_pdf = asyncio.run(tool.generate_firm_map(
                    center_lat, center_lon, self.maps_directory,
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['firm_map_pdf'].get('layout', 'Letter ANSI A Landscape'),
                    output_format=maps_to_generate['firm_map_pdf'].get('format', 'PDF'),
                    output_filename_prefix=maps_to_generate['firm_map_pdf'].get('filename_prefix', 'flood_firm_map_archive')
                ))
                if firm_pdf:
                    generated_maps.append(Path(firm_pdf))
                    logger.info(f"      ✅ Generated FIRM PDF map: {firm_pdf}")
            
            # Generate FIRM map (PNG for embedding)
            if maps_to_generate.get('firm_map_png', {}).get('type') == 'FIRM':
                firm_png = asyncio.run(tool.generate_firm_map(
                    center_lat, center_lon, self.maps_directory,
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['firm_map_png'].get('layout', 'MAP_ONLY'),
                    output_format=maps_to_generate['firm_map_png'].get('format', 'PNG32'),
                    output_filename_prefix=maps_to_generate['firm_map_png'].get('filename_prefix', 'flood_firm_map_embed')
                ))
                if firm_png:
                    generated_maps.append(Path(firm_png))
                    logger.info(f"      ✅ Generated FIRM PNG map: {firm_png}")
            
            # Generate ABFE map if enabled
            if maps_to_generate.get('abfe_map', {}).get('enabled', False):
                abfe_map = asyncio.run(tool.generate_abfe_map(center_lat, center_lon, self.maps_directory))
                if abfe_map:
                    generated_maps.append(Path(abfe_map))
                    logger.info(f"      ✅ Generated ABFE map: {abfe_map}")
        
        except Exception as e:
            logger.error(f"   ❌ Error generating flood maps: {e}")
        
        return generated_maps
    
    def _generate_wetland_maps(self, data_file: Path) -> List[Path]:
        """Generate wetland maps from saved parameters"""
        generated_maps = []
        
        try:
            with open(data_file, 'r') as f:
                wetland_data = json.load(f)
            
            map_params = wetland_data.get('map_generation_parameters', {})
            maps_to_generate = wetland_data.get('maps_to_generate', {})
            
            if not map_params:
                logger.warning("   No map generation parameters found for wetland analysis")
                return generated_maps
            
            map_generator = self.map_generators['wetland']
            
            # Extract parameters
            center_lon = map_params.get('center_longitude', 0)
            center_lat = map_params.get('center_latitude', 0)
            buffer_miles = map_params.get('map_view_buffer_miles', 0.5)
            base_map = map_params.get('base_map_name', 'World_Imagery')
            
            # Generate PDF map
            if 'wetland_map_pdf' in maps_to_generate:
                pdf_file = map_generator.generate_wetland_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Wetland Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['wetland_map_pdf'].get('layout', 'Letter ANSI A Portrait'),
                    output_format=maps_to_generate['wetland_map_pdf'].get('format', 'PDF'),
                    output_filename=str(self.maps_directory / maps_to_generate['wetland_map_pdf'].get('filename', 'wetland_map_archive.pdf'))
                )
                if pdf_file:
                    generated_maps.append(Path(pdf_file))
                    logger.info(f"      ✅ Generated wetland PDF map: {pdf_file}")
            
            # Generate PNG map
            if 'wetland_map_png' in maps_to_generate:
                png_file = map_generator.generate_wetland_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Wetland Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['wetland_map_png'].get('layout', 'MAP_ONLY'),
                    output_format=maps_to_generate['wetland_map_png'].get('format', 'PNG32'),
                    output_filename=str(self.maps_directory / maps_to_generate['wetland_map_png'].get('filename', 'wetland_map_embed.png'))
                )
                if png_file:
                    generated_maps.append(Path(png_file))
                    logger.info(f"      ✅ Generated wetland PNG map: {png_file}")
        
        except Exception as e:
            logger.error(f"   ❌ Error generating wetland maps: {e}")
        
        return generated_maps
    
    def _generate_habitat_maps(self, data_file: Path) -> List[Path]:
        """Generate critical habitat maps from saved parameters"""
        generated_maps = []
        
        try:
            with open(data_file, 'r') as f:
                habitat_data = json.load(f)
            
            map_params = habitat_data.get('map_generation_parameters', {})
            maps_to_generate = habitat_data.get('maps_to_generate', {})
            
            if not map_params:
                logger.warning("   No map generation parameters found for habitat analysis")
                return generated_maps
            
            map_generator = self.map_generators['habitat']
            
            # Extract parameters
            center_lon = map_params.get('center_longitude', 0)
            center_lat = map_params.get('center_latitude', 0)
            buffer_miles = map_params.get('map_view_buffer_miles', 0.5)
            base_map = map_params.get('base_map_name', 'World_Imagery')
            
            # Generate PDF map
            if 'habitat_map_pdf' in maps_to_generate:
                pdf_file = map_generator.generate_critical_habitat_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Critical Habitat Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['habitat_map_pdf'].get('layout', 'Letter ANSI A Portrait'),
                    output_filename=maps_to_generate['habitat_map_pdf'].get('filename', 'critical_habitat_map_archive.pdf')
                )
                if pdf_file:
                    generated_maps.append(Path(pdf_file))
                    logger.info(f"      ✅ Generated habitat PDF map: {pdf_file}")
            
            # Generate PNG map
            if 'habitat_map_png' in maps_to_generate:
                # Note: Critical habitat generator returns PDF by default, we need to set format
                png_file = map_generator.generate_critical_habitat_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Critical Habitat Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['habitat_map_png'].get('layout', 'MAP_ONLY'),
                    output_filename=maps_to_generate['habitat_map_png'].get('filename', 'critical_habitat_map_embed.png')
                )
                if png_file:
                    generated_maps.append(Path(png_file))
                    logger.info(f"      ✅ Generated habitat PNG map: {png_file}")
        
        except Exception as e:
            logger.error(f"   ❌ Error generating habitat maps: {e}")
        
        return generated_maps
    
    def _generate_air_quality_maps(self, data_file: Path) -> List[Path]:
        """Generate air quality maps from saved parameters"""
        generated_maps = []
        
        try:
            with open(data_file, 'r') as f:
                air_data = json.load(f)
            
            map_params = air_data.get('map_generation_parameters', {})
            maps_to_generate = air_data.get('maps_to_generate', {})
            
            if not map_params:
                logger.warning("   No map generation parameters found for air quality analysis")
                return generated_maps
            
            map_generator = self.map_generators['air_quality']
            
            # Extract parameters
            center_lon = map_params.get('center_longitude', 0)
            center_lat = map_params.get('center_latitude', 0)
            buffer_miles = map_params.get('map_view_buffer_miles', 25.0)
            base_map = map_params.get('base_map_name', 'World_Topo_Map')
            
            # Generate PDF map
            if 'air_quality_map_pdf' in maps_to_generate:
                pdf_file = map_generator.generate_nonattainment_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Air Quality Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['air_quality_map_pdf'].get('layout', 'Letter ANSI A Portrait'),
                    output_filename=maps_to_generate['air_quality_map_pdf'].get('filename', 'air_quality_map_archive.pdf')
                )
                if pdf_file:
                    generated_maps.append(Path(pdf_file))
                    logger.info(f"      ✅ Generated air quality PDF map: {pdf_file}")
            
            # Generate PNG map
            if 'air_quality_map_png' in maps_to_generate:
                # Note: The nonattainment generator might need format specification
                png_file = map_generator.generate_nonattainment_map_pdf(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Air Quality Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map=base_map,
                    layout_template=maps_to_generate['air_quality_map_png'].get('layout', 'MAP_ONLY'),
                    output_filename=maps_to_generate['air_quality_map_png'].get('filename', 'air_quality_map_embed.png')
                )
                if png_file:
                    generated_maps.append(Path(png_file))
                    logger.info(f"      ✅ Generated air quality PNG map: {png_file}")
        
        except Exception as e:
            logger.error(f"   ❌ Error generating air quality maps: {e}")
        
        return generated_maps
    
    def _generate_karst_maps(self, data_file: Path) -> List[Path]:
        """Generate karst maps from saved parameters"""
        generated_maps = []
        
        try:
            with open(data_file, 'r') as f:
                karst_data = json.load(f)
            
            map_params = karst_data.get('map_generation_parameters', {})
            maps_to_generate = karst_data.get('maps_to_generate', {})
            
            if not map_params:
                logger.warning("   No map generation parameters found for karst analysis")
                return generated_maps
            
            # Initialize karst map generator
            map_generator = self.map_generators['karst']()
            
            # Extract parameters
            center_lon = map_params.get('center_longitude', 0)
            center_lat = map_params.get('center_latitude', 0)
            buffer_miles = map_params.get('map_view_buffer_miles', 1.0)
            base_map = map_params.get('base_map_name', 'World_Topo_Map')
            
            # Generate PDF map
            if 'karst_map_pdf' in maps_to_generate:
                pdf_file = map_generator.generate_map_export(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Karst Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map_name=base_map,
                    output_format=maps_to_generate['karst_map_pdf'].get('format', 'PDF'),
                    layout_template=maps_to_generate['karst_map_pdf'].get('layout', 'Letter ANSI A Landscape'),
                    output_filename_prefix=maps_to_generate['karst_map_pdf'].get('filename_prefix', 'karst_map_archive')
                )
                if pdf_file:
                    generated_maps.append(Path(pdf_file))
                    logger.info(f"      ✅ Generated karst PDF map: {pdf_file}")
            
            # Generate PNG map
            if 'karst_map_png' in maps_to_generate:
                png_file = map_generator.generate_map_export(
                    longitude=center_lon, latitude=center_lat,
                    location_name=f"Karst Analysis for {self.output_directory.name}",
                    buffer_miles=buffer_miles, base_map_name=base_map,
                    output_format=maps_to_generate['karst_map_png'].get('format', 'PNG32'),
                    layout_template=maps_to_generate['karst_map_png'].get('layout', 'MAP_ONLY'),
                    output_filename_prefix=maps_to_generate['karst_map_png'].get('filename_prefix', 'karst_map_embed')
                )
                if png_file:
                    generated_maps.append(Path(png_file))
                    logger.info(f"      ✅ Generated karst PNG map: {png_file}")
        
        except Exception as e:
            logger.error(f"   ❌ Error generating karst maps: {e}")
        
        return generated_maps
    
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

class StructuredPDFGenerator:
    """Advanced PDF generator that uses structured JSON output for better organization"""
    
    def __init__(self, structured_data: dict, project_directory: str, use_llm: bool = True):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab pillow")
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 is required for PDF merging. Install with: pip install PyPDF2")
        
        self.structured_data = structured_data
        self.project_directory = Path(project_directory).resolve()
        self.use_llm = use_llm
        
        # Validate structured data
        if STRUCTURED_OUTPUT_AVAILABLE:
            try:
                self.validated_data = StructuredScreeningOutput(**structured_data)
            except Exception as e:
                print(f"⚠️ Warning: Could not validate structured data: {e}")
                self.validated_data = None
        else:
            self.validated_data = None
        
        self._setup_pdf_styles()
        self._organize_content_and_maps()
    
    def _setup_pdf_styles(self):
        """Set up sophisticated PDF styles"""
        self.styles = getSampleStyleSheet()
        
        # Enhanced styles for better presentation
        self.styles.add(ParagraphStyle(
            name='ReportTitle', parent=self.styles['Title'], fontSize=28,
            textColor=colors.darkblue, spaceAfter=30, alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader', parent=self.styles['Heading1'], fontSize=18,
            textColor=colors.white, backColor=colors.darkblue,
            spaceAfter=12, spaceBefore=20, borderWidth=0,
            borderPadding=8, alignment=TA_LEFT, fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubSectionHeader', parent=self.styles['Heading2'], fontSize=14,
            textColor=colors.darkgreen, spaceAfter=8, spaceBefore=12,
            fontName='Helvetica-Bold', borderWidth=1,
            borderColor=colors.darkgreen, borderPadding=3
        ))
        
        self.styles.add(ParagraphStyle(
            name='AnalysisText', parent=self.styles['Normal'], fontSize=11,
            spaceAfter=6, alignment=TA_JUSTIFY, fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='HighlightBox', parent=self.styles['Normal'], fontSize=11,
            backColor=colors.lightgrey, borderWidth=1, borderColor=colors.grey,
            borderPadding=8, spaceAfter=10, spaceBefore=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='MapCaption', parent=self.styles['Normal'], fontSize=10,
            textColor=colors.darkblue, alignment=TA_CENTER, 
            spaceAfter=15, spaceBefore=5, fontName='Helvetica-Oblique'
        ))
    
    def _organize_content_and_maps(self):
        """Organize content and maps according to the structured data"""
        self.content_map = {
            'cadastral_analysis': {
                'title': 'Property & Cadastral Analysis',
                'maps': [],
                'content': None
            },
            'karst_analysis': {
                'title': 'Karst Analysis (Puerto Rico)',
                'maps': [],
                'content': None
            },
            'flood_analysis': {
                'title': 'Flood Analysis',
                'maps': [],
                'content': None
            },
            'wetland_analysis': {
                'title': 'Wetland Analysis',
                'maps': [],
                'content': None
            },
            'critical_habitat_analysis': {
                'title': 'Critical Habitat Analysis',
                'maps': [],
                'content': None
            },
            'air_quality_analysis': {
                'title': 'Air Quality Analysis',
                'maps': [],
                'content': None
            }
        }
        
        # Map structured data to file paths
        self._map_structured_data_to_files()
    
    def _map_structured_data_to_files(self):
        """Map structured data fields to actual file paths"""
        # Extract file paths from structured data
        if self.validated_data:
            # Use validated Pydantic model
            if self.validated_data.flood_analysis and hasattr(self.validated_data.flood_analysis, 'firme_map_path'):
                if self.validated_data.flood_analysis.firme_map_path:
                    self.content_map['flood_analysis']['maps'].append(
                        self.project_directory / self.validated_data.flood_analysis.firme_map_path
                    )
            
            if self.validated_data.wetland_analysis and hasattr(self.validated_data.wetland_analysis, 'nwi_map_path'):
                if self.validated_data.wetland_analysis.nwi_map_path:
                    self.content_map['wetland_analysis']['maps'].append(
                        self.project_directory / self.validated_data.wetland_analysis.nwi_map_path
                    )
            
            if self.validated_data.critical_habitat_analysis and hasattr(self.validated_data.critical_habitat_analysis, 'critical_habitat_map_path'):
                if self.validated_data.critical_habitat_analysis.critical_habitat_map_path:
                    self.content_map['critical_habitat_analysis']['maps'].append(
                        self.project_directory / self.validated_data.critical_habitat_analysis.critical_habitat_map_path
                    )
            
            if self.validated_data.air_quality_analysis and hasattr(self.validated_data.air_quality_analysis, 'nonattainment_map_path'):
                if self.validated_data.air_quality_analysis.nonattainment_map_path:
                    self.content_map['air_quality_analysis']['maps'].append(
                        self.project_directory / self.validated_data.air_quality_analysis.nonattainment_map_path
                    )
        else:
            # Use raw dictionary
            self._extract_from_raw_dict()
    
    def _extract_from_raw_dict(self):
        """Extract file paths from raw dictionary format"""
        data = self.structured_data
        
        # Flood analysis maps
        flood_data = data.get('flood_analysis', {})
        if flood_data and flood_data.get('firme_map_path'):
            self.content_map['flood_analysis']['maps'].append(
                self.project_directory / flood_data['firme_map_path']
            )
        
        # Wetland analysis maps
        wetland_data = data.get('wetland_analysis', {})
        if wetland_data and wetland_data.get('nwi_map_path'):
            self.content_map['wetland_analysis']['maps'].append(
                self.project_directory / wetland_data['nwi_map_path']
            )
        
        # Habitat analysis maps
        habitat_data = data.get('critical_habitat_analysis', {})
        if habitat_data and habitat_data.get('critical_habitat_map_path'):
            self.content_map['critical_habitat_analysis']['maps'].append(
                self.project_directory / habitat_data['critical_habitat_map_path']
            )
        
        # Air quality analysis maps
        air_data = data.get('air_quality_analysis', {})
        if air_data and air_data.get('nonattainment_map_path'):
            self.content_map['air_quality_analysis']['maps'].append(
                self.project_directory / air_data['nonattainment_map_path']
            )
        
        # Additional maps from other sources
        other_maps = data.get('maps_generated_other', [])
        if other_maps:
            for map_path in other_maps:
                # Try to categorize the map based on filename
                map_file = self.project_directory / map_path
                category = self._categorize_additional_map(map_file.name)
                if category in self.content_map:
                    self.content_map[category]['maps'].append(map_file)
    
    def _categorize_additional_map(self, filename: str) -> str:
        """Categorize additional maps based on filename"""
        filename_lower = filename.lower()
        if any(term in filename_lower for term in ['flood', 'fema', 'firm']):
            return 'flood_analysis'
        elif any(term in filename_lower for term in ['wetland', 'nwi']):
            return 'wetland_analysis'
        elif any(term in filename_lower for term in ['habitat', 'critical', 'species']):
            return 'critical_habitat_analysis'
        elif any(term in filename_lower for term in ['nonattainment', 'air']):
            return 'air_quality_analysis'
        elif any(term in filename_lower for term in ['karst', 'geology']):
            return 'karst_analysis'
        elif any(term in filename_lower for term in ['cadastral', 'property']):
            return 'cadastral_analysis'
        return 'cadastral_analysis'  # Default
    
    def generate_sophisticated_pdf_report(self, output_filename: str = None) -> str:
        """Generate a sophisticated PDF report using structured data and proper map placement"""
        
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.structured_data.get('project_name', 'Environmental_Screening')
            output_filename = f"comprehensive_screening_report_{project_name}_{timestamp}.pdf"
        
        # Ensure reports directory exists
        reports_dir = self.project_directory / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        output_path = reports_dir / output_filename
        
        print(f"📄 Generating sophisticated PDF report: {output_filename}")
        print(f"   Using structured data with {len([m for maps in self.content_map.values() for m in maps['maps']])} embedded maps")
        
        # Build the story with structured content
        story = self._build_sophisticated_story()
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18
        )
        
        doc.build(story)
        
        print(f"✅ Sophisticated PDF report generated: {output_path}")
        return str(output_path)
    
    def _build_sophisticated_story(self) -> List:
        """Build the sophisticated PDF story with proper section organization"""
        story = []
        
        # Title page
        story.extend(self._build_title_page())
        story.append(PageBreak())
        
        # Executive summary with key findings
        story.extend(self._build_executive_summary())
        story.append(PageBreak())
        
        # Analysis sections with embedded maps
        for section_key, section_info in self.content_map.items():
            if self._has_content_for_section(section_key):
                story.extend(self._build_analysis_section(section_key, section_info))
                story.append(PageBreak())
        
        # Risk assessment and recommendations
        story.extend(self._build_risk_assessment())
        story.append(PageBreak())
        
        story.extend(self._build_recommendations())
        
        return story
    
    def _has_content_for_section(self, section_key: str) -> bool:
        """Check if a section has content in the structured data"""
        return self.structured_data.get(section_key) is not None
    
    def _build_analysis_section(self, section_key: str, section_info: dict) -> List:
        """Build an analysis section with integrated maps"""
        story = []
        
        # Section header
        story.append(Paragraph(
            f"{section_info['title']}",
            self.styles['SectionHeader']
        ))
        story.append(Spacer(1, 12))
        
        # Section content from structured data
        section_data = self.structured_data.get(section_key, {})
        if section_data:
            story.extend(self._format_section_content(section_key, section_data))
        
        # Embedded maps for this section
        maps = section_info.get('maps', [])
        if maps:
            story.append(Spacer(1, 12))
            for map_file in maps:
                if map_file.exists():
                    story.extend(self._embed_map_in_section(map_file, section_info['title']))
        
        return story
    
    def _format_section_content(self, section_key: str, section_data: dict) -> List:
        """Format section content based on structured data"""
        story = []
        
        if section_key == 'flood_analysis':
            story.extend(self._format_flood_content(section_data))
        elif section_key == 'wetland_analysis':
            story.extend(self._format_wetland_content(section_data))
        elif section_key == 'critical_habitat_analysis':
            story.extend(self._format_habitat_content(section_data))
        elif section_key == 'air_quality_analysis':
            story.extend(self._format_air_quality_content(section_data))
        elif section_key == 'karst_analysis':
            story.extend(self._format_karst_content(section_data))
        elif section_key == 'cadastral_analysis':
            story.extend(self._format_property_content(section_data))
        
        return story
    
    def _format_flood_content(self, data: dict) -> List:
        """Format flood analysis content"""
        story = []
        
        if data.get('flood_zone_code'):
            story.append(Paragraph(
                f"<b>FEMA Flood Zone:</b> {data['flood_zone_code']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('base_flood_elevation_ft'):
            story.append(Paragraph(
                f"<b>Base Flood Elevation:</b> {data['base_flood_elevation_ft']} feet",
                self.styles['AnalysisText']
            ))
        
        if data.get('flood_risk_category'):
            story.append(Paragraph(
                f"<b>Flood Risk Category:</b> {data['flood_risk_category']}",
                self.styles['HighlightBox']
            ))
        
        if data.get('insurance_requirements'):
            story.append(Paragraph(
                f"<b>Insurance Requirements:</b> {data['insurance_requirements']}",
                self.styles['AnalysisText']
            ))
        
        return story
    
    def _format_wetland_content(self, data: dict) -> List:
        """Format wetland analysis content"""
        story = []
        
        if 'wetlands_on_property' in data:
            status = "Yes" if data['wetlands_on_property'] else "No"
            story.append(Paragraph(
                f"<b>Wetlands on Property:</b> {status}",
                self.styles['AnalysisText']
            ))
        
        if data.get('wetland_types_present'):
            types_text = ", ".join(data['wetland_types_present'])
            story.append(Paragraph(
                f"<b>Wetland Types:</b> {types_text}",
                self.styles['AnalysisText']
            ))
        
        if data.get('distance_to_nearest_wetland_miles'):
            story.append(Paragraph(
                f"<b>Distance to Nearest Wetland:</b> {data['distance_to_nearest_wetland_miles']} miles",
                self.styles['AnalysisText']
            ))
        
        if data.get('regulatory_complexity_assessment'):
            story.append(Paragraph(
                f"<b>Regulatory Complexity:</b> {data['regulatory_complexity_assessment']}",
                self.styles['HighlightBox']
            ))
        
        return story
    
    def _format_habitat_content(self, data: dict) -> List:
        """Format habitat analysis content"""
        story = []
        
        if 'within_designated_critical_habitat' in data:
            status = "Yes" if data['within_designated_critical_habitat'] else "No"
            story.append(Paragraph(
                f"<b>Within Critical Habitat:</b> {status}",
                self.styles['AnalysisText']
            ))
        
        if data.get('threatened_or_endangered_species_potentially_affected'):
            species_text = ", ".join(data['threatened_or_endangered_species_potentially_affected'])
            story.append(Paragraph(
                f"<b>Affected Species:</b> {species_text}",
                self.styles['AnalysisText']
            ))
        
        if 'esa_consultation_potentially_required' in data:
            consultation = "Yes" if data['esa_consultation_potentially_required'] else "No"
            story.append(Paragraph(
                f"<b>ESA Consultation Required:</b> {consultation}",
                self.styles['HighlightBox']
            ))
        
        return story
    
    def _format_air_quality_content(self, data: dict) -> List:
        """Format air quality analysis content"""
        story = []
        
        if data.get('nonattainment_area_status'):
            story.append(Paragraph(
                f"<b>Nonattainment Status:</b> {data['nonattainment_area_status']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('designated_nonattainment_pollutants'):
            pollutants_text = ", ".join(data['designated_nonattainment_pollutants'])
            story.append(Paragraph(
                f"<b>Nonattainment Pollutants:</b> {pollutants_text}",
                self.styles['AnalysisText']
            ))
        
        if 'meets_naaqs_standards' in data:
            meets_standards = "Yes" if data['meets_naaqs_standards'] else "No"
            story.append(Paragraph(
                f"<b>Meets NAAQS Standards:</b> {meets_standards}",
                self.styles['HighlightBox']
            ))
        
        return story
    
    def _format_karst_content(self, data: dict) -> List:
        """Format karst analysis content"""
        story = []
        
        if 'within_karst_area' in data:
            status = "Yes" if data['within_karst_area'] else "No"
            story.append(Paragraph(
                f"<b>Within Karst Area:</b> {status}",
                self.styles['AnalysisText']
            ))
        
        if data.get('nearby_karst_features') is not None:
            nearby = "Yes" if data['nearby_karst_features'] else "No"
            story.append(Paragraph(
                f"<b>Nearby Karst Features:</b> {nearby}",
                self.styles['AnalysisText']
            ))
        
        if data.get('distance_to_nearest_feature_miles'):
            story.append(Paragraph(
                f"<b>Distance to Nearest Karst Feature:</b> {data['distance_to_nearest_feature_miles']} miles",
                self.styles['AnalysisText']
            ))
        
        if data.get('regulatory_impact'):
            story.append(Paragraph(
                f"<b>Regulatory Impact:</b> {data['regulatory_impact']}",
                self.styles['HighlightBox']
            ))
        
        # Add additional karst-specific fields that may be present
        if data.get('karst_proximity'):
            story.append(Paragraph(
                f"<b>Karst Proximity:</b> {data['karst_proximity']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('geological_significance'):
            story.append(Paragraph(
                f"<b>Geological Significance:</b> {data['geological_significance']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('development_constraints'):
            story.append(Paragraph(
                "<b>Development Constraints:</b>",
                self.styles['SubSectionHeader']
            ))
            constraints = data['development_constraints']
            if isinstance(constraints, list):
                for constraint in constraints:
                    story.append(Paragraph(f"• {constraint}", self.styles['AnalysisText']))
            else:
                story.append(Paragraph(f"• {constraints}", self.styles['AnalysisText']))
        
        if data.get('permit_requirements'):
            story.append(Paragraph(
                "<b>Permit Requirements:</b>",
                self.styles['SubSectionHeader']
            ))
            requirements = data['permit_requirements']
            if isinstance(requirements, list):
                for req in requirements:
                    story.append(Paragraph(f"• {req}", self.styles['AnalysisText']))
            else:
                story.append(Paragraph(f"• {requirements}", self.styles['AnalysisText']))
        
        return story
    
    def _format_property_content(self, data: dict) -> List:
        """Format property analysis content"""
        story = []
        
        if data.get('cadastral_number'):
            story.append(Paragraph(
                f"<b>Cadastral Number:</b> {data['cadastral_number']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('area_acres'):
            story.append(Paragraph(
                f"<b>Property Area:</b> {data['area_acres']} acres",
                self.styles['AnalysisText']
            ))
        
        if data.get('land_use'):
            story.append(Paragraph(
                f"<b>Land Use:</b> {data['land_use']}",
                self.styles['AnalysisText']
            ))
        
        if data.get('development_potential'):
            story.append(Paragraph(
                f"<b>Development Potential:</b> {data['development_potential']}",
                self.styles['HighlightBox']
            ))
        
        return story
    
    def _embed_map_in_section(self, map_file: Path, section_name: str) -> List:
        """Embed a map directly in a section with proper formatting"""
        story = []
        
        try:
            if map_file.suffix.lower() == '.pdf':
                # For PDF maps, add a reference and note
                story.append(Paragraph(
                    f"<b>Map Reference:</b> {map_file.name}",
                    self.styles['MapCaption']
                ))
                story.append(Paragraph(
                    f"<i>See attached {section_name} map: {map_file.name}</i>",
                    self.styles['MapCaption']
                ))
            else:
                # For image maps, try to embed directly
                try:
                    img = Image(str(map_file), width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Paragraph(
                        f"<b>Figure:</b> {section_name} Analysis Map",
                        self.styles['MapCaption']
                    ))
                except Exception as e:
                    print(f"⚠️ Could not embed image {map_file.name}: {e}")
                    story.append(Paragraph(
                        f"<b>Map Reference:</b> {map_file.name}",
                        self.styles['MapCaption']
                    ))
            
            story.append(Spacer(1, 12))
        except Exception as e:
            print(f"⚠️ Error processing map {map_file.name}: {e}")
        
        return story
    
    def _build_title_page(self) -> List:
        """Build sophisticated title page"""
        story = []
        
        story.append(Spacer(1, 2*inch))
        
        # Main title
        story.append(Paragraph(
            "Comprehensive Environmental Screening Report",
            self.styles['ReportTitle']
        ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Project name
        project_name = self.structured_data.get('project_name', 'Environmental Assessment Project')
        story.append(Paragraph(
            f"<b>{project_name}</b>",
            self.styles['SectionHeader']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Location information
        location_desc = self.structured_data.get('project_input_location_description', 'Location Not Specified')
        story.append(Paragraph(
            f"Location: {location_desc}",
            self.styles['AnalysisText']
        ))
        
        # Coordinates if available
        coords = self.structured_data.get('project_input_coordinates_lng_lat')
        if coords and len(coords) == 2:
            story.append(Paragraph(
                f"Coordinates: {coords[1]:.6f}, {coords[0]:.6f} (Lat, Lng)",
                self.styles['AnalysisText']
            ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Analysis date
        analysis_date = self.structured_data.get('screening_datetime_utc', datetime.now().isoformat())
        story.append(Paragraph(
            f"Analysis Date: {analysis_date}",
            self.styles['AnalysisText']
        ))
        
        story.append(Spacer(1, 1*inch))
        
        # Success status
        success = self.structured_data.get('success', True)
        status_text = "✅ Analysis Completed Successfully" if success else "⚠️ Analysis Completed with Issues"
        story.append(Paragraph(
            status_text,
            self.styles['HighlightBox']
        ))
        
        return story
    
    def _build_executive_summary(self) -> List:
        """Build executive summary from structured data"""
        story = []
        
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Environmental constraints
        constraints = self.structured_data.get('environmental_constraints_summary', [])
        if constraints:
            story.append(Paragraph("<b>Key Environmental Constraints:</b>", self.styles['SubSectionHeader']))
            for constraint in constraints:
                story.append(Paragraph(f"• {constraint}", self.styles['AnalysisText']))
            story.append(Spacer(1, 12))
        
        # Risk assessment
        risk_level = self.structured_data.get('overall_risk_level_assessment', 'Not assessed')
        story.append(Paragraph(
            f"<b>Overall Risk Level:</b> {risk_level}",
            self.styles['HighlightBox']
        ))
        
        # Regulatory requirements
        requirements = self.structured_data.get('key_regulatory_requirements_identified', [])
        if requirements:
            story.append(Paragraph("<b>Key Regulatory Requirements:</b>", self.styles['SubSectionHeader']))
            for req in requirements:
                story.append(Paragraph(f"• {req}", self.styles['AnalysisText']))
            story.append(Spacer(1, 12))
        
        # Recommendations
        recommendations = self.structured_data.get('agent_recommendations', [])
        if recommendations:
            story.append(Paragraph("<b>Primary Recommendations:</b>", self.styles['SubSectionHeader']))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", self.styles['AnalysisText']))
        
        return story
    
    def _build_risk_assessment(self) -> List:
        """Build risk assessment section"""
        story = []
        
        story.append(Paragraph("Cumulative Risk Assessment", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        # Overall assessment
        risk_level = self.structured_data.get('overall_risk_level_assessment', 'Not assessed')
        story.append(Paragraph(
            f"<b>Overall Risk Level:</b> {risk_level}",
            self.styles['HighlightBox']
        ))
        
        # Narrative summary
        narrative = self.structured_data.get('narrative_summary_of_findings')
        if narrative:
            story.append(Paragraph("<b>Summary of Findings:</b>", self.styles['SubSectionHeader']))
            story.append(Paragraph(narrative, self.styles['AnalysisText']))
        
        return story
    
    def _build_recommendations(self) -> List:
        """Build recommendations section"""
        story = []
        
        story.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        story.append(Spacer(1, 12))
        
        recommendations = self.structured_data.get('agent_recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", self.styles['AnalysisText']))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph(
                "No specific recommendations were generated for this analysis.",
                self.styles['AnalysisText']
            ))
        
        return story

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