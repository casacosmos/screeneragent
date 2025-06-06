#!/usr/bin/env python3
"""
Environmental Report Generator

This script loads structured JSON data and generates HTML and PDF environmental 
screening reports using the comprehensive environmental template.

Features:
- Load template data from JSON files
- Generate HTML reports using Jinja2 templating
- Convert HTML to PDF using multiple methods
- Validate data against schema
- Professional report formatting
- Error handling and logging

Usage:
    python generate_environmental_report.py --json template_data_structure.json
    python generate_environmental_report.py --json data.json --output-dir reports/
    python generate_environmental_report.py --json data.json --pdf-method weasyprint
"""

import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Template and PDF generation imports
try:
    from jinja2 import Template, Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("❌ Jinja2 not available. Install with: pip install jinja2")

# PDF generation options
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvironmentalReportGenerator:
    """Generate HTML and PDF environmental screening reports from JSON data"""
    
    def __init__(self, template_file: str = "comprehensive_environmental_template_v2.html",
                 schema_file: str = "improved_template_data_schema.json"):
        """
        Initialize the report generator
        
        Args:
            template_file: Path to HTML template file
            schema_file: Path to JSON schema file for validation
        """
        self.template_file = Path(template_file)
        self.schema_file = Path(schema_file)
        
        # Check if template exists
        if not self.template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        # Configure Jinja2 environment
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required for template rendering")
            
        template_dir = self.template_file.parent # Directory containing the template
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # Add custom filters
        self.jinja_env.filters['yesno'] = self._yesno_filter
        
        # Load template
        self.template = self._load_template()
        
        # Load schema for validation (optional)
        self.schema = self._load_schema()
        
        logger.info(f"📄 Template loaded: {self.template_file}")
        if self.schema:
            logger.info(f"📋 Schema loaded: {self.schema_file}")
    
    @staticmethod
    def _yesno_filter(value):
        """Jinja filter: Convert boolean to Yes/No"""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)
    
    def _load_template(self) -> Template:
        """Load Jinja2 template using the configured environment"""
        
        # Get template by name from the environment
        template = self.jinja_env.get_template(self.template_file.name)
        return template
    
    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load JSON schema for validation"""
        if not self.schema_file.exists():
            logger.warning(f"Schema file not found: {self.schema_file}")
            return None
        
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            return schema
        except Exception as e:
            logger.warning(f"Could not load schema: {e}")
            return None
    
    def load_template_data(self, json_file: str) -> Dict[str, Any]:
        """
        Load template data from JSON file
        
        Args:
            json_file: Path to JSON data file
            
        Returns:
            Dictionary containing template data
        """
        json_path = Path(json_file)
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON data file not found: {json_file}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"📊 Template data loaded: {json_path}")
            logger.info(f"   Project: {data.get('project_name', 'Unknown')}")
            logger.info(f"   Location: {data.get('location_description', 'Unknown')}")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {json_file}: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading JSON data: {e}")
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate template data against schema
        
        Args:
            data: Template data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not self.schema:
            logger.info("⚠️ No schema available for validation")
            return True
        
        # Basic validation - check required fields
        required_fields = self.schema.get('required', [])
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            logger.error(f"❌ Missing required fields: {missing_fields}")
            return False
        
        logger.info("✅ Data validation passed")
        return True
    
    def generate_html(self, data: Dict[str, Any]) -> str:
        """
        Generate HTML report from template data
        
        Args:
            data: Template data dictionary
            
        Returns:
            Generated HTML content
        """
        try:
            # Prepare data for rendering
            template_data = data.copy()
            
            # Render the template using the class template object
            html_content = self.template.render(**template_data)
            
            logger.info("✅ HTML report generated successfully")
            return html_content
            
        except Exception as e:
            raise RuntimeError(f"Error generating HTML: {e}")
    
    def save_html(self, html_content: str, output_file: str) -> str:
        """
        Save HTML content to file
        
        Args:
            html_content: Generated HTML content
            output_file: Output file path
            
        Returns:
            Path to saved HTML file
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"💾 HTML report saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Error saving HTML file: {e}")
    
    def generate_pdf_weasyprint(self, html_content: str, output_file: str) -> str:
        """
        Generate PDF using WeasyPrint
        
        Args:
            html_content: HTML content to convert
            output_file: Output PDF file path
            
        Returns:
            Path to generated PDF file
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint not available. Install with: pip install weasyprint")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Create HTML document
            html_doc = weasyprint.HTML(string=html_content)
            
            # Generate PDF with custom settings
            html_doc.write_pdf(
                str(output_path),
                stylesheets=[],
                optimize_images=True
            )
            
            logger.info(f"📄 PDF generated (WeasyPrint): {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Error generating PDF with WeasyPrint: {e}")
    
    def generate_pdf_pdfkit(self, html_content: str, output_file: str) -> str:
        """
        Generate PDF using pdfkit/wkhtmltopdf
        
        Args:
            html_content: HTML content to convert
            output_file: Output PDF file path
            
        Returns:
            Path to generated PDF file
        """
        if not PDFKIT_AVAILABLE:
            raise ImportError("pdfkit not available. Install with: pip install pdfkit")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Configure PDF options
            options = {
                'page-size': 'Letter',
                'margin-top': '0.5in',
                'margin-right': '0.5in',
                'margin-bottom': '0.5in',
                'margin-left': '0.5in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generate PDF
            pdfkit.from_string(html_content, str(output_path), options=options)
            
            logger.info(f"📄 PDF generated (pdfkit): {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Error generating PDF with pdfkit: {e}")
    
    def generate_pdf_playwright(self, html_content: str, output_file: str) -> str:
        """
        Generate PDF using Playwright (browser-based)
        
        Args:
            html_content: HTML content to convert
            output_file: Output PDF file path
            
        Returns:
            Path to generated PDF file
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available. Install with: pip install playwright")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch()
                page = browser.new_page()
                
                # Load HTML content
                page.set_content(html_content)
                
                # Wait for content to load
                page.wait_for_load_state('networkidle')
                
                # Generate PDF
                page.pdf(
                    path=str(output_path),
                    format='Letter',
                    margin={
                        'top': '0.5in',
                        'right': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.5in'
                    },
                    print_background=True
                )
                
                browser.close()
            
            logger.info(f"📄 PDF generated (Playwright): {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Error generating PDF with Playwright: {e}")
    
    def generate_pdf(self, html_content: str, output_file: str, 
                    method: str = "auto") -> str:
        """
        Generate PDF using specified method
        
        Args:
            html_content: HTML content to convert
            output_file: Output PDF file path
            method: PDF generation method ('weasyprint', 'pdfkit', 'playwright', 'auto')
            
        Returns:
            Path to generated PDF file
        """
        # Auto-select method based on availability
        if method == "auto":
            if WEASYPRINT_AVAILABLE:
                method = "weasyprint"
            elif PDFKIT_AVAILABLE:
                method = "pdfkit"
            elif PLAYWRIGHT_AVAILABLE:
                method = "playwright"
            else:
                raise RuntimeError("No PDF generation libraries available")
        
        # Generate PDF using selected method
        if method == "weasyprint":
            return self.generate_pdf_weasyprint(html_content, output_file)
        elif method == "pdfkit":
            return self.generate_pdf_pdfkit(html_content, output_file)
        elif method == "playwright":
            return self.generate_pdf_playwright(html_content, output_file)
        else:
            raise ValueError(f"Unknown PDF generation method: {method}")
    
    def generate_report(self, json_file: str, output_dir: str = "reports",
                       pdf_method: str = "auto", 
                       generate_html: bool = True,
                       generate_pdf: bool = True) -> Dict[str, str]:
        """
        Generate complete environmental report from JSON data
        
        Args:
            json_file: Path to JSON template data file
            output_dir: Output directory for generated files
            pdf_method: PDF generation method
            generate_html: Whether to generate HTML file
            generate_pdf: Whether to generate PDF file
            
        Returns:
            Dictionary with paths to generated files
        """
        # Load and validate data
        data = self.load_template_data(json_file)
        
        if not self.validate_data(data):
            raise ValueError("Template data validation failed")
        
        # Generate HTML
        html_content = self.generate_html(data)
        
        # Prepare output filenames
        project_name = data.get('project_name', 'Environmental_Report')
        # Clean project name for filename
        clean_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{clean_name}_{timestamp}"
        
        output_path = Path(output_dir)
        html_file = output_path / f"{base_filename}.html"
        pdf_file = output_path / f"{base_filename}.pdf"
        
        results = {}
        
        # Save HTML file
        if generate_html:
            html_path = self.save_html(html_content, str(html_file))
            results['html_file'] = html_path
        
        # Generate PDF file
        if generate_pdf:
            pdf_path = self.generate_pdf(html_content, str(pdf_file), method=pdf_method)
            results['pdf_file'] = pdf_path
        
        # Add metadata
        results.update({
            'project_name': data.get('project_name'),
            'location': data.get('location_description'),
            'analysis_date': data.get('analysis_date'),
            'generation_timestamp': datetime.now().isoformat(),
            'pdf_method': pdf_method if generate_pdf else None
        })
        
        return results


