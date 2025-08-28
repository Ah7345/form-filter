import streamlit as st
import io
import zipfile
from docx import Document
import re

# Utility functions for parsing and cleaning
def normalize_digits(s):
    """Convert Arabic-Indic digits to ASCII digits."""
    if not s:
        return s
    
    # Arabic-Indic to ASCII mapping
    arabic_digits = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    for arabic, ascii_digit in arabic_digits.items():
        s = s.replace(arabic, ascii_digit)
    
    return s

def clean_value(s):
    """Clean and normalize values by removing duplicates, prefixes, and normalizing formatting."""
    if not s:
        return ""
    
    # Normalize digits
    s = normalize_digits(s)
    
    # Split by lines and clean each line
    lines = s.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove repeated prefixes like "المجموعة الرئيسية:" etc.
        prefixes_to_remove = [
            r'^(\s*المجموعة الرئيسية\s*[:：]\s*)+',
            r'^(\s*رمز المجموعة الرئيسية\s*[:：]\s*)+',
            r'^(\s*المجموعة الفرعية\s*[:：]\s*)+',
            r'^(\s*رمز المجموعة الفرعية\s*[:：]\s*)+',
            r'^(\s*المجموعة الثانوية\s*[:：]\s*)+',
            r'^(\s*رمز المجموعة الثانوية\s*[:：]\s*)+',
            r'^(\s*مجموعة الوحدات\s*[:：]\s*)+',
            r'^(\s*رمز الوحدات\s*[:：]\s*)+',
            r'^(\s*المهنة\s*[:：]\s*)+',
            r'^(\s*رمز المهنة\s*[:：]\s*)+',
            r'^(\s*موقع العمل\s*[:：]\s*)+',
            r'^(\s*المرتبة\s*[:：]\s*)+'
        ]
        
        for prefix_pattern in prefixes_to_remove:
            line = re.sub(prefix_pattern, '', line)
        
        # Normalize separators (Arabic semicolons/commas)
        line = line.replace('؛', ';').replace('،', ',')
        
        # Collapse multiple spaces
        line = re.sub(r'\s+', ' ', line).strip()
        
        if line and line not in cleaned_lines:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def extract_reference_data(text):
    """Extract reference data for 'البيانات المرجعية للمهنة' section."""
    expected_labels = [
        "المجموعة الرئيسية", "رمز المجموعة الرئيسية", "المجموعة الفرعية", "رمز المجموعة الفرعية",
        "المجموعة الثانوية", "رمز المجموعة الثانوية", "مجموعة الوحدات", "رمز الوحدات",
        "المهنة", "رمز المهنة", "موقع العمل", "المرتبة"
    ]
    
    # Build regex pattern for all labels
    label_pattern = '|'.join(map(re.escape, expected_labels))
    pattern = rf'^\s*({label_pattern})\s*[:：]\s*(.+)$'
    
    extracted_data = {}
    lines = text.split('\n')
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            label = match.group(1)
            value = clean_value(match.group(2))
            if label not in extracted_data and value:
                extracted_data[label] = value
    
    # Ensure all expected labels exist (fill with empty if missing)
    result = {}
    for label in expected_labels:
        result[label] = extracted_data.get(label, "")
    
    return result

def extract_communication_channels(text):
    """Extract internal and external communication channels."""
    internal_channels = []
    external_channels = []
    
    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'الجهات الداخلية' in line or 'داخلي' in line:
            current_section = 'internal'
            # Extract channels from this line
            channels_text = re.sub(r'^.*?[:：]\s*', '', line)
            if channels_text:
                channels = [c.strip() for c in re.split(r'[,،;؛]', channels_text) if c.strip()]
                internal_channels.extend(channels)
        elif 'الجهات الخارجية' in line or 'خارجي' in line:
            current_section = 'external'
            # Extract channels from this line
            channels_text = re.sub(r'^.*?[:：]\s*', '', line)
            if channels_text:
                channels = [c.strip() for c in re.split(r'[,،;؛]', channels_text) if c.strip()]
                external_channels.extend(channels)
        elif 'الغرض من التواصل' in line and current_section:
            purpose_text = re.sub(r'^.*?[:：]\s*', '', line)
            if purpose_text:
                purpose = clean_value(purpose_text)
                if current_section == 'internal' and internal_channels:
                    # Associate purpose with internal channels
                    pass  # Will be handled in the table creation
                elif current_section == 'external' and external_channels:
                    # Associate purpose with external channels
                    pass  # Will be handled in the table creation
    
    return {
        'internal': internal_channels,
        'external': external_channels
    }

