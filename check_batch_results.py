#!/usr/bin/env python3
"""
Check the results of the batch screening test
"""

import requests
import json

def check_batch_results():
    """Check the batch results and individual screening statuses"""
    
    print('🔍 Checking Batch Screening Results')
    print('=' * 50)
    
    # The batch ID from our latest test
    batch_id = "batch_1748474837_0"
    screening_ids = ['batch_1748474837_0_item_0', 'batch_1748474837_0_item_1']
    
    try:
        # Check overall batch status
        print(f'📊 Checking batch status for: {batch_id}')
        batch_response = requests.get(
            f'http://localhost:8000/api/batch-environmental-screening/{batch_id}/status',
            timeout=10
        )
        
        if batch_response.status_code == 200:
            batch_status = batch_response.json()
            print(f'✅ Batch Status: {batch_status["status"]}')
            print(f'📈 Progress: {batch_status["completed_items"]}/{batch_status["total_items"]} completed')
            print(f'❌ Failed: {batch_status["failed_items"]} items')
            
            print(f'\n📋 Individual Screening Results:')
            print('-' * 40)
            
            # Check each individual screening
            for i, screening_id in enumerate(screening_ids, 1):
                try:
                    response = requests.get(
                        f'http://localhost:8000/api/environmental-screening/{screening_id}/status',
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        status = response.json()
                        print(f'\n🏗️  Project {i}: {status.get("request", {}).get("project_name", "Unknown")}')
                        print(f'   📍 Location: {status.get("request", {}).get("location_name", "Unknown")}')
                        print(f'   🔍 Cadastral: {status.get("request", {}).get("cadastral_number", "N/A")}')
                        print(f'   ✅ Status: {status["status"]}')
                        print(f'   📊 Progress: {status["progress"]}%')
                        print(f'   💬 Message: {status["message"]}')
                        
                        if status.get("error"):
                            print(f'   ❌ Error: {status["error"]}')
                            
                        # Show log entries
                        log_entries = status.get("log_entries", [])
                        if log_entries:
                            print(f'   📝 Recent logs ({len(log_entries)} entries):')
                            for log in log_entries[-3:]:  # Show last 3 log entries
                                print(f'      {log["timestamp"]}: {log["message"]}')
                    else:
                        print(f'❌ Failed to get status for {screening_id}: {response.status_code}')
                        
                except requests.exceptions.RequestException as e:
                    print(f'❌ Error checking {screening_id}: {e}')
        else:
            print(f'❌ Failed to get batch status: {batch_response.status_code}')
            print(f'Response: {batch_response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Connection failed - server not running')
    except Exception as e:
        print(f'❌ Unexpected error: {e}')

    # Check projects and reports
    try:
        print(f'\n📁 Checking Projects Database:')
        projects_response = requests.get('http://localhost:8000/api/projects', timeout=10)
        if projects_response.status_code == 200:
            projects_data = projects_response.json()
            projects = projects_data.get('projects', [])
            print(f'📊 Total projects in database: {len(projects)}')
            
            # Show recent projects
            for project in projects[-2:]:  # Show last 2 projects
                print(f'   🏗️  {project.get("name", "Unknown")}')
                print(f'      Status: {project.get("status", "Unknown")}')
                print(f'      Reports: {project.get("reports_count", 0)}')
                print(f'      Risk: {project.get("risk_level", "Unknown")}')
        
        print(f'\n📄 Checking Reports Database:')
        reports_response = requests.get('http://localhost:8000/api/reports', timeout=10)
        if reports_response.status_code == 200:
            reports_data = reports_response.json()
            reports = reports_data.get('reports', [])
            print(f'📊 Total reports generated: {len(reports)}')
            
            # Show recent reports
            for report in reports[-5:]:  # Show last 5 reports
                print(f'   📄 {report.get("filename", "Unknown")}')
                print(f'      Type: {report.get("category", "Unknown")}')
                print(f'      Size: {report.get("size", 0)} bytes')
                print(f'      PDF: {"Yes" if report.get("is_pdf") else "No"}')
                
    except Exception as e:
        print(f'❌ Error checking database: {e}')

if __name__ == "__main__":
    check_batch_results() 