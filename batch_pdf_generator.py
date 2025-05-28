#!/usr/bin/env python3
"""
Batch PDF Report Generator

This script finds all report.txt files in the output subdirectories and generates
single-page PDF reports for each one using the PDF report generator tool.
"""

import os
import glob
from datetime import datetime
from pdf_report_generator import generate_pdf_report

def find_report_files(base_dir: str = "output") -> list:
    """Find all report.txt files in subdirectories"""
    
    pattern = os.path.join(base_dir, "*", "report.txt")
    report_files = glob.glob(pattern)
    
    print(f"🔍 Searching for report.txt files in: {base_dir}")
    print(f"📁 Found {len(report_files)} report files:")
    
    for i, file_path in enumerate(report_files, 1):
        # Extract directory name for display
        dir_name = os.path.basename(os.path.dirname(file_path))
        print(f"   {i}. {dir_name}/report.txt")
    
    return report_files

def read_report_content(file_path: str) -> tuple:
    """Read report content and extract title from directory name"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Extract project name from directory
        dir_name = os.path.basename(os.path.dirname(file_path))
        
        # Create a nice title
        title = f"Environmental Screening Report"
        subtitle = f"{dir_name.title()} - Site Analysis"
        
        return content, title, subtitle, dir_name
        
    except Exception as e:
        print(f"❌ Error reading {file_path}: {str(e)}")
        return None, None, None, None

def generate_single_pdf(file_path: str, content: str, title: str, subtitle: str, project_name: str) -> dict:
    """Generate a single-page PDF for one report"""
    
    print(f"\n📄 Processing: {project_name}")
    
    # Create safe filename
    safe_project_name = project_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"single_page_report_{safe_project_name}_{timestamp}"
    
    try:
        result = generate_pdf_report.invoke({
            "report_text": content,
            "report_title": title,
            "report_subtitle": subtitle,
            "author": "Environmental Screening Agent",
            "location": f"Project: {project_name}",
            "template": "environmental",
            "include_toc": False,  # No TOC for single page
            "single_page": True,   # Enable single page mode
            "page_size": "letter",
            "output_filename": output_filename
        })
        
        if result.get('success'):
            print(f"   ✅ PDF generated: {os.path.basename(result['filename'])}")
            print(f"   📏 File size: {result.get('file_size_mb', 0)} MB")
            print(f"   ⏱️  Generation time: {result.get('generation_time_seconds', 0)} seconds")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"success": False, "error": str(e)}

def batch_generate_pdfs():
    """Main function to batch generate PDFs for all report files"""
    
    print("📄 Batch PDF Report Generator")
    print("=" * 60)
    print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find all report files
    report_files = find_report_files()
    
    if not report_files:
        print("\n⚠️  No report.txt files found in output subdirectories.")
        return
    
    print(f"\n🚀 Starting batch processing of {len(report_files)} reports...")
    
    # Process each report
    results = []
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(report_files, 1):
        print(f"\n📋 Processing {i}/{len(report_files)}")
        
        # Read content
        content, title, subtitle, project_name = read_report_content(file_path)
        
        if content is None:
            failed += 1
            continue
        
        # Generate PDF
        result = generate_single_pdf(file_path, content, title, subtitle, project_name)
        results.append({
            "project": project_name,
            "source_file": file_path,
            "result": result
        })
        
        if result.get('success'):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"📊 Total reports processed: {len(report_files)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {(successful/len(report_files)*100):.1f}%")
    
    # List generated files
    print(f"\n📁 Generated PDF files:")
    for result_info in results:
        if result_info["result"].get("success"):
            filename = os.path.basename(result_info["result"]["filename"])
            file_size = result_info["result"].get("file_size_mb", 0)
            print(f"   • {filename} ({file_size} MB) - {result_info['project']}")
    
    # List any failures
    if failed > 0:
        print(f"\n❌ Failed reports:")
        for result_info in results:
            if not result_info["result"].get("success"):
                error = result_info["result"].get("error", "Unknown error")
                print(f"   • {result_info['project']}: {error}")
    
    print(f"\n🕒 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 All PDF files saved to: output/")
    
    return results

if __name__ == "__main__":
    try:
        results = batch_generate_pdfs()
        
        if results:
            successful_count = sum(1 for r in results if r["result"].get("success"))
            if successful_count > 0:
                print(f"\n🎉 Batch processing completed successfully!")
                print(f"📄 {successful_count} single-page PDF reports generated.")
            else:
                print(f"\n⚠️  No PDFs were generated successfully.")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Batch processing interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Batch processing failed: {str(e)}") 