def extract_profession_levels(text):
    """Extract profession levels information."""
    levels_data = {}
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if 'مستوى المهنة' in line:
            levels_data['مستوى المهنة القياسي'] = clean_value(re.sub(r'^.*?[:：]\s*', '', line))
        elif 'رمز المستوى' in line:
            levels_data['رمز المستوى المهني'] = clean_value(re.sub(r'^.*?[:：]\s*', '', line))
        elif 'الدور المهني' in line:
            levels_data['الدور المهني'] = clean_value(re.sub(r'^.*?[:：]\s*', '', line))
        elif 'الترتيب' in line or 'التدرج المهني' in line:
            levels_data['التدرج المهني (المرتبة)'] = clean_value(re.sub(r'^.*?[:：]\s*', '', line))
    
    # Ensure all expected fields exist
    expected_fields = ['مستوى المهنة القياسي', 'رمز المستوى المهني', 'الدور المهني', 'التدرج المهني (المرتبة)']
    for field in expected_fields:
        if field not in levels_data:
            levels_data[field] = ""
    
    return levels_data

def extract_competencies(text):
    """Extract competencies split by type."""
    competencies = {
        'الجدارات السلوكية': [],
        'الجدارات الأساسية': [],
        'الجدارات القيادية': [],
        'الجدارات الفنية': []
    }
    
    lines = text.split('\n')
    current_type = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Determine competency type
        if 'سلوكية' in line:
            current_type = 'الجدارات السلوكية'
        elif 'أساسية' in line:
            current_type = 'الجدارات الأساسية'
        elif 'قيادية' in line:
            current_type = 'الجدارات القيادية'
        elif 'فنية' in line:
            current_type = 'الجدارات الفنية'
        elif current_type and ':' in line:
            # Extract competencies from this line
            comp_text = re.sub(r'^.*?[:：]\s*', '', line)
            if comp_text:
                comps = [c.strip() for c in re.split(r'[,،;؛]', comp_text) if c.strip()]
                competencies[current_type].extend(comps)
    
    return competencies

def extract_tasks(text):
    """Extract tasks split by category."""
    tasks = {
        'المهام القيادية/الإشرافية': [],
        'المهام التخصصية': [],
        'مهام أخرى إضافية': []
    }
    
    lines = text.split('\n')
    current_category = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Determine task category
        if 'قيادية' in line or 'إشرافية' in line:
            current_category = 'المهام القيادية/الإشرافية'
        elif 'تخصصية' in line:
            current_category = 'المهام التخصصية'
        elif 'مهام أخرى' in line or 'إضافية' in line:
            current_category = 'مهام أخرى إضافية'
        elif current_category and ':' in line:
            # Extract tasks from this line
            task_text = re.sub(r'^.*?[:：]\s*', '', line)
            if task_text:
                task_list = [t.strip() for t in re.split(r'[,،;؛]', task_text) if t.strip()]
                tasks[current_category].extend(task_list)
    
    return tasks

