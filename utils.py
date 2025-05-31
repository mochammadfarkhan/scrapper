import os
import shutil
import json
from PIL import Image
import hashlib
from config import Config

def create_class_folder(base_path, class_name):
    """Create a folder for the specified class within the scraped_images directory.

    Note: base_path parameter is kept for backward compatibility but is ignored.
    All class folders are now created within the scraped_images directory.
    """
    # Always ensure the class folder is created within scraped_images
    # Use Config.UPLOAD_FOLDER for consistency
    scraped_images_dir = Config.UPLOAD_FOLDER

    # Create scraped_images directory if it doesn't exist
    if not os.path.exists(scraped_images_dir):
        os.makedirs(scraped_images_dir)

    # Create the class folder within scraped_images
    class_path = os.path.join(scraped_images_dir, class_name)
    if not os.path.exists(class_path):
        os.makedirs(class_path)
    return class_path

def get_all_classes(base_path):
    """Get all class folders and their image counts."""
    classes = []
    if not os.path.exists(base_path):
        return classes

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            image_count = count_images_in_folder(item_path)
            classes.append({
                'name': item,
                'path': item_path,
                'image_count': image_count
            })
    return classes

def get_grouped_classes(base_path):
    """Get all classes grouped by categories for dashboard tabs."""
    classes = get_all_classes(base_path)
    if not classes:
        return {}

    # Define category keywords for grouping
    category_keywords = {
        'Animals': ['cat', 'dog', 'bird', 'fish', 'animal', 'pet', 'wildlife', 'horse', 'cow', 'sheep', 'pig', 'chicken', 'duck', 'rabbit', 'mouse', 'rat', 'elephant', 'lion', 'tiger', 'bear', 'wolf', 'fox', 'deer', 'monkey', 'ape', 'snake', 'lizard', 'frog', 'turtle', 'shark', 'whale', 'dolphin', 'penguin', 'eagle', 'owl', 'parrot', 'butterfly', 'bee', 'spider', 'ant'],
        'Vehicles': ['car', 'truck', 'bus', 'bike', 'motorcycle', 'bicycle', 'vehicle', 'auto', 'plane', 'airplane', 'helicopter', 'boat', 'ship', 'train', 'subway', 'taxi', 'van', 'suv', 'sedan', 'coupe', 'convertible', 'jeep', 'scooter', 'skateboard'],
        'Food': ['food', 'pizza', 'burger', 'sandwich', 'salad', 'fruit', 'apple', 'banana', 'orange', 'grape', 'strawberry', 'cake', 'bread', 'pasta', 'rice', 'meat', 'chicken', 'beef', 'pork', 'fish', 'seafood', 'vegetable', 'tomato', 'potato', 'carrot', 'onion', 'cheese', 'milk', 'coffee', 'tea', 'juice', 'water', 'wine', 'beer', 'dessert', 'chocolate', 'candy', 'cookie'],
        'Nature': ['tree', 'flower', 'plant', 'garden', 'forest', 'mountain', 'river', 'lake', 'ocean', 'beach', 'sky', 'cloud', 'sun', 'moon', 'star', 'nature', 'landscape', 'sunset', 'sunrise', 'grass', 'leaf', 'branch', 'rock', 'stone', 'sand', 'snow', 'rain', 'storm', 'rainbow'],
        'Objects': ['chair', 'table', 'book', 'phone', 'computer', 'laptop', 'keyboard', 'mouse', 'monitor', 'camera', 'watch', 'glasses', 'bag', 'shoe', 'clothes', 'shirt', 'pants', 'dress', 'hat', 'toy', 'ball', 'game', 'tool', 'hammer', 'screwdriver', 'knife', 'fork', 'spoon', 'plate', 'cup', 'bottle', 'box', 'key', 'lock', 'door', 'window', 'mirror', 'lamp', 'clock'],
        'People': ['person', 'people', 'man', 'woman', 'child', 'baby', 'boy', 'girl', 'family', 'couple', 'friend', 'student', 'teacher', 'doctor', 'nurse', 'worker', 'business', 'professional', 'athlete', 'artist', 'musician', 'actor', 'model', 'face', 'portrait', 'smile', 'happy', 'sad', 'angry'],
        'Sports': ['sport', 'football', 'soccer', 'basketball', 'baseball', 'tennis', 'golf', 'swimming', 'running', 'cycling', 'skiing', 'snowboarding', 'surfing', 'climbing', 'hiking', 'gym', 'fitness', 'exercise', 'yoga', 'dance', 'boxing', 'wrestling', 'hockey', 'volleyball', 'badminton', 'cricket', 'rugby'],
        'Technology': ['technology', 'tech', 'computer', 'laptop', 'smartphone', 'tablet', 'software', 'hardware', 'internet', 'web', 'app', 'digital', 'electronic', 'robot', 'ai', 'artificial', 'intelligence', 'code', 'programming', 'data', 'network', 'server', 'database', 'cloud', 'cyber', 'virtual', 'augmented', 'reality']
    }

    # Initialize groups
    groups = {'All': classes}

    # Group classes by categories
    for category, keywords in category_keywords.items():
        category_classes = []
        for class_item in classes:
            class_name_lower = class_item['name'].lower()
            if any(keyword in class_name_lower for keyword in keywords):
                category_classes.append(class_item)

        if category_classes:  # Only add category if it has classes
            groups[category] = category_classes

    # Group remaining classes alphabetically
    categorized_names = set()
    for category, category_classes in groups.items():
        if category != 'All':
            categorized_names.update(class_item['name'] for class_item in category_classes)

    uncategorized_classes = [c for c in classes if c['name'] not in categorized_names]

    # Create alphabetical groups for uncategorized classes
    alpha_groups = {}
    for class_item in uncategorized_classes:
        first_letter = class_item['name'][0].upper()
        if first_letter not in alpha_groups:
            alpha_groups[first_letter] = []
        alpha_groups[first_letter].append(class_item)

    # Add alphabetical groups to main groups
    for letter in sorted(alpha_groups.keys()):
        groups[f"#{letter}"] = alpha_groups[letter]

    return groups

