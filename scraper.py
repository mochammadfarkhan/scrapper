import requests
import os
import time
import hashlib
from urllib.parse import urlparse
from PIL import Image
import io
from utils import create_class_folder, validate_image, generate_unique_filename

class GoogleImageScraper:
    def __init__(self, headless=True):
        # For now, we'll use a simple approach without Selenium
        # This is a demo version that uses placeholder images
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search_images(self, query, max_images=20):
        """Search for images - Demo version with placeholder images."""
        # For demonstration purposes, we'll use placeholder images
        # In a real implementation, you would parse Google Images results

        # Using placeholder image service for demo
        image_urls = []
        for i in range(min(max_images, 10)):  # Limit to 10 for demo
            # Different placeholder services and sizes for variety
            services = [
                f"https://picsum.photos/400/300?random={hash(query + str(i)) % 1000}",
                f"https://via.placeholder.com/400x300/0066cc/ffffff?text={query.replace(' ', '+')}+{i+1}",
                f"https://dummyimage.com/400x300/ff6b6b/ffffff&text={query.replace(' ', '+')}+{i+1}",
            ]
            image_urls.append(services[i % len(services)])

        return image_urls

    def download_image(self, url, folder_path, filename_prefix="image"):
        """Download a single image from URL."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Try to determine file extension from URL or content type
            parsed_url = urlparse(url)
            ext = os.path.splitext(parsed_url.path)[1]
            if not ext:
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default

            # Generate unique filename
            base_filename = f"{filename_prefix}_{hashlib.md5(url.encode()).hexdigest()[:8]}{ext}"
            filename = generate_unique_filename(base_filename, folder_path)
            file_path = os.path.join(folder_path, filename)

            # Save image
            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Validate image (skip validation for demo placeholder images)
            if 'placeholder' in url or 'picsum' in url or 'dummyimage' in url:
                return filename
            elif validate_image(file_path):
                return filename
            else:
                os.remove(file_path)
                return None

        except Exception as e:
            print(f"Error downloading image from {url}: {str(e)}")
            return None

    def scrape_images(self, query, destination_folder, class_name, max_images=20, progress_callback=None):
        """Main method to scrape images."""
        try:
            # Create class folder
            class_folder = create_class_folder(destination_folder, class_name)

            # Search for images
            if progress_callback:
                progress_callback(f"Searching for images: {query}")

            image_urls = self.search_images(query, max_images)

            if progress_callback:
                progress_callback(f"Found {len(image_urls)} images. Starting download...")

            downloaded_count = 0
            for i, url in enumerate(image_urls):
                if progress_callback:
                    progress_callback(f"Downloading image {i+1}/{len(image_urls)}")

                filename = self.download_image(url, class_folder, class_name)
                if filename:
                    downloaded_count += 1

                time.sleep(0.5)  # Be respectful to the server

            if progress_callback:
                progress_callback(f"Download complete! {downloaded_count} images saved to {class_folder}")

            return downloaded_count, class_folder

        except Exception as e:
            error_msg = f"Error during scraping: {str(e)}"
            if progress_callback:
                progress_callback(error_msg)
            return 0, None

    def close(self):
        """Close the session."""
        if hasattr(self, 'session'):
            self.session.close()
