#!/usr/bin/env python3
"""
Test script for the Comprehensive Environmental Agent

This script demonstrates the complete workflow:
1. Comprehensive Query Tool (data collection)
2. Comprehensive Screening Report Tool (analysis)
3. HTML PDF Generator (professional PDF)
"""

import asyncio
import json
from pathlib import Path
from comprehensive_environmental_agent import ComprehensiveEnvironmentalAgent

async def test_workflow():
    """Test the complete environmental screening workflow"""
    
    print("🧪 Testing Comprehensive Environmental Agent Workflow")
    print("=" * 60)
    
    # Initialize the agent
    agent = ComprehensiveEnvironmentalAgent(
        output_directory="test_workflow_output",
        include_maps=True,
        prefer_png_maps=True,
        buffer_distance=1.0
    )
    
    # Test with the same coordinates from our schema test
    test_location = "18.4058, -66.7135"
    project_name = "Workflow_Test_Project"
    
    print(f"📍 Testing location: {test_location}")
    print(f"🏗️ Project name: {project_name}")
    print(f"🔧 Agent session: {agent.session_id}")
    
    # Run the complete workflow
    result = await agent.process_location(
        location=test_location,
        project_name=project_name,
        cadastral_number=None
    )
    
    # Display results
    print("\n📊 Workflow Results:")
    print(f"   Overall Success: {'✅ YES' if result['success'] else '❌ NO'}")
    print(f"   Steps Completed: {result['workflow_info']['successful_steps']}/3")
    print(f"   Duration: {result['workflow_info']['duration_seconds']:.1f} seconds")
    print(f"   Files Generated: {len(result['generated_files'])}")
    print(f"   Errors: {len(result['errors'])}")
    
    # Show step details
    print("\n🔍 Step Details:")
    
    # Step 1: Query Results
    if result['step1_query_results']:
        query_info = result['step1_query_results']['summary']
        print(f"   Step 1 - Query Tool: ✅ {query_info['successful_queries']}/{query_info['total_queries']} queries successful")
        project_dir = result['step1_query_results']['project_info']['project_directory']
        print(f"     Project Directory: {project_dir}")
    else:
        print(f"   Step 1 - Query Tool: ❌ Failed")
    
    # Step 2: Screening Report
    if result.get('step2_screening_report', {}).get('success'):
        print(f"   Step 2 - Screening Report: ✅ Generated successfully")
        report_file = result['step2_screening_report'].get('report_file', 'N/A')
        print(f"     Report File: {report_file}")
    else:
        error = result.get('step2_screening_report', {}).get('error', 'Unknown error')
        print(f"   Step 2 - Screening Report: ❌ Failed - {error}")
    
    # Step 3: PDF Report
    if result.get('step3_pdf_report', {}).get('success'):
        pdf_info = result['step3_pdf_report']
        print(f"   Step 3 - PDF Report: ✅ Generated successfully")
        print(f"     PDF File: {pdf_info['pdf_file']}")
        print(f"     File Size: {pdf_info['file_size_mb']} MB")
        print(f"     Source JSON: {pdf_info['json_source']}")
    else:
        print(f"   Step 3 - PDF Report: ❌ Failed")
    
    # Show all generated files
    if result['generated_files']:
        print("\n📄 Generated Files:")
        for i, file_path in enumerate(result['generated_files'], 1):
            file_size = ""
            if Path(file_path).exists():
                size_mb = Path(file_path).stat().st_size / (1024*1024)
                file_size = f" ({size_mb:.2f} MB)"
            print(f"   {i:2d}. {file_path}{file_size}")
    
    # Show workflow log
    print("\n📝 Workflow Log:")
    for log_entry in agent.workflow_log:
        status_icon = "✅" if log_entry['status'] == "SUCCESS" else "❌" if log_entry['status'] == "ERROR" else "🔄"
        duration = f" ({log_entry.get('duration_seconds', 0):.1f}s)" if 'duration_seconds' in log_entry else ""
        print(f"   {status_icon} {log_entry['step']}: {log_entry['status']}{duration}")
        if log_entry['details']:
            print(f"      {log_entry['details']}")
    
    # Show errors if any
    if result['errors']:
        print("\n❌ Errors Encountered:")
        for error in result['errors']:
            print(f"   Step {error.get('step', 'Unknown')}: {error.get('error', 'Unknown error')}")
    
    return result

