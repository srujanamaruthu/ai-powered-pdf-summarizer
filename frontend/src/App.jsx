import React, { useState } from 'react';
import Header from './components/Header';
import DragDropUpload from './components/DragDropUpload';
import ExtractedTextSection from './components/ExtractedTextSection';
import SummaryCard from './components/SummaryCard';

export default function App() {
  const [fileInfo, setFileInfo] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [summaryResult, setSummaryResult] = useState(null);

  const handleUploadStart = () => {
    setFileInfo(null);
    setExtractedText('');
    setSummaryResult(null);
  };

  const handleUploadSuccess = (data) => {
    setFileInfo({
      filename: data.filename,
      fileSizeKb: data.fileSizeKb,
      pages: data.pages,
      wordCount: data.wordCount,
      methodUsed: data.methodUsed
    });
    setExtractedText(data.text);
  };

  const handleUploadError = (errorMsg) => {
    setFileInfo(null);
    setExtractedText('');
    setSummaryResult(null);
  };

  const handleReset = () => {
    setFileInfo(null);
    setExtractedText('');
    setSummaryResult(null);
  };

  return (
    <div className="app-container">
      <Header />
      
      <main className="hero-section">
        <h1 className="hero-title">
          Summarize Any PDF with <span>AI Precision</span>
        </h1>
        <p className="hero-subtitle">
          Instantly extract text and generate high-quality summaries from your PDF files. Choose your preferred AI model and length settings.
        </p>
      </main>

      <div className="dashboard-grid">
        {/* Left Side: Upload & Raw Text Display */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          <DragDropUpload 
            onUploadStart={handleUploadStart}
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
            onReset={handleReset}
            fileInfo={fileInfo}
          />
          <ExtractedTextSection 
            text={extractedText} 
            wordCount={fileInfo?.wordCount} 
          />
        </div>

        {/* Right Side: Summarizer Controls & Result */}
        <div>
          <SummaryCard 
            text={extractedText}
            summaryResult={summaryResult}
            setSummaryResult={setSummaryResult}
          />
        </div>
      </div>
    </div>
  );
}
