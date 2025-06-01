#!/usr/bin/env python3
"""
Demo script for the enhanced image management functionality.
This script demonstrates the bulk operations with real images.
"""

import requests
import json
import sys
import os

# Configuration
BASE_URL = "http://localhost:5000"

def get_real_images_from_folder(folder_name):
    """Get actual image filenames from a folder by parsing the view page."""
    print(f"🔍 Getting real images from {folder_name} folder...")
    
    try:
        response = requests.get(f"{BASE_URL}/view_images/{folder_name}")
        if response.status_code == 200:
            content = response.text
            
            # Simple parsing to find image filenames
            # Look for data-filename attributes
            import re
            pattern = r'data-filename="([^"]+)"'
            matches = re.findall(pattern, content)
            
            if matches:
                print(f"✅ Found {len(matches)} images in {folder_name}")
                return matches[:3]  # Return first 3 for demo
            else:
                print(f"⚠️ No images found in {folder_name}")
                return []
        else:
            print(f"❌ Could not access {folder_name} folder")
            return []
    except Exception as e:
        print(f"❌ Error getting images from {folder_name}: {e}")
        return []

def demo_create_folder():
    """Demo: Create a new folder for testing."""
    print("\n🎬 DEMO: Creating a new folder...")
    
    folder_name = "demo_destination"
    
    payload = {
        "folder_name": folder_name
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/create-folder",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"✅ Created folder: {folder_name}")
                return folder_name
            else:
                print(f"❌ Failed to create folder: {data.get('message')}")
                return None
        else:
            print(f"❌ Create folder failed with status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        return None

def demo_move_images(source_folder, destination_folder, image_filenames):
    """Demo: Move real images between folders."""
    print(f"\n🎬 DEMO: Moving {len(image_filenames)} images from {source_folder} to {destination_folder}...")
    
    # Convert filenames to relative paths
    image_paths = [f"{source_folder}/{filename}" for filename in image_filenames]
    
    payload = {
        "images": image_paths,
        "destination_folder": destination_folder,
        "source_folder": source_folder,
        "create_new": False
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/move-images",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                moved_count = data.get('moved_count', 0)
                print(f"✅ Successfully moved {moved_count} images")
                print(f"📁 Images moved to: {destination_folder}")
                return True
            else:
                print(f"❌ Move failed: {data.get('message')}")
                return False
        else:
            print(f"❌ Move request failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error moving images: {e}")
        return False

def demo_verify_move(destination_folder):
    """Demo: Verify images were moved successfully."""
    print(f"\n🔍 DEMO: Verifying images in {destination_folder}...")
    
    moved_images = get_real_images_from_folder(destination_folder)
    if moved_images:
        print(f"✅ Verification successful - Found {len(moved_images)} images in destination")
        for img in moved_images:
            print(f"   📷 {img}")
        return True
    else:
        print(f"⚠️ No images found in destination folder")
        return False

def demo_move_back(destination_folder, source_folder):
    """Demo: Move images back to original folder."""
    print(f"\n🎬 DEMO: Moving images back from {destination_folder} to {source_folder}...")
    
    # Get images from destination folder
    image_filenames = get_real_images_from_folder(destination_folder)
    if not image_filenames:
        print("⚠️ No images to move back")
        return False
    
    # Move them back
    image_paths = [f"{destination_folder}/{filename}" for filename in image_filenames]
    
    payload = {
        "images": image_paths,
        "destination_folder": source_folder,
        "source_folder": destination_folder,
        "create_new": False
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/move-images",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                moved_count = data.get('moved_count', 0)
                print(f"✅ Successfully moved {moved_count} images back to {source_folder}")
                return True
            else:
                print(f"❌ Move back failed: {data.get('message')}")
                return False
        else:
            print(f"❌ Move back request failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error moving images back: {e}")
        return False

def cleanup_demo_folder(folder_name):
    """Clean up the demo folder."""
    print(f"\n🧹 DEMO: Cleaning up {folder_name}...")
    
    try:
        payload = {"folder_name": folder_name}
        headers = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/delete_folder",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ Cleaned up demo folder: {folder_name}")
        else:
            print(f"⚠️ Could not clean up demo folder")
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")

def main():
    """Run the demo."""
    print("🎬 Enhanced Image Management - Live Demo")
    print("=" * 50)
    
    # Choose a source folder with images
    source_folder = "karbo"  # This folder has many images
    
    # Step 1: Get real images from source folder
    print(f"\n📋 Step 1: Getting images from {source_folder}")
    image_filenames = get_real_images_from_folder(source_folder)
    
    if not image_filenames:
        print("❌ No images found for demo. Please run bulk search first to create some images.")
        return 1
    
    print(f"📷 Demo will use these images:")
    for img in image_filenames:
        print(f"   • {img}")
    
    # Step 2: Create destination folder
    print(f"\n📋 Step 2: Creating destination folder")
    destination_folder = demo_create_folder()
    
    if not destination_folder:
        print("❌ Could not create destination folder")
        return 1
    
    # Step 3: Move images
    print(f"\n📋 Step 3: Moving images")
    move_success = demo_move_images(source_folder, destination_folder, image_filenames)
    
    if not move_success:
        cleanup_demo_folder(destination_folder)
        return 1
    
    # Step 4: Verify move
    print(f"\n📋 Step 4: Verifying move")
    verify_success = demo_verify_move(destination_folder)
    
    # Step 5: Move back (to restore original state)
    print(f"\n📋 Step 5: Moving images back to restore original state")
    move_back_success = demo_move_back(destination_folder, source_folder)
    
    # Step 6: Cleanup
    print(f"\n📋 Step 6: Cleanup")
    cleanup_demo_folder(destination_folder)
    
    # Summary
    print(f"\n{'='*50}")
    print("🎬 DEMO SUMMARY")
    print('='*50)
    
    steps = [
        ("Get Images", bool(image_filenames)),
        ("Create Folder", bool(destination_folder)),
        ("Move Images", move_success),
        ("Verify Move", verify_success),
        ("Move Back", move_back_success)
    ]
    
    for step_name, success in steps:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {step_name}")
    
    all_success = all(success for _, success in steps)
    
    if all_success:
        print("\n🎉 Demo completed successfully! Enhanced image management is working perfectly.")
        print("\n💡 You can now:")
        print("   • Visit any folder's view images page")
        print("   • Select multiple images by clicking on them")
        print("   • Use bulk move and delete operations")
        print("   • Create new folders on the fly")
        return 0
    else:
        print("\n⚠️ Some demo steps failed, but this might be expected in a test environment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