def extract_kpis(text):
    """Extract KPIs with measurement methods."""
    kpis = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for KPI patterns like "1- {kpi} - طريقة القياس: {method}"
        kpi_match = re.match(r'^(\d+)[-ـ]\s*(.+?)\s*[-ـ]\s*طريقة القياس\s*[:：]\s*(.+)$', line)
        if kpi_match:
            kpis.append({
                'الرقم': kpi_match.group(1),
                'مؤشر الأداء': clean_value(kpi_match.group(2)),
                'طريقة القياس': clean_value(kpi_match.group(3))
            })
    
    # If no structured KPIs found, try to extract from general text
    if not kpis:
        kpi_text = clean_value(text)
        if kpi_text:
            kpis = [{'الرقم': '1', 'مؤشر الأداء': kpi_text, 'طريقة القياس': 'قياس مباشر'}]
    
    return kpis

# DOCX building helper functions
def add_title(doc, text):
    """Add a centered, bold title."""
    title = doc.add_heading(text, 0)
    title.alignment = 1  # Center alignment
    return title

def add_keyval_table(doc, title, rows):
    """Add a 2-column key-value table."""
    if not rows:
        return
    
    # Create table
    table = doc.add_table(rows=len(rows) + 1, cols=2)
    table.style = 'Table Grid'
    
    # Header row
    header_cells = table.rows[0].cells
    header_cells[0].text = title
    header_cells[1].text = "القيمة"
    
    # Make header bold and center
    for cell in header_cells:
        for paragraph in cell.paragraphs:
            paragraph.alignment = 1  # Center
            for run in paragraph.runs:
                run.bold = True
    
    # Data rows
    for i, (key, value) in enumerate(rows.items() if isinstance(rows, dict) else enumerate(rows)):
        row_cells = table.rows[i + 1].cells
        if isinstance(rows, dict):
            row_cells[0].text = str(key)
            row_cells[1].text = str(value) if value else ""
        else:
            row_cells[0].text = str(key)
            row_cells[1].text = str(value) if value else ""
        
        # Make label column bold
        for paragraph in row_cells[0].paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Set RTL alignment for all cells
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 2  # RTL alignment
    
    # Add spacing after table
    doc.add_paragraph("")

def add_list_table(doc, title, items):
    """Add a single-column list table."""
    if not items:
        return
    
    # Create table
    table = doc.add_table(rows=len(items) + 1, cols=1)
    table.style = 'Table Grid'
    
    # Header row
    header_cell = table.rows[0].cells[0]
    header_cell.text = title
    
    # Make header bold and center
    for paragraph in header_cell.paragraphs:
        paragraph.alignment = 1  # Center
        for run in paragraph.runs:
            run.bold = True
    
    # Data rows
    for i, item in enumerate(items):
        row_cell = table.rows[i + 1].cells[0]
        row_cell.text = str(item)
    
    # Set RTL alignment for all cells
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 2  # RTL alignment
    
    # Add spacing after table
    doc.add_paragraph("")

def add_two_col_table(doc, title, rows):
    """Add a two-column table for communication channels."""
    if not rows:
        return
    
    # Create table
    table = doc.add_table(rows=len(rows) + 1, cols=2)
    table.style = 'Table Grid'
    
    # Header row
    header_cells = table.rows[0].cells
    header_cells[0].text = title
    header_cells[1].text = "الغرض من التواصل"
    
    # Make header bold and center
    for cell in header_cells:
        for paragraph in cell.paragraphs:
            paragraph.alignment = 1  # Center
            for run in paragraph.runs:
                run.bold = True
    
    # Data rows
    for i, row_data in enumerate(rows):
        row_cells = table.rows[i + 1].cells
        if isinstance(row_data, dict):
            row_cells[0].text = str(row_data.get('جهة', ''))
            row_cells[1].text = str(row_data.get('غرض', ''))
        else:
            row_cells[0].text = str(row_data[0]) if len(row_data) > 0 else ""
            row_cells[1].text = str(row_data[1]) if len(row_data) > 1 else ""
    
    # Set RTL alignment for all cells
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 2  # RTL alignment
    
    # Add spacing after table
    doc.add_paragraph("")

