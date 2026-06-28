# AI-Powered PDF Summarizer

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-blue?style=for-the-badge&logo=react)](https://pdf-summarizer-frontend-ahc3.onrender.com)
[![Backend API](https://img.shields.io/badge/API-Online-green?style=for-the-badge&logo=flask)](https://ai-powered-pdf-summarizer.onrender.com)

A modern, responsive web application that extracts text from PDF documents and generates summaries of adjustable lengths (Short, Medium, Detailed) using multiple NLP approaches (TextRank, OpenAI GPT). It features a premium light blue and white glassmorphism user interface.

## Core Features

- **Drag-and-Drop PDF Upload**: An interactive, responsive upload zone that supports files up to 20MB.
- **Robust Text Extraction**: Operates on a fallback chain starting from the pure-Python `pypdf` library (which installs instantly on any OS/Python environment), with hooks to automatically adopt `pymupdf` or `pdfplumber` if installed.
- **Adjustable Summarization Lengths**:
  - **Short**: captures the core thesis in under 100 words (~10% size reduction).
  - **Medium**: summarizes the argument flow in under 250 words (~25% size reduction).
  - **Detailed**: generates structured bullet-point details under 500 words (~50% size reduction).
- **Flexible NLP Engines**:
  - **TextRank (Local Extractive)**: Runs offline on the server. Uses sentence tokenization and term frequency metrics to identify key sentences. Highly reliable with zero configuration or API keys required.
  - **OpenAI GPT (Cloud Abstractive)**: Uses `gpt-4o-mini` for high-quality semantic summaries. Integrates an API key input in the frontend, securely stored locally in the browser's `localStorage`.
- **Extracted Text Viewer**: A scrollable panel showing the raw extracted text along with the file's metadata (filename, page count, word count).
- **Interactive Action Bar**: Includes buttons to copy the summary to the clipboard, download the summary as a formatted `.txt` file, or clear the dashboard.

---

## Folder Structure

```
pdf-summarizer/
├── frontend/                 # Vite + React Frontend
│   ├── src/
│   │   ├── components/       # UI Components (Header, DragDropUpload, etc.)
│   │   ├── App.jsx           # Main Dashboard Orchestrator
│   │   ├── index.css         # Global Stylesheet (Custom fonts & Design Tokens)
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js        # Vite Config with Backend proxy config
│   └── package.json
│
├── backend/                  # Flask REST API Backend
│   ├── app.py                # Flask Server with Upload & Summarize endpoints
│   ├── summarizer.py         # TextRank & OpenAI summarization engine
│   ├── pdf_reader.py         # PDF text extractor with fallback chains
│   ├── requirements.txt      # Python Dependencies
│   └── uploads/              # Dynamic folder for temporary file parsing
│
└── README.md                 # Project Documentation
```

---

## Getting Started

### Prerequisites

- **Python** (version 3.10 or higher)
- **Node.js** (version 18 or higher) and **npm**

### Step 1: Set up the Backend Server

1. Open your terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask API server:
   ```bash
   python app.py
   ```
   The backend API will run locally at `http://127.0.0.1:5000/`.

### Step 2: Set up the Frontend Application

1. Open a new terminal window and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install the frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
   The application will run locally at `http://localhost:5173/`. Open this link in your browser to view the application.

---

## Advanced Local Summarization (Optional)

To enable offline Hugging Face neural network summarization (using a local BART model), uncomment the optional packages in `backend/requirements.txt` and install them inside your activated virtual environment:
```bash
pip install torch transformers pymupdf
```
*Note: Downloading local PyTorch and transformers models will fetch ~300MB of data and requires compatible OS build tools.*
