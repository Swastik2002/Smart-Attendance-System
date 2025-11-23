import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './components/Landing';
import AdminLogin from './pages/Auth/AdminLogin';
import FacultyLogin from './pages/Auth/FacultyLogin';
import StudentLogin from './pages/Auth/StudentLogin';
import AddStudent from './pages/Admin/AddStudent';
import AddFaculty from './pages/Admin/AddFaculty';
import AddSubject from './pages/Admin/AddSubject';
import MarkAttendance from './pages/Faculty/MarkAttendance';
import EditAttendance from './pages/Faculty/EditAttendance';
import StudentDashboard from './pages/Student/StudentDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/faculty/login" element={<FacultyLogin />} />
        <Route path="/student/login" element={<StudentLogin />} />
        <Route path="/admin/add-student" element={<AddStudent />} />
        <Route path="/admin/add-faculty" element={<AddFaculty />} />
        <Route path="/admin/add-subject" element={<AddSubject />} />
        <Route path="/faculty/mark-attendance" element={<MarkAttendance />} />
        <Route path="/faculty/edit-attendance" element={<EditAttendance />} />
        <Route path="/student/dashboard" element={<StudentDashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
