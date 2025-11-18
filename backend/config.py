import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "attendance.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'face_data', 'students')
    TEMP_FOLDER = os.path.join(BASE_DIR, 'uploads', 'temp')

    ENCODINGS_FILE = os.path.join(BASE_DIR, 'attendance_encodings.pkl')

    ADMIN_EMAIL = 'admin@gmail.com'
    ADMIN_PASSWORD = 'admin123'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
