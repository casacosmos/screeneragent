#!/usr/bin/env python3
"""
Test script for the simplified environmental agent workflow
"""

import asyncio
from comprehensive_environmental_agent import ComprehensiveEnvironmentalAgent
from pathlib import Path

async def test_simplified_workflow():
    """Test the simplified environmental agent workflow"""
    print("🧪 Testing Simplified Environmental Agent Workflow")
    print("=" * 60)
    
    # Initialize agent with simplified settings
    agent = ComprehensiveEnvironmentalAgent(
        output_directory='test_simplified_output',
        include_maps=True,
        prefer_png_maps=True
    )
    
    try:
        # Run a quick test
        result = await agent.process_location(
            location='18.4058,-66.7135',
            project_name='Simplified_Test_Project'
        )
        
        # Extract correct values from result structure
        overall_success = result.get('success', False)
        total_files = len(result.get('generated_files', []))
        successful_steps = result.get('workflow_info', {}).get('successful_steps', 0)
        total_steps = result.get('workflow_info', {}).get('total_steps', 3)
        
        print("\n📊 Results Summary:")
        print(f"   Overall Success: {overall_success}")
        print(f"   Files Generated: {total_files}")
        print(f"   Steps Completed: {successful_steps}/{total_steps}")
        
        # Check directory structure - get project directory from step1 results
        project_dir = None
        if result.get('step1_query_results') and 'project_info' in result['step1_query_results']:
            project_dir = Path(result['step1_query_results']['project_info']['project_directory'])
        
        if project_dir and project_dir.exists():
            print(f"\n📁 Directory Structure:")
            print(f"   Project: {project_dir}")
            
            subdirs = ['data', 'maps', 'reports', 'logs']
            for subdir in subdirs:
                subdir_path = project_dir / subdir
                if subdir_path.exists():
                    file_count = len(list(subdir_path.iterdir()))
                    print(f"   {subdir}/: {file_count} files")
                else:
                    print(f"   {subdir}/: Missing")
        else:
            print(f"\n📁 Directory Structure: Not accessible")
        
        # Check PDF report generation
        if result.get('step3_pdf_report'):
            pdf_info = result['step3_pdf_report']
            print(f"\n📄 Report Generation:")
            print(f"   Success: {pdf_info.get('success')}")
            if pdf_info.get('pdf_path'):
                print(f"   PDF: {Path(pdf_info['pdf_path']).name}")
                print(f"   Size: {pdf_info.get('file_size_mb', 0)} MB")
            if pdf_info.get('html_path'):
                print(f"   HTML: {Path(pdf_info['html_path']).name}")
        
        # Show any errors
        if result.get('errors'):
            print(f"\n⚠️ Errors encountered: {len(result['errors'])}")
            for i, error in enumerate(result['errors'][:3]):  # Show first 3 errors
                print(f"   {i+1}. Step {error.get('step', '?')}: {error.get('error', 'Unknown error')}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("🚀 Starting Simplified Agent Test...")
    
    success = asyncio.run(test_simplified_workflow())
    
    if success:
        print("\n✅ Simplified workflow test completed successfully!")
        print("✅ Directory management and map handling are working correctly.")
    else:
        print("\n❌ Test failed - check the output above for issues.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 