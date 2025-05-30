from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
import os
import threading
import time
import json
from config import Config
from utils import get_all_classes, get_images_in_class, delete_image, create_class_folder
from scraper import GoogleImageScraper
from logger import scraping_logger

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
            # Clear previous logs
            scraping_logger.clear_logs()
            scraping_logger.info("🎬 Starting new scraping session")

            scraping_status['is_running'] = True
            scraping_status['progress'] = 'Initializing scraper...'

            def progress_callback(message):
                scraping_status['progress'] = message

            scraper = GoogleImageScraper(headless=True)
            downloaded_count, class_folder = scraper.scrape_images(
                keywords, destination_folder, class_name, max_images, progress_callback
            )

            scraping_status['progress'] = f'Completed! Downloaded {downloaded_count} images.'
            scraping_logger.info("🎉 Scraping session completed")
            time.sleep(2)  # Keep message visible for a moment

        except Exception as e:
            error_msg = f'Error: {str(e)}'
            scraping_status['progress'] = error_msg
            scraping_logger.error(f"💥 Scraping session failed: {str(e)}")
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

@app.route('/api/scraping_logs')
def api_scraping_logs():
    """API endpoint to get scraping logs."""
    logs = scraping_logger.get_logs()
    return jsonify({
        'logs': logs,
        'total_count': len(logs)
    })

@app.route('/api/scraping_logs/stream')
def api_scraping_logs_stream():
    """Server-Sent Events endpoint for real-time log streaming."""
    def generate_log_stream():
        """Generate log events for SSE."""
        last_log_count = 0
        max_iterations = 300  # Maximum 5 minutes (300 seconds)
        iteration_count = 0

        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'message': 'Log stream connected'})}\n\n"

        while iteration_count < max_iterations:
            try:
                # Get new logs since last check
                all_logs = scraping_logger.get_logs()
                new_logs = all_logs[last_log_count:]

                if new_logs:
                    for log_entry in new_logs:
                        # Format log entry for SSE
                        log_data = {
                            'type': 'log',
                            'timestamp': log_entry['timestamp'],
                            'level': log_entry['level'],
                            'message': log_entry['message'],
                            'formatted': scraping_logger.format_log_for_display(log_entry)
                        }

                        yield f"data: {json.dumps(log_data)}\n\n"

                    last_log_count = len(all_logs)

                # Send heartbeat every 10 seconds
                if iteration_count % 10 == 0:
                    heartbeat_data = {
                        'type': 'heartbeat',
                        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'log_count': len(all_logs),
                        'scraping_running': scraping_status['is_running']
                    }
                    yield f"data: {json.dumps(heartbeat_data)}\n\n"

                # Check if scraping is still running
                if not scraping_status['is_running'] and last_log_count > 0 and iteration_count > 5:
                    # Send completion signal
                    completion_data = {
                        'type': 'complete',
                        'message': 'Scraping completed',
                        'total_logs': len(all_logs)
                    }
                    yield f"data: {json.dumps(completion_data)}\n\n"
                    break

                time.sleep(1)  # Poll every second
                iteration_count += 1

            except Exception as e:
                error_data = {
                    'type': 'error',
                    'message': f"Log streaming error: {str(e)}"
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break

        # Send final disconnect message
        yield f"data: {json.dumps({'type': 'disconnect', 'message': 'Log stream disconnected'})}\n\n"

    return Response(
        generate_log_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

@app.route('/api/scraping_logs/download')
def api_scraping_logs_download():
    """Download logs as a text file."""
    logs_text = scraping_logger.export_logs_to_text()

    response = Response(
        logs_text,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=scraping_logs_{int(time.time())}.txt'
        }
    )

    return response

@app.route('/api/scraping_logs/clear', methods=['POST'])
def api_scraping_logs_clear():
    """Clear all logs."""
    scraping_logger.clear_logs()
    return jsonify({'status': 'success', 'message': 'Logs cleared'})

@app.route('/api/scraping_logs/new')
def api_scraping_logs_new():
    """Get only new logs since last request."""
    new_logs = scraping_logger.get_new_logs()
    return jsonify({
        'logs': new_logs,
        'count': len(new_logs)
    })

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
