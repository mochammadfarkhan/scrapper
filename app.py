from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, Response
import os
import shutil
import re
import threading
import time
import json
from config import Config
from utils import (get_all_classes, get_images_in_class, delete_image, create_class_folder,
                   get_grouped_classes, get_grouped_classes_with_manual_assignments,
                   add_folder_to_tab, remove_folder_from_tab, get_folder_tab_info,
                   delete_folder, get_folder_info)
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

@app.route('/bulk-search')
def bulk_search():
    """Bulk image search form page."""
    return render_template('bulk_search.html')

@app.route('/dashboard')
def dashboard():
    """Image management dashboard."""
    classes = get_all_classes(app.config['UPLOAD_FOLDER'])
    grouped_classes = get_grouped_classes_with_manual_assignments(app.config['UPLOAD_FOLDER'])
    return render_template('dashboard.html', classes=classes, grouped_classes=grouped_classes)

@app.route('/view_images/<class_name>')
def view_images(class_name):
    """View images for a specific class."""
    images = get_images_in_class(app.config['UPLOAD_FOLDER'], class_name)
    return render_template('view_images.html', class_name=class_name, images=images)

@app.route('/scrape', methods=['POST'])
def scrape_images():
    """Start image scraping process."""
    global scraping_status

    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if scraping_status['is_running']:
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': 'Scraping is already in progress. Please wait for it to complete.'
            })
        else:
            flash('Scraping is already in progress. Please wait for it to complete.', 'warning')
            return redirect(url_for('index'))

    # Get form data
    keywords = request.form.get('keywords', '').strip()
    destination_folder = request.form.get('destination_folder', '').strip()
    class_name = request.form.get('class_name', '').strip()
    max_images = int(request.form.get('max_images', 20))

    # Validation
    if not keywords:
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': 'Please enter search keywords.'
            })
        else:
            flash('Please enter search keywords.', 'error')
            return redirect(url_for('index'))

    if not class_name:
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': 'Please enter a class/category name.'
            })
        else:
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

    if is_ajax:
        return jsonify({
            'status': 'success',
            'message': 'Image scraping started! You can monitor progress below.'
        })
    else:
        flash('Image scraping started! You can monitor progress below.', 'success')
        return redirect(url_for('scraping_progress'))

