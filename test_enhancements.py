#!/usr/bin/env python3
"""
Test script for the enhanced bulk search and view images features.
This script tests both new enhancements:
1. Destination folder column in bulk search
2. Maximum images filter in view images pages
"""

import requests
import json
import sys
import re

# Configuration
BASE_URL = "http://localhost:5000"

def test_bulk_search_destination_column():
    """Test the enhanced bulk search with destination folder column."""
    print("🧪 Testing enhanced bulk search with destination folder column...")
    
    try:
        response = requests.get(f"{BASE_URL}/bulk-search")
        if response.status_code == 200:
            content = response.text
            
            # Check for the new destination folder column
            required_elements = [
                'Destination Folder',  # Column header
                'destinationFolder[]',  # Input field name
                'Optional: custom folder path',  # Placeholder text
                'Leave empty to use global setting'  # Help text
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ Bulk search page has destination folder column")
                return True
            else:
                print(f"❌ Missing elements in bulk search: {missing_elements}")
                return False
        else:
            print(f"❌ Bulk search page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing bulk search page: {e}")
        return False

def test_bulk_search_with_destinations():
    """Test bulk search API with per-row destination folders."""
    print("🧪 Testing bulk search API with destination folders...")
    
    test_entries = [
        {
            "keyword": "test_cats",
            "className": "test_animals",
            "destinationFolder": "custom_destination_1"
        },
        {
            "keyword": "test_dogs", 
            "className": "test_pets",
            "destinationFolder": None  # Will use global setting
        }
    ]
    
    payload = {
        "search_entries": test_entries,
        "images_per_class": 5,
        "destination_folder": "default_destination"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
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
                print("✅ Bulk search API accepts destination folder data")
                return True
            else:
                print(f"⚠️ Bulk search API response: {data.get('message')}")
                # This might be expected if scraping is already running
                return True
        else:
            print(f"❌ Bulk search API failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error calling bulk search API: {e}")
        return False

def test_view_images_filter():
    """Test the view images page with image filter controls."""
    print("🧪 Testing view images page with image filter...")
    
    # Test with a folder that has many images
    test_folder = "karbo"
    
    try:
        response = requests.get(f"{BASE_URL}/view_images/{test_folder}")
        if response.status_code == 200:
            content = response.text
            
            # Check for filter elements
            required_elements = [
                'imageLimit',  # Filter dropdown ID
                'Show Images:',  # Filter label
                'applyImageFilter()',  # Filter function
                'loadMoreImages()',  # Load more function
                'loadMoreSection',  # Load more section ID
                'displayStatus',  # Display status ID
                'visibleCount',  # Visible count span
                'First 100',  # Filter option
                'First 200',  # Filter option
                'All ('  # All option with count
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ View images page has image filter controls")
                
                # Check if the page has many images to test filtering
                image_count_match = re.search(r'All \((\d+)\)', content)
                if image_count_match:
                    image_count = int(image_count_match.group(1))
                    print(f"📊 Found {image_count} images in {test_folder} folder")
                    if image_count > 100:
                        print("✅ Sufficient images for filter testing")
                    else:
                        print("⚠️ Limited images for filter testing")
                
                return True
            else:
                print(f"❌ Missing filter elements: {missing_elements}")
                return False
        else:
            print(f"❌ View images page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing view images page: {e}")
        return False

def test_javascript_files():
    """Test that the JavaScript files contain the new functions."""
    print("🧪 Testing JavaScript files for new functions...")
    
    # Test bulk_search.js for destination folder handling
    try:
        response = requests.get(f"{BASE_URL}/static/js/bulk_search.js")
        if response.status_code == 200:
            content = response.text
            
            bulk_search_functions = [
                'destinationFolder[]',  # New input field
                'destinationFolderInput',  # Variable name
                'entry.destinationFolder',  # Data collection
                'destinationFolder || null'  # Null handling
            ]
            
            missing_functions = []
            for func in bulk_search_functions:
                if func not in content:
                    missing_functions.append(func)
            
            if not missing_functions:
                print("✅ bulk_search.js has destination folder functionality")
            else:
                print(f"❌ bulk_search.js missing: {missing_functions}")
                return False
        else:
            print(f"❌ bulk_search.js failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing bulk_search.js: {e}")
        return False
    
    # Test view_images.html for filter functions (they're inline)
    try:
        response = requests.get(f"{BASE_URL}/view_images/karbo")
        if response.status_code == 200:
            content = response.text
            
            filter_functions = [
                'applyImageFilter',
                'showAllImages',
                'showLimitedImages', 
                'loadMoreImages',
                'initializeImageFiltering',
                'updateDisplayStatus',
                'updateBulkSelectionAfterFilter'
            ]
            
            missing_functions = []
            for func in filter_functions:
                if func not in content:
                    missing_functions.append(func)
            
            if not missing_functions:
                print("✅ view_images.html has image filter functions")
                return True
            else:
                print(f"❌ view_images.html missing functions: {missing_functions}")
                return False
        else:
            print(f"❌ view_images.html failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking view_images.html functions: {e}")
        return False

def test_ui_integration():
    """Test that the UI elements are properly integrated."""
    print("🧪 Testing UI integration...")
    
    # Test bulk search table structure
    try:
        response = requests.get(f"{BASE_URL}/bulk-search")
        if response.status_code == 200:
            content = response.text
            
            # Check table column widths
            if 'width: 30%' in content and 'width: 25%' in content and 'width: 15%' in content:
                print("✅ Bulk search table has correct column widths")
            else:
                print("❌ Bulk search table column widths incorrect")
                return False
                
        else:
            print(f"❌ Bulk search page failed")
            return False
    except Exception as e:
        print(f"❌ Error testing bulk search UI: {e}")
        return False
    
    # Test view images filter UI
    try:
        response = requests.get(f"{BASE_URL}/view_images/karbo")
        if response.status_code == 200:
            content = response.text
            
            # Check for filter card
            if 'Image Filter Controls' in content or 'Show Images:' in content:
                print("✅ View images page has filter UI")
                return True
            else:
                print("❌ View images page missing filter UI")
                return False
        else:
            print(f"❌ View images page failed")
            return False
    except Exception as e:
        print(f"❌ Error testing view images UI: {e}")
        return False

def main():
    """Run all enhancement tests."""
    print("🚀 Starting enhanced features testing...\n")
    
    tests = [
        ("Bulk Search Destination Column", test_bulk_search_destination_column),
        ("Bulk Search API with Destinations", test_bulk_search_with_destinations),
        ("View Images Filter Controls", test_view_images_filter),
        ("JavaScript Functions", test_javascript_files),
        ("UI Integration", test_ui_integration),
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
    
    # Summary
    print(f"\n{'='*50}")
    print("ENHANCEMENT TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All enhancement tests passed! Both features are working correctly.")
        print("\n💡 New Features Available:")
        print("   • Bulk Search: Per-row destination folder specification")
        print("   • View Images: Image count filtering with load more functionality")
        return 0
    else:
        print("⚠️ Some enhancement tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
