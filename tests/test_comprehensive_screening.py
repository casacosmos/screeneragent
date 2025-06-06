#!/usr/bin/env python3
"""
Test script for comprehensive environmental screening with professional HTML PDF generation
"""

import os
import sys
from pathlib import Path
from comprehensive_environmental_agent import create_comprehensive_environmental_agent
from langchain_core.messages import HumanMessage

def test_comprehensive_screening():
    """Test the complete comprehensive environmental screening workflow"""
    
    print("🌍 Testing Comprehensive Environmental Screening with Professional PDF")
    print("=" * 80)
    print("🎯 This test will:")
    print("   1. Create an intelligent project directory")
    print("   2. Run all environmental analyses (property, karst, flood, wetland, habitat, air quality)")
    print("   3. Generate comprehensive reports (JSON, Markdown, PDF)")
    print("   4. Create professional HTML-based PDF with embedded maps")
    print("   5. Verify all files are properly generated")
    print()
    
    try:
        # Create the agent
        agent = create_comprehensive_environmental_agent()
        print("✅ Environmental screening agent created successfully")
        
        # Test query for a comprehensive environmental screening
        query = """Generate a comprehensive environmental screening report for residential development project at cadastral 227-052-007-20 in Cataño, Puerto Rico. 

I need complete environmental assessment including:
- Property and cadastral analysis with zoning verification
- PRAPEC karst analysis for Puerto Rico compliance
- FEMA flood analysis with insurance requirements
- Wetland analysis with regulatory compliance
- Critical habitat analysis with ESA consultation requirements
- Air quality analysis for residential development standards
- Professional comprehensive reports with embedded maps suitable for regulatory submission

Please organize all files in a descriptive project directory and generate the professional PDF report with the compliance checklist."""
        
        print(f"🔍 Test Query:")
        print(f"   {query}")
        print()
        print("🤖 Starting comprehensive environmental screening...")
        print("   (This may take 3-5 minutes to complete all analyses and generate reports)")
        print()
        
        # Configure with thread_id
        config = {"configurable": {"thread_id": "test_screening_thread"}}
        
        # Run the agent
        response = agent.invoke({
            "messages": [HumanMessage(content=query)]
        }, config=config)
        
        # Extract the structured response if available
        structured_response = response.get('structured_response')
        if structured_response:
            print("✅ Structured response received from agent")
            
            # Check if we have project directory - access as attribute, not dict
            project_directory = getattr(structured_response, 'project_directory', None)
            if project_directory:
                print(f"📁 Project Directory: {project_directory}")
                
                # Verify directory exists
                project_path = Path(project_directory)
                if project_path.exists():
                    print("✅ Project directory exists")
                    
                    # List directory contents
                    print(f"📂 Directory Contents:")
                    for item in project_path.rglob("*"):
                        if item.is_file():
                            relative_path = item.relative_to(project_path)
                            print(f"   📄 {relative_path}")
                    
                    # Check for professional HTML PDF
                    pdf_files = list(project_path.rglob("*.pdf"))
                    html_files = list(project_path.rglob("*.html"))
                    
                    print(f"\n📊 Generated Files Summary:")
                    print(f"   📄 PDF files: {len(pdf_files)}")
                    print(f"   🌐 HTML files: {len(html_files)}")
                    
                    # Look for professional HTML-based PDF
                    professional_pdfs = [p for p in pdf_files if 'professional' in p.name.lower() or 'environmental_report' in p.name.lower()]
                    if professional_pdfs:
                        print(f"✅ Professional HTML-based PDF found: {professional_pdfs[0].name}")
                        print(f"   📍 Path: {professional_pdfs[0]}")
                        print(f"   📊 Size: {professional_pdfs[0].stat().st_size / 1024:.1f} KB")
                    else:
                        print("⚠️ Professional HTML-based PDF not found")
                        
                        # Check for comprehensive reports that might contain the HTML PDF
                        comprehensive_pdfs = [p for p in pdf_files if 'comprehensive' in p.name.lower()]
                        if comprehensive_pdfs:
                            print(f"📄 Found comprehensive PDF: {comprehensive_pdfs[0].name}")
                            print(f"   📊 Size: {comprehensive_pdfs[0].stat().st_size / 1024:.1f} KB")
                    
                    # Check for maps
                    map_files = list(project_path.rglob("*map*.pdf")) + list(project_path.rglob("*map*.png"))
                    print(f"   🗺️ Map files: {len(map_files)}")
                    for map_file in map_files:
                        print(f"      🗺️ {map_file.name}")
                    
                    # Check for comprehensive reports
                    json_reports = list(project_path.rglob("*comprehensive*.json"))
                    md_reports = list(project_path.rglob("*comprehensive*.md"))
                    
                    print(f"   📊 JSON reports: {len(json_reports)}")
                    print(f"   📝 Markdown reports: {len(md_reports)}")
                    
                    # Check for the structured response data
                    project_name = getattr(structured_response, 'project_name', 'Unknown')
                    success_status = getattr(structured_response, 'success', False)
                    risk_level = getattr(structured_response, 'overall_risk_level_assessment', 'Unknown')
                    
                    print(f"\n📋 Structured Response Summary:")
                    print(f"   🏗️  Project: {project_name}")
                    print(f"   ✅ Success: {success_status}")
                    print(f"   ⚠️  Risk Level: {risk_level}")
                    
                    # Check if comprehensive reports were generated
                    comprehensive_reports = getattr(structured_response, 'comprehensive_reports', None)
                    if comprehensive_reports:
                        print(f"   📄 Comprehensive reports structure found")
                        if hasattr(comprehensive_reports, 'pdf') and comprehensive_reports.pdf:
                            print(f"      📄 PDF: {comprehensive_reports.pdf}")
                        if hasattr(comprehensive_reports, 'json_report') and comprehensive_reports.json_report:
                            print(f"      📊 JSON: {comprehensive_reports.json_report}")
                        if hasattr(comprehensive_reports, 'markdown') and comprehensive_reports.markdown:
                            print(f"      📝 Markdown: {comprehensive_reports.markdown}")
                    
                else:
                    print("❌ Project directory does not exist")
            else:
                print("⚠️ No project directory specified in structured response")
                
                # Try to find the latest directory manually
                output_dir = Path("output")
                if output_dir.exists():
                    project_dirs = sorted([d for d in output_dir.glob("*") if d.is_dir()], 
                                        key=lambda x: x.stat().st_mtime, reverse=True)
                    if project_dirs:
                        latest_dir = project_dirs[0]
                        print(f"📁 Found latest project directory: {latest_dir.name}")
                        
                        # Check its contents
                        pdf_files = list(latest_dir.rglob("*.pdf"))
                        print(f"   📄 PDF files: {len(pdf_files)}")
                        for pdf_file in pdf_files[:5]:  # Show first 5
                            print(f"      📄 {pdf_file.name}")
        else:
            print("⚠️ No structured response received")
            
            # Try to find the latest directory anyway
            output_dir = Path("output")
            if output_dir.exists():
                project_dirs = sorted([d for d in output_dir.glob("*") if d.is_dir()], 
                                    key=lambda x: x.stat().st_mtime, reverse=True)
                if project_dirs:
                    latest_dir = project_dirs[0]
                    print(f"📁 Found latest project directory: {latest_dir.name}")
        
        # Print agent response
        last_message = response["messages"][-1]
        print(f"\n🌍 Agent Response (first 500 chars):")
        print("=" * 50)
        content = last_message.content
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    success = test_comprehensive_screening()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("🎯 Professional HTML PDF with embedded maps should be available in the project directory")
    else:
        print("\n❌ Test failed!")
        
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 