@app.route('/perform-bulk-search', methods=['POST'])
def perform_bulk_search():
    """Handle bulk image search requests."""
    global scraping_status

    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if scraping_status['is_running']:
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': 'Scraping is already in progress. Please wait for it to complete.'
            })
        else:
            flash('Scraping is already in progress. Please wait for it to complete.', 'warning')
            return redirect(url_for('bulk_search'))

    try:
        # Get form data
        if is_ajax:
            data = request.get_json()
            search_entries = data.get('search_entries', [])
            images_per_class = int(data.get('images_per_class', 100))
            destination_folder = data.get('destination_folder', '').strip() or app.config['UPLOAD_FOLDER']
        else:
            # Handle form submission (fallback)
            search_entries = []
            keywords_list = request.form.getlist('keyword[]')
            class_names_list = request.form.getlist('className[]')

            for keyword, class_name in zip(keywords_list, class_names_list):
                if keyword.strip() and class_name.strip():
                    search_entries.append({
                        'keyword': keyword.strip(),
                        'className': class_name.strip()
                    })

            images_per_class = int(request.form.get('images_per_class', 100))
            destination_folder = request.form.get('destination_folder', '').strip() or app.config['UPLOAD_FOLDER']

        # Validate input
        if not search_entries:
            error_msg = 'No valid search entries provided'
            if is_ajax:
                return jsonify({'status': 'error', 'message': error_msg})
            else:
                flash(error_msg, 'error')
                return redirect(url_for('bulk_search'))

        if images_per_class < 1 or images_per_class > 500:
            error_msg = 'Images per class must be between 1 and 500'
            if is_ajax:
                return jsonify({'status': 'error', 'message': error_msg})
            else:
                flash(error_msg, 'error')
                return redirect(url_for('bulk_search'))

        # Start bulk scraping in background thread
        def bulk_scrape_worker():
            global scraping_status
            scraper = None
            total_downloaded = 0

            try:
                # Clear previous logs
                scraping_logger.clear_logs()
                scraping_logger.info("🎬 Starting bulk scraping session")
                scraping_logger.info(f"📝 Processing {len(search_entries)} search entries, {images_per_class} images each")

                scraping_status['is_running'] = True
                scraping_status['progress'] = 'Initializing bulk scraper...'

                scraper = GoogleImageScraper(headless=True)

                for i, entry in enumerate(search_entries, 1):
                    keyword = entry['keyword']
                    class_name = entry['className']
                    entry_destination = entry.get('destinationFolder')

                    # Use per-row destination folder if specified, otherwise use global setting
                    current_destination = entry_destination if entry_destination else destination_folder

                    scraping_status['progress'] = f'Processing {i}/{len(search_entries)}: {keyword} -> {class_name}'
                    if entry_destination:
                        scraping_logger.info(f"🔍 [{i}/{len(search_entries)}] Processing: '{keyword}' -> '{class_name}' (destination: {current_destination})")
                    else:
                        scraping_logger.info(f"🔍 [{i}/{len(search_entries)}] Processing: '{keyword}' -> '{class_name}'")

                    def progress_callback(message):
                        scraping_status['progress'] = f'[{i}/{len(search_entries)}] {message}'

                    try:
                        downloaded_count, class_folder = scraper.scrape_images(
                            keyword, current_destination, class_name, images_per_class, progress_callback
                        )
                        total_downloaded += downloaded_count
                        if entry_destination:
                            scraping_logger.success(f"✅ [{i}/{len(search_entries)}] Completed: {downloaded_count} images for '{class_name}' in '{current_destination}'")
                        else:
                            scraping_logger.success(f"✅ [{i}/{len(search_entries)}] Completed: {downloaded_count} images for '{class_name}'")

                    except Exception as e:
                        scraping_logger.error(f"❌ [{i}/{len(search_entries)}] Failed '{keyword}' -> '{class_name}': {str(e)}")
                        continue

                scraping_status['progress'] = f'Bulk scraping completed! Downloaded {total_downloaded} images total.'
                scraping_logger.info(f"🎉 Bulk scraping session completed - {total_downloaded} images total")
                time.sleep(2)  # Keep message visible for a moment

            except Exception as e:
                error_msg = f'Bulk scraping error: {str(e)}'
                scraping_status['progress'] = error_msg
                scraping_logger.error(f"💥 Bulk scraping session failed: {str(e)}")
            finally:
                if scraper:
                    scraper.close()
                scraping_status['is_running'] = False

        # Start background thread
        thread = threading.Thread(target=bulk_scrape_worker)
        thread.daemon = True
        thread.start()

        if is_ajax:
            return jsonify({
                'status': 'success',
                'message': f'Bulk image scraping started for {len(search_entries)} entries! You can monitor progress below.',
                'entries_count': len(search_entries),
                'images_per_class': images_per_class
            })
        else:
            flash(f'Bulk image scraping started for {len(search_entries)} entries! You can monitor progress below.', 'success')
            return redirect(url_for('scraping_progress'))

    except Exception as e:
        error_msg = f'Error starting bulk scraping: {str(e)}'
        if is_ajax:
            return jsonify({'status': 'error', 'message': error_msg})
        else:
            flash(error_msg, 'error')
            return redirect(url_for('bulk_search'))

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

@app.route('/api/scraping_reset', methods=['POST'])
def api_scraping_reset():
    """Reset scraping status (for testing purposes)."""
    global scraping_status
    scraping_status['is_running'] = False
    scraping_status['progress'] = ''
    scraping_status['current_task'] = None
    scraping_logger.clear_logs()
    return jsonify({'status': 'success', 'message': 'Scraping status reset'})

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
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        success = delete_image(app.config['UPLOAD_FOLDER'], class_name, filename)

        if success:
            message = f'Image {filename} deleted successfully.'
            if is_ajax:
                return jsonify({
                    'status': 'success',
                    'message': message
                })
            else:
                flash(message, 'success')
        else:
            error_message = f'Failed to delete image {filename}. File not found.'
            if is_ajax:
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 404
            else:
                flash(error_message, 'error')

    except Exception as e:
        error_message = f'Error deleting image {filename}: {str(e)}'
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 500
        else:
            flash(error_message, 'error')

    # For non-AJAX requests, redirect back to the view_images page
    return redirect(url_for('view_images', class_name=class_name))

