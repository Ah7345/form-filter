# Form Filler

A Streamlit web app that fills templates (DOCX/PDF/XLSX) with data from various sources (JSON/CSV/YAML).

## Features

- **DOCX**: Uses `{{key}}` placeholders for best Arabic text rendering
- **PDF**: Fills AcroForm fields (must be fillable PDF)
- **XLSX**: Replaces `{{key}}` placeholders across all sheets
- **Data Sources**: JSON, YAML, CSV (first row with headers)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

3. Open browser at `http://localhost:8501`

## Usage

1. Upload a template file (DOCX/PDF/XLSX)
2. Upload a data source (JSON/CSV/YAML)
3. Click "Fill Template"
4. Download the filled file

## Notes

- For Arabic text, prefer DOCX templates
- PDF must be AcroForm (fillable)
- CSV uses first row only
- All processing is local (no network calls)