async def test_with_existing_data():
    """Test HTML PDF generator with existing schema test data"""
    
    print("\n🧪 Testing with Existing Schema Test Data")
    print("=" * 60)
    
    # Use existing schema test data
    existing_json = "schema_test/Schema_Test_Project_20250529_023509/data/comprehensive_query_results.json"
    existing_project_dir = "schema_test/Schema_Test_Project_20250529_023509"
    
    if not Path(existing_json).exists():
        print(f"❌ Existing test data not found: {existing_json}")
        return None
    
    print(f"📄 Using existing JSON: {existing_json}")
    print(f"📁 Project directory: {existing_project_dir}")
    
    try:
        # Test the comprehensive screening report tool directly
        print("\n🔄 Step 2: Testing Comprehensive Screening Report Tool...")
        from comprehensive_screening_report_tool import generate_comprehensive_screening_report
        
        # Use the LangChain tool invoke method with proper parameters
        screening_result = generate_comprehensive_screening_report.invoke({
            'output_directory': existing_project_dir,
            'output_format': 'both',
            'include_pdf': True,
            'use_professional_html_pdf': True,
            'prefer_png_maps': True
        })
        
        if screening_result and screening_result.get('success'):
            print(f"   ✅ Screening report generated successfully")
            print(f"   📄 PDF Generated: {'Yes' if screening_result.get('pdf_generated') else 'No'}")
            if screening_result.get('output_files'):
                print(f"   📋 Files generated: {len(screening_result['output_files'])}")
                for file_path in screening_result['output_files']:
                    print(f"      • {file_path}")
            
            # Use the first available file for PDF generation (prefer JSON)
            json_files = [f for f in screening_result['output_files'] if f.endswith('.json')]
            if json_files:
                json_source = json_files[0]
            else:
                json_source = existing_json
        else:
            print(f"   ❌ Screening report failed: {screening_result.get('error', 'Unknown error')}")
            json_source = existing_json
        
        # Test the HTML PDF generator with improved map generation
        print("\n🔄 Step 3: Testing Enhanced HTML PDF Generator...")
        from html_pdf_generator import HTMLEnvironmentalPDFGenerator
        
        pdf_generator = HTMLEnvironmentalPDFGenerator(
            json_report_path=json_source,
            project_directory=existing_project_dir,
            prefer_png_maps=True
        )
        
        # Test individual map generation capabilities
        print("\n🗺️ Testing Enhanced Map Generation Capabilities:")
        
        # Test if the data normalization works
        print("   🔧 Testing data structure normalization...")
        normalized_data = pdf_generator._normalize_data_structure(pdf_generator.report_data)
        print(f"   ✅ Data normalization: {'Success' if normalized_data else 'Failed'}")
        
        # Test map generation for each domain
        map_domains = [
            ('flood_analysis', 'Flood/FEMA maps'),
            ('wetland_analysis', 'Wetland/NWI maps'),
            ('critical_habitat_analysis', 'Critical habitat maps'),
            ('air_quality_analysis', 'Nonattainment maps'),
            ('karst_analysis', 'Karst maps')
        ]
        
        for domain_key, domain_name in map_domains:
            if domain_key in normalized_data:
                print(f"   🗺️ Testing {domain_name}...")
                domain_data = normalized_data[domain_key]
                
                # Test the specific map generation method
                if domain_key == 'flood_analysis':
                    updated_data = pdf_generator._generate_missing_flood_maps(domain_data)
                elif domain_key == 'wetland_analysis':
                    updated_data = pdf_generator._generate_missing_wetland_maps(domain_data)
                elif domain_key == 'critical_habitat_analysis':
                    updated_data = pdf_generator._generate_missing_critical_habitat_maps(domain_data)
                elif domain_key == 'air_quality_analysis':
                    updated_data = pdf_generator._generate_missing_nonattainment_maps(domain_data)
                elif domain_key == 'karst_analysis':
                    updated_data = pdf_generator._generate_missing_karst_maps(domain_data)
                
                if updated_data != domain_data:
                    print(f"      ✅ {domain_name}: Map generation attempted")
                else:
                    print(f"      ℹ️ {domain_name}: No new maps needed")
            else:
                print(f"   ⚠️ {domain_name}: No data available for testing")
        
        # Test data validation for screening tool compatibility
        print("\n🔍 Testing Data Validation for Screening Tool Compatibility:")
        validated_data = pdf_generator._validate_and_prepare_for_screening_tool(normalized_data)
        print(f"   ✅ Data validation completed")
        
        # Test final PDF generation
        print("\n📄 Testing Final PDF Generation:")
        pdf_output = pdf_generator.generate_pdf_report()
        
        if pdf_output and Path(pdf_output).exists():
            pdf_size = Path(pdf_output).stat().st_size / (1024*1024)
            print(f"   ✅ PDF report generated: {pdf_output} ({pdf_size:.2f} MB)")
            
            # Test map embedding
            print("\n🖼️ Testing Map Embedding:")
            with open(pdf_output.replace('.pdf', '.html'), 'r') as f:
                html_content = f.read()
            
            # Count embedded images
            base64_images = html_content.count('data:image/')
            print(f"   📊 Maps embedded: {base64_images} base64 images found")
            
            if base64_images > 0:
                print(f"   ✅ Map embedding successful")
            else:
                print(f"   ⚠️ No embedded maps detected")
            
            return pdf_output
        else:
            print(f"   ❌ PDF generation failed")
            return None
        
    except Exception as e:
        print(f"   ❌ Error testing with existing data: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_map_generation_fixes():
    """Test the specific map generation fixes"""
    
    print("\n🧪 Testing Map Generation Fixes")
    print("=" * 60)
    
    # Test coordinates (Puerto Rico)
    test_lat, test_lng = 18.4058, -66.7135
    
    print(f"📍 Testing coordinates: {test_lat}, {test_lng}")
    
    # Test each map generation tool directly
    map_tests = [
        ("WetlandsINFO", "generate_adaptive_wetland_map"),
        ("HabitatINFO", "generate_adaptive_critical_habitat_map"),
        ("NonAttainmentINFO", "generate_adaptive_nonattainment_map")
    ]
    
    for module_name, tool_name in map_tests:
        print(f"\n🗺️ Testing {module_name}.{tool_name}:")
        
        try:
            # Test the import fix
            if module_name == "WetlandsINFO":
                from WetlandsINFO.tools import generate_adaptive_wetland_map
                result = generate_adaptive_wetland_map.invoke({
                    'longitude': test_lng,
                    'latitude': test_lat,
                    'location_name': f"Test_{module_name}"
                })
            elif module_name == "HabitatINFO":
                from HabitatINFO.map_tools import generate_adaptive_critical_habitat_map
                result = generate_adaptive_critical_habitat_map.invoke({
                    'longitude': test_lng,
                    'latitude': test_lat,
                    'location_name': f"Test_{module_name}",
                    'base_map': 'World_Imagery',
                    'include_proposed': True
                })
                # Parse JSON result
                if isinstance(result, str):
                    import json
                    result = json.loads(result)
            elif module_name == "NonAttainmentINFO":
                from NonAttainmentINFO.tools import generate_adaptive_nonattainment_map
                result = generate_adaptive_nonattainment_map.invoke({
                    'longitude': test_lng,
                    'latitude': test_lat,
                    'location_name': f"Test_{module_name}"
                })
                # Parse JSON result
                if isinstance(result, str):
                    import json
                    result = json.loads(result)
            
            # Check result
            if result and (result.get('success') or result.get('status') == 'success'):
                print(f"   ✅ Import and invocation successful")
                
                # Check for output file
                output_file = result.get('filename') or result.get('pdf_path') or result.get('map_generation', {}).get('file_path')
                if output_file and Path(output_file).exists():
                    file_size = Path(output_file).stat().st_size / 1024  # KB
                    print(f"   📄 Map file generated: {Path(output_file).name} ({file_size:.1f} KB)")
                else:
                    print(f"   ⚠️ Map generation completed but file not found: {output_file}")
            else:
                print(f"   ❌ Tool execution failed: {result.get('message', 'Unknown error')}")
                
        except ImportError as e:
            print(f"   ❌ Import failed: {e}")
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")
    
    print("\n✅ Map generation testing completed")

def main():
    """Main test function"""
    
    print("🌍 Comprehensive Environmental Agent Workflow Test")
    print("=" * 60)
    print("This test demonstrates the complete 3-step workflow:")
    print("1. 🔍 Comprehensive Query Tool (environmental data collection)")
    print("2. 📊 Comprehensive Screening Report Tool (analysis & report generation)")
    print("3. 📋 HTML PDF Generator (professional PDF creation)")
    print()
    
    # Test workflow options
    test_options = [
        ("Complete workflow test", test_workflow),
        ("Test with existing schema data", test_with_existing_data),
        ("Test map generation fixes", test_map_generation_fixes)
    ]
    
    print("Select test option:")
    for i, (description, _) in enumerate(test_options, 1):
        print(f"   {i}. {description}")
    
    try:
        choice = input("\nEnter choice (1-3) or press Enter for option 1: ").strip()
        if not choice:
            choice = "1"
        
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(test_options):
            description, test_func = test_options[choice_idx]
            print(f"\n🚀 Running: {description}")
            
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            
            if result:
                print(f"\n✅ Test completed successfully!")
            else:
                print(f"\n⚠️ Test completed with issues")
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    main() 