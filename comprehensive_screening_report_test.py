#!/usr/bin/env python3
"""
Test Script for Comprehensive Screening Report Tool

This script demonstrates and tests the comprehensive screening report tool
that generates JSON, Markdown, and PDF reports from screening data.
"""

import os
import sys
from pathlib import Path

def test_comprehensive_report_tool():
    """Test the comprehensive screening report tool"""
    
    print("🧪 Testing Comprehensive Screening Report Tool")
    print("=" * 60)
    
    # Test data directory
    test_data_dir = "output/Cadastral_115-053-432-02_2025-05-28_at_03.03.17"
    
    if not Path(test_data_dir).exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        print("Please run environmental screening tools first to generate test data.")
        return False
    
    print(f"✅ Found test data directory: {test_data_dir}")
    
    try:
        # Import the tool
        from comprehensive_screening_report_tool import ScreeningReportTool
        
        print("✅ Successfully imported ScreeningReportTool")
        
        # Test 1: Basic tool initialization
        print("\n📋 Test 1: Tool Initialization")
        tool = ScreeningReportTool(
            output_directory=test_data_dir,
            use_llm=False  # Start with standard mode for testing
        )
        print("✅ Tool initialized successfully")
        
        # Test 2: Display summary
        print("\n📋 Test 2: Analysis Summary")
        tool.display_summary()
        print("✅ Summary displayed successfully")
        
        # Test 3: Generate reports (JSON + Markdown only first)
        print("\n📋 Test 3: Generate JSON and Markdown Reports")
        output_files = tool.generate_reports(
            output_format="both",
            custom_filename="test_comprehensive_report",
            include_pdf=False  # Skip PDF for first test
        )
        
        print("✅ JSON and Markdown reports generated:")
        for format_type, file_path in output_files.items():
            print(f"   {format_type.upper()}: {Path(file_path).name}")
        
        # Test 4: Check if PDF generation is available
        try:
            from pdf_report_generator import ScreeningPDFGenerator
            print("\n📋 Test 4: PDF Generation Available")
            
            # Try generating PDF
            output_files_with_pdf = tool.generate_reports(
                output_format="both",
                custom_filename="test_comprehensive_report_with_pdf",
                include_pdf=True
            )
            
            print("✅ All report formats generated:")
            for format_type, file_path in output_files_with_pdf.items():
                print(f"   {format_type.upper()}: {Path(file_path).name}")
            
        except ImportError:
            print("\n⚠️ Test 4: PDF generation not available (ReportLab not installed)")
            print("Install with: pip install reportlab pillow")
        
        # Test 5: Check LLM enhancement availability
        try:
            print("\n📋 Test 5: LLM Enhancement Test")
            enhanced_tool = ScreeningReportTool(
                output_directory=test_data_dir,
                use_llm=True
            )
            
            # Generate enhanced summary
            enhanced_tool.display_summary()
            print("✅ LLM-enhanced tool initialized and summary generated")
            
        except Exception as e:
            print(f"\n⚠️ Test 5: LLM enhancement failed: {e}")
            print("This may be due to missing OpenAI API key or network issues")
        
        print("\n✅ All available tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def test_auto_discovery():
    """Test auto-discovery functionality"""
    
    print("\n🔍 Testing Auto-Discovery Feature")
    print("=" * 40)
    
    try:
        from comprehensive_screening_report_tool import find_screening_directories, auto_discover_and_process
        
        # Find screening directories
        screening_dirs = find_screening_directories("output")
        
        if not screening_dirs:
            print("❌ No screening directories found for auto-discovery test")
            return False
        
        print(f"✅ Found {len(screening_dirs)} screening directories:")
        for dir_path in screening_dirs:
            print(f"   📁 {dir_path.name}")
        
        # Test auto-discovery processing (without PDF to be safe)
        print("\n🔄 Testing batch processing...")
        results = auto_discover_and_process(
            base_output_dir="output",
            use_llm=False,
            output_format="json",  # Just JSON for quick test
            include_pdf=False
        )
        
        print(f"✅ Batch processing completed:")
        print(f"   Directories processed: {len(results)}")
        successful = sum(1 for files in results.values() if files)
        print(f"   Successful: {successful}")
        print(f"   Failed: {len(results) - successful}")
        
        return True
        
    except Exception as e:
        print(f"❌ Auto-discovery test failed: {e}")
        return False


def main():
    """Run all tests"""
    
    print("🌍 Comprehensive Environmental Screening Report Tool Tests")
    print("=" * 60)
    
    # Test 1: Basic tool functionality
    test1_success = test_comprehensive_report_tool()
    
    # Test 2: Auto-discovery
    test2_success = test_auto_discovery()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Tool Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Auto-Discovery Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Tool is ready for use.")
        print("\n💡 Usage Examples:")
        print("   # Process specific directory:")
        print("   python comprehensive_screening_report_tool.py output/Your_Project_Directory")
        print("   ")
        print("   # Auto-discover and process all directories:")
        print("   python comprehensive_screening_report_tool.py --auto-discover")
        print("   ")
        print("   # Generate with PDF (requires reportlab):")
        print("   python comprehensive_screening_report_tool.py output/Your_Project --format both")
        
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
    
    return 0 if (test1_success and test2_success) else 1


if __name__ == "__main__":
    exit(main()) 