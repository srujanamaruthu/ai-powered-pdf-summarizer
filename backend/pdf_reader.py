import os
import pypdf

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

class PDFExtractionError(Exception):
    """Custom exception for PDF extraction issues."""
    pass

def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extracts text and metadata from a PDF file using a fallback mechanism:
    1. PyMuPDF (fitz) - fastest and most accurate
    2. pdfplumber - good for layout and fallback
    3. pypdf - general backup
    
    Args:
        file_path (str): The absolute path to the PDF file.
        
    Returns:
        dict: A dictionary containing:
            - text (str): The extracted text.
            - pages (int): Number of pages in the PDF.
            - success (bool): Extraction status.
            - method_used (str): The library that successfully extracted the text.
            - file_size_kb (float): File size in kilobytes.
    """
    if not os.path.exists(file_path):
        raise PDFExtractionError("PDF file does not exist at the specified path.")
    
    file_size_bytes = os.path.getsize(file_path)
    file_size_kb = round(file_size_bytes / 1024, 2)
    
    # Check for encryption and corruption using PyPDF first
    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            num_pages = len(reader.pages)
            if reader.is_encrypted:
                # Try decrypting with empty password
                try:
                    reader.decrypt("")
                except Exception:
                    raise PDFExtractionError("The PDF file is encrypted and password-protected.")
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"The PDF file appears to be corrupted or invalid: {str(e)}")

    extracted_text = ""
    method_used = ""

    # Method 1: PyMuPDF (fitz)
    if HAS_FITZ:
        try:
            doc = fitz.open(file_path)
            num_pages = len(doc)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            
            raw_text = "\n".join(text_parts).strip()
            if raw_text:
                extracted_text = raw_text
                method_used = "PyMuPDF (fitz)"
            doc.close()
        except Exception as e:
            # Fallback to next method
            pass

    # Method 2: pdfplumber
    if not extracted_text and HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(file_path) as pdf:
                num_pages = len(pdf.pages)
                text_parts = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                raw_text = "\n".join(text_parts).strip()
                if raw_text:
                    extracted_text = raw_text
                    method_used = "pdfplumber"
        except Exception as e:
            # Fallback to next method
            pass

    # Method 3: pypdf
    if not extracted_text:
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                num_pages = len(reader.pages)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                raw_text = "\n".join(text_parts).strip()
                if raw_text:
                    extracted_text = raw_text
                    method_used = "pypdf"
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract text from PDF using all methods. Error: {str(e)}")

    if not extracted_text:
        raise PDFExtractionError(
            "The PDF was read successfully, but no text could be extracted. "
            "It might contain only scanned images/photos. OCR is not supported."
        )

    # Clean whitespace and return
    cleaned_text = clean_extracted_text(extracted_text)
    
    return {
        "text": cleaned_text,
        "pages": num_pages,
        "success": True,
        "method_used": method_used,
        "file_size_kb": file_size_kb,
        "word_count": len(cleaned_text.split())
    }

def clean_extracted_text(text: str) -> str:
    """
    Cleans up the extracted text by fixing hyphenations, removing extra whitespaces,
    and removing non-printable characters.
    """
    import re
    # Replace soft hyphens and fix line-break hyphens
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    # Replace multiple vertical/horizontal whitespace characters with a single space or newline
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()
