#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Flask Image Scraper Application

This test suite covers:
1. ScrapingLogger class functionality
2. Flask API endpoints
3. Google Images scraper functionality
4. Integration tests for complete workflow
5. Error handling and edge cases

Run with: python -m pytest test_scraper.py -v
"""

import pytest
import json
import tempfile
import shutil
import os
import time
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import requests

# Import the application modules
from app import app, scraping_logger, scraping_status
from scraper import GoogleImageScraper
from logger import ScrapingLogger


class TestScrapingLogger:
    """Test suite for the ScrapingLogger class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.logger = ScrapingLogger()
        self.logger.clear_logs()

    def test_logger_initialization(self):
        """Test logger initialization."""
        assert self.logger.log_history == []
        assert hasattr(self.logger, 'lock')

    def test_log_creation(self):
        """Test basic log entry creation."""
        self.logger.info("Test message")
        logs = self.logger.get_logs()

        assert len(logs) == 1
        assert logs[0]['level'] == 'INFO'
        assert logs[0]['message'] == 'Test message'
        assert 'timestamp' in logs[0]

    def test_different_log_levels(self):
        """Test all log levels."""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.success("Success message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")

        logs = self.logger.get_logs()
        assert len(logs) == 5

        levels = [log['level'] for log in logs]
        assert 'DEBUG' in levels
        assert 'INFO' in levels
        assert 'SUCCESS' in levels
        assert 'WARNING' in levels
        assert 'ERROR' in levels

    def test_log_formatting(self):
        """Test log formatting for display."""
        self.logger.info("Test message")
        logs = self.logger.get_logs()

        formatted = self.logger.format_log_for_display(logs[0])
        assert logs[0]['timestamp'] in formatted
        assert '[INFO]' in formatted
        assert 'Test message' in formatted

    def test_log_export(self):
        """Test log export functionality."""
        self.logger.info("Message 1")
        self.logger.error("Message 2")

        export_text = self.logger.export_logs_to_text()

        assert 'GOOGLE IMAGES SCRAPER - SESSION LOGS' in export_text
        assert 'Total Log Entries: 2' in export_text
        assert '[INFO] Message 1' in export_text
        assert '[ERROR] Message 2' in export_text

    def test_clear_logs(self):
        """Test log clearing functionality."""
        self.logger.info("Test message")
        assert len(self.logger.get_logs()) == 1

        self.logger.clear_logs()
        assert len(self.logger.get_logs()) == 0

    def test_thread_safety(self):
        """Test thread safety of logger."""
        import threading

        def add_logs():
            for i in range(10):
                self.logger.info(f"Thread message {i}")

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_logs)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        logs = self.logger.get_logs()
        assert len(logs) == 30  # 3 threads × 10 messages each


