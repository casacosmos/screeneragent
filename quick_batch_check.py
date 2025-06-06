#!/usr/bin/env python3
"""
Quick check of the current batch status
"""

import requests

def check_batch():
    batch_id = 'batch_1748475309_0'
    try:
        response = requests.get(f'http://localhost:8000/api/batch-environmental-screening/{batch_id}/status', timeout=10)
        if response.status_code == 200:
            status = response.json()
            print(f'Batch Status: {status["status"]}')
            print(f'Progress: {status["completed_items"]}/{status["total_items"]} completed')
            print(f'Failed: {status["failed_items"]} items')
            
            # Check individual items
            for i, item in enumerate(status.get('item_statuses', [])):
                print(f'Item {i+1}: {item["status"]} - {item["message"]}')
                if 'error' in item and item['error']:
                    print(f'  Error: {item["error"]}')
        else:
            print(f'Error: {response.status_code}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    check_batch() 