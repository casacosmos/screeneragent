#!/usr/bin/env python3
"""
Simplified HTML Environmental PDF Generator

Uses the professional environmental_report_template.html with JSON data.
Clear directory structure and proper template rendering.

Directory Structure:
project_directory/
├── data/           # JSON data files  
├── maps/           # All map files (PDF and PNG)
├── reports/        # Generated HTML and PDF reports
└── logs/           # Log files
"""

import json
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Check for dependencies
try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

class SimplifiedHTMLPDFGenerator:
    """PDF generator using environmental_report_template.html with JSON data"""
    
    def __init__(self, json_report_path: str, project_directory: str):
        """
        Initialize generator with template-based rendering
        
        Args:
            json_report_path: Path to environmental data JSON
            project_directory: Single project directory for ALL outputs
        """
        # Set paths - everything in project directory
        self.project_dir = Path(project_directory).resolve()
        self.json_path = Path(json_report_path).resolve()
        
        # Standard subdirectories 
        self.data_dir = self.project_dir / "data"
        self.maps_dir = self.project_dir / "maps"
        self.reports_dir = self.project_dir / "reports"
        self.logs_dir = self.project_dir / "logs"
        
        # Create directories
        for d in [self.data_dir, self.maps_dir, self.reports_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Load data
        with open(self.json_path, 'r') as f:
            self.data = json.load(f)
        
        # Find template file
        self.template_path = self._find_template_file()
        
        print(f"📁 Simplified Generator Ready")
        print(f"   Project: {self.project_dir}")
        print(f"   Template: {self.template_path}")
        print(f"   Maps: {self.maps_dir}")
        print(f"   Reports: {self.reports_dir}")
    
    def _find_template_file(self) -> Path:
        """Find the environmental report template"""
        # Look for template in current directory first
        current_dir = Path.cwd()
        template_name = "environmental_report_template.html"
        
        # Check current directory
        template_path = current_dir / template_name
        if template_path.exists():
            return template_path
        
        # Check project directory
        template_path = self.project_dir / template_name
        if template_path.exists():
            return template_path
            
        # Check parent directories
        for parent in current_dir.parents:
            template_path = parent / template_name
            if template_path.exists():
                return template_path
        
        raise FileNotFoundError(f"Could not find {template_name} in current directory or parents")
    
    def find_maps(self) -> Dict[str, str]:
        """Find all maps and return as base64 for embedding"""
        maps = {}
        
        # Enhanced map finding - look for both PNG and PDF files
        patterns = {
            'flood_map': ['*flood*.png', '*firmette*.png', '*abfe*.png', '*flood*.pdf', '*firmette*.pdf', '*abfe*.pdf'],
            'wetland_map': ['*wetland*.png', '*nwi*.png', '*wetland*.pdf', '*nwi*.pdf'],
            'habitat_map': ['*habitat*.png', '*critical*.png', '*habitat*.pdf', '*critical*.pdf'],
            'air_map': ['*nonattainment*.png', '*air*.png', '*nonattainment*.pdf', '*air*.pdf'],
            'karst_map': ['*karst*.png', '*karst*.png32', '*karst*.pdf']
        }
        
        for map_type, file_patterns in patterns.items():
            for pattern in file_patterns:
                found_files = list(self.maps_dir.glob(pattern))
                if found_files:
                    # Use most recent file
                    map_file = max(found_files, key=lambda x: x.stat().st_mtime)
                    base64_data = self._encode_image(map_file)
                    if base64_data:
                        maps[map_type] = base64_data
                        print(f"   ✅ {map_type}: {map_file.name}")
                        break
        
        return maps
    
    def _encode_image(self, image_path: Path) -> Optional[str]:
        """Convert image to base64 for HTML embedding with PDF conversion support"""
        try:
            # Handle .png32 files (rename to .png)
            if image_path.suffix.lower() == '.png32':
                png_path = image_path.with_suffix('.png')
                if not png_path.exists():
                    # Copy .png32 to .png
                    png_path.write_bytes(image_path.read_bytes())
                image_path = png_path
            
            # Handle PDF files - try to convert to PNG
            elif image_path.suffix.lower() == '.pdf':
                png_path = image_path.with_suffix('.png')
                if not png_path.exists():
                    success = self._convert_pdf_to_png(image_path, png_path)
                    if not success:
                        print(f"⚠️ Could not convert PDF to PNG: {image_path}")
                        return None
                image_path = png_path
            
            # Now encode the image
            with open(image_path, 'rb') as f:
                data = base64.b64encode(f.read()).decode('utf-8')
            
            if image_path.suffix.lower() == '.png':
                return f"data:image/png;base64,{data}"
            elif image_path.suffix.lower() in ['.jpg', '.jpeg']:
                return f"data:image/jpeg;base64,{data}"
            
            return None
        except Exception as e:
            print(f"⚠️ Failed to encode {image_path}: {e}")
            return None
    
    def _convert_pdf_to_png(self, pdf_path: Path, png_path: Path) -> bool:
        """Convert PDF to PNG using available methods"""
        try:
            # Try pdf2image first (if available)
            try:
                from pdf2image import convert_from_path
                print(f"🔄 Converting PDF to PNG: {pdf_path.name}")
                images = convert_from_path(str(pdf_path), first_page=1, last_page=1, dpi=150)
                if images:
                    images[0].save(str(png_path), 'PNG')
                    print(f"✅ PDF converted successfully: {png_path.name}")
                    return True
            except ImportError:
                pass
            
            # Try using Pillow directly (for simple PDFs)
            try:
                from PIL import Image
                print(f"🔄 Trying Pillow conversion: {pdf_path.name}")
                with Image.open(pdf_path) as img:
                    img.save(png_path, 'PNG')
                    print(f"✅ PDF converted via Pillow: {png_path.name}")
                    return True
            except Exception:
                pass
            
            print(f"⚠️ Could not convert PDF {pdf_path.name} - no conversion method available")
            return False
            
        except Exception as e:
            print(f"⚠️ Error converting PDF to PNG: {e}")
            return False
    
    def _process_data_for_template(self, maps: Dict[str, str]) -> Dict[str, Any]:
        """Process JSON data to match template variables"""
        project_info = self.data.get('project_info', {})
        query_results = self.data.get('query_results', {})
        
        # Extract coordinates
        lat = project_info.get('latitude', 0)
        lng = project_info.get('longitude', 0)
        coordinates = f"{lat:.6f}, {lng:.6f}"
        
        # Process each analysis domain
        flood_analysis = self._process_flood_data(query_results.get('flood', {}))
        wetland_analysis = self._process_wetland_data(query_results.get('wetland', {}))
        habitat_analysis = self._process_habitat_data(query_results.get('habitat', {}))
        air_analysis = self._process_air_data(query_results.get('air_quality', {}))
        karst_analysis = self._process_karst_data(query_results.get('karst', {}))
        cadastral_analysis = self._process_cadastral_data(query_results.get('cadastral', {}))
        
        # Add map paths to analyses
        if 'flood_map' in maps:
            flood_analysis['firmette_map_path'] = maps['flood_map']
        if 'wetland_map' in maps:
            wetland_analysis['wetland_map_path'] = maps['wetland_map']
        if 'habitat_map' in maps:
            habitat_analysis['habitat_map_path'] = maps['habitat_map']
        if 'air_map' in maps:
            air_analysis['air_quality_map_path'] = maps['air_map']
        if 'karst_map' in maps:
            karst_analysis['karst_map_path'] = maps['karst_map']
        
        # Calculate overall risk and status
        risk_info = self._calculate_risk_assessment(flood_analysis, wetland_analysis, habitat_analysis, air_analysis, karst_analysis)
        
        # Template data structure
        template_data = {
            # Basic project info
            'project_name': project_info.get('project_name', 'Environmental Assessment'),
            'analysis_date': datetime.now().strftime('%B %d, %Y'),
            'coordinates': coordinates,
            'location_description': f"Lat: {lat:.6f}, Lng: {lng:.6f}",
            
            # Risk assessment
            'overall_risk_level': risk_info['level'],
            'risk_class': risk_info['class'],
            
            # Analysis domains
            'flood_analysis': flood_analysis,
            'wetland_analysis': wetland_analysis,
            'critical_habitat_analysis': habitat_analysis,
            'air_quality_analysis': air_analysis,
            'karst_analysis': karst_analysis,
            'cadastral_analysis': cadastral_analysis,
            
            # Status determinations for screening table
            'flood_status': self._get_flood_status(flood_analysis),
            'flood_status_class': self._get_status_class_for_status(self._get_flood_status(flood_analysis)),
            'flood_action': self._get_flood_action(flood_analysis),
            
            'wetland_status': self._get_wetland_status(wetland_analysis),
            'wetland_status_class': self._get_status_class_for_status(self._get_wetland_status(wetland_analysis)),
            'wetland_action': self._get_wetland_action(wetland_analysis),
            
            'habitat_status': self._get_habitat_status(habitat_analysis),
            'habitat_status_class': self._get_status_class_for_status(self._get_habitat_status(habitat_analysis)),
            'habitat_action': self._get_habitat_action(habitat_analysis),
            
            'air_status': self._get_air_status(air_analysis),
            'air_status_class': self._get_status_class_for_status(self._get_air_status(air_analysis)),
            'air_action': self._get_air_action(air_analysis),
            
            'karst_status': self._get_karst_status(karst_analysis),
            'karst_status_class': self._get_status_class_for_status(self._get_karst_status(karst_analysis)),
            'karst_action': self._get_karst_action(karst_analysis),
            
            'zoning_status': self._get_zoning_status(cadastral_analysis),
            'zoning_status_class': self._get_status_class_for_status(self._get_zoning_status(cadastral_analysis)),
            'zoning_action': self._get_zoning_action(cadastral_analysis),
            
            # Executive summary
            'executive_summary': self._generate_executive_summary(risk_info, flood_analysis, wetland_analysis, habitat_analysis, air_analysis, karst_analysis)
        }
        
        return template_data
    
    def _process_flood_data(self, flood_data: Dict) -> Dict[str, Any]:
        """Process flood analysis data"""
        return {
            'primary_flood_zone': flood_data.get('primary_flood_zone', 'Unknown'),
            'primary_base_flood_elevation': flood_data.get('primary_base_flood_elevation'),
            'primary_firm_panel': flood_data.get('primary_firm_panel'),
            'primary_effective_date': flood_data.get('primary_effective_date'),
            'flood_insurance_required': flood_data.get('flood_insurance_required', False),
            'community_id': flood_data.get('community_id'),
            'preliminary_changes_pending': flood_data.get('preliminary_changes_pending', False),
            'flood_zones': flood_data.get('flood_zones', [])
        }
    
    def _process_wetland_data(self, wetland_data: Dict) -> Dict[str, Any]:
        """Process wetland analysis data"""
        wetland_analysis = wetland_data.get('wetland_analysis', {})
        return {
            'directly_on_property': wetland_analysis.get('is_in_wetland', False),
            'wetlands_found_count': wetland_analysis.get('wetlands_count', 0),
            'distance_to_nearest': wetland_analysis.get('distance_to_nearest_miles'),
            'wetland_types_found': wetland_analysis.get('wetland_types', []),
            'requires_usace_permit': wetland_analysis.get('likely_jurisdictional', False),
            'section_404_required': wetland_analysis.get('section_404_required', False),
            'impact_assessment': wetland_analysis.get('impact_level', 'Low'),
            'mitigation_required': wetland_analysis.get('mitigation_required', False),
            'wetland_details': wetland_analysis.get('wetland_features', [])
        }
    
    def _process_habitat_data(self, habitat_data: Dict) -> Dict[str, Any]:
        """Process critical habitat data"""
        habitat_assessment = habitat_data.get('habitat_assessment', {})
        return {
            'within_designated_habitat': habitat_assessment.get('is_in_critical_habitat', False),
            'within_proposed_habitat': habitat_assessment.get('is_in_proposed_habitat', False),
            'affected_species_count': len(habitat_data.get('endangered_species', [])),
            'consultation_required': habitat_data.get('regulatory_assessment', {}).get('esa_consultation_required', False),
            'species_list': habitat_data.get('endangered_species', [])
        }
    
    def _process_air_data(self, air_data: Dict) -> Dict[str, Any]:
        """Process air quality data"""
        air_quality_status = air_data.get('air_quality_status', {})
        return {
            'area_classification': air_quality_status.get('classification', 'Attainment'),
            'nonattainment_status': air_quality_status.get('is_nonattainment', False),
            'maintenance_area': air_quality_status.get('is_maintenance', False),
            'naaqs_status': air_quality_status.get('naaqs_compliance', 'Compliant'),
            'pollutants_of_concern': air_data.get('nonattainment_areas', [])
        }
    
    def _process_karst_data(self, karst_data: Dict) -> Dict[str, Any]:
        """Process karst geology data"""
        return {
            'regulatory_impact_level': karst_data.get('regulatory_impact_level', 'None'),
            'within_karst_area_general': karst_data.get('within_karst_area_general', False),
            'karst_zone_designation': karst_data.get('karst_zone_designation'),
            'planning_restrictions': karst_data.get('planning_restrictions', False),
            'geological_stability': karst_data.get('geological_assessment', {}).get('stability', 'Unknown'),
            'sinkhole_risk': karst_data.get('geological_assessment', {}).get('sinkhole_risk', 'Low'),
            'groundwater_protection': karst_data.get('regulatory_requirements', {}).get('groundwater_protection', 'Standard'),
            'special_studies_required': karst_data.get('regulatory_requirements', {}).get('special_studies_required', False)
        }
    
    def _process_cadastral_data(self, cadastral_data: Dict) -> Dict[str, Any]:
        """Process cadastral/property data"""
        property_info = cadastral_data.get('property_info', {})
        return {
            'cadastral_number': property_info.get('cadastral_number'),
            'area_acres': property_info.get('area_acres'),
            'land_use_classification': property_info.get('land_use'),
            'zoning_designation': property_info.get('zoning'),
            'municipality': property_info.get('municipality'),
            'barrio': property_info.get('barrio')
        }
    
    def _calculate_risk_assessment(self, flood, wetland, habitat, air, karst) -> Dict[str, str]:
        """Calculate overall risk level"""
        risk_factors = []
        
        # Check each domain for risks
        if flood.get('primary_flood_zone') and flood['primary_flood_zone'] not in ['X', 'ZONE X']:
            risk_factors.append('flood')
        if wetland.get('directly_on_property'):
            risk_factors.append('wetland')
        if habitat.get('within_designated_habitat'):
            risk_factors.append('habitat')
        if air.get('nonattainment_status'):
            risk_factors.append('air')
        if karst.get('regulatory_impact_level') == 'high':
            risk_factors.append('karst')
        
        # Determine risk level
        if len(risk_factors) >= 3:
            return {'level': 'HIGH RISK', 'class': 'risk-high'}
        elif len(risk_factors) >= 1:
            return {'level': 'MODERATE RISK', 'class': 'risk-moderate'}
        else:
            return {'level': 'LOW RISK', 'class': 'risk-low'}
    
    def _get_flood_status(self, flood_data: Dict) -> str:
        """Get flood zone status"""
        zone = flood_data.get('primary_flood_zone', 'Unknown')
        if zone in ['X', 'ZONE X']:
            return 'Compliant'
        elif zone in ['AE', 'A', 'VE', 'V']:
            return 'Review Required'
        else:
            return 'Unknown'
    
    def _get_wetland_status(self, wetland_data: Dict) -> str:
        """Get wetland status"""
        if wetland_data.get('directly_on_property'):
            return 'Critical Review'
        elif wetland_data.get('wetlands_found_count', 0) > 0:
            return 'Review Required'
        else:
            return 'Compliant'
    
    def _get_habitat_status(self, habitat_data: Dict) -> str:
        """Get habitat status"""
        if habitat_data.get('within_designated_habitat'):
            return 'Critical Review'
        elif habitat_data.get('consultation_required'):
            return 'Review Required'
        else:
            return 'Compliant'
    
    def _get_air_status(self, air_data: Dict) -> str:
        """Get air quality status"""
        if air_data.get('nonattainment_status'):
            return 'Review Required'
        else:
            return 'Compliant'
    
    def _get_karst_status(self, karst_data: Dict) -> str:
        """Get karst status"""
        impact_level = karst_data.get('regulatory_impact_level', 'None')
        if impact_level == 'high':
            return 'Critical Review'
        elif impact_level in ['moderate', 'medium']:
            return 'Review Required'
        else:
            return 'Compliant'
    
    def _get_zoning_status(self, cadastral_data: Dict) -> str:
        """Get zoning status"""
        return 'Compliant'  # Default - would need specific zoning rules
    
    def _get_status_class(self, data: Dict) -> str:
        """Get CSS class for status"""
        # This would map status to CSS classes
        return 'status-compliant'  # Default
    
    def _get_status_class_for_status(self, status: str) -> str:
        """Get CSS class based on status string"""
        status_lower = status.lower()
        if 'critical' in status_lower:
            return 'status-critical'
        elif 'review' in status_lower:
            return 'status-review'
        elif 'compliant' in status_lower:
            return 'status-compliant'
        else:
            return 'status-unknown'
    
    def _get_flood_action(self, flood_data: Dict) -> str:
        """Get recommended flood actions"""
        zone = flood_data.get('primary_flood_zone', 'Unknown')
        if zone in ['AE', 'A', 'VE', 'V']:
            return 'Flood insurance required. Elevation certificate recommended. Building restrictions apply.'
        else:
            return 'Standard construction practices apply.'
    
    def _get_wetland_action(self, wetland_data: Dict) -> str:
        """Get recommended wetland actions"""
        if wetland_data.get('directly_on_property'):
            return 'Jurisdictional determination required. USACE Section 404 permit likely needed.'
        elif wetland_data.get('wetlands_found_count', 0) > 0:
            return 'Wetland field verification recommended. Avoid impacts to wetland areas.'
        else:
            return 'No wetland restrictions identified.'
    
    def _get_habitat_action(self, habitat_data: Dict) -> str:
        """Get recommended habitat actions"""
        if habitat_data.get('within_designated_habitat'):
            return 'ESA Section 7 consultation required. Biological assessment needed.'
        elif habitat_data.get('consultation_required'):
            return 'Species surveys recommended. Coordinate with USFWS.'
        else:
            return 'No special habitat requirements identified.'
    
    def _get_air_action(self, air_data: Dict) -> str:
        """Get recommended air quality actions"""
        if air_data.get('nonattainment_status'):
            return 'Air quality conformity analysis required. Emission controls may apply.'
        else:
            return 'Standard air quality regulations apply.'
    
    def _get_karst_action(self, karst_data: Dict) -> str:
        """Get recommended karst actions"""
        impact_level = karst_data.get('regulatory_impact_level', 'None')
        if impact_level == 'high':
            return 'Detailed geological study required. Special foundation design needed.'
        elif impact_level in ['moderate', 'medium']:
            return 'Geological assessment recommended. Standard karst precautions apply.'
        else:
            return 'Standard construction practices apply.'
    
    def _get_zoning_action(self, cadastral_data: Dict) -> str:
        """Get recommended zoning actions"""
        return 'Verify local zoning compliance and obtain necessary permits.'
    
    def _generate_executive_summary(self, risk_info: Dict, flood, wetland, habitat, air, karst) -> Dict[str, Any]:
        """Generate executive summary"""
        constraints = []
        recommendations = []
        
        # Identify constraints
        if flood.get('primary_flood_zone') not in ['X', 'ZONE X', None]:
            constraints.append(f"FEMA Flood Zone {flood.get('primary_flood_zone', 'Unknown')}")
            recommendations.append("Obtain elevation certificate and comply with flood insurance requirements")
        
        if wetland.get('directly_on_property'):
            constraints.append("Direct wetland impacts identified")
            recommendations.append("Conduct jurisdictional determination and obtain USACE permits")
        
        if habitat.get('within_designated_habitat'):
            constraints.append("Critical habitat designation present")
            recommendations.append("Initiate ESA Section 7 consultation process")
        
        if air.get('nonattainment_status'):
            constraints.append("EPA nonattainment area")
            recommendations.append("Prepare air quality conformity analysis")
        
        if karst.get('regulatory_impact_level') == 'high':
            constraints.append("High-concern karst geology")
            recommendations.append("Conduct detailed geological investigation")
        
        # Default recommendations if no constraints
        if not recommendations:
            recommendations = [
                "Obtain necessary local permits and approvals",
                "Conduct field verification of environmental conditions",
                "Implement standard environmental protection measures"
            ]
        
        findings = f"Environmental screening identified {len(constraints)} primary constraint(s) requiring attention."
        if not constraints:
            findings = "Environmental screening found no major constraints for the proposed project location."
        
        return {
            'findings': findings,
            'constraints': constraints,
            'recommendations': recommendations
        }

    def generate_html(self, output_name: str = None) -> str:
        """Generate HTML using the professional template"""
        if not JINJA2_AVAILABLE:
            print("⚠️ Jinja2 not available - creating basic HTML")
            return self._create_basic_html(output_name)
        
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"environmental_report_{timestamp}.html"
        
        output_path = self.reports_dir / output_name
        
        try:
            # Find maps
            maps = self.find_maps()
            
            # Process data for template
            template_data = self._process_data_for_template(maps)
            
            # Load template
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create Jinja2 environment with custom filters
            env = Environment()
            
            # Add custom yesno filter (Django-style)
            def yesno_filter(value, arg="Yes,No"):
                """Convert boolean to Yes/No string like Django's yesno filter"""
                if isinstance(value, bool):
                    options = arg.split(',')
                    return options[0] if value else options[1] if len(options) > 1 else options[0]
                elif value is None:
                    options = arg.split(',')
                    return options[2] if len(options) > 2 else "Unknown"
                else:
                    # Try to convert to boolean
                    try:
                        bool_val = bool(value)
                        options = arg.split(',')
                        return options[0] if bool_val else options[1] if len(options) > 1 else options[0]
                    except:
                        return str(value)
            
            env.filters['yesno'] = yesno_filter
            
            # Render with Jinja2
            template = env.from_string(template_content)
            rendered_html = template.render(**template_data)
            
            # Save rendered HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)
            
            print(f"✅ Professional HTML report generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"⚠️ Template rendering failed: {e}")
            print("   Falling back to basic HTML generation")
            return self._create_basic_html(output_name)
    
    def _create_basic_html(self, output_name: str = None) -> str:
        """Fallback basic HTML generation"""
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"basic_report_{timestamp}.html"
        
        output_path = self.reports_dir / output_name
        
        # Find maps
        maps = self.find_maps()
        
        # Simple HTML template
        html_content = self._create_html_template(maps)
        
        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Basic HTML saved: {output_path}")
        return str(output_path)
    
    def _create_html_template(self, maps: Dict[str, str]) -> str:
        """Create simple HTML with embedded maps (fallback)"""
        project_info = self.data.get('project_info', {})
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Environmental Screening Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f8ff; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .map {{ text-align: center; margin: 20px 0; }}
        .map img {{ max-width: 100%; height: auto; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Environmental Screening Report</h1>
        <p><strong>Project:</strong> {project_info.get('project_name', 'N/A')}</p>
        <p><strong>Location:</strong> {project_info.get('latitude', 'N/A')}, {project_info.get('longitude', 'N/A')}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
"""
        
        # Add maps
        for map_type, base64_data in maps.items():
            map_title = map_type.replace('_', ' ').title()
            html += f"""
    <div class="section">
        <h2>{map_title}</h2>
        <div class="map">
            <img src="{base64_data}" alt="{map_title}">
        </div>
    </div>
"""
        
        # Add basic data
        if 'query_results' in self.data:
            html += '<div class="section"><h2>Analysis Results</h2>'
            for analysis_type, results in self.data['query_results'].items():
                html += f'<h3>{analysis_type.replace("_", " ").title()}</h3>'
                html += f'<p>Status: {results.get("success", "Unknown")}</p>'
            html += '</div>'
        
        html += """
</body>
</html>
"""
        return html
    
    def generate_pdf(self, output_name: str = None) -> str:
        """Generate PDF from HTML"""
        # First generate HTML
        html_path = self.generate_html()
        
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"environmental_report_{timestamp}.pdf"
        
        pdf_path = self.reports_dir / output_name
        
        if WEASYPRINT_AVAILABLE:
            try:
                weasyprint.HTML(filename=html_path).write_pdf(str(pdf_path))
                print(f"✅ Professional PDF report generated: {pdf_path}")
                return str(pdf_path)
            except Exception as e:
                print(f"⚠️ PDF generation failed: {e}")
        
        print("⚠️ WeasyPrint not available - HTML only")
        return html_path

# Global configuration for all tools
def configure_global_directories(base_project_dir: str):
    """Configure directory structure for all environmental tools"""
    base_path = Path(base_project_dir).resolve()
    
    # Set environment variables that other tools can use
    os.environ['ENV_PROJECT_DIR'] = str(base_path)
    os.environ['ENV_MAPS_DIR'] = str(base_path / "maps")
    os.environ['ENV_DATA_DIR'] = str(base_path / "data")
    os.environ['ENV_REPORTS_DIR'] = str(base_path / "reports")
    
    print(f"🌍 Global directories configured:")
    print(f"   Project: {base_path}")
    print(f"   Maps: {base_path / 'maps'}")
    print(f"   Data: {base_path / 'data'}")
    print(f"   Reports: {base_path / 'reports'}")

def create_project_structure(project_name: str, base_dir: str = "environmental_projects") -> str:
    """Create standardized project directory structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = Path(base_dir) / f"{project_name}_{timestamp}"
    
    # Create structure
    subdirs = ["data", "maps", "reports", "logs"]
    for subdir in subdirs:
        (project_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Configure global directories
    configure_global_directories(str(project_dir))
    
    print(f"📁 Project structure created: {project_dir}")
    return str(project_dir)

def main():
    """Test the simplified generator"""
    # Create test project
    project_dir = create_project_structure("Test_Simple")
    
    # Create test data
    test_data = {
        'project_info': {
            'project_name': 'Test Environmental Assessment',
            'latitude': 18.4058,
            'longitude': -66.7135
        },
        'query_results': {
            'flood_analysis': {'success': True},
            'wetland_analysis': {'success': True},
            'habitat_analysis': {'success': True}
        }
    }
    
    # Save test data
    data_file = Path(project_dir) / "data" / "test_data.json"
    with open(data_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Generate reports
    generator = SimplifiedHTMLPDFGenerator(
        json_report_path=str(data_file),
        project_directory=project_dir
    )
    
    html_report = generator.generate_html()
    pdf_report = generator.generate_pdf()
    
    print(f"\n✅ Test completed:")
    print(f"   HTML: {html_report}")
    print(f"   PDF: {pdf_report}")

if __name__ == "__main__":
    main() 