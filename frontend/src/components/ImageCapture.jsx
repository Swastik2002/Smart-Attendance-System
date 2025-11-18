import React, { useRef, useState, useEffect } from 'react';

function ImageCapture({ onCapture, multiple = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [capturedImages, setCapturedImages] = useState([]);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });
      videoRef.current.srcObject = mediaStream;
      setStream(mediaStream);
      setIsCameraOn(true);
    } catch (err) {
      alert('Failed to access camera: ' + err.message);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsCameraOn(false);
    }
  };

  const capturePhoto = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      const file = new File([blob], `capture_${Date.now()}.jpg`, { type: 'image/jpeg' });

      if (multiple) {
        const newImages = [...capturedImages, file];
        setCapturedImages(newImages);
        onCapture(newImages);
      } else {
        onCapture([file]);
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
            onClick={() => fileInputRef.current.click()}
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