@app.route('/api/folders')
def api_folders():
    """Get list of available folders excluding the current one."""
    try:
        current_folder = request.args.get('current', '')
        all_classes = get_all_classes(app.config['UPLOAD_FOLDER'])

        # Filter out the current folder
        available_folders = [cls['name'] for cls in all_classes if cls['name'] != current_folder]

        return jsonify({
            'status': 'success',
            'folders': available_folders,
            'current_folder': current_folder
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/move-images', methods=['POST'])
def api_move_images():
    """Move multiple images to a different folder."""
    try:
        data = request.get_json()
        images = data.get('images', [])
        destination_folder = data.get('destination_folder', '').strip()
        source_folder = data.get('source_folder', '').strip()
        create_new = data.get('create_new', False)

        if not images:
            return jsonify({
                'status': 'error',
                'message': 'No images specified'
            }), 400

        if not destination_folder:
            return jsonify({
                'status': 'error',
                'message': 'No destination folder specified'
            }), 400

        if not source_folder:
            return jsonify({
                'status': 'error',
                'message': 'No source folder specified'
            }), 400

        # Create destination folder if needed
        if create_new:
            from utils import create_class_folder
            create_class_folder(app.config['UPLOAD_FOLDER'], destination_folder)

        # Move images
        moved_count = 0
        failed_images = []

        for image_relative_path in images:
            try:
                # Extract filename from relative path
                filename = os.path.basename(image_relative_path)
                source_path = os.path.join(app.config['UPLOAD_FOLDER'], source_folder, filename)
                dest_path = os.path.join(app.config['UPLOAD_FOLDER'], destination_folder, filename)

                # Ensure destination directory exists
                dest_dir = os.path.dirname(dest_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                # Move the file
                if os.path.exists(source_path):
                    shutil.move(source_path, dest_path)
                    moved_count += 1
                else:
                    failed_images.append(filename)

            except Exception as e:
                failed_images.append(f"{filename}: {str(e)}")

        response_data = {
            'status': 'success',
            'moved_count': moved_count,
            'destination_folder': destination_folder
        }

        if failed_images:
            response_data['failed_images'] = failed_images
            response_data['message'] = f'Moved {moved_count} images. {len(failed_images)} failed.'
        else:
            response_data['message'] = f'Successfully moved {moved_count} images to {destination_folder}'

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/delete-images', methods=['POST'])
def api_delete_images():
    """Delete multiple images."""
    try:
        data = request.get_json()
        images = data.get('images', [])
        folder = data.get('folder', '').strip()

        if not images:
            return jsonify({
                'status': 'error',
                'message': 'No images specified'
            }), 400

        if not folder:
            return jsonify({
                'status': 'error',
                'message': 'No folder specified'
            }), 400

        # Delete images
        deleted_count = 0
        failed_images = []

        for image_relative_path in images:
            try:
                # Extract filename from relative path
                filename = os.path.basename(image_relative_path)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
                else:
                    failed_images.append(filename)

            except Exception as e:
                failed_images.append(f"{filename}: {str(e)}")

        response_data = {
            'status': 'success',
            'deleted_count': deleted_count
        }

        if failed_images:
            response_data['failed_images'] = failed_images
            response_data['message'] = f'Deleted {deleted_count} images. {len(failed_images)} failed.'
        else:
            response_data['message'] = f'Successfully deleted {deleted_count} images'

        return jsonify(response_data)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/create-folder', methods=['POST'])
def api_create_folder():
    """Create a new folder."""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name', '').strip()

        if not folder_name:
            return jsonify({
                'status': 'error',
                'message': 'No folder name specified'
            }), 400

        # Validate folder name
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', folder_name):
            return jsonify({
                'status': 'error',
                'message': 'Folder name can only contain letters, numbers, spaces, hyphens, and underscores'
            }), 400

        # Check if folder already exists
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        if os.path.exists(folder_path):
            return jsonify({
                'status': 'error',
                'message': 'Folder already exists'
            }), 400

        # Create folder
        from utils import create_class_folder
        create_class_folder(app.config['UPLOAD_FOLDER'], folder_name)

        # Return updated folder list
        all_classes = get_all_classes(app.config['UPLOAD_FOLDER'])
        folder_names = [cls['name'] for cls in all_classes]

        return jsonify({
            'status': 'success',
            'message': f'Folder "{folder_name}" created successfully',
            'folders': folder_names
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/folder_tab_info/<folder_name>')
def api_folder_tab_info(folder_name):
    """Get tab information for a specific folder."""
    try:
        tab_info = get_folder_tab_info(folder_name, app.config['UPLOAD_FOLDER'])
        return jsonify({
            'status': 'success',
            'data': tab_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/add_folder_to_tab', methods=['POST'])
def api_add_folder_to_tab():
    """Add a folder to a specific tab."""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        tab_name = data.get('tab_name')

        if not folder_name or not tab_name:
            return jsonify({
                'status': 'error',
                'message': 'Missing folder_name or tab_name'
            }), 400

        success = add_folder_to_tab(folder_name, tab_name)
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Folder "{folder_name}" added to "{tab_name}" tab'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save tab assignment'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/remove_folder_from_tab', methods=['POST'])
def api_remove_folder_from_tab():
    """Remove a folder from a specific tab."""
    try:
        data = request.get_json()
        folder_name = data.get('folder_name')
        tab_name = data.get('tab_name')

        if not folder_name or not tab_name:
            return jsonify({
                'status': 'error',
                'message': 'Missing folder_name or tab_name'
            }), 400

        if tab_name == 'All':
            return jsonify({
                'status': 'error',
                'message': 'Cannot remove folders from the "All" tab'
            }), 400

        success = remove_folder_from_tab(folder_name, tab_name)
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Folder "{folder_name}" removed from "{tab_name}" tab'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to save tab assignment'
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/folder_info/<folder_name>')
def api_folder_info(folder_name):
    """Get detailed information about a folder."""
    try:
        folder_info = get_folder_info(app.config['UPLOAD_FOLDER'], folder_name)
        if folder_info:
            return jsonify({
                'status': 'success',
                'data': folder_info
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Folder not found'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/delete_folder', methods=['POST'])
def api_delete_folder():
    """Delete an entire folder and all its contents."""
    try:
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if is_ajax:
            data = request.get_json()
            folder_name = data.get('folder_name') if data else None
        else:
            folder_name = request.form.get('folder_name')

        if not folder_name:
            error_message = 'Missing folder_name'
            if is_ajax:
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 400
            else:
                flash(error_message, 'error')
                return redirect(url_for('dashboard'))

        # Get folder info before deletion for confirmation
        folder_info = get_folder_info(app.config['UPLOAD_FOLDER'], folder_name)
        if not folder_info:
            error_message = f'Folder "{folder_name}" not found'
            if is_ajax:
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 404
            else:
                flash(error_message, 'error')
                return redirect(url_for('dashboard'))

        # Delete the folder
        success = delete_folder(app.config['UPLOAD_FOLDER'], folder_name)
        if success:
            message = f'Folder "{folder_name}" and all its contents ({folder_info["image_count"]} images) have been deleted successfully.'
            if is_ajax:
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'deleted_folder': folder_info
                })
            else:
                flash(message, 'success')
        else:
            error_message = f'Failed to delete folder "{folder_name}". It may be in use or you may not have permission.'
            if is_ajax:
                return jsonify({
                    'status': 'error',
                    'message': error_message
                }), 500
            else:
                flash(error_message, 'error')

    except Exception as e:
        error_message = f'Error deleting folder: {str(e)}'
        if is_ajax:
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 500
        else:
            flash(error_message, 'error')

    # For non-AJAX requests, redirect back to the dashboard
    return redirect(url_for('dashboard'))

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
