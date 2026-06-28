import React from 'react';

export default function Header() {
  return (
    <header className="app-header">
      <div className="logo-container">
        <div className="logo-icon">PDF</div>
        <span className="logo-text">AI Summarizer</span>
      </div>
      <div className="header-tagline">
        Smart NLP Document Summaries
      </div>
    </header>
  );
}
