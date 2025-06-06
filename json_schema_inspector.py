#!/usr/bin/env python3
"""
JSON Schema Inspector for Environmental Screening Data

This tool inspects the JSON data structure produced by the comprehensive query tool
and verifies compatibility with the HTML PDF generator parsing expectations.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

def analyze_json_structure(json_path: str) -> Dict[str, Any]:
    """Analyze the JSON structure and field availability"""
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    analysis = {
        'file_path': json_path,
        'structure_valid': True,
        'missing_sections': [],
        'missing_fields': [],
        'data_quality_issues': [],
        'sections_analysis': {}
    }
    
    print('🔍 JSON DATA STRUCTURE ANALYSIS')
    print('=' * 60)
    
    # Check top-level structure
    print('Top-level keys:')
    for key in data.keys():
        print(f'  ✓ {key}: {type(data[key]).__name__}')
    
    # Expected sections for comprehensive environmental screening
    expected_sections = [
        'project_info',
        'flood_analysis', 
        'wetland_analysis',
        'critical_habitat_analysis',
        'air_quality_analysis',
        'karst_analysis',
        'cadastral_analysis',
        'executive_summary',
        'cumulative_risk_assessment'
    ]
    
    # Check for missing sections
    for section in expected_sections:
        if section not in data:
            analysis['missing_sections'].append(section)
            analysis['structure_valid'] = False
    
    # Analyze each section in detail
    
    # PROJECT_INFO Analysis
    print('\n📊 PROJECT_INFO Analysis:')
    project_info = data.get('project_info', {})
    analysis['sections_analysis']['project_info'] = {}
    
    if project_info:
        required_fields = ['project_name', 'latitude', 'longitude', 'location_name', 'analysis_date_time']
        for field in required_fields:
            value = project_info.get(field)
            print(f'  - {field}: {value if value is not None else "MISSING"}')
            if value is None:
                analysis['missing_fields'].append(f'project_info.{field}')
                analysis['sections_analysis']['project_info'][field] = 'MISSING'
            else:
                analysis['sections_analysis']['project_info'][field] = 'OK'
    else:
        print('  ❌ MISSING project_info section')
        analysis['missing_sections'].append('project_info')
    
    # FLOOD_ANALYSIS Analysis
    print('\n🌊 FLOOD_ANALYSIS Analysis:')
    flood_data = data.get('flood_analysis', {})
    analysis['sections_analysis']['flood_analysis'] = {}
    
    if flood_data:
        # Check for expected fields that HTML PDF generator looks for
        flood_fields = {
            'primary_flood_zone': flood_data.get('primary_flood_zone'),
            'fema_flood_zone': flood_data.get('fema_flood_zone'),  # Alternative field name
            'flood_zone': flood_data.get('flood_zone'),  # Alternative field name
            'flood_zones': flood_data.get('flood_zones', []),
            'base_flood_elevation': flood_data.get('base_flood_elevation'),
            'generated_files': flood_data.get('generated_files', []),
            'flood_reports_generated': flood_data.get('flood_reports_generated', {}),
            'firmette_map_path': flood_data.get('firmette_map_path'),
            'prefirm_map_path': flood_data.get('prefirm_map_path'),
            'abfe_map_path': flood_data.get('abfe_map_path')
        }
        
        for field, value in flood_fields.items():
            status = 'OK' if value is not None else 'MISSING'
            if field == 'flood_zones':
                status = f'OK ({len(value)} zones)' if value else 'EMPTY'
            elif field == 'generated_files':
                status = f'OK ({len(value)} files)' if value else 'EMPTY'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['flood_analysis'][field] = status
            
        # Specific check for flood zone detection
        flood_zone = (flood_data.get('fema_flood_zone') or 
                     flood_data.get('primary_flood_zone') or 
                     flood_data.get('flood_zone'))
        if flood_zone:
            print(f'  ✅ Flood zone identified: {flood_zone}')
        else:
            print('  ⚠️ No flood zone identified')
            analysis['data_quality_issues'].append('No flood zone identified in flood_analysis')
    else:
        print('  ❌ MISSING flood_analysis section')
        analysis['missing_sections'].append('flood_analysis')
    
    # WETLAND_ANALYSIS Analysis  
    print('\n🌿 WETLAND_ANALYSIS Analysis:')
    wetland_data = data.get('wetland_analysis', {})
    analysis['sections_analysis']['wetland_analysis'] = {}
    
    if wetland_data:
        wetland_fields = {
            'directly_on_property': wetland_data.get('directly_on_property'),
            'distance_to_nearest': wetland_data.get('distance_to_nearest'),
            'wetlands_at_location': wetland_data.get('wetlands_at_location', []),
            'nearby_wetlands': wetland_data.get('nearby_wetlands', []),
            'within_search_radius': wetland_data.get('within_search_radius'),
            'nwi_map_path': wetland_data.get('nwi_map_path'),
            'wetland_map_path': wetland_data.get('wetland_map_path')
        }
        
        for field, value in wetland_fields.items():
            if field in ['wetlands_at_location', 'nearby_wetlands']:
                status = f'OK ({len(value)} wetlands)' if value else 'EMPTY'
            else:
                status = 'OK' if value is not None else 'MISSING'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['wetland_analysis'][field] = status
    else:
        print('  ❌ MISSING wetland_analysis section')
        analysis['missing_sections'].append('wetland_analysis')
    
    # CRITICAL_HABITAT_ANALYSIS Analysis
    print('\n🦅 CRITICAL_HABITAT_ANALYSIS Analysis:')
    habitat_data = data.get('critical_habitat_analysis', {})
    analysis['sections_analysis']['critical_habitat_analysis'] = {}
    
    if habitat_data:
        habitat_fields = {
            'within_designated_habitat': habitat_data.get('within_designated_habitat'),
            'within_proposed_habitat': habitat_data.get('within_proposed_habitat'),
            'distance_to_nearest': habitat_data.get('distance_to_nearest'),
            'affected_species': habitat_data.get('affected_species', []),
            'critical_habitat_areas': habitat_data.get('critical_habitat_areas', []),
            'endangered_species': habitat_data.get('endangered_species', []),
            'critical_habitat_map_path': habitat_data.get('critical_habitat_map_path'),
            'habitat_map_path': habitat_data.get('habitat_map_path')
        }
        
        for field, value in habitat_fields.items():
            if field in ['affected_species', 'critical_habitat_areas', 'endangered_species']:
                status = f'OK ({len(value)} items)' if value else 'EMPTY'
            else:
                status = 'OK' if value is not None else 'MISSING'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['critical_habitat_analysis'][field] = status
    else:
        print('  ❌ MISSING critical_habitat_analysis section')
        analysis['missing_sections'].append('critical_habitat_analysis')
    
    # AIR_QUALITY_ANALYSIS Analysis
    print('\n🌫️ AIR_QUALITY_ANALYSIS Analysis:')
    air_data = data.get('air_quality_analysis', {})
    analysis['sections_analysis']['air_quality_analysis'] = {}
    
    if air_data:
        air_fields = {
            'nonattainment_status': air_data.get('nonattainment_status'),
            'area_classification': air_data.get('area_classification'),
            'affected_pollutants': air_data.get('affected_pollutants', []),
            'nonattainment_areas': air_data.get('nonattainment_areas', []),
            'monitoring_data': air_data.get('monitoring_data', []),
            'nonattainment_map_path': air_data.get('nonattainment_map_path'),
            'air_quality_map_path': air_data.get('air_quality_map_path')
        }
        
        for field, value in air_fields.items():
            if field in ['affected_pollutants', 'nonattainment_areas', 'monitoring_data']:
                status = f'OK ({len(value)} items)' if value else 'EMPTY'
            else:
                status = 'OK' if value is not None else 'MISSING'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['air_quality_analysis'][field] = status
    else:
        print('  ❌ MISSING air_quality_analysis section')
        analysis['missing_sections'].append('air_quality_analysis')
    
    # KARST_ANALYSIS Analysis
    print('\n🕳️ KARST_ANALYSIS Analysis:')
    karst_data = data.get('karst_analysis', {})
    analysis['sections_analysis']['karst_analysis'] = {}
    
    if karst_data:
        karst_fields = {
            'within_karst_area_general': karst_data.get('within_karst_area_general'),
            'karst_status_general': karst_data.get('karst_status_general'),
            'regulatory_impact_level': karst_data.get('regulatory_impact_level'),
            'karst_type_detailed': karst_data.get('karst_type_detailed'),
            'development_constraints': karst_data.get('development_constraints', []),
            'permit_requirements': karst_data.get('permit_requirements', []),
            'map_reference': karst_data.get('map_reference'),
            'karst_map_embed_path': karst_data.get('karst_map_embed_path')
        }
        
        for field, value in karst_fields.items():
            if field in ['development_constraints', 'permit_requirements']:
                status = f'OK ({len(value)} items)' if value else 'EMPTY'
            else:
                status = 'OK' if value is not None else 'MISSING'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['karst_analysis'][field] = status
    else:
        print('  ❌ MISSING karst_analysis section')
        analysis['missing_sections'].append('karst_analysis')
    
    # CADASTRAL_ANALYSIS Analysis
    print('\n🏠 CADASTRAL_ANALYSIS Analysis:')
    cadastral_data = data.get('cadastral_analysis', {})
    analysis['sections_analysis']['cadastral_analysis'] = {}
    
    if cadastral_data:
        cadastral_fields = {
            'municipality': cadastral_data.get('municipality'),
            'neighborhood': cadastral_data.get('neighborhood'),
            'land_use_classification': cadastral_data.get('land_use_classification'),
            'zoning_designation': cadastral_data.get('zoning_designation'),
            'area_acres': cadastral_data.get('area_acres'),
            'area_hectares': cadastral_data.get('area_hectares'),
            'cadastral_numbers': cadastral_data.get('cadastral_numbers', [])
        }
        
        for field, value in cadastral_fields.items():
            if field == 'cadastral_numbers':
                status = f'OK ({len(value)} numbers)' if value else 'EMPTY'
            else:
                status = 'OK' if value is not None else 'MISSING'
            print(f'  - {field}: {status}')
            analysis['sections_analysis']['cadastral_analysis'][field] = status
    else:
        print('  ❌ MISSING cadastral_analysis section')
        analysis['missing_sections'].append('cadastral_analysis')
    
    # Summary
    print('\n📋 COMPATIBILITY SUMMARY:')
    print('=' * 40)
    
    if analysis['structure_valid']:
        print('✅ JSON structure is valid for HTML PDF generator')
    else:
        print('❌ JSON structure has compatibility issues')
    
    if analysis['missing_sections']:
        print(f'❌ Missing sections: {", ".join(analysis["missing_sections"])}')
    
    if analysis['missing_fields']:
        print(f'⚠️ Missing fields: {len(analysis["missing_fields"])} fields')
        for field in analysis['missing_fields'][:5]:  # Show first 5
            print(f'   - {field}')
        if len(analysis['missing_fields']) > 5:
            print(f'   ... and {len(analysis["missing_fields"]) - 5} more')
    
    if analysis['data_quality_issues']:
        print(f'⚠️ Data quality issues: {len(analysis["data_quality_issues"])}')
        for issue in analysis['data_quality_issues']:
            print(f'   - {issue}')
    
    return analysis

def check_html_pdf_generator_compatibility(data: Dict[str, Any]) -> List[str]:
    """Check specific compatibility with HTML PDF generator parsing logic"""
    
    compatibility_issues = []
    
    # Check flood zone parsing logic
    flood_data = data.get('flood_analysis', {})
    if flood_data:
        flood_zone = (flood_data.get('fema_flood_zone') or 
                     flood_data.get('primary_flood_zone') or 
                     flood_data.get('flood_zone'))
        if not flood_zone:
            compatibility_issues.append('Flood zone not detectable by HTML PDF generator parsing logic')
    
    # Check wetland parsing logic
    wetland_data = data.get('wetland_analysis', {})
    if wetland_data:
        if 'directly_on_property' not in wetland_data:
            compatibility_issues.append('wetland_analysis missing directly_on_property field')
        if 'distance_to_nearest' not in wetland_data:
            compatibility_issues.append('wetland_analysis missing distance_to_nearest field')
    
    # Check habitat parsing logic
    habitat_data = data.get('critical_habitat_analysis', {})
    if habitat_data:
        if 'within_designated_habitat' not in habitat_data:
            compatibility_issues.append('critical_habitat_analysis missing within_designated_habitat field')
        if 'within_proposed_habitat' not in habitat_data:
            compatibility_issues.append('critical_habitat_analysis missing within_proposed_habitat field')
    
    # Check air quality parsing logic
    air_data = data.get('air_quality_analysis', {})
    if air_data:
        if 'nonattainment_status' not in air_data:
            compatibility_issues.append('air_quality_analysis missing nonattainment_status field')
    
    # Check karst parsing logic
    karst_data = data.get('karst_analysis', {})
    if karst_data:
        if 'regulatory_impact_level' not in karst_data:
            compatibility_issues.append('karst_analysis missing regulatory_impact_level field')
    
    return compatibility_issues

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Inspect JSON schema compatibility')
    parser.add_argument('json_file', help='Path to JSON file to inspect')
    parser.add_argument('--output', help='Output analysis to file')
    
    args = parser.parse_args()
    
    if not Path(args.json_file).exists():
        print(f'❌ JSON file not found: {args.json_file}')
        return 1
    
    try:
        # Perform structure analysis
        analysis = analyze_json_structure(args.json_file)
        
        # Load data for compatibility check
        with open(args.json_file, 'r') as f:
            data = json.load(f)
        
        # Check HTML PDF generator compatibility
        print('\n🔧 HTML PDF GENERATOR COMPATIBILITY:')
        print('=' * 45)
        
        compatibility_issues = check_html_pdf_generator_compatibility(data)
        
        if not compatibility_issues:
            print('✅ Fully compatible with HTML PDF generator parsing logic')
        else:
            print(f'❌ {len(compatibility_issues)} compatibility issues found:')
            for issue in compatibility_issues:
                print(f'   - {issue}')
        
        # Output to file if requested
        if args.output:
            analysis['compatibility_issues'] = compatibility_issues
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f'\n📄 Analysis saved to: {args.output}')
        
        return 0 if analysis['structure_valid'] and not compatibility_issues else 1
        
    except Exception as e:
        print(f'❌ Error analyzing JSON file: {e}')
        return 1

if __name__ == '__main__':
    exit(main()) 