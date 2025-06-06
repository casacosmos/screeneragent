#!/usr/bin/env python3
"""
Test script to verify data normalization in HTML PDF generator
"""

from html_pdf_generator import HTMLEnvironmentalPDFGenerator
import json

def test_normalization():
    # Load and normalize the data
    generator = HTMLEnvironmentalPDFGenerator(
        'schema_test/Schema_Test_Project_20250529_023509/data/comprehensive_query_results.json', 
        'schema_test/Schema_Test_Project_20250529_023509'
    )

    # Save normalized data for inspection
    with open('normalized_data_schema_test_20250529_023509.json', 'w') as f:
        json.dump(generator.report_data, f, indent=2, default=str)

    print('📄 Normalized data saved to: normalized_data_schema_test_20250529_023509.json')
    
    # Check key sections exist
    sections = ['project_info', 'cadastral_analysis', 'wetland_analysis', 'critical_habitat_analysis', 
                'air_quality_analysis', 'karst_analysis', 'executive_summary', 'cumulative_risk_assessment']
    
    print('\n🔍 Checking normalized structure:')
    for section in sections:
        if section in generator.report_data:
            print(f'  ✅ {section}: Present')
        else:
            print(f'  ❌ {section}: Missing')
    
    # Check specific fields
    print('\n📊 Field verification:')
    project_info = generator.report_data.get('project_info', {})
    print(f'  - location_name: {project_info.get("location_name", "MISSING")}')
    print(f'  - analysis_date_time: {project_info.get("analysis_date_time", "MISSING")}')
    
    cadastral = generator.report_data.get('cadastral_analysis', {})
    print(f'  - municipality: {cadastral.get("municipality", "MISSING")}')
    print(f'  - area_acres: {cadastral.get("area_acres", "MISSING")}')
    
    wetland = generator.report_data.get('wetland_analysis', {})
    print(f'  - directly_on_property: {wetland.get("directly_on_property", "MISSING")}')
    
    executive = generator.report_data.get('executive_summary', {})
    print(f'  - property_overview: {"Present" if executive.get("property_overview") else "MISSING"}')

if __name__ == '__main__':
    test_normalization() 