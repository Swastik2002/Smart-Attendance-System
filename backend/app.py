# backend/app.py
import os
from flask import Flask, send_from_directory, request
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

    # Restrict origins to your dev front-end; adjust or add production origins as needed
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # ensure upload/temp folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

    # initialize DB
    init_db(app)

    # register blueprints (with same prefixes you used previously)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')       # faculty endpoints
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance') # attendance endpoints
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # face blueprint (train) comes from admin_routes (face_bp)
    from routes.admin_routes import face_bp
    app.register_blueprint(face_bp, url_prefix='/api/face')

    # Static route for serving annotated images saved in TEMP_FOLDER
    # Example: GET http://localhost:5000/temp/recognized_123.jpg
    @app.route('/temp/<path:filename>')
    def temp_file(filename):
        return send_from_directory(app.config['TEMP_FOLDER'], filename)

    # Extra: ensure OPTIONS requests and custom headers are allowed
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin and origin in allowed_origins:
            response.headers.setdefault('Access-Control-Allow-Origin', origin)
            response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
            response.headers.setdefault('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
            response.headers.setdefault('Access-Control-Allow-Credentials', 'true')
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    # bind to 0.0.0.0 for convenience; runs on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
