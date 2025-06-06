#!/usr/bin/env python3
"""
Test script to manually verify the comprehensive report generation tools
work with existing data in the output directories.
"""

import json
from pathlib import Path
from comprehensive_screening_report_tool import (
    find_latest_screening_directory,
    generate_comprehensive_screening_report
)

def test_manual_report_generation():
    """Test manual execution of report generation tools"""
    
    print("🧪 Testing Manual Report Generation")
    print("=" * 60)
    
    # Step 1: Find latest screening directory
    print("\n🔍 Step 1: Finding latest screening directory...")
    latest_result = find_latest_screening_directory(base_dir="output")
    
    print(f"   Success: {latest_result.get('success', False)}")
    if latest_result.get('success'):
        latest_dir = latest_result.get('latest_directory')
        print(f"   Latest directory: {latest_dir}")
        print(f"   Project name: {latest_result.get('project_name')}")
        print(f"   Available directories: {len(latest_result.get('available_directories', []))}")
        
        # Step 2: Generate comprehensive report for latest directory
        print("\n📄 Step 2: Generating comprehensive report...")
        try:
            report_result = generate_comprehensive_screening_report(
                output_directory=latest_dir,
                output_format="both",
                include_pdf=True,
                use_llm=False  # Disable LLM for faster testing
            )
            
            print(f"   Success: {report_result.get('success', False)}")
            if report_result.get('success'):
                print(f"   Output files: {len(report_result.get('output_files', []))}")
                for file_path in report_result.get('output_files', []):
                    print(f"      • {file_path}")
                print(f"   PDF generated: {report_result.get('pdf_generated', False)}")
                
                # Check if files actually exist
                print("\n🔍 Verifying generated files...")
                base_path = Path(latest_dir)
                reports_dir = base_path / "reports"
                
                if reports_dir.exists():
                    report_files = list(reports_dir.glob("*"))
                    print(f"   Files in reports directory: {len(report_files)}")
                    for file in report_files:
                        print(f"      • {file.name} ({file.stat().st_size} bytes)")
                else:
                    print("   ❌ Reports directory not found")
                    
            else:
                print(f"   ❌ Error: {report_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception during report generation: {e}")
            
    else:
        print(f"   ❌ Error: {latest_result.get('error', 'Unknown error')}")
        
        # List available directories for debugging
        print("\n📁 Available output directories:")
        output_path = Path("output")
        if output_path.exists():
            dirs = [d for d in output_path.iterdir() if d.is_dir()]
            for i, dir_path in enumerate(dirs, 1):
                data_dir = dir_path / "data"
                has_data = data_dir.exists() and any(data_dir.glob("*.json"))
                print(f"   {i}. {dir_path.name} {'✅' if has_data else '❌'}")
        else:
            print("   No output directory found")

if __name__ == "__main__":
    test_manual_report_generation() 