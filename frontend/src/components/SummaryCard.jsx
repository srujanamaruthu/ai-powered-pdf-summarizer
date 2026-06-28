import React, { useState, useEffect } from 'react';

export default function SummaryCard({ text, onSummaryGenerated, summaryResult, setSummaryResult }) {
  const [model, setModel] = useState('textrank'); // 'textrank', 'transformers', 'openai'
  const [length, setLength] = useState('medium'); // 'short', 'medium', 'detailed'
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  // Load API key from localStorage if it exists
  useEffect(() => {
    const savedKey = localStorage.getItem('pdf_summarizer_openai_key');
    if (savedKey) {
      setApiKey(savedKey);
    }
  }, []);

  const handleApiKeyChange = (e) => {
    const val = e.target.value;
    setApiKey(val);
    localStorage.setItem('pdf_summarizer_openai_key', val);
  };

  const handleSummarize = async () => {
    if (!text) return;
    
    if (model === 'openai' && !apiKey) {
      setError("Please enter your OpenAI API key to use GPT models.");
      return;
    }

    setLoading(true);
    setError(null);
    setSummaryResult(null);

    const API_BASE = import.meta.env.VITE_API_URL || '';
    try {
      const response = await fetch(`${API_BASE}/api/summarize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          model_type: model,
          length,
          api_key: model === 'openai' ? apiKey : null
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate summary.");
      }

      setSummaryResult(data);
      if (onSummaryGenerated) {
        onSummaryGenerated(data);
      }
    } catch (err) {
      setError(err.message || "An error occurred during summarization.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!summaryResult?.summary) return;
    try {
      await navigator.clipboard.writeText(summaryResult.summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy summary: ", err);
    }
  };

  const handleDownload = () => {
    if (!summaryResult?.summary) return;
    const element = document.createElement("a");
    const file = new Blob([
      `AI-POWERED PDF SUMMARY\n`,
      `========================\n`,
      `Model Used: ${summaryResult.model_used.toUpperCase()}\n`,
      `Length: ${length.toUpperCase()}\n`,
      `Word Count (Before): ${summaryResult.word_count_before}\n`,
      `Word Count (After): ${summaryResult.word_count_after}\n`,
      `Reduction: ${summaryResult.reduction_percentage}%\n`,
      `========================\n\n`,
      summaryResult.summary
    ], { type: 'text/plain;charset=utf-8' });
    
    element.href = URL.createObjectURL(file);
    element.download = `pdf_summary_${length}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleReset = () => {
    setSummaryResult(null);
    setError(null);
  };

  return (
    <div className="summary-card-el">
      <h2 className="card-title">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        Summary Engine
      </h2>



      {/* 2. Summary Length Selector */}
      <div className="control-group">
        <label className="control-label">Summary Length</label>
        <div className="options-selector">
          <button 
            type="button"
            className={`option-btn ${length === 'short' ? 'active' : ''}`}
            onClick={() => setLength('short')}
          >
            Short (~10%)
          </button>
          <button 
            type="button"
            className={`option-btn ${length === 'medium' ? 'active' : ''}`}
            onClick={() => setLength('medium')}
          >
            Medium (~25%)
          </button>
          <button 
            type="button"
            className={`option-btn ${length === 'detailed' ? 'active' : ''}`}
            onClick={() => setLength('detailed')}
          >
            Detailed (~50%)
          </button>
        </div>
      </div>

      {/* 3. Action Buttons */}
      {!loading && !summaryResult && (
        <button 
          className="summarize-action-btn"
          onClick={handleSummarize}
          disabled={!text}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          Generate Summary
        </button>
      )}

      {/* 4. Loading State */}
      {loading && (
        <div className="loading-wrapper">
          <div className="loading-spinner"></div>
          <div className="loading-text">Generating Summary...</div>
        </div>
      )}

      {/* 5. Error Alerts */}
      {error && (
        <div className="alert-box error">
          <span className="alert-icon">⚠️</span>
          <div>{error}</div>
        </div>
      )}

      {/* 6. Summary Warnings (e.g. Model Fallback) */}
      {summaryResult?.warning && (
        <div className="alert-box warning">
          <span className="alert-icon">⚡</span>
          <div>{summaryResult.warning}</div>
        </div>
      )}

      {/* 7. Summary Result Card */}
      {summaryResult && !loading && (
        <div className="summary-result-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px', animation: 'fadeIn 0.5s ease-out' }}>
          <div className="summary-result-header">
            <h3 className="control-label" style={{ fontSize: '15px' }}>Generated Summary</h3>
            <div className="summary-stats-wrapper">
              <span className="stat-tag reduction">-{summaryResult.reduction_percentage}% size</span>
              <span className="stat-tag words">{summaryResult.word_count_after} words</span>
            </div>
          </div>

          <div className="summary-text-box">
            {summaryResult.summary}
          </div>

          <div className="summary-actions-row">
            <button className="action-btn" onClick={handleCopy}>
              {copied ? (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <span style={{ color: 'var(--success)' }}>Copied!</span>
                </>
              ) : (
                <>
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  Copy
                </>
              )}
            </button>
            <button className="action-btn" onClick={handleDownload} title="Download as TXT file">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download
            </button>
            <button className="action-btn" onClick={handleReset} title="Clear Summary">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
              Clear
            </button>
          </div>
        </div>
      )}

      {/* Empty State when no PDF is uploaded */}
      {!text && !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          </div>
          <div>Upload a PDF document first to enable the summarizer.</div>
        </div>
      )}
    </div>
  );
}
