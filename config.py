import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'scraped_images'
    MAX_IMAGES_PER_SEARCH = int(os.environ.get('MAX_IMAGES_PER_SEARCH', 20))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
