#!/usr/bin/env python3
"""
Test script for the batch screening endpoint
"""

import requests
import json
import time

def test_batch_endpoint():
    """Test the batch screening endpoint"""
    
    # Test data for batch screening
    batch_data = [
        {
            'project_name': 'Residential Development Project A',
            'location_name': 'Cataño, Puerto Rico',
            'cadastral_number': '227-052-007-20',
            'coordinates': [-66.150906, 18.434059],
            'analyses_requested': ['cadastral', 'flood', 'wetland', 'habitat'],
            'include_comprehensive_report': True,
            'include_pdf': True,
            'use_llm_enhancement': True
        },
        {
            'project_name': 'Commercial Property Assessment B',
            'location_name': 'San Juan, Puerto Rico', 
            'cadastral_number': '389-077-300-08',
            'coordinates': [-66.105721, 18.465539],
            'analyses_requested': ['cadastral', 'flood', 'karst'],
            'include_comprehensive_report': True,
            'include_pdf': True,
            'use_llm_enhancement': False
        }
    ]

    print('🧪 Testing Batch Screening Endpoint')
    print('=' * 50)

    # Test the batch endpoint
    try:
        print('📡 Sending batch screening request...')
        response = requests.post(
            'http://localhost:8000/api/batch-environmental-screening',
            json=batch_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print('✅ Batch request accepted!')
            print(f'📋 Batch ID: {result["batch_id"]}')
            print(f'📊 Total items: {result["total_items"]}')
            print(f'🔍 Screening IDs: {result["screening_ids"]}')
            
            # Store batch ID for status checking
            batch_id = result['batch_id']
            print(f'\n⏱️  Monitoring batch progress for: {batch_id}')
            
            # Monitor batch status
            for i in range(10):  # Check 10 times
                time.sleep(3)  # Wait 3 seconds between checks
                
                try:
                    status_response = requests.get(
                        f'http://localhost:8000/api/batch-environmental-screening/{batch_id}/status',
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f'📊 Status check {i+1}: {status["status"]} - Completed: {status["completed_items"]}/{status["total_items"]}')
                        
                        if status['status'] == 'completed':
                            print('✅ Batch processing completed!')
                            break
                        elif status['status'] == 'failed':
                            print('❌ Batch processing failed!')
                            break
                    else:
                        print(f'⚠️  Status check failed: {status_response.status_code}')
                        
                except requests.exceptions.RequestException as e:
                    print(f'⚠️  Status check error: {e}')
                    
        elif response.status_code == 503:
            print('⚠️  Service unavailable - agent not ready')
            print('💡 Make sure the environmental agent is properly initialized')
        else:
            print(f'❌ Request failed: {response.status_code}')
            print(f'Response: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Connection failed - server not running')
        print('💡 Start the server first with: python advanced_frontend_server.py')
    except requests.exceptions.RequestException as e:
        print(f'❌ Request error: {e}')
    except Exception as e:
        print(f'❌ Unexpected error: {e}')

if __name__ == "__main__":
    test_batch_endpoint() 