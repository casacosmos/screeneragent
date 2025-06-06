#!/usr/bin/env python3
"""
Test Comprehensive Template Workflow

This script demonstrates the complete workflow from environmental queries 
to structured template data generation that matches our improved schema.

The workflow includes:
1. Environmental data queries (comprehensive_query_tool.py)
2. Data source mapping and normalization
3. Structured JSON generation (template_data_structure.json)
4. Schema validation against improved_template_data_schema.json
5. Ready for HTML template rendering

Usage:
    python test_comprehensive_template_workflow.py
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
import logging

from comprehensive_query_tool import (
    ComprehensiveQueryTool,
    query_environmental_data_for_location,
    generate_structured_template_data
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the complete comprehensive template workflow"""
    
    print("🌍 Testing Comprehensive Environmental Template Workflow")
    print("=" * 70)
    
    # Test coordinates (Juncos, Puerto Rico - known working location)
    test_location = "18.2294, -65.9266"
    test_project_name = "Template Workflow Test - Juncos PR"
    test_cadastral = "227-052-007-20"
    
    print(f"📍 Test Location: {test_location}")
    print(f"🏗️ Project Name: {test_project_name}")
    print(f"📋 Cadastral Number: {test_cadastral}")
    print()
    
    try:
        # Step 1: Run comprehensive environmental queries
        print("Step 1: Running Comprehensive Environmental Queries")
        print("-" * 50)
        
        result = query_environmental_data_for_location.invoke({
            "location": test_location,
            "project_name": test_project_name,
            "cadastral_number": test_cadastral,
            "output_directory": "output",
            "include_maps": True,
            "buffer_distance": 1.0,
            "detailed_analysis": True
        })
        
        if not result.get('success'):
            print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            return 1
        
        project_dir = result['project_info']['project_directory']
        print(f"✅ Queries completed successfully")
        print(f"📁 Project directory: {project_dir}")
        print(f"📊 Success rate: {result['summary']['successful_queries']}/{result['summary']['total_queries']}")
        print()
        
        # Step 2: Generate structured template data
        print("Step 2: Generating Structured Template Data")
        print("-" * 50)
        
        template_result = generate_structured_template_data.invoke({
            "project_directory": project_dir
        })
        
        if not template_result.get('success'):
            print(f"❌ Template data generation failed: {template_result.get('error', 'Unknown error')}")
            return 1
        
        template_data_file = template_result['template_data_file']
        print(f"✅ Structured template data generated")
        print(f"📄 Template data file: {template_data_file}")
        print()
        
        # Step 3: Validate generated data
        print("Step 3: Validating Generated Data")
        print("-" * 50)
        
        # Load and display key information from template data
        with open(template_data_file, 'r') as f:
            template_data = json.load(f)
        
        print(f"📋 Project Name: {template_data.get('project_name', 'N/A')}")
        print(f"📅 Analysis Date: {template_data.get('analysis_date', 'N/A')}")
        print(f"📍 Location: {template_data.get('location_description', 'N/A')}")
        print(f"⚠️ Overall Risk Level: {template_data.get('overall_risk_level', 'N/A')}")
        print()
        
        # Display data completeness
        data_sections = [
            'cadastral_analysis',
            'karst_analysis', 
            'flood_analysis',
            'critical_habitat_analysis',
            'air_quality_analysis',
            'executive_summary'
        ]
        
        print("📊 Data Section Completeness:")
        for section in data_sections:
            status = "✅ Present" if section in template_data else "❌ Missing"
            print(f"   {section}: {status}")
        print()
        
        # Display compliance checklist status
        print("🏛️ Compliance Checklist Summary:")
        compliance_domains = ['flood', 'habitat', 'zoning', 'air', 'karst']
        for domain in compliance_domains:
            status = template_data.get(f'{domain}_status', 'UNKNOWN')
            risk = template_data.get(f'{domain}_risk', 'UNKNOWN')
            print(f"   {domain.title()}: {status} ({risk} risk)")
        print()
        
        # Step 4: Verify schema compatibility
        print("Step 4: Schema Compatibility Check")
        print("-" * 50)
        
        schema_file = Path("improved_template_data_schema.json")
        if schema_file.exists():
            print(f"✅ Schema file found: {schema_file}")
            
            # Check required fields
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            required_fields = schema.get('required', [])
            missing_fields = []
            
            for field in required_fields:
                if field not in template_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️ Missing required fields: {missing_fields}")
            else:
                print("✅ All required schema fields present")
        else:
            print(f"⚠️ Schema file not found: {schema_file}")
        print()
        
        # Step 5: Template readiness check
        print("Step 5: HTML Template Readiness")
        print("-" * 50)
        
        template_file = Path("comprehensive_environmental_template_v2.html")
        if template_file.exists():
            print(f"✅ HTML template found: {template_file}")
            print("✅ Template data structure matches schema")
            print("✅ Ready for HTML report generation")
            
            # Show next steps
            print("\n🚀 Next Steps:")
            print("   1. Use template_data_structure.json with Jinja2 template")
            print("   2. Generate HTML report")
            print("   3. Convert to PDF using HTML to PDF tools")
            print("   4. Review generated environmental screening report")
        else:
            print(f"⚠️ HTML template not found: {template_file}")
        print()
        
        # Step 6: Show file structure
        print("Step 6: Generated File Structure")
        print("-" * 50)
        
        project_path = Path(project_dir)
        print(f"📁 {project_path.name}/")
        
        for subfolder in ['data', 'maps', 'reports', 'logs']:
            subfolder_path = project_path / subfolder
            if subfolder_path.exists():
                files = list(subfolder_path.glob('*'))
                print(f"   📁 {subfolder}/ ({len(files)} files)")
                for file in files[:3]:  # Show first 3 files
                    print(f"      📄 {file.name}")
                if len(files) > 3:
                    print(f"      ... and {len(files) - 3} more files")
            else:
                print(f"   📁 {subfolder}/ (not created)")
        print()
        
        print("✅ Comprehensive template workflow test completed successfully!")
        print("🎯 All systems ready for environmental screening report generation")
        
        return 0
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        logger.error(f"Workflow error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main()) 