def get_manual_tab_assignments():
    """Get manual tab assignments from JSON file."""
    assignments_file = os.path.join(Config.UPLOAD_FOLDER, '.tab_assignments.json')
    if os.path.exists(assignments_file):
        try:
            with open(assignments_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_manual_tab_assignments(assignments):
    """Save manual tab assignments to JSON file."""
    assignments_file = os.path.join(Config.UPLOAD_FOLDER, '.tab_assignments.json')
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(assignments_file), exist_ok=True)
        with open(assignments_file, 'w') as f:
            json.dump(assignments, f, indent=2)
        return True
    except IOError:
        return False

def add_folder_to_tab(folder_name, tab_name):
    """Add a folder to a specific tab."""
    assignments = get_manual_tab_assignments()
    if folder_name not in assignments:
        assignments[folder_name] = {'added_to': [], 'removed_from': []}

    # Add to the tab if not already there
    if tab_name not in assignments[folder_name]['added_to']:
        assignments[folder_name]['added_to'].append(tab_name)

    # Remove from removed_from list if it was there
    if tab_name in assignments[folder_name]['removed_from']:
        assignments[folder_name]['removed_from'].remove(tab_name)

    return save_manual_tab_assignments(assignments)

def remove_folder_from_tab(folder_name, tab_name):
    """Remove a folder from a specific tab."""
    assignments = get_manual_tab_assignments()
    if folder_name not in assignments:
        assignments[folder_name] = {'added_to': [], 'removed_from': []}

    # Add to removed_from list if not already there
    if tab_name not in assignments[folder_name]['removed_from']:
        assignments[folder_name]['removed_from'].append(tab_name)

    # Remove from added_to list if it was there
    if tab_name in assignments[folder_name]['added_to']:
        assignments[folder_name]['added_to'].remove(tab_name)

    return save_manual_tab_assignments(assignments)

