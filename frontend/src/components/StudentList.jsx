import React from 'react';

function StudentList({ students, onMarkAttendance }) {
  return (
    <div className="card">
      <h3 style={{ marginBottom: '20px', color: '#2d3748' }}>Student List</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Roll No</th>
            <th>Name</th>
            <th>Email</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {students.map((student) => (
            <tr key={student.id}>
              <td>{student.roll}</td>
              <td>{student.name}</td>
              <td>{student.email}</td>
              <td>
                <button
                  className="btn btn-success"
                  style={{ padding: '6px 12px', fontSize: '14px' }}
                  onClick={() => onMarkAttendance(student.id, 'Present')}
                >
                  Present
                </button>
                {' '}
                <button
                  className="btn btn-danger"
                  style={{ padding: '6px 12px', fontSize: '14px' }}
                  onClick={() => onMarkAttendance(student.id, 'Absent')}
                >
                  Absent
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default StudentList;
