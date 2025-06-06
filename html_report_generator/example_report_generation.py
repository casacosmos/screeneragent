#!/usr/bin/env python3
"""
Example: Environmental Report Generation

This script demonstrates how to use the EnvironmentalReportGenerator to:
1. Load JSON template data
2. Generate HTML reports
3. Create PDF reports
4. Handle different PDF generation methods

Usage:
    python example_report_generation.py
"""

import json
from pathlib import Path
from generate_environmental_report import EnvironmentalReportGenerator

def create_sample_data():
    """Create sample template data for demonstration"""
    sample_data = {
        "project_name": "Sample Environmental Assessment",
        "analysis_date": "2025-01-29T15:30:00",
        "location_description": "Juncos, Puerto Rico - Public Land",
        "coordinates": "18.229400, -65.926600",
        "project_directory": "/sample/project/directory",
        "overall_risk_level": "Low",
        "risk_class": "risk-low",
        
        # Cadastral analysis
        "cadastral_analysis": {
            "success": True,
            "municipality": "Juncos",
            "neighborhood": "Pueblo",
            "total_area_hectares": 6.65,
            "total_area_m2": 66500.0,
            "classification_description": "Public Land",
            "status": "Active"
        },
        
        # Karst analysis
        "karst_analysis": {
            "processed_summary": {
                "karst_status": "no_karst",
                "distance_miles": 0.15,
                "message": "No karst constraints within 0.5 miles"
            },
            "regulatory_impact_level": "low"
        },
        
        # Flood analysis
        "flood_analysis": {
            "success": True,
            "current_effective_data": {
                "flood_zones": [
                    {"flood_zone": "X"}
                ]
            },
            "analysis_metadata": {
                "source": "FEMA",
                "last_updated": "2025-01-01"
            }
        },
        
        # Critical habitat analysis
        "critical_habitat_analysis": {
            "critical_habitat_analysis": {
                "distance_to_nearest_habitat_miles": 1.19,
                "nearest_habitat": {
                    "species_common_name": "Puerto Rican Coqui"
                }
            }
        },
        
        # Air quality analysis
        "air_quality_analysis": {
            "regulatory_assessment": {
                "compliance_status": "Compliant"
            }
        },
        
        # Executive summary
        "executive_summary": {
            "property_overview": "6.65-hectare public land in Juncos municipality with comprehensive environmental compliance achieved across all assessed domains.",
            "risk_assessment": "Low environmental risk with no critical constraints identified.",
            "key_environmental_constraints": [],
            "regulatory_highlights": [
                "Public land classification - coordinate with planning authorities",
                "Air quality compliant - meets all NAAQS standards"
            ],
            "primary_recommendations": [
                "Proceed with standard development permitting process",
                "Coordinate with Puerto Rico Planning Board for public land development permissions"
            ]
        },
        
        # Compliance checklist fields
        "flood_status": "COMPLIANT",
        "flood_status_class": "status-green",
        "flood_risk": "LOW", 
        "flood_risk_class": "status-green",
        "flood_action": "Standard compliance - Zone X minimal risk",
        
        "habitat_status": "REVIEW",
        "habitat_status_class": "status-yellow", 
        "habitat_risk": "MODERATE",
        "habitat_risk_class": "status-yellow",
        "habitat_action": "ESA consultation recommended - Puerto Rican Coqui habitat nearby",
        
        "zoning_status": "COMPLIANT",
        "zoning_status_class": "status-green",
        "zoning_risk": "LOW",
        "zoning_risk_class": "status-green", 
        "zoning_action": "Public land - coordinate with planning board",
        
        "air_status": "COMPLIANT",
        "air_status_class": "status-green",
        "air_risk": "LOW",
        "air_risk_class": "status-green",
        "air_action": "Meets all NAAQS - standard permits apply",
        
        "karst_status": "COMPLIANT", 
        "karst_status_class": "status-green",
        "karst_risk": "LOW",
        "karst_risk_class": "status-green",
        "karst_action": "No karst constraints - proceed with development"
    }
    
    return sample_data

