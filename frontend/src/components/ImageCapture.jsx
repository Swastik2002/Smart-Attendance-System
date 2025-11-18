import React, { useRef, useState, useEffect } from 'react';

function ImageCapture({ onCapture, multiple = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [capturedImages, setCapturedImages] = useState([]);

  // cleanup when component unmounts or stream changes
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (videoRef.current) {
        if ('srcObject' in videoRef.current) videoRef.current.srcObject = null;
        else videoRef.current.src = '';
      }
    };
  }, [stream]);

  // Attach the stream to the video element AFTER the video has rendered
  useEffect(() => {
    if (isCameraOn && stream && videoRef.current) {
      const videoEl = videoRef.current;
      try {
        if ('srcObject' in videoEl) {
          videoEl.srcObject = stream;
        } else {
          // fallback for very old browsers
          videoEl.src = URL.createObjectURL(stream);
        }
        // attempt to play (some browsers require user gesture, ignore errors)
        videoEl.play().catch(() => {});
      } catch (err) {
        // If attaching fails, stop the stream and surface error
        stream.getTracks().forEach(t => t.stop());
        setStream(null);
        setIsCameraOn(false);
        alert('Failed to attach camera stream: ' + err.message);
      }
    }
  }, [isCameraOn, stream]);

  const startCamera = async () => {
    try {
      // obtain the media stream first, then enable UI (so video element mounts)
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false
      });
      setStream(mediaStream);
      setIsCameraOn(true);
      // do NOT set videoRef.current.srcObject here — wait for effect above
    } catch (err) {
      alert('Failed to access camera: ' + (err.message || String(err)));
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setIsCameraOn(false);
    if (videoRef.current) {
      if ('srcObject' in videoRef.current) videoRef.current.srcObject = null;
      else videoRef.current.src = '';
    }
  };

  const capturePhoto = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    if (!video) {
      alert('Video not ready yet. Try again.');
      return;
    }

    // if video metadata not loaded yet, wait a tick
    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;

    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);

    canvas.toBlob((blob) => {
      if (!blob) {
        alert('Failed to capture image');
        return;
      }
      const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' });

      if (multiple) {
        const newImages = [...capturedImages, file];
        setCapturedImages(newImages);
        onCapture(newImages);
      } else {
        onCapture([file]);
        // stop camera after single capture (existing behavior)
        stopCamera();
      }
    }, 'image/jpeg');
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    if (multiple) {
      const newImages = [...capturedImages, ...files];
      setCapturedImages(newImages);
      onCapture(newImages);
    } else {
      onCapture(files);
    }
  };

  return (
    <div>
      {!isCameraOn ? (
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={startCamera}
          >
            Start Camera
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            multiple={multiple}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => fileInputRef.current && fileInputRef.current.click()}
          >
            Upload Image{multiple ? 's' : ''}
          </button>
        </div>
      ) : (
        <div className="video-container">
          <video ref={videoRef} autoPlay playsInline />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <div className="video-controls">
            <button
              type="button"
              className="btn btn-success"
              onClick={capturePhoto}
            >
              Capture Photo
            </button>
            <button
              type="button"
              className="btn btn-danger"
              onClick={stopCamera}
            >
              Stop Camera
            </button>
          </div>
        </div>
      )}

      {capturedImages.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <p><strong>Captured Images: {capturedImages.length}</strong></p>
        </div>
      )}
    </div>
  );
}

export default ImageCapture;
