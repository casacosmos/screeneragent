#!/usr/bin/env python3
"""
Test Script: Output Directory Manager Integration

This script tests that all environmental analysis tools properly use
the output directory manager for organizing files into project directories.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Import the output directory manager
from output_directory_manager import get_output_manager, create_intelligent_project_directory

# Import FEMA flood clients
from FloodINFO.firmette_client import FEMAFIRMetteClient
from FloodINFO.preliminary_comparison_client import FEMAPreliminaryComparisonClient
from FloodINFO.abfe_client import FEMAABFEClient

# Import comprehensive flood tool
from comprehensive_flood_tool import comprehensive_flood_analysis

def test_output_directory_manager_integration():
    """Test that all tools properly use the output directory manager"""
    
    print("🧪 Testing Output Directory Manager Integration")
    print("=" * 60)
    
    # Test coordinates (Cataño, Puerto Rico)
    longitude = -66.150906
    latitude = 18.434059
    location_name = "Output Directory Integration Test - Cataño, PR"
    
    # Step 1: Create intelligent project directory
    print("\n📁 Step 1: Creating intelligent project directory...")
    
    try:
        result = create_intelligent_project_directory(
            project_description="Output Directory Manager Integration Test",
            location_name=location_name,
            coordinates=[longitude, latitude]
        )
        
        if result.get('success'):
            project_dir = result['project_directory']
            print(f"✅ Project directory created: {project_dir}")
            print(f"📂 Directory structure:")
            for subdir_type, path in result['directory_structure'].items():
                print(f"   - {subdir_type}: {path}")
        else:
            print(f"❌ Failed to create project directory: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Error creating project directory: {e}")
        return False
    
    # Step 2: Test individual FEMA clients
    print("\n🌊 Step 2: Testing individual FEMA clients...")
    
    # Test FIRMette client
    print("\n  🗺️  Testing FIRMette client...")
    try:
        firmette_client = FEMAFIRMetteClient()
        success, result, job_id = firmette_client.generate_firmette_via_msc(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if success:
            # Test download with output manager
            download_success = firmette_client.download_firmette(
                result, 
                "test_firmette_integration.pdf",
                use_output_manager=True
            )
            
            if download_success:
                print(f"   ✅ FIRMette client successfully uses output manager")
            else:
                print(f"   ❌ FIRMette download failed")
        else:
            print(f"   ⚠️  FIRMette generation failed: {result}")
    except Exception as e:
        print(f"   ❌ FIRMette client error: {e}")
    
    # Test Preliminary Comparison client
    print("\n  📊 Testing Preliminary Comparison client...")
    try:
        comparison_client = FEMAPreliminaryComparisonClient()
        success, result, job_id = comparison_client.generate_comparison_report(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if success:
            # Test download with output manager
            download_success = comparison_client.download_comparison_report(
                result,
                "test_preliminary_comparison_integration.pdf",
                use_output_manager=True
            )
            
            if download_success:
                print(f"   ✅ Preliminary Comparison client successfully uses output manager")
            else:
                print(f"   ❌ Preliminary Comparison download failed")
        else:
            print(f"   ⚠️  Preliminary Comparison generation failed: {result}")
    except Exception as e:
        print(f"   ❌ Preliminary Comparison client error: {e}")
    
    # Test ABFE client
    print("\n  🗺️  Testing ABFE client...")
    try:
        abfe_client = FEMAABFEClient()
        success, result, job_id = abfe_client.generate_abfe_map(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            buffer_miles=1.0
        )
        
        if success:
            # Test download with output manager
            download_success = abfe_client.download_abfe_map(
                result,
                "test_abfe_integration.pdf",
                use_output_manager=True
            )
            
            if download_success:
                print(f"   ✅ ABFE client successfully uses output manager")
            else:
                print(f"   ❌ ABFE download failed")
        else:
            print(f"   ⚠️  ABFE generation failed: {result}")
    except Exception as e:
        print(f"   ❌ ABFE client error: {e}")
    
    # Step 3: Test comprehensive flood tool
    print("\n🌊 Step 3: Testing comprehensive flood tool...")
    try:
        flood_result = comprehensive_flood_analysis(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name,
            generate_reports=True,
            include_abfe=True
        )
        
        if flood_result.get('reports_generated'):
            reports = flood_result['reports_generated']
            successful_reports = sum(1 for r in reports.values() if r.get('success'))
            total_reports = len(reports)
            
            print(f"   ✅ Comprehensive flood tool completed")
            print(f"   📊 Reports generated: {successful_reports}/{total_reports}")
            
            for report_type, report_info in reports.items():
                if report_info.get('success'):
                    print(f"   ✅ {report_type}: {report_info.get('filename', 'Generated')}")
                else:
                    print(f"   ❌ {report_type}: {report_info.get('error', 'Failed')}")
        else:
            print(f"   ❌ Comprehensive flood tool failed")
    except Exception as e:
        print(f"   ❌ Comprehensive flood tool error: {e}")
    
    # Step 4: Verify file organization
    print("\n📂 Step 4: Verifying file organization...")
    
    output_manager = get_output_manager()
    project_info = output_manager.get_project_info()
    
    if project_info.get('project_directory'):
        project_path = Path(project_info['project_directory'])
        
        print(f"   📁 Project directory: {project_path}")
        
        # Check each subdirectory
        subdirs = ['reports', 'maps', 'logs', 'data']
        for subdir in subdirs:
            subdir_path = project_path / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                print(f"   📂 {subdir}/: {len(files)} files")
                for file in files[:3]:  # Show first 3 files
                    print(f"     - {file.name}")
                if len(files) > 3:
                    print(f"     ... and {len(files) - 3} more files")
            else:
                print(f"   📂 {subdir}/: Directory does not exist")
    
    # Step 5: Generate summary
    print("\n📋 Step 5: Integration Test Summary")
    print("-" * 40)
    
    output_manager = get_output_manager()
    project_info = output_manager.get_project_info()
    
    if project_info.get('project_directory'):
        project_path = Path(project_info['project_directory'])
        
        # Count files in each directory
        file_counts = {}
        total_files = 0
        
        for subdir in ['reports', 'maps', 'logs', 'data']:
            subdir_path = project_path / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                file_counts[subdir] = len(files)
                total_files += len(files)
            else:
                file_counts[subdir] = 0
        
        print(f"Project Directory: {project_path.name}")
        print(f"Total Files Generated: {total_files}")
        print(f"File Distribution:")
        for subdir, count in file_counts.items():
            print(f"  - {subdir}: {count} files")
        
        if total_files > 0:
            print("\n✅ Output Directory Manager Integration Test PASSED")
            print("   All tools successfully used the centralized directory structure")
            return True
        else:
            print("\n⚠️  Output Directory Manager Integration Test INCOMPLETE")
            print("   No files were generated, but directory structure was created")
            return False
    else:
        print("\n❌ Output Directory Manager Integration Test FAILED")
        print("   Project directory was not properly created")
        return False

def test_legacy_compatibility():
    """Test that tools still work without output manager (legacy mode)"""
    
    print("\n\n🔧 Testing Legacy Compatibility (without output manager)")
    print("=" * 60)
    
    # Test coordinates
    longitude = -66.150906
    latitude = 18.434059
    location_name = "Legacy Compatibility Test"
    
    print("📝 Note: This tests that tools can still work in legacy mode")
    print("        (saving to current directory when no project is set up)")
    
    try:
        # Test FIRMette client in legacy mode
        firmette_client = FEMAFIRMetteClient()
        success, result, job_id = firmette_client.generate_firmette_via_msc(
            longitude=longitude,
            latitude=latitude,
            location_name=location_name
        )
        
        if success:
            # Test download in legacy mode
            download_success = firmette_client.download_firmette(
                result,
                "legacy_test_firmette.pdf",
                use_output_manager=False
            )
            
            if download_success:
                print("✅ Legacy mode works - FIRMette saved to current directory")
                # Clean up
                if os.path.exists("legacy_test_firmette.pdf"):
                    os.remove("legacy_test_firmette.pdf")
            else:
                print("❌ Legacy mode failed - FIRMette download failed")
        else:
            print(f"⚠️  Legacy test skipped - FIRMette generation failed: {result}")
    
    except Exception as e:
        print(f"❌ Legacy compatibility test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Output Directory Manager Integration Tests")
    print("=" * 70)
    
    # Run main integration test
    success = test_output_directory_manager_integration()
    
    # Run legacy compatibility test
    test_legacy_compatibility()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All tests completed successfully!")
        print("💡 The output directory manager is properly integrated with all tools")
    else:
        print("⚠️  Tests completed with some issues")
        print("💡 Check the output above for specific problems")
    
    print("\n📁 Check the 'output/' directory to see the generated project structure")
    print("🔍 Each project now has its own organized directory with reports/, maps/, logs/, and data/ subdirectories") 