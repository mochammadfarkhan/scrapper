# Image Scraper Web Application

A Flask-based Python web application for scraping images from Google Images with an intuitive web interface for management and organization.

## Features

### 🔍 Image Scraping
- Search and download images from Google Images
- Customizable number of images (10-100)
- Automatic image validation and filtering
- Background processing with real-time progress updates

### 📁 Organization & Management
- Organize images by custom categories/classes
- Visual dashboard showing all image collections
- Grid-based image gallery with hover effects
- Individual image deletion with confirmation

### 🎨 User Interface
- Modern, responsive design with Bootstrap 5
- Real-time progress tracking during scraping
- Intuitive navigation between pages
- Mobile-friendly interface

## Installation

1. **Clone or download the project**
   ```bash
   cd scrapper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

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

## Usage

### Scraping Images
1. Go to the main page
2. Enter search keywords (e.g., "cats", "cars", "nature")
3. Specify a category name for organization
4. Choose the number of images to download
5. Click "Start Scraping" and monitor progress

### Managing Images
1. Visit the Dashboard to see all your image categories
2. Click "View Images" on any category to see the gallery
3. Hover over images to reveal the delete button
4. Use the navigation to move between sections

## Project Structure

```
scrapper/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── scraper.py            # Google Images scraping logic
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── view_images.html
│   └── scraping_progress.html
├── static/               # CSS, JS, and static files
│   ├── css/style.css
│   └── js/main.js
└── scraped_images/       # Default image storage (created automatically)
```

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for sessions
- `UPLOAD_FOLDER`: Directory for storing scraped images
- `MAX_IMAGES_PER_SEARCH`: Maximum images per scraping session

### Default Settings
- Images are saved to `scraped_images/` folder
- Maximum 20 images per search (configurable)
- Headless Chrome browser for scraping
- Automatic image validation

## Requirements

- Python 3.7+
- Chrome browser (for Selenium WebDriver)
- Internet connection for image scraping

## Dependencies

- **Flask**: Web framework
- **Selenium**: Web browser automation
- **Requests**: HTTP library for downloading images
- **Pillow**: Image processing and validation
- **BeautifulSoup4**: HTML parsing
- **WebDriver Manager**: Automatic Chrome driver management

## Troubleshooting

### Common Issues

1. **Chrome driver issues**
   - The app automatically downloads the Chrome driver
   - Ensure Chrome browser is installed

2. **Permission errors**
   - Check write permissions for the upload folder
   - Run with appropriate user permissions

3. **Network issues**
   - Ensure stable internet connection
   - Some images may fail to download due to server restrictions

### Error Handling
- Invalid images are automatically filtered out
- Failed downloads are logged and skipped
- Progress updates show current status

## License

This project is for educational purposes. Please respect website terms of service and copyright laws when scraping images.

## Contributing

Feel free to submit issues and enhancement requests!
