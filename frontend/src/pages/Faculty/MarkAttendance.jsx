// frontend/src/pages/Faculty/MarkAttendance.jsx
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ImageCapture from "../../components/ImageCapture";
import { getSubjects, getStudents, markAttendanceFromFace, submitAttendance, downloadAttendance } from "../../services/apiClient";

function formatHour(hour) {
  const ampm = hour >= 12 ? "pm" : "am";
  const h = ((hour + 11) % 12) + 1;
  return `${h}:00 ${ampm}`;
}

export default function MarkAttendance() {
  const navigate = useNavigate();
  const facultyName = localStorage.getItem("facultyName") || "Faculty";

  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState("");
  const [students, setStudents] = useState([]); // [{id,name,roll,checked,disabled}]
  const [message, setMessage] = useState("");
  const [showFaceRecognition, setShowFaceRecognition] = useState(false);

  const [imageSrc, setImageSrc] = useState(null);
  const [matches, setMatches] = useState([]); // results array from backend
  const imgRef = useRef(null);
  const canvasRef = useRef(null);

  const [dateVal, setDateVal] = useState(new Date().toISOString().slice(0, 10));
  const [timeVal, setTimeVal] = useState("08:00");

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    drawBoxes();
    // eslint-disable-next-line
  }, [imageSrc, matches]);

  async function loadSubjects() {
    const res = await getSubjects();
    if (res?.success) setSubjects(res.data || []);
  }

  async function handleSubjectChange(e) {
    const subjectId = e.target.value;
    setSelectedSubject(subjectId);
    setMatches([]);
    setImageSrc(null);

    if (!subjectId) {
      setStudents([]);
      return;
    }
    const res = await getStudents(subjectId);
    if (res?.success) {
      const list = (res.data || []).map((s) => ({
        id: s.id || s.student_id,
        name: s.name || s.student_name || (s.user && s.user.name) || `Student ${s.id || s.student_id || ""}`,
        roll: s.roll || s.roll_no || "",
        checked: false,
        disabled: false,
      }));
      setStudents(list);
    }
  }

  function drawBoxes() {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas || !imageSrc) return;

    const naturalW = img.naturalWidth || img.width;
    const naturalH = img.naturalHeight || img.height;
    const displayW = img.clientWidth;
    const displayH = img.clientHeight;

    canvas.width = displayW;
    canvas.height = displayH;
    canvas.style.width = `${displayW}px`;
    canvas.style.height = `${displayH}px`;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const sx = displayW / Math.max(naturalW, 1);
    const sy = displayH / Math.max(naturalH, 1);

    // dedupe by bbox position (string) to avoid duplicate overlays
    const seen = new Map();
    matches.forEach(m => {
      const key = (m.bbox && m.bbox.join(",")) || (m.student_id ? `id_${m.student_id}` : `name_${m.name}`);
      if (!seen.has(key)) seen.set(key, m);
    });
    const uniqueMatches = Array.from(seen.values());

    const drawnPos = new Set();

    uniqueMatches.forEach((m) => {
      const bbox = m.bbox || [];
      let x = 0, y = 0, bw = 0, bh = 0;
      if (bbox.length === 4) {
        const [a, b, c, d] = bbox;
        // support two bbox formats: either [x,y,w,h] or [top,right,bottom,left]
        if (c > a && b > d && (b - d) > 0 && (c - a) > 0 && (a < 1000 && d < 1000)) {
          // treat as top,right,bottom,left -> convert
          y = a;
          const right = b;
          const bottom = c;
          x = d;
          bw = right - x;
          bh = bottom - y;
        } else {
          [x, y, bw, bh] = bbox;
        }
      }

      const dx = x * sx;
      const dy = y * sy;
      const dW = bw * sx;
      const dH = bh * sy;

      let stroke = "#00FF88"; // matched default
      if (m.status === "unknown") stroke = "#FF4444";
      if (m.already_marked) stroke = "#000000";

      ctx.lineWidth = 3;
      ctx.strokeStyle = stroke;
      ctx.strokeRect(dx, dy, dW, dH);

      // label: prefer student_name -> name -> fallback to 'UNKNOWN'
      const label = m.student_name || m.name || (m.student_id ? String(m.student_id) : "UNKNOWN");

      ctx.font = "16px Arial";
      const textW = ctx.measureText(label).width;
      const textH = 18;
      const padding = 4;

      let labelX = Math.max(dx + padding, 2);
      let labelY = dy - textH - padding;
      if (labelY < 2) labelY = dy + dH + padding;
      if (labelY + textH > canvas.height - 2) labelY = Math.max(dy - textH - padding, 2);

      const posKey = `${Math.round(labelX)}_${Math.round(labelY)}_${Math.round(textW)}`;
      if (drawnPos.has(posKey)) return;
      drawnPos.add(posKey);

      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(labelX - 2, labelY - 2, textW + 6, textH + 4);

      ctx.fillStyle = stroke;
      ctx.textBaseline = "top";
      ctx.fillText(label, labelX + 2, labelY);
    });
  }

  function buildMatchesFromResponse(res) {
    const top = res?.data || res || {};
    const results = top?.results || res?.results || [];
    const out = [];

    if (Array.isArray(results) && results.length > 0) {
      results.forEach(r => {
        out.push({
          student_id: r.student_id ?? null,
          student_name: r.student_name ?? r.name ?? null,
          name: r.name ?? r.student_name ?? null,
          confidence: r.confidence ?? 0,
          bbox: r.bbox ?? [],
          status: r.status ?? (r.student_id ? 'matched' : 'unknown'),
          already_marked: !!r.get ? !!r.get('already_marked') : !!r.already_marked
        });
      });
    } else {
      const bboxes = top?.face_bboxes || res?.face_bboxes || [];
      const names = top?.recognized_names || res?.recognized_names || [];
      const confidences = top?.confidences || res?.confidences || [];
      for (let i = 0; i < bboxes.length; i++) {
        out.push({
          student_id: null,
          student_name: names[i] || null,
          name: names[i] || null,
          confidence: confidences[i] || 0,
          bbox: bboxes[i],
          status: 'unknown',
          already_marked: false
        });
      }
    }
    return out;
  }

  const handleFaceRecognition = async (filesArray) => {
    if (!selectedSubject) {
      setMessage("Please select a subject first");
      return;
    }
    if (!filesArray || filesArray.length === 0) return;

    setMessage("Processing face recognition...");

    const form = new FormData();
    form.append("image", filesArray[0]);
    form.append("subject_id", selectedSubject);
    form.append("date", dateVal);
    form.append("time", timeVal);

    const res = await markAttendanceFromFace(form);

    // set annotated image if server returned it
    const annotated = res?.annotated_base64 || res?.data?.annotated_base64 || res?.data?.annotated_url || res?.annotated_url;
    if (annotated) {
      setImageSrc(annotated);
    } else {
      const reader = new FileReader();
      reader.onload = (ev) => setImageSrc(ev.target.result);
      reader.readAsDataURL(filesArray[0]);
    }

    const built = buildMatchesFromResponse(res);
    // normalize flags
    built.forEach(m => {
      m.already_marked = !!(m.already_marked || m.is_marked || m.alreadyMarked);
      if (!m.status) m.status = m.student_id ? 'matched' : 'unknown';
    });
    setMatches(built);

    // auto-check matched students but don't save yet; keep checkboxes editable
    setStudents(prev =>
      prev.map(s => {
        const found = built.find(m => m.student_id && String(m.student_id) === String(s.id));
        if (found) {
          // set checked true; keep editable (faculty can toggle)
          return { ...s, checked: true, disabled: false };
        }
        return s;
      })
    );

    if (res?.success) {
      setMessage("Recognition processed (check boxes & then Submit to save).");
    } else {
      setMessage(res?.message || "Face recognition processed.");
    }
    setTimeout(() => setMessage(""), 4000);
  };

  async function handleFileUpload(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    await handleFaceRecognition([f]);
  }

  function toggleCheckbox(id) {
    setStudents(prev => prev.map(s => (s.id === id ? { ...s, checked: !s.checked } : s)));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedSubject) {
      alert("Select a subject first");
      return;
    }
    const entries = students.map(s => ({ student_id: s.id, status: s.checked ? "Present" : "Absent" }));
    try {
      setMessage("Saving attendance...");
      const payload = { subject_id: parseInt(selectedSubject, 10), date: dateVal, time: timeVal, entries };
      const res = await submitAttendance(payload);
      if (res?.success) {
        setMessage("Attendance saved successfully");
        // after saving, clear checked flags and preview
        setStudents(prev => prev.map(s => ({ ...s, checked: false, disabled: false })));
        setMatches([]);
        setImageSrc(null);
      } else {
        setMessage(res?.message || "Failed to save attendance");
      }
    } catch (err) {
      setMessage(err?.message || "Error saving attendance");
    }
    setTimeout(() => setMessage(""), 4000);
  }

  async function handleDownload() {
    if (!selectedSubject) {
      setMessage("Select subject to download attendance");
      return;
    }
    setMessage("Preparing download...");
    try {
      const blob = await downloadAttendance(selectedSubject);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_subject_${selectedSubject}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setMessage("Download ready");
    } catch (err) {
      setMessage("Failed to prepare download");
    }
    setTimeout(() => setMessage(""), 3000);
  }

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h2>Faculty Dashboard - {facultyName}</h2>
          <button className="btn btn-danger" onClick={() => navigate("/")}>Logout</button>
        </div>
      </div>

      <div className="container">
        <div className="card">
          <h2 style={{ marginBottom: 20, color: "#2d3748" }}>Mark Attendance</h2>

          {message && <div className={`alert ${message.toLowerCase().includes("saved") ? "alert-success" : "alert-info"}`}>{message}</div>}

          <div className="form-group" style={{ marginBottom: 12 }}>
            <label>Select Subject</label>
            <select value={selectedSubject} onChange={handleSubjectChange} style={{ padding: 12, borderRadius: 6, border: "2px solid #e2e8f0", width: "100%" }}>
              <option value="">-- Select Subject --</option>
              {subjects.map(subject => <option key={subject.id} value={subject.id}>{subject.name} ({subject.code})</option>)}
            </select>
          </div>

          {selectedSubject && (
            <div style={{ marginTop: 12 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
                <div>
                  <label>Date:</label>
                  <input type="date" value={dateVal} onChange={(e) => setDateVal(e.target.value)} />
                </div>
                <div>
                  <label>Time:</label>
                  <select value={timeVal} onChange={(e) => setTimeVal(e.target.value)}>
                    {Array.from({ length: 10 }).map((_, i) => {
                      const hour = 8 + i;
                      const val = `${hour.toString().padStart(2, "0")}:00`;
                      return <option key={val} value={val}>{formatHour(hour)}</option>;
                    })}
                  </select>
                </div>

                <div style={{ marginLeft: "auto" }}>
                  <button className="btn btn-secondary" onClick={handleDownload}>Download Attendance</button>
                </div>
              </div>

              <button className="btn btn-primary" onClick={() => setShowFaceRecognition(s => !s)} style={{ marginBottom: 12 }}>
                {showFaceRecognition ? "Hide Face Recognition" : "Show Face Recognition"}
              </button>

              {showFaceRecognition && (
                <div className="card" style={{ background: "#f7fafc", padding: 12, marginBottom: 12 }}>
                  <h3>Face Recognition Attendance</h3>
                  <ImageCapture onCapture={handleFaceRecognition} multiple={false} />
                  <div style={{ marginTop: 8 }}>
                    <label>Or upload an image:</label>
                    <input type="file" accept="image/*" onChange={handleFileUpload} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {students.length > 0 && (
          <div className="card" style={{ marginTop: 16 }}>
            <h3 style={{ marginTop: 0 }}>Student List</h3>

            <form onSubmit={handleSubmit}>
              <div style={{ maxHeight: 360, overflowY: "auto", padding: 8 }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ textAlign: "left" }}>
                      <th>Present</th>
                      <th>Roll</th>
                      <th>Name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map(s => (
                      <tr key={s.id}>
                        <td style={{ padding: 8 }}>
                          <input type="checkbox" checked={!!s.checked} disabled={!!s.disabled} onChange={() => toggleCheckbox(s.id)} />
                        </td>
                        <td style={{ padding: 8 }}>{s.roll}</td>
                        <td style={{ padding: 8 }}>{s.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div style={{ marginTop: 12 }}>
                <button type="submit" className="btn btn-success">Submit Attendance</button>
              </div>
            </form>
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          <h3>Captured / Annotated Image</h3>
          <div style={{ position: "relative", display: imageSrc ? "inline-block" : "block" }}>
            {imageSrc ? (
              <>
                <img ref={imgRef} src={imageSrc} alt="annotated" style={{ maxWidth: "100%", display: "block" }} />
                <canvas ref={canvasRef} style={{ position: "absolute", left: 0, top: 0, pointerEvents: "none" }} />
              </>
            ) : (
              <div style={{ color: "#666" }}>No captured image to preview</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