def example_basic_usage():
    """Example 1: Basic HTML and PDF generation"""
    print("📄 Example 1: Basic Report Generation")
    print("-" * 40)
    
    try:
        # Create sample data
        sample_data = create_sample_data()
        
        # Save sample data to JSON file
        sample_json_file = "sample_template_data.json"
        with open(sample_json_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        print(f"✅ Sample data created: {sample_json_file}")
        
        # Initialize report generator
        generator = EnvironmentalReportGenerator(
            template_file="html_report_generator/comprehensive_environmental_template_v2.html",
            schema_file="html_report_generator/improved_template_data_schema.json"
        )
        
        # Generate report (both HTML and PDF)
        results = generator.generate_report(
            json_file=sample_json_file,
            output_dir="example_reports",
            pdf_method="auto"
        )
        
        print(f"✅ Report generated successfully!")
        print(f"📁 HTML Report: {results.get('html_file')}")
        print(f"📄 PDF Report: {results.get('pdf_file')}")
        print(f"🔧 PDF Method: {results.get('pdf_method')}")
        
    except Exception as e:
        print(f"❌ Error in basic example: {e}")

def example_html_only():
    """Example 2: Generate only HTML report"""
    print("\n🌐 Example 2: HTML-Only Generation")
    print("-" * 40)
    
    try:
        # Initialize generator
        generator = EnvironmentalReportGenerator(
            template_file="html_report_generator/comprehensive_environmental_template_v2.html",
            schema_file="html_report_generator/improved_template_data_schema.json"
        )
        
        # Generate only HTML
        results = generator.generate_report(
            json_file="sample_template_data.json",
            output_dir="example_reports",
            generate_html=True,
            generate_pdf=False
        )
        
        print(f"✅ HTML report generated: {results.get('html_file')}")
        
    except Exception as e:
        print(f"❌ Error in HTML-only example: {e}")

def example_custom_pdf_method():
    """Example 3: Use specific PDF generation method"""
    print("\n📄 Example 3: Custom PDF Method")
    print("-" * 40)
    
    # Check available methods
    from generate_environmental_report import (
        WEASYPRINT_AVAILABLE, PDFKIT_AVAILABLE, PLAYWRIGHT_AVAILABLE
    )
    
    available_methods = []
    if WEASYPRINT_AVAILABLE:
        available_methods.append("weasyprint")
    if PDFKIT_AVAILABLE:
        available_methods.append("pdfkit") 
    if PLAYWRIGHT_AVAILABLE:
        available_methods.append("playwright")
    
    print(f"Available PDF methods: {available_methods}")
    
    if not available_methods:
        print("❌ No PDF generation methods available")
        print("   Install with: pip install weasyprint")
        return
    
    try:
        # Use first available method
        pdf_method = available_methods[0]
        print(f"Using PDF method: {pdf_method}")
        
        generator = EnvironmentalReportGenerator(
            template_file="html_report_generator/comprehensive_environmental_template_v2.html",
            schema_file="html_report_generator/improved_template_data_schema.json"
        )
        
        results = generator.generate_report(
            json_file="sample_template_data.json",
            output_dir="example_reports",
            pdf_method=pdf_method,
            generate_html=False,  # PDF only
            generate_pdf=True
        )
        
        print(f"✅ PDF generated with {pdf_method}: {results.get('pdf_file')}")
        
    except Exception as e:
        print(f"❌ Error in custom PDF example: {e}")

def example_programmatic_usage():
    """Example 4: Programmatic usage without files"""
    print("\n🔧 Example 4: Programmatic Usage")
    print("-" * 40)
    
    try:
        # Create sample data
        sample_data = create_sample_data()
        
        # Initialize generator
        generator = EnvironmentalReportGenerator(
            template_file="html_report_generator/comprehensive_environmental_template_v2.html",
            schema_file="html_report_generator/improved_template_data_schema.json"
        )
        
        # Validate data
        if not generator.validate_data(sample_data):
            print("❌ Data validation failed")
            return
        
        # Generate HTML content
        html_content = generator.generate_html(sample_data)
        
        # Save HTML
        html_file = generator.save_html(html_content, "example_reports/programmatic_report.html")
        print(f"✅ HTML saved: {html_file}")
        
        # Generate PDF if possible
        from generate_environmental_report import WEASYPRINT_AVAILABLE
        if WEASYPRINT_AVAILABLE:
            pdf_file = generator.generate_pdf(
                html_content, 
                "example_reports/programmatic_report.pdf",
                method="weasyprint"
            )
            print(f"✅ PDF saved: {pdf_file}")
        else:
            print("⚠️ WeasyPrint not available - skipping PDF generation")
        
    except Exception as e:
        print(f"❌ Error in programmatic example: {e}")

def example_with_existing_data():
    """Example 5: Use existing template data from comprehensive query"""
    print("\n📊 Example 5: Using Existing Query Data")
    print("-" * 40)
    
    # Look for existing template data files
    existing_files = list(Path(".").glob("**/template_data_structure.json"))
    
    if existing_files:
        print(f"Found existing template data files:")
        for i, file in enumerate(existing_files[:3]):  # Show first 3
            print(f"   {i+1}. {file}")
        
        try:
            # Use the first found file
            data_file = existing_files[0]
            print(f"Using: {data_file}")
            
            generator = EnvironmentalReportGenerator(
                template_file="html_report_generator/comprehensive_environmental_template_v2.html",
                schema_file="html_report_generator/improved_template_data_schema.json"
            )
            
            results = generator.generate_report(
                json_file=str(data_file),
                output_dir="example_reports",
                pdf_method="auto"
            )
            
            print(f"✅ Report generated from existing data!")
            print(f"📁 HTML: {results.get('html_file')}")
            print(f"📄 PDF: {results.get('pdf_file')}")
            
        except Exception as e:
            print(f"❌ Error using existing data: {e}")
    else:
        print("⚠️ No existing template_data_structure.json files found")
        print("   Run comprehensive_query_tool.py first to generate data")

def main():
    """Run all examples"""
    print("🌍 Environmental Report Generator Examples")
    print("=" * 60)
    
    # Create output directory
    Path("example_reports").mkdir(exist_ok=True)
    
    # Run examples
    example_basic_usage()
    example_html_only()
    example_custom_pdf_method()
    example_programmatic_usage()
    example_with_existing_data()
    
    print("\n🎯 Examples completed!")
    print("📁 Check the 'example_reports' directory for generated files")
    print("\n💡 Usage Tips:")
    print("   - Use WeasyPrint for best CSS support")
    print("   - Use pdfkit for fast, reliable PDF generation")
    print("   - Use Playwright for browser-quality rendering")
    print("   - Always validate your JSON data against the schema")

if __name__ == "__main__":
    main() 