# 🖼️ Google Images Scraper Web Application

A powerful Flask-based Python web application for scraping images from Google Images with real Selenium WebDriver automation and an intuitive web interface for management and organization.

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![Selenium](https://img.shields.io/badge/Selenium-4.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1+-purple.svg)

## ✨ Features

### 🔍 **Real Google Images Scraping**

- **Selenium WebDriver automation** for authentic browser interaction
- **Real-time image extraction** from Google Images search results
- **Smart image filtering** and validation
- **Automatic Chrome driver management** with webdriver-manager
- **Headless browser operation** for background processing
- **Customizable image count** (10-100 images per search)

### 📁 **Advanced Organization & Management**

- **Category-based organization** with custom class names
- **Visual dashboard** showing all image collections with statistics
- **Interactive image gallery** with responsive grid layout
- **Individual image deletion** with confirmation modals
- **Real-time progress tracking** during scraping operations
- **Automatic folder structure** creation and management

### 🎨 **Modern User Interface**

- **Responsive design** with Bootstrap 5 and custom CSS
- **Real-time progress updates** with AJAX polling
- **Intuitive navigation** between scraping, dashboard, and gallery
- **Mobile-friendly interface** that works on all devices
- **Interactive hover effects** and smooth animations
- **Error handling** with user-friendly messages

### 🛠️ **Technical Features**

- **Background processing** with threading for non-blocking operations
- **Robust error handling** for network issues and WebDriver problems
- **Image validation** with Pillow to ensure file integrity
- **Smart URL filtering** to avoid duplicates and invalid images
- **Chunked downloads** for efficient memory usage
- **Automatic cleanup** of invalid or corrupted files

## 🚀 Quick Start

### Prerequisites

- **Python 3.7+** installed on your system
- **Google Chrome browser** (for Selenium WebDriver)
- **Internet connection** for image scraping

### Installation

1. **Clone or download the project**

   ```bash
   git clone <repository-url>
   cd scrapper
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   This will install:

   - Flask (web framework)
   - Selenium (browser automation)
   - WebDriver Manager (automatic driver management)
   - Pillow (image processing)
   - Requests (HTTP library)
   - BeautifulSoup4 (HTML parsing)
   - Python-dotenv (environment variables)

3. **Set up environment variables (optional)**

   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 📖 Usage Guide

### 🔍 **Scraping Images**

1. **Navigate** to the main page (`http://localhost:5000`)
2. **Enter search keywords** (e.g., "cats", "nature", "technology")
3. **Specify a category name** for organization (e.g., "animals", "landscapes")
4. **Choose destination folder** (optional - defaults to `scraped_images`)
5. **Select number of images** to download (10-100)
6. **Click "Start Scraping"** and monitor real-time progress
7. **View completion status** and navigate to results

### 📊 **Managing Images**

1. **Visit the Dashboard** to see all your image categories
2. **View statistics** including total classes, images, and averages
3. **Click "View Images"** on any category to open the gallery
4. **Browse images** in a responsive grid layout
5. **Delete unwanted images** using the trash button with confirmation
6. **Navigate seamlessly** between sections using breadcrumbs

### 🖼️ **Gallery Features**

- **Responsive grid layout** that adapts to screen size
- **Hover effects** with smooth animations
- **Image preview** with proper aspect ratio handling
- **Delete functionality** with confirmation modals
- **Breadcrumb navigation** for easy movement between sections

## 🏗️ Project Structure

```
scrapper/
├── 📄 app.py                    # Main Flask application with routes
├── ⚙️ config.py                 # Configuration settings and environment
├── 🤖 scraper.py                # Google Images scraping with Selenium
├── 🛠️ utils.py                  # Utility functions for file management
├── 📋 requirements.txt          # Python dependencies
├── 🌐 templates/               # Jinja2 HTML templates
│   ├── 🏠 base.html            # Base template with navigation
│   ├── 🔍 index.html           # Main scraping form page
│   ├── 📊 dashboard.html       # Image management dashboard
│   ├── 🖼️ view_images.html     # Image gallery view
│   ├── ⏳ scraping_progress.html # Real-time progress tracking
│   ├── ❌ 404.html             # Error page for not found
│   └── 💥 500.html             # Error page for server errors
├── 🎨 static/                  # Static assets
│   ├── 🎨 css/style.css        # Custom styling and animations
│   └── ⚡ js/main.js           # JavaScript for interactivity
├── 📁 scraped_images/          # Default image storage (auto-created)
├── 🧪 test_scraper.py          # Test script for scraping functionality
├── 📝 .env.example             # Environment variables template
└── 📖 README.md               # This documentation file
```

## ⚙️ Configuration

### 🌍 **Environment Variables**

Create a `.env` file based on `.env.example`:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Image Scraping Configuration
UPLOAD_FOLDER=scraped_images
MAX_IMAGES_PER_SEARCH=20
```

### 🔧 **Default Settings**

- **Image storage**: `scraped_images/` folder (auto-created)
- **Default image limit**: 20 images per search
- **Browser mode**: Headless Chrome for background operation
- **Image validation**: Automatic with Pillow
- **File organization**: Category-based folder structure

## 🔧 Technical Details

### 🤖 **Selenium WebDriver Configuration**

- **Headless Chrome** for background operation
- **Automatic driver management** with webdriver-manager
- **Optimized browser options** for stability and performance
- **Smart error handling** for WebDriver issues
- **Proper resource cleanup** after scraping

### 🖼️ **Image Processing Pipeline**

1. **URL Extraction**: Multiple CSS selectors for comprehensive coverage
2. **URL Validation**: Smart filtering to avoid invalid or duplicate images
3. **Download Process**: Chunked downloads with proper headers
4. **Image Validation**: Pillow-based validation to ensure file integrity
5. **File Organization**: Automatic categorization and unique naming
6. **Cleanup**: Removal of invalid or corrupted files

### 🌐 **Web Interface Architecture**

- **Flask backend** with RESTful routes
- **Jinja2 templating** for dynamic content
- **Bootstrap 5** for responsive design
- **Custom CSS** for enhanced styling
- **JavaScript** for real-time updates and interactivity
- **AJAX polling** for progress tracking

## 🧪 Testing

### 🔬 **Run Tests**

```bash
# Test the scraping functionality
python test_scraper.py

# Test with specific parameters
python -c "
from scraper import GoogleImageScraper
scraper = GoogleImageScraper()
count, folder = scraper.scrape_images('cats', 'test_images', 'test_category', 3)
print(f'Downloaded {count} images to {folder}')
scraper.close()
"
```

### ✅ **Verification Steps**

1. **Check WebDriver initialization**: Should see "WebDriver initialized successfully"
2. **Verify Google Images navigation**: Should navigate to correct search URL
3. **Confirm image extraction**: Should find and extract valid image URLs
4. **Validate downloads**: Should download and save images to correct folders
5. **Test web interface**: Should display images in dashboard and gallery

## 🛠️ Dependencies

### 📦 **Core Dependencies**

- **Flask** (≥2.0.0): Web framework for the application
- **Selenium** (≥4.0.0): Browser automation for Google Images scraping
- **WebDriver Manager** (≥3.8.0): Automatic Chrome driver management
- **Requests** (≥2.25.0): HTTP library for downloading images
- **Pillow** (≥8.0.0): Image processing and validation
- **BeautifulSoup4** (≥4.9.0): HTML parsing utilities
- **Python-dotenv** (≥0.19.0): Environment variable management

### 🌐 **Frontend Dependencies** (CDN)

- **Bootstrap 5.1.3**: Responsive CSS framework
- **Font Awesome 6.0.0**: Icon library
- **Custom CSS/JS**: Enhanced styling and interactivity

## 🚨 Troubleshooting

### 🔧 **Common Issues & Solutions**

#### **Chrome Driver Issues**

```bash
# The app automatically downloads ChromeDriver, but ensure Chrome is installed
# On Windows: Download from https://www.google.com/chrome/
# On Ubuntu: sudo apt-get install google-chrome-stable
# On macOS: brew install --cask google-chrome
```

#### **Permission Errors**

```bash
# Ensure write permissions for the upload folder
chmod 755 scraped_images/
# Or run with appropriate user permissions
sudo python app.py  # Not recommended for production
```

#### **Network Issues**

- Ensure stable internet connection
- Some images may fail due to server restrictions (this is normal)
- Check firewall settings if experiencing connection issues

#### **Memory Issues**

- Reduce the number of images per search if experiencing memory problems
- The app uses chunked downloads to minimize memory usage
- Close other applications if running low on system resources

### 📊 **Error Handling Features**

- **Automatic retry** for failed downloads
- **Invalid image filtering** with automatic cleanup
- **Progress tracking** with detailed error messages
- **Graceful degradation** when some images fail to download
- **WebDriver cleanup** to prevent resource leaks

## 🔒 Legal & Ethical Considerations

### ⚖️ **Important Notes**

- **Educational Purpose**: This project is designed for educational and research purposes
- **Respect Terms of Service**: Always respect Google's Terms of Service and robots.txt
- **Copyright Awareness**: Be mindful of copyright laws when downloading images
- **Rate Limiting**: The app includes delays to be respectful to servers
- **Personal Use**: Recommended for personal projects and learning

### 🛡️ **Best Practices**

- Use reasonable delays between requests
- Don't overwhelm servers with too many concurrent requests
- Respect website terms of service and robots.txt files
- Consider the copyright status of downloaded images
- Use downloaded images responsibly and legally

## 🤝 Contributing

### 🔄 **How to Contribute**

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### 🐛 **Reporting Issues**

- Use the GitHub Issues tab to report bugs
- Include detailed steps to reproduce the issue
- Provide system information (OS, Python version, Chrome version)
- Include error messages and logs when possible

### 💡 **Feature Requests**

- Suggest new features through GitHub Issues
- Explain the use case and expected behavior
- Consider contributing the implementation yourself

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Flask** team for the excellent web framework
- **Selenium** project for browser automation capabilities
- **Bootstrap** team for the responsive CSS framework
- **Google** for providing the image search functionality
- **Open source community** for the various libraries and tools used

---

**⭐ If you find this project useful, please consider giving it a star on GitHub!**

**🔗 For questions, issues, or contributions, please visit the [GitHub repository](https://github.com/your-username/image-scraper)**
