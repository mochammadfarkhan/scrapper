#!/usr/bin/env python3
"""
Test script for the Google Images scraper functionality.
"""

import os
import sys
from scraper import GoogleImageScraper

def test_scraper():
    """Test the Google Images scraper with a simple query."""
    print("Testing Google Images Scraper...")
    
    # Create test directory
    test_dir = "test_images"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    scraper = None
    try:
        # Initialize scraper
        print("Initializing scraper...")
        scraper = GoogleImageScraper(headless=True)
        
        # Test search
        query = "cats"
        max_images = 3  # Small number for testing
        
        print(f"Searching for '{query}' images...")
        
        def progress_callback(message):
            print(f"Progress: {message}")
        
        # Test the scraping process
        downloaded_count, class_folder = scraper.scrape_images(
            query=query,
            destination_folder=test_dir,
            class_name="test_cats",
            max_images=max_images,
            progress_callback=progress_callback
        )
        
        print(f"\nTest completed!")
        print(f"Downloaded {downloaded_count} images")
        print(f"Images saved to: {class_folder}")
        
        # List downloaded files
        if class_folder and os.path.exists(class_folder):
            files = os.listdir(class_folder)
            print(f"Files in folder: {files}")
        
        return downloaded_count > 0
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        return False
    
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\n✅ Test PASSED - Real Google Images scraping is working!")
    else:
        print("\n❌ Test FAILED - Check the error messages above")
    
    sys.exit(0 if success else 1)
