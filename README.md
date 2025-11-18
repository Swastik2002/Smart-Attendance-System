# College Attendance System 2.0

AI-Powered Face Recognition Attendance System built with React and Flask.

## Features

- Admin Dashboard: Add students, faculty, and subjects
- Faculty Portal: Mark attendance manually or using face recognition
- Student Portal: View attendance statistics by subject
- Face Recognition: Automated attendance marking using AI

## Structure

```
/
├── frontend/          # React application
└── backend/           # Flask API with face recognition
```

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Backend runs on http://localhost:5000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

## Default Admin Credentials

- Email: admin@gmail.com
- Password: admin123

## Technology Stack

- Frontend: React, React Router, Axios
- Backend: Flask, SQLite, SQLAlchemy
- Face Recognition: OpenCV, face_recognition library
- Authentication: Session-based for Faculty & Students
