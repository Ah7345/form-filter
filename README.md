# نظام بطاقة الوصف المهني - Job Description Card System

A professional Streamlit application for creating and managing job description cards with AI-powered analysis and PDF generation.

## 🌟 Features

- **AI-Powered Analysis**: Upload documents and automatically extract job information
- **Professional PDF Reports**: Generate beautiful, formatted PDFs with Arabic text support
- **RTL UI**: Right-to-left interface optimized for Arabic users
- **File Upload Support**: PDF, DOCX, and TXT file processing
- **Comprehensive Forms**: Complete job description data collection

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- pip package manager

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd tem

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Font Setup (Required for Arabic PDFs)

The app requires Arabic fonts for proper PDF generation. These fonts are automatically downloaded:

- `fonts/NotoNaskhArabic-Regular.ttf` - Regular Arabic text
- `fonts/NotoNaskhArabic-Bold.ttf` - Bold Arabic text

**Important**: If fonts are missing, the app will show an error and cannot generate PDFs.

### 4. OpenAI API Key Setup

#### Option A: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

#### Option B: Streamlit Secrets
Create `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "your-api-key-here"
```

### 5. Run the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## 🔧 Configuration

### Font Configuration

The app automatically uses the Noto Naskh Arabic fonts for PDF generation. These fonts provide:

- **Proper Arabic Text Rendering**: No more boxes (■■■■) in PDFs
- **RTL Support**: Right-to-left text alignment
- **Professional Appearance**: Clean, readable Arabic text

### API Configuration

- **Model**: Uses GPT-4o-mini for optimal performance
- **Temperature**: Set to 0.1 for consistent, structured output
- **Max Tokens**: 3000 for comprehensive analysis

## 📁 Project Structure

```
tem/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── fonts/                # Arabic font files
│   ├── NotoNaskhArabic-Regular.ttf
│   └── NotoNaskhArabic-Bold.ttf
├── .streamlit/           # Streamlit configuration
│   └── secrets.toml     # API keys and secrets
└── README.md            # This file
```

## 🎯 Usage

### 1. File Upload & AI Analysis

1. Upload a job description document (PDF, DOCX, TXT)
2. Click "🤖 تحليل باستخدام AI" to analyze with AI
3. The AI will automatically extract and fill form fields

### 2. Manual Data Entry

1. Fill in the job description form manually
2. Use the expandable sections for different data categories
3. Save your progress as you go

### 3. PDF Generation

1. Click "📄 إنشاء تقرير PDF احترافي"
2. Download the professionally formatted PDF
3. All Arabic text will render correctly with proper fonts

## 🔍 Troubleshooting

### Arabic Text Shows as Boxes (■■■■)

**Solution**: Ensure the font files exist in the `fonts/` directory:
```bash
ls -la fonts/
# Should show:
# NotoNaskhArabic-Regular.ttf
# NotoNaskhArabic-Bold.ttf
```

### OpenAI API Errors

**Solution**: Verify your API key is set correctly:
```bash
echo $OPENAI_API_KEY
# Should show your API key
```

### Font Registration Errors

**Solution**: Check font file permissions and paths:
```bash
ls -la fonts/*.ttf
# Ensure files are readable
```

## 🛡️ Security

- **No Hardcoded Keys**: API keys are read from environment or secrets
- **Secure Storage**: Use environment variables or Streamlit secrets
- **Input Validation**: All user inputs are validated and sanitized

## 📊 Dependencies

- **Streamlit**: Web application framework
- **OpenAI**: AI text analysis
- **ReportLab**: PDF generation
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **arabic-reshaper**: Arabic text reshaping
- **python-bidi**: Right-to-left text support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the error messages in the app
3. Ensure all dependencies are installed
4. Verify font files are present

---

**Note**: This application requires the Noto Naskh Arabic fonts for proper Arabic text rendering in PDFs. These fonts are automatically downloaded during setup.