def add_kpi_table(doc, title, rows):
    """Add a 3-column KPI table."""
    if not rows:
        return
    
    # Create table
    table = doc.add_table(rows=len(rows) + 1, cols=3)
    table.style = 'Table Grid'
    
    # Header row
    header_cells = table.rows[0].cells
    header_cells[0].text = "الرقم"
    header_cells[1].text = "مؤشرات الأداء الرئيسية"
    header_cells[2].text = "طريقة القياس"
    
    # Make header bold and center
    for cell in header_cells:
        for paragraph in cell.paragraphs:
            paragraph.alignment = 1  # Center
            for run in paragraph.runs:
                run.bold = True
    
    # Data rows
    for i, row_data in enumerate(rows):
        row_cells = table.rows[i + 1].cells
        if isinstance(row_data, dict):
            row_cells[0].text = str(row_data.get('الرقم', i + 1))
            row_cells[1].text = str(row_data.get('مؤشر الأداء', ''))
            row_cells[2].text = str(row_data.get('طريقة القياس', ''))
        else:
            row_cells[0].text = str(i + 1)
            row_cells[1].text = str(row_data[0]) if len(row_data) > 0 else ""
            row_cells[2].text = str(row_data[1]) if len(row_data) > 1 else ""
    
    # Set RTL alignment for all cells
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 2  # RTL alignment
    
    # Add spacing after table
    doc.add_paragraph("")

def build_filled_docx_bytes(template_bytes: bytes, job_title: str, data: dict) -> bytes:
    """
    Build a filled DOCX using structured tables following the exact template design.
    This creates clean, professional documents with proper table structures.
    """
    try:
        # Create a new document
        doc = Document()
        
        # Add title - centered and bold
        title = add_title(doc, f"نموذج بطاقة الوصف المهني — {job_title}")
        
        # Add spacing after title
        doc.add_paragraph("")
        
        # Section 1: البيانات المرجعية للمهنة (Job Reference Data)
        ref_data = extract_reference_data(data.get("ref", ""))
        # Override with job title
        ref_data["المهنة"] = job_title
        add_keyval_table(doc, "1- البيانات المرجعية للمهنة", ref_data)
        
        # Section 2: الملخص العام للمهنة (General Summary)
        summary_data = clean_value(data.get("summary", "")) or "لا يوجد ملخص"
        add_keyval_table(doc, "2- الملخص العام للمهنة", {"الملخص العام": summary_data})
        
        # Section 3: قنوات التواصل (Communication Channels)
        channels = extract_communication_channels(data.get("channels", ""))
        
        # Internal channels table
        if channels['internal']:
            internal_rows = [{'جهة': channel, 'غرض': 'تنسيق العمل'} for channel in channels['internal']]
            add_two_col_table(doc, "3- قنوات التواصل الداخلية", internal_rows)
        
        # External channels table
        if channels['external']:
            external_rows = [{'جهة': channel, 'غرض': 'التواصل مع العملاء'} for channel in channels['external']]
            add_two_col_table(doc, "3- قنوات التواصل الخارجية", external_rows)
        
        # Section 4: مستويات المهنة القياسية (Standard Profession Levels)
        levels_data = extract_profession_levels(data.get("levels", ""))
        add_keyval_table(doc, "4- مستويات المهنة القياسية", levels_data)
        
        # Section 5: الجدارات (Competencies)
        competencies = extract_competencies(data.get("competencies", ""))
        for comp_type, comp_list in competencies.items():
            if comp_list:
                add_list_table(doc, f"5- {comp_type}", comp_list)
        
        # Section 6: إدارة الأداء المهني (Performance Management)
        kpis = extract_kpis(data.get("kpis", ""))
        if kpis:
            add_kpi_table(doc, "6- إدارة الأداء المهني", kpis)
        
        # Section 7: المهام (Tasks)
        tasks = extract_tasks(data.get("tasks", ""))
        for task_type, task_list in tasks.items():
            if task_list:
                add_list_table(doc, f"7- {task_type}", task_list)
        
        # Add Form B: نموذج الوصف الفعلي (Actual Description Form)
        doc.add_heading("نموذج الوصف الفعلي", level=1)
        doc.add_paragraph("")
        
        # Form B Section 1: المهام (Tasks)
        if tasks:
            for task_type, task_list in tasks.items():
                if task_list:
                    add_list_table(doc, f"1- {task_type}", task_list)
        
        # Form B Section 2: الجدارات السلوكية والفنية (Behavioral and Technical Competencies)
        behavioral_comps = competencies.get('الجدارات السلوكية', [])
        technical_comps = competencies.get('الجدارات الفنية', [])
        
        if behavioral_comps:
            behavioral_rows = [{'الرقم': i+1, 'الجدارة': comp, 'مستوى الإتقان': 'متقدم'} 
                             for i, comp in enumerate(behavioral_comps[:5])]
            add_kpi_table(doc, "2- الجدارات السلوكية والفنية", behavioral_rows)
        
        if technical_comps:
            technical_rows = [{'الرقم': i+1, 'الجدارة': comp, 'مستوى الإتقان': 'متقدم'} 
                            for i, comp in enumerate(technical_comps[:5])]
            add_kpi_table(doc, "2- الجدارات الفنية", technical_rows)
        
        # Form B Section 3: إدارة الأداء المهني (Performance Management)
        if kpis:
            add_kpi_table(doc, "3- إدارة الأداء المهني", kpis)
        
        # Save the rendered document to bytes
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.read()
        
    except Exception as e:
        st.error(f"خطأ في ملء القالب: {e}")
        return template_bytes

