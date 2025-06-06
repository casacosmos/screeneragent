#!/usr/bin/env python3
"""
Test single environmental screening to verify fixes
"""

import requests
import json
import time

def test_single_screening():
    """Test a single environmental screening"""
    
    print('🧪 Testing Single Environmental Screening')
    print('=' * 50)
    
    # Test data
    project_data = {
        "project_name": "Test Property Assessment",
        "location_name": "Ponce, Puerto Rico",
        "cadastral_number": "389-077-300-08",
        "analyses_requested": ["cadastral", "flood"],
        "include_comprehensive_report": True,
        "include_pdf": True,
        "use_llm_enhancement": True
    }
    
    try:
        # Submit screening request
        print('📡 Submitting screening request...')
        response = requests.post(
            'http://localhost:8000/api/environmental-screening',
            json=project_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            screening_id = result['screening_id']
            print(f'✅ Screening started successfully!')
            print(f'🔍 Screening ID: {screening_id}')
            
            # Monitor progress
            print(f'\n⏱️  Monitoring progress...')
            for i in range(5):  # Check 5 times over 50 seconds
                time.sleep(10)
                status_response = requests.get(
                    f'http://localhost:8000/api/environmental-screening/{screening_id}/status',
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f'📊 Status: {status["status"]} - Progress: {status["progress"]}%')
                    print(f'💬 Message: {status["message"]}')
                    
                    if status["status"] in ["completed", "failed"]:
                        if status["status"] == "completed":
                            print(f'🎉 Screening completed successfully!')
                        else:
                            print(f'❌ Screening failed: {status.get("error", "Unknown error")}')
                        break
                else:
                    print(f'⚠️  Status check failed: {status_response.status_code}')
            else:
                print(f'⏰ Monitoring timeout - screening may still be running')
                
        else:
            print(f'❌ Request failed: {response.status_code}')
            print(f'Response: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Connection failed - server not running')
    except Exception as e:
        print(f'❌ Unexpected error: {e}')

if __name__ == "__main__":
    test_single_screening() 