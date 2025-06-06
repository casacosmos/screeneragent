#!/usr/bin/env python3
"""
HTML-based Professional PDF Generator for Environmental Screening Reports

This module generates professional PDF reports using HTML templates with:
- Sophisticated formatting and styling
- Embedded maps in their relevant sections (prefers PNG over PDF)
- Color-coded compliance checklist (Green/Yellow/Red)
- Easy-to-copy data fields
- Professional layout suitable for regulatory submission
- Support for both PNG and PDF map formats with automatic conversion fallback
"""

import json
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Jinja2 not available. Install with: pip install jinja2")
    JINJA2_AVAILABLE = False

# WeasyPrint for professional HTML to PDF conversion (optional)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    # Will warn only when actually trying to use HTML-to-PDF conversion

# pdf2image for PDF to image conversion (optional) 
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    # Will warn only when actually trying to use PDF-to-image conversion

# Fallback to reportlab if weasyprint not available
if not WEASYPRINT_AVAILABLE:
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False


class HTMLEnvironmentalPDFGenerator:
    """Professional HTML-based PDF generator for environmental screening reports"""
    
    def __init__(self, json_report_path: str, project_directory: str, prefer_png_maps: bool = True):
        """
        Initialize the HTML PDF generator
        
        Args:
            json_report_path: Path to the JSON report file
            project_directory: Path to the project directory containing maps
            prefer_png_maps: Whether to prefer PNG maps over PDF maps for embedding
        """
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required. Install with: pip install jinja2")
        
        self.json_report_path = Path(json_report_path)
        self.project_directory = Path(project_directory)
        self.template_path = Path(__file__).parent / "environmental_report_template.html"
        self.prefer_png_maps = prefer_png_maps
        
        # Load the JSON data
        with open(self.json_report_path, 'r') as f:
            self.report_data = json.load(f)
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.jinja_env.filters['yesno'] = self._yesno_filter
        
        print(f"🗺️ Map format preference: {'PNG (direct embedding)' if prefer_png_maps else 'PDF (with conversion)'}")
    
    def _yesno_filter(self, value):
        """Jinja2 filter to convert boolean to Yes/No"""
        if value is True:
            return "Yes"
        elif value is False:
            return "No"
        else:
            return "Unknown"
    
    def _find_best_map_file(self, base_path: Path, map_patterns: List[str]) -> Optional[Path]:
        """
        Find the best map file format for embedding
        
        Args:
            base_path: Base path relative to project directory
            map_patterns: List of filename patterns to search for
        
        Returns:
            Path to the best map file (PNG preferred, PDF fallback)
        """
        if not base_path.is_absolute():
            base_path = self.project_directory / base_path
        
        # If base_path points to a specific file, use it
        if base_path.is_file():
            return base_path
        
        # Search for map files in the directory
        search_dirs = [base_path, self.project_directory / "maps", self.project_directory / "reports"]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for pattern in map_patterns:
                # First, look for PNG files if preferred
                if self.prefer_png_maps:
                    png_files = list(search_dir.glob(f"{pattern}*.png"))
                    if png_files:
                        # Sort by modification time, newest first
                        png_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                        print(f"🎯 Found PNG map: {png_files[0].relative_to(self.project_directory)}")
                        return png_files[0]
                
                # Then look for PDF files
                pdf_files = list(search_dir.glob(f"{pattern}*.pdf"))
                if pdf_files:
                    # Sort by modification time, newest first
                    pdf_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    print(f"📄 Found PDF map: {pdf_files[0].relative_to(self.project_directory)}")
                    return pdf_files[0]
        
        return None
    
    def _convert_pdf_to_png(self, pdf_path: Path) -> Optional[Path]:
        """Convert PDF file to PNG for HTML embedding"""
        if not PDF2IMAGE_AVAILABLE:
            print(f"⚠️ Cannot convert PDF to PNG: pdf2image not available")
            return None
        
        try:
            print(f"🔄 Converting PDF to PNG: {pdf_path}")
            
            # Convert PDF to images (get first page only)
            images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=300)
            
            if not images:
                print(f"⚠️ No images could be extracted from PDF: {pdf_path}")
                return None
            
            # Save as PNG in the same directory
            png_path = pdf_path.with_suffix('.png')
            images[0].save(str(png_path), 'PNG')
            
            print(f"✅ PDF converted to PNG: {png_path}")
            return png_path
            
        except Exception as e:
            print(f"⚠️ Error converting PDF to PNG: {e}")
            return None
    
    def _encode_image_to_base64(self, image_path: Path) -> Optional[str]:
        """Convert image to base64 for embedding in HTML"""
        try:
            if not image_path.exists():
                print(f"⚠️ Map file not found: {image_path}")
                return None
            
            print(f"📄 Processing map file: {image_path}")
            
            # Handle PDF files by converting to PNG first (if not preferring PNG)
            ext = image_path.suffix.lower()
            if ext == '.pdf' and not self.prefer_png_maps:
                png_path = self._convert_pdf_to_png(image_path)
                if png_path and png_path.exists():
                    image_path = png_path
                    ext = '.png'
                else:
                    print(f"⚠️ Failed to convert PDF to PNG: {image_path}")
                    return None
            elif ext == '.pdf' and self.prefer_png_maps:
                # If we prefer PNG but only have PDF, try conversion as fallback
                png_path = self._convert_pdf_to_png(image_path)
                if png_path and png_path.exists():
                    image_path = png_path
                    ext = '.png'
                else:
                    print(f"⚠️ PDF map found but PNG preferred - conversion failed: {image_path}")
                    return None
            
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                
                # Determine MIME type
                if ext in ['.png']:
                    mime_type = 'image/png'
                elif ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                else:
                    print(f"⚠️ Unsupported image format: {ext}")
                    return None
                
                print(f"✅ Successfully encoded {image_path} ({len(img_data)} bytes)")
                return f"data:{mime_type};base64,{img_base64}"
        except Exception as e:
            print(f"⚠️ Could not encode image {image_path}: {e}")
            return None
    
    def _resolve_map_paths(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve map file paths and convert to base64 for embedding with intelligent format detection"""
        resolved_data = data.copy()
        
        map_search_patterns = {
            'flood_analysis': ['firmette', 'firm_map', 'fema', 'abfe', 'prefirm', 'flood_map'],
            'wetland_analysis': ['wetland', 'nwi', 'wetland_map'],
            'critical_habitat_analysis': ['habitat', 'critical_habitat', 'habitat_map'],
            'air_quality_analysis': ['nonattainment', 'air_quality', 'epa'],
            'karst_analysis': ['karst_map_embed', 'karst_map_archive', 'karst'] # Prioritize embeddable karst map
        }
        
        for section_key in ['flood_analysis', 'wetland_analysis', 'critical_habitat_analysis', 'air_quality_analysis', 'karst_analysis']:
            section_data = resolved_data.get(section_key) # Use .get() for safety, defaults to None
            
            if isinstance(section_data, dict): # Proceed only if section_data is a dictionary
                map_embedded_for_section = False
                
                # Special handling for flood_analysis - check for multiple map types
                if section_key == 'flood_analysis':
                    # Look for FIRMette, preFIRM, and ABFE maps
                    flood_map_types = {
                        'firmette_map_path': ['firmette', 'firm_map', 'FIRMette'],
                        'prefirm_map_path': ['prefirm', 'pre_firm', 'preliminary'],
                        'abfe_map_path': ['abfe', 'advisory', 'base_flood_elevation']
                    }
                    
                    for map_field, patterns in flood_map_types.items():
                        # Check if the field exists in the data
                        if map_field in section_data and section_data.get(map_field):
                            map_path = Path(section_data[map_field]) if Path(section_data[map_field]).is_absolute() else self.project_directory / section_data[map_field]
                            if map_path.exists():
                                base64_data = self._encode_image_to_base64(map_path)
                                if base64_data:
                                    section_data[map_field] = base64_data
                                    print(f"✅ Embedded specific {map_field}: {map_path.name}")
                                else:
                                    section_data[map_field] = None
                            else:
                                section_data[map_field] = None
                        else:
                            # Try to find the map by pattern search
                            best_map = None
                            for pattern in patterns:
                                found_maps = list((self.project_directory / "maps").glob(f"*{pattern}*"))
                                if found_maps:
                                    # Sort by modification time, newest first
                                    found_maps.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                                    # Prefer PNG over PDF for embedding
                                    png_maps = [m for m in found_maps if m.suffix.lower() == '.png']
                                    if png_maps:
                                        best_map = png_maps[0]
                                    else:
                                        best_map = found_maps[0]
                                    break
                            
                            if best_map:
                                base64_data = self._encode_image_to_base64(best_map)
                                if base64_data:
                                    section_data[map_field] = base64_data
                                    print(f"✅ Found and embedded {map_field} via search: {best_map.name}")
                                else:
                                    section_data[map_field] = None
                            else:
                                section_data[map_field] = None
                    
                    # For backward compatibility, also set the generic firme_map_path field
                    if section_data.get('firmette_map_path'):
                        section_data['firme_map_path'] = section_data['firmette_map_path']
                        map_embedded_for_section = True
                
                # Check specific map path fields first (e.g., karst_map_embed_path)
                # For karst, we specifically look for 'karst_map_embed_path' or 'map_reference'
                elif section_key == 'karst_analysis':
                    map_path_field_to_try = section_data.get('karst_map_embed_path') or section_data.get('map_reference')
                    if map_path_field_to_try:
                        map_path = Path(map_path_field_to_try) if Path(map_path_field_to_try).is_absolute() else self.project_directory / map_path_field_to_try
                        if map_path.exists():
                            base64_data = self._encode_image_to_base64(map_path)
                            if base64_data:
                                # Update the primary map reference field used by the template
                                section_data['map_reference'] = base64_data
                                map_embedded_for_section = True
                                print(f"✅ Embedded specific map for {section_key}: {map_path.name}")
                            else:
                                section_data['map_reference'] = None
                        else:
                            print(f"⚠️ Specified map path for {section_key} not found: {map_path}")
                            section_data['map_reference'] = None 
                else:
                    # Generic check for other sections, could be more specific if needed
                    for potential_field in ['map_reference', 'firme_map_path', 'nwi_map_path', 'critical_habitat_map_path', 'nonattainment_map_path']:
                        if potential_field in section_data and section_data.get(potential_field):
                            map_path_field_to_try = section_data.get(potential_field)
                            break
                    else:
                        map_path_field_to_try = None
                    
                    if map_path_field_to_try:
                        map_path = Path(map_path_field_to_try) if Path(map_path_field_to_try).is_absolute() else self.project_directory / map_path_field_to_try
                        if map_path.exists():
                            base64_data = self._encode_image_to_base64(map_path)
                            if base64_data:
                                # Update the primary map reference field used by the template
                                if section_key == 'wetland_analysis': section_data['nwi_map_path'] = base64_data
                                elif section_key == 'critical_habitat_analysis': section_data['critical_habitat_map_path'] = base64_data
                                elif section_key == 'air_quality_analysis': section_data['nonattainment_map_path'] = base64_data
                                map_embedded_for_section = True
                                print(f"✅ Embedded specific map for {section_key}: {map_path.name}")
                        else:
                            print(f"⚠️ Specified map path for {section_key} not found: {map_path}")
                            # Nullify if path doesn't exist
                            if section_key == 'wetland_analysis': section_data['nwi_map_path'] = None
                            elif section_key == 'critical_habitat_analysis': section_data['critical_habitat_map_path'] = None
                            elif section_key == 'air_quality_analysis': section_data['nonattainment_map_path'] = None

                # Fallback to intelligent search if no specific path worked or was found for this section
                if not map_embedded_for_section and section_key != 'flood_analysis':  # flood_analysis already handled above
                    print(f"🔍 No specific map path worked for {section_key}. Trying intelligent search in maps/ directory...")
                    patterns = map_search_patterns.get(section_key, [section_key.split('_')[0]])
                    best_map = self._find_best_map_file(self.project_directory / "maps", patterns)
                    
                    if best_map:
                        base64_data = self._encode_image_to_base64(best_map)
                        if base64_data:
                            # Update the primary map reference field used by the template for this section
                            if section_key == 'karst_analysis': section_data['map_reference'] = base64_data
                            elif section_key == 'wetland_analysis': section_data['nwi_map_path'] = base64_data
                            elif section_key == 'critical_habitat_analysis': section_data['critical_habitat_map_path'] = base64_data
                            elif section_key == 'air_quality_analysis': section_data['nonattainment_map_path'] = base64_data
                            print(f"✅ Found and embedded map for {section_key} via search: {best_map.name}")
                        else:
                            if section_key == 'karst_analysis': section_data['map_reference'] = None # Failed encoding
                    else:
                        print(f"⚠️ No suitable map found for {section_key} via intelligent search.")
                        if section_key == 'karst_analysis': section_data['map_reference'] = None # No map found
            elif section_data is None:
                 print(f"ℹ️ Section {section_key} is not present in report data, skipping map resolution.")
        
        return resolved_data
    
    def _evaluate_compliance_checklist(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate environmental factors for the compliance checklist"""
        checklist_data = {}
        
        # Flood Zone Evaluation
        flood_data = data.get('flood_analysis', {})
        flood_zone = flood_data.get('fema_flood_zone', 'Unknown')
        
        if flood_zone in ['AE', 'VE', 'A', 'V']:
            checklist_data.update({
                'flood_status': 'CRITICAL',
                'flood_status_class': 'status-red',
                'flood_risk': 'HIGH',
                'flood_risk_class': 'status-red',
                'flood_action': 'FEMA consultation required, flood insurance mandatory, elevation requirements'
            })
        elif flood_zone in ['AH', 'AO']:
            checklist_data.update({
                'flood_status': 'REVIEW',
                'flood_status_class': 'status-yellow',
                'flood_risk': 'MODERATE',
                'flood_risk_class': 'status-yellow',
                'flood_action': 'Review flood requirements, insurance recommended'
            })
        elif flood_zone in ['X', 'C']:
            checklist_data.update({
                'flood_status': 'COMPLIANT',
                'flood_status_class': 'status-green',
                'flood_risk': 'LOW',
                'flood_risk_class': 'status-green',
                'flood_action': 'Standard construction practices'
            })
        else:
            checklist_data.update({
                'flood_status': 'UNKNOWN',
                'flood_status_class': 'status-yellow',
                'flood_risk': 'UNKNOWN',
                'flood_risk_class': 'status-yellow',
                'flood_action': 'Verify flood zone designation'
            })
        
        # Wetland Evaluation
        wetland_data = data.get('wetland_analysis', {})
        wetlands_on_property = wetland_data.get('directly_on_property', False)
        distance_to_wetlands = wetland_data.get('distance_to_nearest', 999)
        
        if wetlands_on_property:
            checklist_data.update({
                'wetland_status': 'CRITICAL',
                'wetland_status_class': 'status-red',
                'wetland_risk': 'HIGH',
                'wetland_risk_class': 'status-red',
                'wetland_action': 'USACE Section 404 permit required, delineation study mandatory'
            })
        elif distance_to_wetlands < 0.5:
            checklist_data.update({
                'wetland_status': 'REVIEW',
                'wetland_status_class': 'status-yellow',
                'wetland_risk': 'MODERATE',
                'wetland_risk_class': 'status-yellow',
                'wetland_action': 'Wetland delineation study recommended, buffer considerations'
            })
        else:
            checklist_data.update({
                'wetland_status': 'COMPLIANT',
                'wetland_status_class': 'status-green',
                'wetland_risk': 'LOW',
                'wetland_risk_class': 'status-green',
                'wetland_action': 'No immediate wetland concerns'
            })
        
        # Critical Habitat Evaluation
        habitat_data = data.get('critical_habitat_analysis', {})
        within_habitat = habitat_data.get('within_designated_habitat', False)
        within_proposed = habitat_data.get('within_proposed_habitat', False)
        
        if within_habitat:
            checklist_data.update({
                'habitat_status': 'CRITICAL',
                'habitat_status_class': 'status-red',
                'habitat_risk': 'HIGH',
                'habitat_risk_class': 'status-red',
                'habitat_action': 'ESA Section 7 consultation required, biological assessment needed'
            })
        elif within_proposed:
            checklist_data.update({
                'habitat_status': 'REVIEW',
                'habitat_status_class': 'status-yellow',
                'habitat_risk': 'MODERATE',
                'habitat_risk_class': 'status-yellow',
                'habitat_action': 'ESA consultation recommended, impact assessment suggested'
            })
        else:
            checklist_data.update({
                'habitat_status': 'COMPLIANT',
                'habitat_status_class': 'status-green',
                'habitat_risk': 'LOW',
                'habitat_risk_class': 'status-green',
                'habitat_action': 'No critical habitat concerns'
            })
        
        # Zoning Evaluation
        cadastral_data = data.get('cadastral_analysis', {})
        land_use = cadastral_data.get('land_use_classification', '').lower()
        zoning = cadastral_data.get('zoning_designation', '').lower()
        
        # Check for restrictive zoning
        restrictive_zones = ['agricultural', 'farming', 'conservation', 'preservation', 'open space']
        if any(zone in land_use or zone in zoning for zone in restrictive_zones):
            checklist_data.update({
                'zoning_status': 'CRITICAL',
                'zoning_status_class': 'status-red',
                'zoning_risk': 'HIGH',
                'zoning_risk_class': 'status-red',
                'zoning_action': 'Zoning variance/change required, development restrictions apply'
            })
        elif 'industrial' in land_use or 'commercial' in land_use or 'residential' in land_use:
            checklist_data.update({
                'zoning_status': 'COMPLIANT',
                'zoning_status_class': 'status-green',
                'zoning_risk': 'LOW',
                'zoning_risk_class': 'status-green',
                'zoning_action': 'Development permitted by zoning'
            })
        else:
            checklist_data.update({
                'zoning_status': 'REVIEW',
                'zoning_status_class': 'status-yellow',
                'zoning_risk': 'MODERATE',
                'zoning_risk_class': 'status-yellow',
                'zoning_action': 'Verify permitted uses and development restrictions'
            })
        
        # Air Quality Evaluation
        air_data = data.get('air_quality_analysis', {})
        nonattainment_status = air_data.get('nonattainment_status', False)
        area_classification = air_data.get('area_classification', '')
        
        if nonattainment_status or 'nonattainment' in area_classification.lower():
            checklist_data.update({
                'air_status': 'REVIEW',
                'air_status_class': 'status-yellow',
                'air_risk': 'MODERATE',
                'air_risk_class': 'status-yellow',
                'air_action': 'Emission controls required, air quality permits needed'
            })
        else:
            checklist_data.update({
                'air_status': 'COMPLIANT',
                'air_status_class': 'status-green',
                'air_risk': 'LOW',
                'air_risk_class': 'status-green',
                'air_action': 'Standard air quality compliance'
            })
        
        # Karst Evaluation
        karst_data = data.get('karst_analysis', {})
        # Handle case where karst_analysis is None/null
        if karst_data is None:
            karst_data = {}
        
        # Use new field names from the KarstAnalysis dataclass
        within_karst_general = karst_data.get('within_karst_area_general', False)
        # Consider 'direct' or 'buffer' (if APE-ZC) as high impact for checklist, 
        # or rely on regulatory_impact_level directly.
        # For simplicity, let's use regulatory_impact_level if available.
        impact_level = karst_data.get('regulatory_impact_level', 'none').lower()

        if impact_level == 'high':
            checklist_data.update({
                'karst_status': 'CRITICAL',
                'karst_status_class': 'status-red',
                'karst_risk': 'HIGH',
                'karst_risk_class': 'status-red',
                'karst_action': 'PRAPEC consultation required, geological study mandatory. Refer to detailed report section.'
            })
        elif impact_level == 'moderate':
            checklist_data.update({
                'karst_status': 'REVIEW',
                'karst_status_class': 'status-yellow',
                'karst_risk': 'MODERATE',
                'karst_risk_class': 'status-yellow',
                'karst_action': 'Geological assessment recommended, karst considerations in design. Refer to detailed report section.'
            })
        elif karst_data.get('karst_status_general') == 'nearby_extended_search' or impact_level == 'low':
            checklist_data.update({
                'karst_status': 'REVIEW',
                'karst_status_class': 'status-yellow',
                'karst_risk': 'LOW',
                'karst_risk_class': 'status-yellow',
                'karst_action': 'Review nearby karst features if identified. Standard diligence otherwise.'
            })
        else: # 'none' or other unhandled impact
            checklist_data.update({
                'karst_status': 'COMPLIANT',
                'karst_status_class': 'status-green',
                'karst_risk': 'LOW',
                'karst_risk_class': 'status-green',
                'karst_action': 'No immediate karst-related concerns based on available data.'
            })
        
        return checklist_data
    
    def _prepare_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        template_data = data.copy()
        
        # CRITICAL: Resolve map paths to base64 for embedding
        template_data = self._resolve_map_paths(template_data)
        
        # Extract project information
        project_info = data.get('project_info', {})
        template_data['project_name'] = project_info.get('project_name', 'Environmental Screening Project')
        template_data['analysis_date'] = project_info.get('analysis_date_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Location and coordinates
        template_data['location_description'] = project_info.get('location_name', 'Location not specified')
        
        # Get coordinates from project_info
        lat = project_info.get('latitude')
        lng = project_info.get('longitude')
        if lat is not None and lng is not None:
            template_data['coordinates'] = f"{lat:.6f}, {lng:.6f}"
        else:
            template_data['coordinates'] = "Coordinates not available"
        
        template_data['project_directory'] = project_info.get('project_directory', 'Not specified')
        
        # Risk level from cumulative risk assessment
        cumulative_risk = data.get('cumulative_risk_assessment', {})
        risk_level = cumulative_risk.get('overall_risk_profile', 'Not assessed')
        template_data['overall_risk_level'] = risk_level
        
        # Determine risk class for styling
        if 'high' in risk_level.lower():
            template_data['risk_class'] = 'risk-high'
        elif 'moderate' in risk_level.lower():
            template_data['risk_class'] = 'risk-moderate'
        else:
            template_data['risk_class'] = 'risk-low'
        
        # Add compliance checklist data
        checklist_data = self._evaluate_compliance_checklist(data)
        template_data.update(checklist_data)
        
        return template_data
    
    def generate_html_report(self, output_path: str = None) -> str:
        """Generate HTML report"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.report_data.get('project_info', {}).get('project_name', 'Environmental_Screening')
            # Clean project name for filename
            clean_name = re.sub(r'[^\w\s-]', '', project_name).strip()
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
            output_path = f"environmental_report_{clean_name}_{timestamp}.html"
        
        # Load template
        template = self.jinja_env.get_template('environmental_report_template.html')
        
        # Prepare template data
        template_data = self._prepare_template_data(self.report_data)
        
        # Render template
        html_content = template.render(**template_data)
        
        # Save HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML report generated: {output_path}")
        return output_path
    
    def generate_pdf_report(self, output_path: str = None) -> str:
        """Generate PDF report from HTML template"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.report_data.get('project_info', {}).get('project_name', 'Environmental_Screening')
            # Clean project name for filename
            clean_name = re.sub(r'[^\w\s-]', '', project_name).strip()
            clean_name = re.sub(r'[-\s]+', '_', clean_name)
            output_path = f"professional_environmental_report_{clean_name}_{timestamp}.pdf"
        
        # Generate HTML first
        html_path = self.generate_html_report(output_path.replace('.pdf', '.html'))
        
        if WEASYPRINT_AVAILABLE:
            try:
                # Use WeasyPrint for high-quality PDF generation
                print("📄 Generating PDF using WeasyPrint...")
                weasyprint.HTML(filename=html_path).write_pdf(output_path)
                print(f"✅ Professional PDF report generated: {output_path}")
                
                # Clean up HTML file
                os.remove(html_path)
                
                return output_path
            except Exception as e:
                print(f"⚠️ WeasyPrint failed: {e}")
                print("Falling back to basic PDF generation...")
        
        # Fallback to basic PDF generation
        if REPORTLAB_AVAILABLE:
            return self._generate_basic_pdf(output_path)
        else:
            print("❌ No PDF generation libraries available")
            print(f"📄 HTML report available at: {html_path}")
            return html_path
    
    def _generate_basic_pdf(self, output_path: str) -> str:
        """Generate basic PDF using reportlab as fallback"""
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.pagesizes import letter
            
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add basic content
            story.append(Paragraph("Professional Environmental Screening Report", styles['Title']))
            story.append(Spacer(1, 12))
            
            project_name = self.report_data.get('project_info', {}).get('project_name', 'Environmental Screening')
            story.append(Paragraph(f"Project: {project_name}", styles['Heading1']))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("⚠️ This is a basic PDF version. For full professional formatting with embedded maps and compliance checklist, install WeasyPrint:", styles['Normal']))
            story.append(Paragraph("pip install weasyprint", styles['Code']))
            story.append(Spacer(1, 12))
            
            story.append(Paragraph("The full HTML version with all features is available alongside this PDF.", styles['Normal']))
            
            doc.build(story)
            print(f"📄 Basic PDF generated: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Basic PDF generation failed: {e}")
            return None

    @staticmethod
    def configure_env_tools_for_png_output():
        """
        Configure environmental analysis tools to generate PNG maps instead of PDF maps.
        This modifies the tools to prefer PNG output format for better HTML embedding.
        """
        print("🛠️ Configuring environmental analysis tools for PNG output...")
        
        # This is a placeholder for tool configuration
        # In a real implementation, you would modify the tool configuration files
        # or environment variables to set PNG as the preferred output format
        
        # For now, we'll document what should be configured:
        configuration_notes = {
            "wetland_tools": {
                "file": "WetlandsINFO/generate_wetland_map_pdf_v3.py",
                "change": "Modify 'format': 'PDF' to 'format': 'PNG' in _create_web_map_json method",
                "line_approx": 301
            },
            "habitat_tools": {
                "file": "HabitatINFO/generate_critical_habitat_map_pdf.py", 
                "change": "Modify 'format': 'PDF' to 'format': 'PNG' in _create_web_map_json method",
                "line_approx": 330
            },
            "flood_tools": {
                "file": "FloodINFO/abfe_client.py",
                "change": "Set default map_format to 'PNG' instead of 'PDF'",
                "line_approx": 34
            },
            "air_quality_tools": {
                "file": "nonattainment_analysis_tool.py",
                "change": "Configure map export format to PNG if supported"
            }
        }
        
        print("📝 Tool configuration required for PNG output:")
        for tool, config in configuration_notes.items():
            print(f"   • {tool}:")
            print(f"     File: {config['file']}")
            print(f"     Change: {config['change']}")
            if 'line_approx' in config:
                print(f"     Line: ~{config['line_approx']}")
        
        print("\n💡 Alternatively, tools can be configured at runtime via environment variables")
        print("   or by passing format parameters to the analysis functions.")
        
        return configuration_notes


def main():
    """Test the HTML PDF generator with an existing JSON report"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate professional PDF reports from JSON environmental screening data')
    parser.add_argument('json_file', nargs='?', help='Path to JSON screening report')
    parser.add_argument('project_directory', nargs='?', help='Path to project directory containing maps')
    parser.add_argument('--output', help='Output PDF filename')
    parser.add_argument('--html-only', action='store_true', help='Generate HTML only (no PDF)')
    parser.add_argument('--prefer-png', action='store_true', default=True, help='Prefer PNG maps over PDF maps (default: True)')
    parser.add_argument('--prefer-pdf', action='store_true', help='Prefer PDF maps over PNG maps (overrides --prefer-png)')
    parser.add_argument('--configure-png', action='store_true', help='Show configuration needed for PNG map output')
    
    args = parser.parse_args()
    
    # Handle configuration command
    if args.configure_png:
        print("🛠️ PNG Map Configuration Guide")
        print("=" * 60)
        HTMLEnvironmentalPDFGenerator.configure_env_tools_for_png_output()
        print("\n✅ Configuration guide displayed. Use these settings to enable PNG map generation.")
        return 0
    
    if not args.json_file or not args.project_directory:
        print("❌ Missing required arguments")
        print("\nUsage examples:")
        print("  python html_pdf_generator.py report.json project_dir/")
        print("  python html_pdf_generator.py --configure-png")
        print("  python html_pdf_generator.py report.json project_dir/ --prefer-png --output custom.pdf")
        return 1
    
    if not Path(args.json_file).exists():
        print(f"❌ JSON file not found: {args.json_file}")
        return 1
    
    if not Path(args.project_directory).exists():
        print(f"❌ Project directory not found: {args.project_directory}")
        return 1
    
    # Determine PNG preference
    prefer_png = args.prefer_png and not args.prefer_pdf
    
    try:
        generator = HTMLEnvironmentalPDFGenerator(
            json_report_path=args.json_file,
            project_directory=args.project_directory,
            prefer_png_maps=prefer_png
        )
        
        print(f"🗺️ Map format preference: {'PNG (direct embedding)' if prefer_png else 'PDF (with conversion)'}")
        
        if args.html_only:
            output_file = generator.generate_html_report(args.output)
            print(f"✅ HTML report generated: {output_file}")
        else:
            output_file = generator.generate_pdf_report(args.output)
            print(f"✅ Professional PDF report generated: {output_file}")
            
            # Show map embedding summary
            print(f"\n📊 Map Embedding Summary:")
            print(f"   • Format preference: {'PNG' if prefer_png else 'PDF with conversion'}")
            print(f"   • PDF2Image available: {'Yes' if PDF2IMAGE_AVAILABLE else 'No'}")
            print(f"   • WeasyPrint available: {'Yes' if WEASYPRINT_AVAILABLE else 'No'}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main()) 