def zip_many(named_bytes: dict[str, bytes]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w') as zf:
        for name, data in named_bytes.items():
            zf.writestr(name, data)
    bio.seek(0)
    return bio.read()

def read_docx_paragraphs(file_bytes: bytes) -> str:
    """Read DOCX file and return all text content."""
    try:
        doc = Document(io.BytesIO(file_bytes))
        text_content = ""
        
        # Read paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content += paragraph.text.strip() + "\n"
        
        # Read tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_content += cell.text.strip() + "\n"
        
        return text_content.strip()
    except Exception as e:
        st.error(f"خطأ في قراءة ملف DOCX: {e}")
        return ""

def slice_jobs_from_source(source_text: str) -> list:
    """Extract job blocks from source text using flexible patterns."""
    if not source_text:
        return []
    
    # Split by lines and look for job patterns
    lines = source_text.split('\n')
    jobs = []
    current_job = []
    current_job_title = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for job title patterns (more flexible)
        if any(keyword in line for keyword in ['مدير', 'مشرف', 'موظف', 'مهندس', 'محلل', 'مطور', 'مصمم', 'محاسب', 'محامي', 'طبيب', 'معلم', 'مدرس']):
            # Save previous job if exists
            if current_job and current_job_title:
                jobs.append({
                    'title': current_job_title,
                    'content': '\n'.join(current_job)
                })
            
            # Start new job
            current_job_title = line
            current_job = [line]
        else:
            # Add line to current job
            current_job.append(line)
    
    # Add the last job
    if current_job and current_job_title:
        jobs.append({
            'title': current_job_title,
            'content': '\n'.join(current_job)
        })
    
    # If no jobs found with strict patterns, try relaxed approach
    if not jobs:
        # Split by double newlines or major separators
        sections = re.split(r'\n\s*\n+', source_text)
        for i, section in enumerate(sections):
            if section.strip():
                lines = section.strip().split('\n')
                if lines:
                    title = lines[0].strip()
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                    jobs.append({
                        'title': title,
                        'content': content
                    })
    
    return jobs

# Streamlit UI
st.set_page_config(
    page_title="نظام ملء النماذج المهنية",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .upload-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #007bff;
    }
    
    .mode-selector {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .info-box {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    
    .download-section {
        background: #e8f5e8;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">نظام ملء النماذج المهنية</div>', unsafe_allow_html=True)

# Mode selector
with st.container():
    st.markdown('<div class="mode-selector">', unsafe_allow_html=True)
    mode = st.radio(
        "اختر وضع المعالجة:",
        ["Multi-Job", "Single Job"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Template upload section
with st.container():
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📄 رفع القالب")
    
    template_file = st.file_uploader(
        "ارفع قالب DOCX",
        type=['docx'],
        help="ارفع قالب DOCX فارغ أو يحتوي على محتوى أساسي"
    )
    
    if template_file:
        st.markdown('<div class="success-box">✅ تم رفع القالب بنجاح</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Data source upload section
with st.container():
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("### 📊 رفع مصدر البيانات")
    
    src_file = st.file_uploader(
        "ارفع ملف مصدر البيانات",
        type=['docx', 'json', 'csv'],
        help="ارفع ملف DOCX يحتوي على بيانات الوظائف، أو ملف JSON/CSV"
    )
    
    if src_file:
        st.markdown('<div class="success-box">✅ تم رفع مصدر البيانات بنجاح</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Processing and download section
if template_file and src_file:
    with st.container():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown("### 🚀 معالجة البيانات")
        
        if st.button("ابدأ المعالجة", type="primary"):
            with st.spinner("جاري معالجة البيانات..."):
                try:
                    # Load data based on file type
                    if src_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        # DOCX source file
                        source_text = read_docx_paragraphs(src_file.read())
                        jobs = slice_jobs_from_source(source_text)
                        
                        if not jobs:
                            st.error("لم يتم اكتشاف أي وظائف في ملف المصدر")
                            st.stop()
                        
                        # Limit jobs based on mode
                        if mode == "Single Job":
                            jobs = jobs[:1]
                        
                        st.success(f"تم اكتشاف {len(jobs)} وظيفة")
                        
                        # Process each job
                        filled_docs = {}
                        for i, job in enumerate(jobs):
                            job_title = job['title']
                            job_content = job['content']
                            
                            # Extract data from job content
                            data = {
                                "ref": job_content,
                                "summary": job_content,
                                "channels": job_content,
                                "levels": job_content,
                                "competencies": job_content,
                                "kpis": job_content,
                                "tasks": job_content
                            }
                            
                            # Generate filled document
                            filled_doc = build_filled_docx_bytes(
                                template_file.read(),
                                job_title,
                                data
                            )
                            
                            # Create filename
                            filename = f"نموذج_مملوء_{i+1}_{job_title[:30]}.docx"
                            filled_docs[filename] = filled_doc
                        
                        # Download options
                        if len(filled_docs) == 1:
                            # Single file download
                            filename = list(filled_docs.keys())[0]
                            st.download_button(
                                label="📥 تحميل النموذج المملوء",
                                data=filled_docs[filename],
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        else:
                            # Multiple files - ZIP download
                            zip_data = zip_many(filled_docs)
                            st.download_button(
                                label="📦 تحميل جميع النماذج (ZIP)",
                                data=zip_data,
                                file_name="نماذج_مملوءة.zip",
                                mime="application/zip"
                            )
                            
                            # Individual file downloads
                            st.markdown("**أو قم بتحميل كل ملف على حدة:**")
                            for filename, doc_data in filled_docs.items():
                                st.download_button(
                                    label=f"📥 {filename}",
                                    data=doc_data,
                                    file_name=filename,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                )
                    
                    else:
                        # JSON/CSV source files
                        st.info("معالجة ملفات JSON/CSV قيد التطوير")
                
                except Exception as e:
                    st.error(f"حدث خطأ أثناء المعالجة: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6c757d; padding: 1rem;'>"
    "نظام ملء النماذج المهنية - إصدار 2.0 | تم التطوير باستخدام Streamlit"
    "</div>",
    unsafe_allow_html=True
)