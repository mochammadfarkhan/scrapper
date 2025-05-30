from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import os
import threading
import time
from config import Config
from utils import get_all_classes, get_images_in_class, delete_image, create_class_folder
from scraper import GoogleImageScraper

app = Flask(__name__)
app.config.from_object(Config)

# Global variable to track scraping progress
scraping_status = {
    'is_running': False,
    'progress': '',
    'current_task': None
}

@app.route('/')
def index():
    """Main page with input form."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Image management dashboard."""
    classes = get_all_classes(app.config['UPLOAD_FOLDER'])
    return render_template('dashboard.html', classes=classes)

@app.route('/view_images/<class_name>')
def view_images(class_name):
    """View images for a specific class."""
    images = get_images_in_class(app.config['UPLOAD_FOLDER'], class_name)
    return render_template('view_images.html', class_name=class_name, images=images)

@app.route('/scrape', methods=['POST'])
def scrape_images():
    """Start image scraping process."""
    global scraping_status
    
    if scraping_status['is_running']:
        flash('Scraping is already in progress. Please wait for it to complete.', 'warning')
        return redirect(url_for('index'))
    
    # Get form data
    keywords = request.form.get('keywords', '').strip()
    destination_folder = request.form.get('destination_folder', '').strip()
    class_name = request.form.get('class_name', '').strip()
    max_images = int(request.form.get('max_images', 20))
    
    # Validation
    if not keywords:
        flash('Please enter search keywords.', 'error')
        return redirect(url_for('index'))
    
    if not class_name:
        flash('Please enter a class/category name.', 'error')
        return redirect(url_for('index'))
    
    # Use default folder if not specified
    if not destination_folder:
        destination_folder = app.config['UPLOAD_FOLDER']
    
    # Validate max_images
    if max_images < 1 or max_images > 100:
        max_images = 20
    
    # Start scraping in background thread
    def scrape_worker():
        global scraping_status
        scraper = None
        try:
            scraping_status['is_running'] = True
            scraping_status['progress'] = 'Initializing scraper...'
            
            def progress_callback(message):
                scraping_status['progress'] = message
            
            scraper = GoogleImageScraper(headless=True)
            downloaded_count, class_folder = scraper.scrape_images(
                keywords, destination_folder, class_name, max_images, progress_callback
            )
            
            scraping_status['progress'] = f'Completed! Downloaded {downloaded_count} images.'
            time.sleep(2)  # Keep message visible for a moment
            
        except Exception as e:
            scraping_status['progress'] = f'Error: {str(e)}'
        finally:
            if scraper:
                scraper.close()
            scraping_status['is_running'] = False
    
    # Start background thread
    thread = threading.Thread(target=scrape_worker)
    thread.daemon = True
    thread.start()
    
    flash('Image scraping started! You can monitor progress below.', 'success')
    return redirect(url_for('scraping_progress'))

@app.route('/scraping_progress')
def scraping_progress():
    """Show scraping progress page."""
    return render_template('scraping_progress.html')

@app.route('/api/scraping_status')
def api_scraping_status():
    """API endpoint to get current scraping status."""
    return jsonify(scraping_status)

@app.route('/delete_image/<class_name>/<filename>', methods=['POST'])
def delete_image_route(class_name, filename):
    """Delete a specific image."""
    success = delete_image(app.config['UPLOAD_FOLDER'], class_name, filename)
    if success:
        flash(f'Image {filename} deleted successfully.', 'success')
    else:
        flash(f'Failed to delete image {filename}.', 'error')
    
    return redirect(url_for('view_images', class_name=class_name))

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the upload folder."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