class TestFlaskAPIEndpoints:
    """Test suite for Flask API endpoints."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        scraping_logger.clear_logs()

    def test_api_scraping_logs_empty(self):
        """Test logs API with no logs."""
        response = self.client.get('/api/scraping_logs')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['logs'] == []
        assert data['total_count'] == 0

    def test_api_scraping_logs_with_data(self):
        """Test logs API with log data."""
        scraping_logger.info("Test log message")
        scraping_logger.error("Test error message")

        response = self.client.get('/api/scraping_logs')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data['logs']) == 2
        assert data['total_count'] == 2
        assert data['logs'][0]['level'] == 'INFO'
        assert data['logs'][1]['level'] == 'ERROR'

    def test_api_scraping_logs_clear(self):
        """Test logs clearing API."""
        scraping_logger.info("Test message")
        assert len(scraping_logger.get_logs()) == 1

        response = self.client.post('/api/scraping_logs/clear')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert len(scraping_logger.get_logs()) == 0

    def test_api_scraping_logs_download(self):
        """Test logs download API."""
        scraping_logger.info("Download test message")

        response = self.client.get('/api/scraping_logs/download')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert 'attachment; filename=' in response.headers['Content-Disposition']

        content = response.data.decode('utf-8')
        assert 'GOOGLE IMAGES SCRAPER - SESSION LOGS' in content
        assert 'Download test message' in content

    def test_api_scraping_status_not_running(self):
        """Test scraping status API when not running."""
        response = self.client.get('/api/scraping_status')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['is_running'] == False
        assert 'progress' in data

    def test_api_scraping_status_running(self):
        """Test scraping status API when running."""
        # Temporarily modify the global scraping_status
        from app import scraping_status
        original_status = scraping_status.copy()

        try:
            scraping_status['is_running'] = True
            scraping_status['progress'] = 'Downloading images...'

            response = self.client.get('/api/scraping_status')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['is_running'] == True
            assert data['progress'] == 'Downloading images...'
        finally:
            # Restore original status
            scraping_status.clear()
            scraping_status.update(original_status)


class TestGoogleImageScraper:
    """Test suite for GoogleImageScraper class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.scraper = GoogleImageScraper()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        # Note: GoogleImageScraper initializes driver in __init__, so it won't be None
        assert self.scraper.session is not None
        assert hasattr(self.scraper, 'headless')

    @patch('scraper.Service')
    @patch('scraper.webdriver.Chrome')
    def test_setup_driver_success(self, mock_chrome, mock_service):
        """Test successful WebDriver setup."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_service.return_value = Mock()  # Use the mock_service

        # Create a new scraper instance that won't auto-initialize
        scraper = GoogleImageScraper.__new__(GoogleImageScraper)
        scraper.headless = True
        scraper.driver = None
        scraper.session = Mock()

        scraper.setup_driver()

        assert scraper.driver == mock_driver
        mock_chrome.assert_called_once()

    @patch('scraper.Service')
    @patch('scraper.webdriver.Chrome')
    def test_setup_driver_failure(self, mock_chrome, mock_service):
        """Test WebDriver setup failure."""
        mock_chrome.side_effect = Exception("WebDriver failed")
        mock_service.return_value = Mock()  # Use the mock_service

        # Create a new scraper instance that won't auto-initialize
        scraper = GoogleImageScraper.__new__(GoogleImageScraper)
        scraper.headless = True
        scraper.driver = None
        scraper.session = Mock()

        with pytest.raises(Exception):
            scraper.setup_driver()

    def test_is_valid_image_url(self):
        """Test image URL validation."""
        # Valid URLs
        assert self.scraper._is_valid_image_url("https://example.com/image.jpg") == True
        assert self.scraper._is_valid_image_url("https://encrypted-tbn0.gstatic.com/images?q=test") == True
        assert self.scraper._is_valid_image_url("https://upload.wikimedia.org/image.png") == True

        # Invalid URLs
        assert self.scraper._is_valid_image_url("") == False
        assert self.scraper._is_valid_image_url("not_a_url") == False
        assert self.scraper._is_valid_image_url("https://google.com/images/branding/logo.png") == False

    @patch('requests.Session.get')
    def test_download_image_success(self, mock_get):
        """Test successful image download."""
        # Mock successful HTTP response with large enough data
        large_fake_data = b'fake_image_data_' * 100  # Make it large enough (1500+ bytes)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = large_fake_data
        mock_response.iter_content.return_value = [large_fake_data]
        mock_get.return_value = mock_response

        url = 'https://example.com/image.jpg'
        folder_path = self.temp_dir
        filename_prefix = 'test_image'

        # Mock the validate_image function to return True
        with patch('scraper.validate_image', return_value=True):
            result = self.scraper.download_image(url, folder_path, filename_prefix)

        assert result is not None  # Should return a filename
        assert isinstance(result, str)  # Should be a string filename

        # Check that file was actually created
        file_path = os.path.join(folder_path, result)
        assert os.path.exists(file_path)

    @patch('requests.Session.get')
    def test_download_image_http_error(self, mock_get):
        """Test image download with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        url = 'https://example.com/nonexistent.jpg'
        folder_path = self.temp_dir
        filename_prefix = 'test_image'

        result = self.scraper.download_image(url, folder_path, filename_prefix)

        assert result is None  # Should return None on failure

    @patch('requests.Session.get')
    def test_download_image_invalid_content_type(self, mock_get):
        """Test image download with invalid content type."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.iter_content.return_value = [b'html_content']
        mock_get.return_value = mock_response

        url = 'https://example.com/notimage.html'
        folder_path = self.temp_dir
        filename_prefix = 'test_image'

        result = self.scraper.download_image(url, folder_path, filename_prefix)

        assert result is None  # Should return None for invalid content type

    def test_close_functionality(self):
        """Test close functionality."""
        # Mock driver and session
        mock_driver = Mock()
        mock_session = Mock()
        self.scraper.driver = mock_driver
        self.scraper.session = mock_session

        self.scraper.close()

        mock_driver.quit.assert_called_once()
        mock_session.close.assert_called_once()
        assert self.scraper.driver is None

    @patch('scraper.GoogleImageScraper.search_images')
    @patch('scraper.GoogleImageScraper.download_image')
    def test_scrape_images_workflow(self, mock_download, mock_search):
        """Test the complete scrape_images workflow."""
        # Mock search_images to return test URLs
        mock_search.return_value = ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']

        # Mock download_image to return filenames
        mock_download.side_effect = ['image1.jpg', 'image2.jpg']

        # Create a temporary destination folder
        destination_folder = self.temp_dir
        class_name = 'test_class'

        # Mock the create_class_folder function
        with patch('scraper.create_class_folder') as mock_create_folder:
            mock_create_folder.return_value = os.path.join(destination_folder, class_name)

            downloaded_count, class_folder = self.scraper.scrape_images(
                query='test',
                destination_folder=destination_folder,
                class_name=class_name,
                max_images=2
            )

        assert downloaded_count == 2
        assert class_folder == os.path.join(destination_folder, class_name)
        mock_search.assert_called_once_with('test', 2)
        assert mock_download.call_count == 2


class TestIntegrationTests:
    """Integration tests for complete workflow."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        app.config['TESTING'] = True
        self.client = app.test_client()
        scraping_logger.clear_logs()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_flask_routes_exist(self):
        """Test that all required Flask routes exist."""
        # Test main routes
        response = self.client.get('/')
        assert response.status_code == 200

        response = self.client.get('/dashboard')
        assert response.status_code == 200

        response = self.client.get('/scraping_progress')
        assert response.status_code == 200

        # Test API routes
        response = self.client.get('/api/scraping_status')
        assert response.status_code == 200

        response = self.client.get('/api/scraping_logs')
        assert response.status_code == 200

    @patch('app.threading.Thread')
    def test_scrape_endpoint_starts_background_task(self, mock_thread):
        """Test that scrape endpoint starts background task."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        response = self.client.post('/scrape', data={
            'keywords': 'test',
            'class_name': 'test_class',
            'max_images': '2'
        })

        assert response.status_code == 302  # Redirect to progress page
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    def test_scrape_endpoint_validation(self):
        """Test scrape endpoint input validation."""
        # Test missing parameters - should redirect back to index
        response = self.client.post('/scrape', data={})
        assert response.status_code == 302  # Redirect
        assert '/index' in response.location or response.location.endswith('/')

        # Test missing keywords - should redirect back to index
        response = self.client.post('/scrape', data={
            'class_name': 'test_class',
            'max_images': '5'
        })
        assert response.status_code == 302  # Redirect

        # Test missing class_name - should redirect back to index
        response = self.client.post('/scrape', data={
            'keywords': 'test',
            'max_images': '5'
        })
        assert response.status_code == 302  # Redirect

    def test_sse_stream_endpoint(self):
        """Test SSE stream endpoint basic functionality."""
        # Add some test logs
        scraping_logger.info("Test message 1")
        scraping_logger.error("Test message 2")

        response = self.client.get('/api/scraping_logs/stream')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/event-stream; charset=utf-8'

        # Check that response contains SSE data
        data = response.data.decode('utf-8')
        assert 'data: ' in data
        assert 'connected' in data


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.scraper = GoogleImageScraper()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_scraper_with_invalid_folder_permissions(self):
        """Test scraper behavior with invalid folder permissions."""
        # This test is platform-specific and may not work on all systems
        if os.name == 'nt':  # Windows
            pytest.skip("Permission tests not reliable on Windows")

        # Create a folder with no write permissions
        restricted_folder = os.path.join(self.temp_dir, 'restricted')
        os.makedirs(restricted_folder)
        os.chmod(restricted_folder, 0o444)  # Read-only

        try:
            result = self.scraper.create_folder(os.path.join(restricted_folder, 'subfolder'))
            # Should handle permission error gracefully
            assert result is None or isinstance(result, str)
        finally:
            # Restore permissions for cleanup
            os.chmod(restricted_folder, 0o755)

    @patch('requests.Session.get')
    def test_download_with_network_timeout(self, mock_get):
        """Test image download with network timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        url = 'https://example.com/slow_image.jpg'
        folder_path = self.temp_dir
        filename_prefix = 'test_image'

        result = self.scraper.download_image(url, folder_path, filename_prefix)

        assert result is None  # Should return None on network error

    @patch('requests.Session.get')
    def test_download_with_connection_error(self, mock_get):
        """Test image download with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        url = 'https://nonexistent.example.com/image.jpg'
        folder_path = self.temp_dir
        filename_prefix = 'test_image'

        result = self.scraper.download_image(url, folder_path, filename_prefix)

        assert result is None  # Should return None on connection error

    def test_logger_with_unicode_characters(self):
        """Test logger with unicode characters."""
        logger = ScrapingLogger()
        logger.clear_logs()

        # Test various unicode characters
        test_messages = [
            "Test with emoji: 🎉 🚀 ✅",
            "Test with accents: café naïve résumé",
            "Test with symbols: ©®™ ±×÷",
            "Test with Chinese: 你好世界",
            "Test with Arabic: مرحبا بالعالم"
        ]

        for message in test_messages:
            logger.info(message)

        logs = logger.get_logs()
        assert len(logs) == len(test_messages)

        for i, log in enumerate(logs):
            assert log['message'] == test_messages[i]

        # Test export with unicode
        export_text = logger.export_logs_to_text()
        for message in test_messages:
            assert message in export_text

    def test_concurrent_log_access(self):
        """Test concurrent access to logs."""
        import threading
        import time

        logger = ScrapingLogger()
        logger.clear_logs()

        results = []

        def reader_thread():
            """Thread that reads logs."""
            for _ in range(10):
                logs = logger.get_logs()
                results.append(len(logs))
                time.sleep(0.01)

        def writer_thread():
            """Thread that writes logs."""
            for i in range(20):
                logger.info(f"Concurrent message {i}")
                time.sleep(0.01)

        # Start threads
        reader = threading.Thread(target=reader_thread)
        writer = threading.Thread(target=writer_thread)

        reader.start()
        writer.start()

        reader.join()
        writer.join()

        # Verify no race conditions occurred
        final_logs = logger.get_logs()
        assert len(final_logs) == 20
        assert len(results) == 10  # Reader thread completed


# Simple integration test that can run without mocking
def test_simple_integration():
    """Simple integration test without external dependencies."""
    # Test logger integration
    logger = ScrapingLogger()
    logger.clear_logs()

    logger.info("Integration test started")
    logger.success("Test component working")
    logger.info("Integration test completed")

    logs = logger.get_logs()
    assert len(logs) == 3
    assert logs[0]['message'] == "Integration test started"
    assert logs[1]['level'] == "SUCCESS"
    assert logs[2]['message'] == "Integration test completed"

    # Test export functionality
    export_text = logger.export_logs_to_text()
    assert "Integration test started" in export_text
    assert "Test component working" in export_text
    assert "Integration test completed" in export_text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