def get_grouped_classes_with_manual_assignments(base_path):
    """Get all classes grouped by categories with manual assignments applied."""
    classes = get_all_classes(base_path)
    if not classes:
        return {}

    # Get automatic grouping
    groups = get_grouped_classes(base_path)
    manual_assignments = get_manual_tab_assignments()

    # Apply manual assignments
    for folder_name, assignments in manual_assignments.items():
        # Find the folder object
        folder_obj = next((c for c in classes if c['name'] == folder_name), None)
        if not folder_obj:
            continue

        # Remove folder from tabs it was manually removed from
        for tab_name in assignments.get('removed_from', []):
            if tab_name in groups and folder_obj in groups[tab_name]:
                groups[tab_name].remove(folder_obj)

        # Add folder to tabs it was manually added to
        for tab_name in assignments.get('added_to', []):
            if tab_name not in groups:
                groups[tab_name] = []
            if folder_obj not in groups[tab_name]:
                groups[tab_name].append(folder_obj)

    # Remove empty groups (except 'All')
    groups = {k: v for k, v in groups.items() if v or k == 'All'}

    return groups

def get_available_tabs():
    """Get list of all available tab names."""
    return [
        'All', 'Animals', 'Vehicles', 'Food', 'Nature',
        'Objects', 'People', 'Sports', 'Technology'
    ]

def get_folder_tab_info(folder_name, base_path):
    """Get information about which tabs a folder belongs to."""
    groups = get_grouped_classes_with_manual_assignments(base_path)
    manual_assignments = get_manual_tab_assignments()

    # Find which tabs contain this folder
    current_tabs = []
    for tab_name, folders in groups.items():
        if any(f['name'] == folder_name for f in folders):
            current_tabs.append(tab_name)

    # Get manual assignment info
    folder_assignments = manual_assignments.get(folder_name, {'added_to': [], 'removed_from': []})

    return {
        'current_tabs': current_tabs,
        'manually_added_to': folder_assignments['added_to'],
        'manually_removed_from': folder_assignments['removed_from'],
        'available_tabs': get_available_tabs()
    }

def count_images_in_folder(folder_path):
    """Count the number of image files in a folder."""
    if not os.path.exists(folder_path):
        return 0

    count = 0
    for file in os.listdir(folder_path):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            count += 1
    return count

def get_images_in_class(base_path, class_name):
    """Get all images in a specific class folder."""
    class_path = os.path.join(base_path, class_name)
    images = []

    if not os.path.exists(class_path):
        return images

    for file in os.listdir(class_path):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            images.append({
                'filename': file,
                'path': os.path.join(class_path, file),
                'relative_path': os.path.join(class_name, file).replace('\\', '/')
            })
    return images

def delete_image(base_path, class_name, filename):
    """Delete a specific image file."""
    file_path = os.path.join(base_path, class_name, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def delete_folder(base_path, folder_name):
    """Delete an entire folder and all its contents."""
    folder_path = os.path.join(base_path, folder_name)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path)

            # Also remove any manual tab assignments for this folder
            assignments = get_manual_tab_assignments()
            if folder_name in assignments:
                del assignments[folder_name]
                save_manual_tab_assignments(assignments)

            return True
        except OSError as e:
            print(f"Error deleting folder {folder_path}: {e}")
            return False
    return False

def get_folder_info(base_path, folder_name):
    """Get detailed information about a folder."""
    folder_path = os.path.join(base_path, folder_name)
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return None

    image_count = count_images_in_folder(folder_path)

    # Calculate folder size
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except OSError:
        total_size = 0

    # Format size in human readable format
    def format_size(size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    return {
        'name': folder_name,
        'path': folder_path,
        'image_count': image_count,
        'size_bytes': total_size,
        'size_formatted': format_size(total_size)
    }

def validate_image(file_path):
    """Validate if the file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except:
        return False

def generate_unique_filename(original_filename, folder_path):
    """Generate a unique filename to avoid conflicts."""
    name, ext = os.path.splitext(original_filename)
    counter = 1
    new_filename = original_filename

    while os.path.exists(os.path.join(folder_path, new_filename)):
        new_filename = f"{name}_{counter}{ext}"
        counter += 1

    return new_filename
