#!/usr/bin/env python3
"""
Test script for the bulk image search functionality.
This script tests the bulk search API endpoints and functionality.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000"
TEST_ENTRIES = [
    {"keyword": "cats", "className": "animals"},
    {"keyword": "dogs", "className": "pets"},
    {"keyword": "cars", "className": "vehicles"}
]
IMAGES_PER_CLASS = 5  # Small number for testing

def test_bulk_search_page():
    """Test that the bulk search page loads correctly."""
    print("🧪 Testing bulk search page...")
    
    try:
        response = requests.get(f"{BASE_URL}/bulk-search")
        if response.status_code == 200:
            print("✅ Bulk search page loads successfully")
            return True
        else:
            print(f"❌ Bulk search page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing bulk search page: {e}")
        return False

def test_bulk_search_api():
    """Test the bulk search API endpoint."""
    print("🧪 Testing bulk search API...")
    
    payload = {
        "search_entries": TEST_ENTRIES,
        "images_per_class": IMAGES_PER_CLASS,
        "destination_folder": ""
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/perform-bulk-search",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Bulk search API started successfully")
                print(f"📊 Processing {data.get('entries_count')} entries")
                print(f"🖼️ {data.get('images_per_class')} images per class")
                return True
            else:
                print(f"❌ Bulk search API returned error: {data.get('message')}")
                return False
        else:
            print(f"❌ Bulk search API failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error calling bulk search API: {e}")
        return False

def test_scraping_status():
    """Test the scraping status API."""
    print("🧪 Testing scraping status API...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/scraping_status")
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Scraping running: {data.get('is_running')}")
            print(f"📝 Progress: {data.get('progress', 'No progress info')}")
            return True
        else:
            print(f"❌ Scraping status API failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing scraping status API: {e}")
        return False

def monitor_bulk_search_progress():
    """Monitor the progress of bulk search."""
    print("🧪 Monitoring bulk search progress...")
    
    max_wait_time = 300  # 5 minutes max
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/api/scraping_status")
            if response.status_code == 200:
                data = response.json()
                is_running = data.get('is_running', False)
                progress = data.get('progress', 'No progress info')
                
                print(f"⏳ Status: {'Running' if is_running else 'Stopped'} | Progress: {progress}")
                
                if not is_running:
                    print("✅ Bulk search completed!")
                    return True
                
                time.sleep(5)  # Check every 5 seconds
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error monitoring progress: {e}")
            return False
    
    print("⏰ Timeout waiting for bulk search to complete")
    return False

def test_validation():
    """Test form validation."""
    print("🧪 Testing form validation...")
    
    # Test empty entries
    payload = {
        "search_entries": [],
        "images_per_class": 10,
        "destination_folder": ""
    }
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/perform-bulk-search",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'error' and 'No valid search entries' in data.get('message', ''):
                print("✅ Empty entries validation works")
            else:
                print(f"❌ Unexpected response for empty entries: {data}")
                return False
        else:
            print(f"❌ Validation test failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False
    
    # Test invalid images per class
    payload = {
        "search_entries": TEST_ENTRIES,
        "images_per_class": 1000,  # Too high
        "destination_folder": ""
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/perform-bulk-search",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'error' and 'between 1 and 500' in data.get('message', ''):
                print("✅ Images per class validation works")
                return True
            else:
                print(f"❌ Unexpected response for invalid images per class: {data}")
                return False
        else:
            print(f"❌ Validation test failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing validation: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting bulk search functionality tests...\n")
    
    tests = [
        ("Bulk Search Page", test_bulk_search_page),
        ("Form Validation", test_validation),
        ("Scraping Status API", test_scraping_status),
        ("Bulk Search API", test_bulk_search_api),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        result = test_func()
        results.append((test_name, result))
        
        if not result:
            print(f"❌ {test_name} failed!")
        else:
            print(f"✅ {test_name} passed!")
    
    # If bulk search started successfully, monitor it
    if results[-1][1]:  # If bulk search API test passed
        print(f"\n{'='*50}")
        print("Monitoring Bulk Search Progress")
        print('='*50)
        monitor_result = monitor_bulk_search_progress()
        results.append(("Progress Monitoring", monitor_result))
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bulk search functionality is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
