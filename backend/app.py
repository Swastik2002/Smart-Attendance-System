import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config
from db import init_db

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.faculty_routes import faculty_bp, attendance_bp
from routes.student_routes import student_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    # ensure upload/temp folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    # initialize DB
    init_db(app)

    # register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')    # faculty endpoints
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')  # attendance endpoints
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # face blueprint (train) comes from admin_routes (face_bp)
    from routes.admin_routes import face_bp
    app.register_blueprint(face_bp, url_prefix='/api/face')

    # Static route for serving annotated images saved in TEMP_FOLDER
    # Example: GET http://localhost:5000/temp/recognized_123.jpg
    @app.route('/temp/<path:filename>')
    def temp_file(filename):
        return send_from_directory(app.config['TEMP_FOLDER'], filename)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
