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
from logger import scraping_logger

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
            scraping_logger.info("🚀 Initializing Chrome WebDriver...")

            chrome_options = Options()

            # Essential options for stability
            if self.headless:
                chrome_options.add_argument("--headless")
                scraping_logger.debug("✓ Headless mode enabled")
            else:
                scraping_logger.debug("✓ GUI mode enabled")

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

            scraping_logger.debug("✓ Chrome options configured")

            # Install and setup ChromeDriver
            scraping_logger.info("📥 Installing/updating ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            scraping_logger.debug(f"✓ ChromeDriver path: {driver_path}")

            service = Service(driver_path)
            scraping_logger.info("🌐 Starting Chrome browser...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            scraping_logger.success("✅ WebDriver initialized successfully!")
            scraping_logger.debug(f"✓ Browser version: {self.driver.capabilities.get('browserVersion', 'Unknown')}")
            scraping_logger.debug(f"✓ Driver version: {self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'Unknown')}")

        except Exception as e:
            error_msg = f"❌ Error setting up WebDriver: {str(e)}"
            scraping_logger.error(error_msg)
            raise Exception(error_msg)

    def search_images(self, query, max_images=20):
        """Search for images on Google Images and extract image URLs."""
        if not self.driver:
            error_msg = "❌ WebDriver not initialized"
            scraping_logger.error(error_msg)
            raise Exception(error_msg)

        try:
            # Navigate to Google Images
            search_url = f"https://www.google.com/search?q={query}&tbm=isch&hl=en"
            scraping_logger.info(f"🔍 Starting image search for: '{query}'")
            scraping_logger.info(f"🌐 Navigating to: {search_url}")
            scraping_logger.debug(f"✓ Target images: {max_images}")

            self.driver.get(search_url)

            # Wait for page to load
            scraping_logger.debug("⏳ Waiting for page to load...")
            time.sleep(2)

            # Accept cookies if present
            scraping_logger.debug("🍪 Checking for cookie consent dialog...")
            try:
                accept_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept all') or contains(text(), 'I agree') or contains(text(), 'Accept')]"))
                )
                accept_button.click()
                scraping_logger.info("✅ Cookie consent accepted")
                time.sleep(1)
            except TimeoutException:
                scraping_logger.debug("✓ No cookie consent dialog found or already accepted")

            image_urls = set()  # Use set to avoid duplicates
            scroll_attempts = 0
            max_scroll_attempts = 10

            scraping_logger.info(f"🔄 Starting image extraction (max {max_scroll_attempts} scroll attempts)")

            while len(image_urls) < max_images and scroll_attempts < max_scroll_attempts:
                scroll_attempts += 1
                scraping_logger.debug(f"📜 Scroll attempt {scroll_attempts}/{max_scroll_attempts}")

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
                        scraping_logger.debug(f"🔍 Found {len(image_elements)} elements with selector: {selector}")

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
                                scraping_logger.debug(f"✅ Added image URL: {img_url[:80]}...")

                    current_count = len(image_urls)
                    scraping_logger.info(f"📊 Current image count: {current_count}/{max_images}")

                    # Scroll down to load more images
                    scraping_logger.debug("📜 Scrolling to load more images...")
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
            scraping_logger.debug(f"📥 Downloading: {url[:80]}...")

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
            scraping_logger.debug(f"✓ Content-Type: {content_type}")

            if not content_type.startswith('image/'):
                scraping_logger.warning(f"⚠️ URL does not contain image data: {url[:80]}...")
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
            scraping_logger.debug(f"🔍 Validating image: {filename}")
            if validate_image(file_path):
                # Check file size (minimum 1KB to filter out tiny images)
                file_size = os.path.getsize(file_path)
                scraping_logger.debug(f"✓ File size: {file_size} bytes")

                if file_size > 1024:
                    scraping_logger.success(f"✅ Successfully downloaded: {filename}")
                    return filename
                else:
                    scraping_logger.warning(f"⚠️ Image too small ({file_size} bytes), removing: {filename}")
                    os.remove(file_path)
                    return None
            else:
                scraping_logger.warning(f"⚠️ Invalid image file, removing: {filename}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return None

        except requests.exceptions.RequestException as e:
            scraping_logger.error(f"🌐 Network error downloading image: {str(e)}")
            return None
        except Exception as e:
            scraping_logger.error(f"❌ Error downloading image: {str(e)}")
            return None

    def scrape_images(self, query, destination_folder, class_name, max_images=20, progress_callback=None):
        """Main method to scrape images."""
        try:
            scraping_logger.info(f"🚀 Starting scraping session")
            scraping_logger.info(f"📝 Query: '{query}', Class: '{class_name}', Max Images: {max_images}")

            # Create class folder
            class_folder = create_class_folder(destination_folder, class_name)
            scraping_logger.info(f"📁 Created/using folder: {class_folder}")

            # Search for images
            if progress_callback:
                progress_callback(f"Searching for images: {query}")

            scraping_logger.info(f"🔍 Starting image URL extraction...")
            image_urls = self.search_images(query, max_images)

            if progress_callback:
                progress_callback(f"Found {len(image_urls)} images. Starting download...")

            scraping_logger.info(f"📊 Found {len(image_urls)} image URLs, starting downloads...")

            downloaded_count = 0
            failed_count = 0

            for i, url in enumerate(image_urls):
                if progress_callback:
                    progress_callback(f"Downloading image {i+1}/{len(image_urls)}")

                scraping_logger.info(f"📥 Downloading image {i+1}/{len(image_urls)}")
                filename = self.download_image(url, class_folder, class_name)

                if filename:
                    downloaded_count += 1
                    scraping_logger.debug(f"✅ Success: {filename}")
                else:
                    failed_count += 1
                    scraping_logger.debug(f"❌ Failed: {url[:50]}...")

                time.sleep(0.5)  # Be respectful to the server

            success_msg = f"✅ Download complete! {downloaded_count} images saved, {failed_count} failed"
            scraping_logger.success(success_msg)
            scraping_logger.info(f"📁 Images saved to: {class_folder}")

            if progress_callback:
                progress_callback(f"Download complete! {downloaded_count} images saved to {class_folder}")

            return downloaded_count, class_folder

        except Exception as e:
            error_msg = f"❌ Error during scraping: {str(e)}"
            scraping_logger.error(error_msg)
            if progress_callback:
                progress_callback(error_msg)
            return 0, None

    def close(self):
        """Close the WebDriver and session."""
        try:
            if hasattr(self, 'driver') and self.driver:
                scraping_logger.info("🔒 Closing WebDriver...")
                self.driver.quit()
                self.driver = None
                scraping_logger.success("✅ WebDriver closed successfully")
        except Exception as e:
            scraping_logger.error(f"❌ Error closing WebDriver: {str(e)}")

        try:
            if hasattr(self, 'session') and self.session:
                scraping_logger.debug("🔒 Closing HTTP session...")
                self.session.close()
                scraping_logger.debug("✅ HTTP session closed")
        except Exception as e:
            scraping_logger.error(f"❌ Error closing session: {str(e)}")

    def __del__(self):
        """Destructor to ensure WebDriver is closed."""
        self.close()
