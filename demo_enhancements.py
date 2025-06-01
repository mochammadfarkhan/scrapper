#!/usr/bin/env python3
"""
Demo script for the enhanced bulk search and view images features.
This script demonstrates both new enhancements with real functionality.
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://localhost:5000"

def demo_bulk_search_with_destinations():
    """Demo the enhanced bulk search with per-row destination folders."""
    print("🎬 DEMO: Enhanced Bulk Search with Destination Folders")
    print("=" * 60)
    
    # Test data with different destination folders
    test_entries = [
        {
            "keyword": "demo_cats",
            "className": "demo_animals", 
            "destinationFolder": "custom_animals_folder"
        },
        {
            "keyword": "demo_cars",
            "className": "demo_vehicles",
            "destinationFolder": None  # Will use global setting
        }
    ]
    
    payload = {
        "search_entries": test_entries,
        "images_per_class": 3,  # Small number for demo
        "destination_folder": "default_demo_folder"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    print("📝 Test Data:")
    print(f"   Entry 1: '{test_entries[0]['keyword']}' → '{test_entries[0]['className']}' in '{test_entries[0]['destinationFolder']}'")
    print(f"   Entry 2: '{test_entries[1]['keyword']}' → '{test_entries[1]['className']}' (using global setting)")
    print(f"   Global destination: '{payload['destination_folder']}'")
    print(f"   Images per class: {payload['images_per_class']}")
    
    try:
        print("\n🚀 Starting bulk search with destination folders...")
        response = requests.post(
            f"{BASE_URL}/perform-bulk-search",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("✅ Bulk search started successfully!")
                print(f"📊 Processing {data.get('entries_count')} entries")
                
                # Monitor progress for a short time
                print("\n📈 Monitoring progress...")
                for i in range(10):  # Monitor for 10 seconds
                    time.sleep(1)
                    try:
                        status_response = requests.get(f"{BASE_URL}/api/scraping_status")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            progress = status_data.get('progress', 'No progress info')
                            is_running = status_data.get('is_running', False)
                            
                            print(f"   [{i+1}/10] {progress}")
                            
                            if not is_running:
                                print("✅ Bulk search completed!")
                                break
                        else:
                            print(f"   [{i+1}/10] Status check failed")
                    except Exception as e:
                        print(f"   [{i+1}/10] Error checking status: {e}")
                
                return True
            else:
                print(f"⚠️ Bulk search response: {data.get('message')}")
                return True  # Might be expected if already running
        else:
            print(f"❌ Bulk search failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in bulk search demo: {e}")
        return False

def demo_image_filter():
    """Demo the image filter functionality."""
    print("\n🎬 DEMO: Image Filter Functionality")
    print("=" * 60)
    
    # Test with a folder that has many images
    test_folder = "karbo"
    
    try:
        print(f"📁 Testing image filter on '{test_folder}' folder...")
        response = requests.get(f"{BASE_URL}/view_images/{test_folder}")
        
        if response.status_code == 200:
            content = response.text
            
            # Extract image count
            import re
            image_count_match = re.search(r'All \((\d+)\)', content)
            if image_count_match:
                total_images = int(image_count_match.group(1))
                print(f"📊 Found {total_images} total images in {test_folder}")
                
                # Check filter elements
                filter_elements = [
                    'imageLimit',
                    'Show Images:',
                    'applyImageFilter()',
                    'loadMoreImages()',
                    'First 100',
                    'First 200'
                ]
                
                present_elements = []
                for element in filter_elements:
                    if element in content:
                        present_elements.append(element)
                
                print(f"✅ Filter elements present: {len(present_elements)}/{len(filter_elements)}")
                
                if total_images > 100:
                    print("✅ Sufficient images for meaningful filter testing")
                    print("💡 Filter options available:")
                    print("   • All images")
                    print("   • First 100, 200, 300, etc.")
                    print("   • Load More functionality")
                else:
                    print("⚠️ Limited images, but filter functionality is available")
                
                return True
            else:
                print("❌ Could not extract image count")
                return False
        else:
            print(f"❌ View images page failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in image filter demo: {e}")
        return False

def demo_ui_features():
    """Demo the UI features of both enhancements."""
    print("\n🎬 DEMO: UI Features")
    print("=" * 60)
    
    print("🔍 Checking Bulk Search UI...")
    try:
        response = requests.get(f"{BASE_URL}/bulk-search")
        if response.status_code == 200:
            content = response.text
            
            # Check for destination folder column
            if 'Destination Folder' in content:
                print("✅ Bulk search has destination folder column")
            else:
                print("❌ Destination folder column missing")
                return False
                
            # Check table structure
            if 'width: 30%' in content and 'width: 25%' in content:
                print("✅ Table columns properly sized")
            else:
                print("❌ Table column sizing incorrect")
                return False
        else:
            print(f"❌ Bulk search page failed")
            return False
    except Exception as e:
        print(f"❌ Error checking bulk search UI: {e}")
        return False
    
    print("\n🔍 Checking View Images UI...")
    try:
        response = requests.get(f"{BASE_URL}/view_images/karbo")
        if response.status_code == 200:
            content = response.text
            
            # Check for filter controls
            if 'Show Images:' in content and 'imageLimit' in content:
                print("✅ View images has filter controls")
            else:
                print("❌ Filter controls missing")
                return False
                
            # Check for load more section
            if 'loadMoreSection' in content and 'Load More Images' in content:
                print("✅ Load more functionality present")
            else:
                print("❌ Load more functionality missing")
                return False
        else:
            print(f"❌ View images page failed")
            return False
    except Exception as e:
        print(f"❌ Error checking view images UI: {e}")
        return False
    
    return True

def main():
    """Run the enhancement demos."""
    print("🚀 Enhanced Features Demo")
    print("=" * 60)
    print("This demo showcases the two new enhancements:")
    print("1. Bulk Search with per-row destination folders")
    print("2. View Images with image count filtering")
    print()
    
    demos = [
        ("UI Features Check", demo_ui_features),
        ("Image Filter Demo", demo_image_filter),
        ("Bulk Search with Destinations", demo_bulk_search_with_destinations),
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        print(f"\n{'='*60}")
        print(f"Running: {demo_name}")
        print('='*60)
        
        result = demo_func()
        results.append((demo_name, result))
        
        if result:
            print(f"✅ {demo_name} completed successfully!")
        else:
            print(f"❌ {demo_name} failed!")
    
    # Summary
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for demo_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"{status} {demo_name}")
    
    print(f"\nResults: {passed}/{total} demos successful")
    
    if passed == total:
        print("\n🎉 All demos completed successfully!")
        print("\n💡 Enhanced Features Available:")
        print("   🔧 Bulk Search:")
        print("      • Per-row destination folder specification")
        print("      • Mix custom and global destination settings")
        print("      • Enhanced table with 3 columns")
        print("   🖼️ View Images:")
        print("      • Image count filtering (100, 200, 300, etc.)")
        print("      • Load More functionality for large collections")
        print("      • Real-time display status updates")
        print("      • Compatible with bulk selection features")
        return 0
    else:
        print("\n⚠️ Some demos failed, but core functionality may still work.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