def main():
    """Main function for command-line usage"""
    
    parser = argparse.ArgumentParser(
        description='Environmental Report Generator - Convert JSON data to HTML and PDF reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate both HTML and PDF from JSON data
  python generate_environmental_report.py --json template_data_structure.json

  # Specify output directory
  python generate_environmental_report.py --json data.json --output-dir reports/

  # Use specific PDF generation method
  python generate_environmental_report.py --json data.json --pdf-method weasyprint

  # Generate only HTML
  python generate_environmental_report.py --json data.json --no-pdf

  # Generate only PDF
  python generate_environmental_report.py --json data.json --no-html

Available PDF Methods:
  - weasyprint: Best CSS support, good for complex layouts
  - pdfkit: Uses wkhtmltopdf, reliable and fast
  - playwright: Browser-based, excellent rendering
  - auto: Automatically select best available method
        """
    )
    
    parser.add_argument('--json', required=True, help='JSON template data file')
    parser.add_argument('--output-dir', default='reports', help='Output directory')
    parser.add_argument('--pdf-method', default='auto', 
                       choices=['auto', 'weasyprint', 'pdfkit', 'playwright'],
                       help='PDF generation method')
    parser.add_argument('--template', default='html_report_generator/comprehensive_environmental_template_v2.html',
                       help='HTML template file')
    parser.add_argument('--schema', default='html_report_generator/improved_template_data_schema.json',
                       help='JSON schema file for validation')
    parser.add_argument('--no-html', action='store_true', help='Skip HTML generation')
    parser.add_argument('--no-pdf', action='store_true', help='Skip PDF generation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("📄 Environmental Report Generator")
    print("=" * 50)
    
    try:
        # Initialize generator
        generator = EnvironmentalReportGenerator(
            template_file=args.template,
            schema_file=args.schema
        )
        
        # Check what will be generated
        generate_html = not args.no_html
        generate_pdf = not args.no_pdf
        
        if not generate_html and not generate_pdf:
            print("❌ Must generate at least HTML or PDF output")
            return 1
        
        # Show available PDF methods
        available_methods = []
        if WEASYPRINT_AVAILABLE:
            available_methods.append("weasyprint")
        if PDFKIT_AVAILABLE:
            available_methods.append("pdfkit")
        if PLAYWRIGHT_AVAILABLE:
            available_methods.append("playwright")
        
        print(f"🔧 Available PDF methods: {available_methods}")
        
        if generate_pdf and not available_methods:
            print("❌ No PDF generation libraries available")
            print("   Install with: pip install weasyprint")
            print("   Or: pip install pdfkit")
            print("   Or: pip install playwright")
            return 1
        
        # Generate report
        print(f"📊 Processing JSON data: {args.json}")
        print(f"📁 Output directory: {args.output_dir}")
        
        results = generator.generate_report(
            json_file=args.json,
            output_dir=args.output_dir,
            pdf_method=args.pdf_method,
            generate_html=generate_html,
            generate_pdf=generate_pdf
        )
        
        # Show results
        print("\n✅ Report generation completed successfully!")
        print(f"🏗️ Project: {results.get('project_name', 'Unknown')}")
        print(f"📍 Location: {results.get('location', 'Unknown')}")
        
        if 'html_file' in results:
            print(f"🌐 HTML Report: {results['html_file']}")
        
        if 'pdf_file' in results:
            print(f"📄 PDF Report: {results['pdf_file']}")
            print(f"🔧 PDF Method: {results.get('pdf_method', 'Unknown')}")
        
        print(f"⏰ Generated: {results.get('generation_timestamp', 'Unknown')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        logger.error(f"Report generation error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main()) 