// frontend/src/pages/Faculty/EditAttendance.jsx
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getSubjects,
  getAttendanceDates,
  getAttendanceForDate,
  updateAttendance
} from "../../services/apiClient";

export default function EditAttendance() {
  const navigate = useNavigate();
  const facultyName = localStorage.getItem("facultyName") || "Faculty";  // ✅ ADDED

  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [dates, setDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    (async () => {
      const res = await getSubjects();
      if (res?.success) setSubjects(res.data || []);
    })();
  }, []);

  useEffect(() => {
    setDates([]);
    setSelectedDate("");
    setStudents([]);
    setMessage("");

    if (!selectedSubject) return;

    (async () => {
      setLoading(true);
      const res = await getAttendanceDates(selectedSubject);
      if (res?.success) {
        setDates(res.dates || []);
        if (Array.isArray(res.dates) && res.dates.length > 0) {
          setSelectedDate(res.dates[0]);
        }
      } else {
        setMessage(res?.message || "Failed to fetch dates");
      }
      setLoading(false);
    })();
  }, [selectedSubject]);

  useEffect(() => {
    if (!selectedSubject || !selectedDate) return;

    (async () => {
      setLoading(true);
      const res = await getAttendanceForDate(selectedSubject, selectedDate);
      if (res?.success) {
        setStudents(res.students || []);
      } else {
        setStudents([]);
        setMessage(res?.message || "Failed to fetch attendance");
      }
      setLoading(false);
    })();
  }, [selectedDate, selectedSubject]);

  const toggleAll = (val) => {
    setStudents(prev => prev.map(s => ({ ...s, present: !!val })));
  };

  const toggleStudent = (id) => {
    setStudents(prev =>
      prev.map(s =>
        s.id === id ? { ...s, present: !s.present } : s
      )
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedSubject || !selectedDate) {
      setMessage("Select subject and date");
      return;
    }

    const entries = students.map(s => ({
      student_id: s.id,
      present: !!s.present,
      confidence: s.confidence
    }));

    setLoading(true);

    const payload = {
      subject_id: parseInt(selectedSubject, 10),
      date: selectedDate,
      time: new Date().toTimeString().slice(0, 5),
      entries
    };

    const res = await updateAttendance(payload);

    if (res?.success) {
      setMessage("Attendance updated successfully");
    } else {
      setMessage(res?.message || "Failed to update attendance");
    }

    setLoading(false);
    setTimeout(() => setMessage(""), 4000);
  };

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Faculty Dashboard - {facultyName}</h2> {/* ✅ ADDED */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn-primary"
              onClick={() => navigate("/faculty/mark-attendance")}
            >
              Mark Attendance
            </button>

            <button
              className="btn btn-danger"
              onClick={() => navigate("/")}
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="card">
          <h3>Select Subject & Date</h3>

          <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
            <select
              value={selectedSubject}
              onChange={(e) => setSelectedSubject(e.target.value)}
              style={{ padding: 8 }}
            >
              <option value="">-- Select Subject --</option>
              {subjects.map(s =>
                <option key={s.id} value={s.id}>
                  {s.name} ({s.code})
                </option>
              )}
            </select>

            <select
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{ padding: 8 }}
            >
              <option value="">-- Select Date --</option>
              {dates.map(d =>
                <option key={d} value={d}>{d}</option>
              )}
            </select>

            <div style={{ marginLeft: "auto" }}>
              <button className="btn btn-secondary" onClick={() => toggleAll(true)}>
                Check All
              </button>{" "}
              <button className="btn btn-secondary" onClick={() => toggleAll(false)}>
                Uncheck All
              </button>
            </div>
          </div>

          {message && (
            <div className={`alert ${message.toLowerCase().includes("success") ? "alert-success" : "alert-info"}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ maxHeight: 360, overflowY: "auto", padding: 8 }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left" }}>
                    <th>Present</th>
                    <th>Roll</th>
                    <th>Name</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {students.map(s => (
                    <tr key={s.id}>
                      <td style={{ padding: 8 }}>
                        <input
                          type="checkbox"
                          checked={!!s.present}
                          onChange={() => toggleStudent(s.id)}
                        />
                      </td>
                      <td style={{ padding: 8 }}>{s.roll}</td>
                      <td style={{ padding: 8 }}>{s.name}</td>
                      <td style={{ padding: 8 }}>{s.confidence ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div style={{ marginTop: 12 }}>
              <button type="submit" className="btn btn-success" disabled={loading}>
                {loading ? "Saving..." : "Update Attendance"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
