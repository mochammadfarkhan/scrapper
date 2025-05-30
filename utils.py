import os
import shutil
from PIL import Image
import hashlib
from config import Config

def create_class_folder(base_path, class_name):
    """Create a folder for the specified class if it doesn't exist."""
    class_path = os.path.join(base_path, class_name)
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
