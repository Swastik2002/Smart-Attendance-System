import os
from flask import Flask
from flask_cors import CORS
from config import Config
from db import init_db

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.faculty_routes import faculty_bp
from routes.student_routes import student_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    init_db(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(student_bp, url_prefix='/api/student')

    from routes.faculty_routes import attendance_bp
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')

    from routes.admin_routes import face_bp
    app.register_blueprint(face_bp, url_prefix='/api/face')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
