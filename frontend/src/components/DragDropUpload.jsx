import React, { useState, useRef } from 'react';

export default function DragDropUpload({ onUploadStart, onUploadSuccess, onUploadError, onReset, fileInfo }) {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processFile = async (file) => {
    if (!file) return;

    // Validate type
    if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
      const errMsg = "Invalid file type. Please upload a PDF document.";
      setError(errMsg);
      onUploadError(errMsg);
      return;
    }

    // Validate size (20MB limit)
    const maxSizeBytes = 20 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      const errMsg = "File exceeds the 20 MB limit. Please select a smaller PDF.";
      setError(errMsg);
      onUploadError(errMsg);
      return;
    }

    setError(null);
    setLoading(true);
    onUploadStart();

    const formData = new FormData();
    formData.append("file", file);

    const API_BASE = import.meta.env.VITE_API_URL || '';
    try {
      const response = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to extract text from PDF.");
      }

      onUploadSuccess({
        text: data.text,
        filename: data.filename,
        fileSizeKb: data.file_size_kb,
        pages: data.pages,
        wordCount: data.word_count,
        methodUsed: data.method_used
      });
    } catch (err) {
      const errMsg = err.message || "An error occurred while uploading the file.";
      setError(errMsg);
      onUploadError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const handleClear = () => {
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    onReset();
  };

  return (
    <div className="summary-card-el">
      <h2 className="card-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        Upload PDF
      </h2>

      {!fileInfo && !loading && (
        <div 
          className={`upload-zone ${dragActive ? "drag-active" : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={onButtonClick}
        >
          <input 
            ref={fileInputRef}
            type="file"
            className="hidden-file-input"
            style={{ display: 'none' }}
            accept=".pdf"
            onChange={handleChange}
          />
          
          <div className="upload-icon-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          
          <div className="upload-text">Drag & drop your PDF file here</div>
          <div className="upload-subtext">or click to browse from device (up to 20 MB)</div>
        </div>
      )}

      {loading && (
        <div className="loading-wrapper">
          <div className="loading-spinner"></div>
          <div className="loading-text">Extracting PDF text...</div>
        </div>
      )}

      {fileInfo && !loading && (
        <div className="file-info-container">
          <div className="file-info-left">
            <div className="file-pdf-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
            <div className="file-name-meta">
              <div className="file-name" title={fileInfo.filename}>{fileInfo.filename}</div>
              <div className="file-meta-pills">
                <span className="meta-pill">{fileInfo.fileSizeKb} KB</span>
                <span className="meta-pill">{fileInfo.pages} Page{fileInfo.pages > 1 ? 's' : ''}</span>
              </div>
            </div>
          </div>
          <button className="clear-btn" onClick={handleClear} title="Clear PDF">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      )}

      {error && (
        <div className="alert-box error">
          <span className="alert-icon">⚠️</span>
          <div>{error}</div>
        </div>
      )}
    </div>
  );
}
