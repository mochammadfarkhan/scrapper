import requests
import os
import time
import hashlib
import json
import re
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
from utils import create_class_folder, validate_image, generate_unique_filename

class GoogleImageScraper:
    def __init__(self, headless=True):
        """Initialize the Google Images scraper with Selenium WebDriver."""
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()

            # Essential options for stability
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Don't load images in browser for faster loading
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Performance optimizations
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")

            # Install and setup ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            print("WebDriver initialized successfully")

        except Exception as e:
            print(f"Error setting up WebDriver: {str(e)}")
            raise

    def search_images(self, query, max_images=20):
        """Search for images on Google Images and extract image URLs."""
        if not self.driver:
            raise Exception("WebDriver not initialized")

        try:
            # Navigate to Google Images
            search_url = f"https://www.google.com/search?q={query}&tbm=isch&hl=en"
            print(f"Navigating to: {search_url}")
            self.driver.get(search_url)

            # Wait for page to load
            time.sleep(2)

            # Accept cookies if present
            try:
                accept_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'I agree') or contains(text(), 'Accept')]"))
                )
                accept_button.click()
                time.sleep(1)
            except TimeoutException:
                print("No cookie consent dialog found or already accepted")

            image_urls = set()  # Use set to avoid duplicates
            scroll_attempts = 0
            max_scroll_attempts = 10

            while len(image_urls) < max_images and scroll_attempts < max_scroll_attempts:
                # Find image elements using multiple selectors
                try:
                    # Multiple CSS selectors to catch different image formats
                    selectors = [
                        "img[data-src]",
                        "img[src]",
                        "div[data-tbnid] img",
                        ".rg_i",
                        ".Q4LuWd img"
                    ]

                    for selector in selectors:
                        if len(image_urls) >= max_images:
                            break

                        image_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        print(f"Found {len(image_elements)} elements with selector: {selector}")

                        for img_element in image_elements:
                            if len(image_urls) >= max_images:
                                break

                            # Try multiple attributes for image URL
                            img_url = (img_element.get_attribute("data-src") or
                                     img_element.get_attribute("src") or
                                     img_element.get_attribute("data-iurl") or
                                     img_element.get_attribute("data-original"))

                            if img_url and self._is_valid_image_url(img_url):
                                image_urls.add(img_url)
                                print(f"Added image URL: {img_url[:100]}...")

                    print(f"Current image count: {len(image_urls)}")

                    # Scroll down to load more images
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)

                    # Try to click "Show more results" button if available
                    try:
                        show_more_selectors = [
                            "//input[@value='Show more results']",
                            "//div[contains(text(), 'Show more results')]",
                            ".mye4qd"
                        ]

                        for selector in show_more_selectors:
                            try:
                                if selector.startswith("//"):
                                    show_more_button = self.driver.find_element(By.XPATH, selector)
                                else:
                                    show_more_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                                if show_more_button.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", show_more_button)
                                    time.sleep(3)
                                    break
                            except NoSuchElementException:
                                continue
                    except Exception:
                        pass

                    scroll_attempts += 1

                except Exception as e:
                    print(f"Error during image extraction: {str(e)}")
                    scroll_attempts += 1

            final_urls = list(image_urls)[:max_images]
            print(f"Found {len(final_urls)} image URLs for query: {query}")
            return final_urls

        except Exception as e:
            print(f"Error searching for images: {str(e)}")
            return []

    def _is_valid_image_url(self, url):
        """Check if the URL is a valid image URL."""
        if not url or not url.startswith(('http://', 'https://')):
            return False

        # Filter out Google's own images and icons (but allow some encrypted thumbnails)
        invalid_patterns = [
            'google.com/images/branding',
            'gstatic.com/images/icons',
            'data:image/svg',
            'logo.png',
            'favicon'
        ]

        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False

        # Check for common image extensions or image-like URLs
        valid_patterns = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',
            'imgurl=', 'image', 'photo', 'picture', 'media',
            'encrypted-tbn0.gstatic.com',  # Allow Google's encrypted thumbnails
            'upload.wikimedia.org',
            'cdn.',
            'imgur.com'
        ]

        # More permissive - if it looks like it could be an image, allow it
        return any(pattern in url_lower for pattern in valid_patterns) or len(url) > 50

    def _extract_high_res_images(self, image_urls, max_images):
        """Try to extract higher resolution images by clicking on thumbnails."""
        try:
            # Find clickable image thumbnails
            thumbnails = self.driver.find_elements(By.CSS_SELECTOR, "img[data-src]")[:5]  # Limit to first 5 for performance

            for thumbnail in thumbnails:
                if len(image_urls) >= max_images:
                    break

                try:
                    # Click on thumbnail to get larger image
                    self.driver.execute_script("arguments[0].click();", thumbnail)
                    time.sleep(1)

                    # Look for the larger image
                    large_images = self.driver.find_elements(By.CSS_SELECTOR, "img[src*='http']")
                    for large_img in large_images:
                        img_url = large_img.get_attribute("src")
                        if img_url and self._is_valid_image_url(img_url) and 'encrypted-tbn' not in img_url:
                            image_urls.add(img_url)
                            break

                except Exception as e:
                    continue  # Skip this thumbnail if there's an error

        except Exception as e:
            print(f"Error extracting high-res images: {str(e)}")

    def download_image(self, url, folder_path, filename_prefix="image"):
        """Download a single image from URL."""
        try:
            # Add additional headers to mimic a real browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            response = self.session.get(url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()

            # Check if the response contains image data
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                print(f"URL does not contain image data: {url}")
                return None

            # Try to determine file extension from URL or content type
            parsed_url = urlparse(url)
            ext = os.path.splitext(parsed_url.path)[1].lower()

            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                elif 'bmp' in content_type:
                    ext = '.bmp'
                else:
                    ext = '.jpg'  # Default

            # Generate unique filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            base_filename = f"{filename_prefix}_{url_hash}{ext}"
            filename = generate_unique_filename(base_filename, folder_path)
            file_path = os.path.join(folder_path, filename)

            # Download and save image in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Validate the downloaded image
            if validate_image(file_path):
                # Check file size (minimum 1KB to filter out tiny images)
                if os.path.getsize(file_path) > 1024:
                    print(f"Successfully downloaded: {filename}")
                    return filename
                else:
                    print(f"Image too small, removing: {filename}")
                    os.remove(file_path)
                    return None
            else:
                print(f"Invalid image file, removing: {filename}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None

        except requests.exceptions.RequestException as e:
            print(f"Network error downloading image from {url}: {str(e)}")
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
        """Close the WebDriver and session."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.driver = None
                print("WebDriver closed successfully")
        except Exception as e:
            print(f"Error closing WebDriver: {str(e)}")

        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
        except Exception as e:
            print(f"Error closing session: {str(e)}")

    def __del__(self):
        """Destructor to ensure WebDriver is closed."""
        self.close()
