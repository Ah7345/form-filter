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

st.set_page_config(page_title="ملء النماذج (Multi-Job)", layout="centered")
st.title("ملء النماذج — متعدد الوظائف (DOCX → DOCX)")
st.caption("قم برفع قالب DOCX ومصدر بيانات يحتوي على معلومات عدة وظائف. سيقوم التطبيق بملء الجداول الموجودة تلقائياً.")

# Add processing mode selection
processing_mode = st.radio(
    "وضع المعالجة / Processing Mode:",
    ["متعدد الوظائف / Multi-Job", "وظيفة واحدة / Single Job"],
    horizontal=True
)

tmpl_file = st.file_uploader("رفع القالب (DOCX) / Upload Template (DOCX)", type=["docx"])
st.info("💡 **هام**: التطبيق سيقوم بإنشاء العناصر النائبة تلقائياً وملء الجداول")

# Show template upload status
if tmpl_file:
    st.success(f"✅ تم رفع القالب: {tmpl_file.name}")

# Define src_file outside the conditional blocks
if processing_mode == "متعدد الوظائف / Multi-Job":
    src_file = st.file_uploader("رفع مصدر البيانات (DOCX) / Upload Data Source (DOCX)", type=["docx"])
    st.info("📋 وضع متعدد الوظائف: سيقوم بمعالجة جميع الوظائف الموجودة في مصدر البيانات وإنشاء نموذج لكل وظيفة")
else:
    src_file = st.file_uploader("رفع بيانات الوظيفة (DOCX) / Upload Job Data (DOCX)", type=["docx"])
    st.info("📄 وضع وظيفة واحدة: سيقوم بمعالجة الوظيفة الأولى الموجودة في مصدر البيانات")

# Show source file upload status
if src_file:
    st.success(f"✅ تم رفع مصدر البيانات: {src_file.name}")

# ---------- helpers ----------
def create_template_structure():
    """
    Create the standard template structure with placeholders
    """
    template_structure = {
        "نموذج بطاقة الوصف المهني": {
            "البيانات المرجعية للمهنة": {
                "المجموعة الرئيسية": "{{main_group}}",
                "رمز المجموعة الرئيسية": "{{main_group_code}}",
                "المجموعة الفرعية": "{{sub_group}}",
                "رمز المجموعة الفرعية": "{{sub_group_code}}",
                "المجموعة الثانوية": "{{secondary_group}}",
                "رمز المجموعة الثانوية": "{{secondary_group_code}}",
                "مجموعة الوحدات": "{{units_group}}",
                "رمز الوحدات": "{{units_code}}",
                "المهنة": "{{profession}}",
                "رمز المهنة": "{{profession_code}}",
                "موقع العمل": "{{work_location}}",
                "المرتبة": "{{rank}}"
            },
            "الملخص العام للمهنة": "{{summary}}",
            "قنوات التواصل": {
                "جهات التواصل الداخلية": [
                    {
                        "الجهة": "{{internal_party_1}}",
                        "الغرض من التواصل": "{{internal_purpose_1}}"
                    }
                ],
                "جهات التواصل الخارجية": [
                    {
                        "الجهة": "{{external_party_1}}",
                        "الغرض من التواصل": "{{external_purpose_1}}"
                    }
                ]
            },
            "مستويات المهنة القياسية": [
                {
                    "مستوى المهنة القياسي": "{{level_1}}",
                    "رمز المستوى المهني": "{{level_code_1}}",
                    "الدور المهني": "{{role_1}}",
                    "التدرج المهني (المرتبة)": "{{progression_1}}"
                }
            ],
            "الجدارات": {
                "الجدارات السلوكية": ["{{behavioral_comp_1}}", "{{behavioral_comp_2}}", "{{behavioral_comp_3}}"],
                "الجدارات الأساسية": ["{{core_comp_1}}", "{{core_comp_2}}", "{{core_comp_3}}"],
                "الجدارات القيادية": ["{{leadership_comp_1}}", "{{leadership_comp_2}}", "{{leadership_comp_3}}"],
                "الجدارات الفنية": ["{{technical_comp_1}}", "{{technical_comp_2}}", "{{technical_comp_3}}"]
            }
        },
        "نموذج الوصف الفعلي": {
            "المهام": {
                "المهام القيادية/الإشرافية": ["{{leadership_task_1}}", "{{leadership_task_2}}", "{{leadership_task_3}}"],
                "المهام التخصصية": ["{{specialized_task_1}}", "{{specialized_task_2}}", "{{specialized_task_3}}"],
                "مهام أخرى إضافية": ["{{additional_task_1}}", "{{additional_task_2}}", "{{additional_task_3}}"]
            },
            "الجدارات السلوكية والفنية": {
                "الجدارات السلوكية": [
                    {
                        "الرقم": "1",
                        "الجدارة": "{{behavioral_comp_1}}",
                        "مستوى الإتقان": "{{proficiency_1}}"
                    },
                    {
                        "الرقم": "2",
                        "الجدارة": "{{behavioral_comp_2}}",
                        "مستوى الإتقان": "{{proficiency_2}}"
                    },
                    {
                        "الرقم": "3",
                        "الجدارة": "{{behavioral_comp_3}}",
                        "مستوى الإتقان": "{{proficiency_3}}"
                    },
                    {
                        "الرقم": "4",
                        "الجدارة": "{{behavioral_comp_4}}",
                        "مستوى الإتقان": "{{proficiency_4}}"
                    },
                    {
                        "الرقم": "5",
                        "الجدارة": "{{behavioral_comp_5}}",
                        "مستوى الإتقان": "{{proficiency_5}}"
                    }
                ],
                "الجدارات الفنية": [
                    {
                        "الرقم": "1",
                        "الجدارة": "{{technical_comp_1}}",
                        "مستوى الإتقان": "{{proficiency_1}}"
                    },
                    {
                        "الرقم": "2",
                        "الجدارة": "{{technical_comp_2}}",
                        "مستوى الإتقان": "{{proficiency_2}}"
                    },
                    {
                        "الرقم": "3",
                        "الجدارة": "{{technical_comp_3}}",
                        "مستوى الإتقان": "{{proficiency_3}}"
                    },
                    {
                        "الرقم": "4",
                        "الجدارة": "{{technical_comp_4}}",
                        "مستوى الإتقان": "{{proficiency_4}}"
                    },
                    {
                        "الرقم": "5",
                        "الجدارة": "{{technical_comp_5}}",
                        "مستوى الإتقان": "{{proficiency_5}}"
                    }
                ]
            },
            "إدارة الأداء المهني": [
                {
                    "الرقم": "1",
                    "مؤشر الأداء الرئيسي": "{{kpi_1}}",
                    "طريقة القياس": "{{measurement_1}}"
                },
                {
                    "الرقم": "2",
                    "مؤشر الأداء الرئيسي": "{{kpi_2}}",
                    "طريقة القياس": "{{measurement_2}}"
                },
                {
                    "الرقم": "3",
                    "مؤشر الأداء الرئيسي": "{{kpi_3}}",
                    "طريقة القياس": "{{measurement_3}}"
                },
                {
                    "الرقم": "4",
                    "مؤشر الأداء الرئيسي": "{{kpi_4}}",
                    "طريقة القياس": "{{measurement_4}}"
                }
            ]
        }
    }
    return template_structure

def create_template_with_placeholders(template_bytes: bytes) -> bytes:
    """
    Create a new template with placeholders based on the standard structure
    """
    try:
        # Create a new document with placeholders
        doc = Document()
        
        # Add title
        title = doc.add_heading("نموذج بطاقة الوصف المهني", 0)
        
        # Add sections with placeholders
        sections = [
            ("1- البيانات المرجعية للمهنة", [
                "المجموعة الرئيسية: {{main_group}}",
                "رمز المجموعة الرئيسية: {{main_group_code}}",
                "المجموعة الفرعية: {{sub_group}}",
                "رمز المجموعة الفرعية: {{sub_group_code}}",
                "المجموعة الثانوية: {{secondary_group}}",
                "رمز المجموعة الثانوية: {{secondary_group_code}}",
                "مجموعة الوحدات: {{units_group}}",
                "رمز الوحدات: {{units_code}}",
                "المهنة: {{profession}}",
                "رمز المهنة: {{profession_code}}",
                "موقع العمل: {{work_location}}",
                "المرتبة: {{rank}}"
            ]),
            ("2- الملخص العام للمهنة", ["{{summary}}"]),
            ("3- قنوات التواصل", [
                "جهات التواصل الداخلية: {{internal_party_1}} - {{internal_purpose_1}}",
                "جهات التواصل الخارجية: {{external_party_1}} - {{external_purpose_1}}"
            ]),
            ("4- مستويات المهنة القياسية", [
                "المستوى 1: {{level_1}} ({{level_code_1}}) - {{role_1}} - {{progression_1}}"
            ]),
            ("5- الجدارات", [
                "الجدارات السلوكية: {{behavioral_comp_1}}, {{behavioral_comp_2}}, {{behavioral_comp_3}}",
                "الجدارات الأساسية: {{core_comp_1}}, {{core_comp_2}}, {{core_comp_3}}",
                "الجدارات القيادية: {{leadership_comp_1}}, {{leadership_comp_2}}, {{leadership_comp_3}}",
                "الجدارات الفنية: {{technical_comp_1}}, {{technical_comp_2}}, {{technical_comp_3}}"
            ])
        ]
        
        for section_title, items in sections:
            doc.add_heading(section_title, level=1)
            for item in items:
                doc.add_paragraph(item)
            doc.add_paragraph("")  # Add space between sections
        
        # Add Form B
        doc.add_heading("نموذج الوصف الفعلي", level=0)
        
        # Tasks section
        doc.add_heading("1- المهام", level=1)
        doc.add_paragraph("المهام القيادية/الإشرافية: {{leadership_task_1}}, {{leadership_task_2}}, {{leadership_task_3}}")
        doc.add_paragraph("المهام التخصصية: {{specialized_task_1}}, {{specialized_task_2}}, {{specialized_task_3}}")
        doc.add_paragraph("مهام أخرى إضافية: {{additional_task_1}}, {{additional_task_2}}, {{additional_task_3}}")
        
        # Competencies section
        doc.add_heading("2- الجدارات السلوكية والفنية", level=1)
        doc.add_paragraph("الجدارات السلوكية:")
        for i in range(1, 6):
            doc.add_paragraph(f"{i}- {{behavioral_comp_{i}}} - مستوى الإتقان: {{proficiency_{i}}}")
        
        doc.add_paragraph("الجدارات الفنية:")
        for i in range(1, 6):
            doc.add_paragraph(f"{i}- {{technical_comp_{i}}} - مستوى الإتقان: {{proficiency_{i}}}")
        
        # Performance section
        doc.add_heading("3- إدارة الأداء المهني", level=1)
        for i in range(1, 5):
            doc.add_paragraph(f"{i}- {{kpi_{i}}} - طريقة القياس: {{measurement_{i}}}")
        
        # Save the new template
        out = io.BytesIO()
        doc.save(out)
        out.seek(0)
        return out.read()
        
    except Exception as e:
        st.error(f"Error creating template: {e}")
        return template_bytes

def read_docx_paragraphs(file_bytes) -> list[str]:
    """
    Read paragraphs from a DOCX file using python-docx Document.
    This function is used to parse the source document for job information.
    """
    try:
        # Use Document for reading source files (more reliable for parsing)
        doc = Document(io.BytesIO(file_bytes))
        
        paras = []
        for p in doc.paragraphs:
            text = (p.text or "").strip()
            if text != "":
                paras.append(text)
        return paras
    except Exception as e:
        st.error(f"خطأ في قراءة ملف DOCX: {e}")
        return []

def slice_jobs_from_source(paras: list[str], single_job: bool = False) -> dict:
    """
    Heuristic parser for job data:
    - A job block starts at a line that looks like a job title (Arabic words, not starting with digits or bullets),
      and within the next ~6 lines we see a numbered section like '1)'.
    - Sections inside each job: 1) ... 7)
    Returns: { job_title: { 'ref':..., 'summary':..., 'channels':..., 'levels':..., 'competencies':..., 'kpis':..., 'tasks':... } }
    """
    text = "\n".join(paras)

    # Split into candidates by lines that look like headings
    # We'll treat any line without leading digit and with Arabic letters as a potential job start.
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    job_indices = []
    
    # More flexible job detection - look for lines that could be job titles
    for i, line in enumerate(lines):
        # Check if line looks like a job title (has Arabic text, reasonable length, no leading numbers)
        if (len(line) > 3 and 
            re.search(r"[\u0600-\u06FF]", line) and  # Contains Arabic text
            not re.match(r"^\d", line) and            # Doesn't start with number
            not re.match(r"^[•\-\*]", line) and      # Doesn't start with bullet
            not re.match(r"^\s*\d+\)", line)):       # Doesn't start with numbered section
            
            # Look ahead to see if this could be a job section
            # Check if within next 10 lines we have some numbered content
            window_lines = lines[i:i+10]
            window_text = "\n".join(window_lines)
            
            # More flexible pattern matching for numbered sections
            has_numbered_sections = (
                re.search(r"\b1\)", window_text) or           # 1)
                re.search(r"\b2\)", window_text) or           # 2)
                re.search(r"\b3\)", window_text) or           # 3)
                re.search(r"\b4\)", window_text) or           # 4)
                re.search(r"\b5\)", window_text) or           # 5)
                re.search(r"\b6\)", window_text) or           # 6)
                re.search(r"\b7\)", window_text) or           # 7)
                re.search(r"البيانات", window_text) or        # Contains "البيانات"
                re.search(r"الملخص", window_text) or          # Contains "الملخص"
                re.search(r"المهام", window_text)             # Contains "المهام"
            )
            
            if has_numbered_sections:
                job_indices.append(i)

    # If no jobs found with strict criteria, try more relaxed approach
    if not job_indices:
        st.warning("لم يتم العثور على وظائف بالمعايير الصارمة. جاري المحاولة بطريقة أكثر مرونة...")
        
        # Look for any line with Arabic text that could be a job title
        for i, line in enumerate(lines):
            if (len(line) > 2 and 
                re.search(r"[\u0600-\u06FF]", line) and  # Contains Arabic text
                not re.match(r"^\d", line) and            # Doesn't start with number
                not re.match(r"^[•\-\*]", line)):         # Doesn't start with bullet
                
                # Check if this line is followed by content (not just empty lines)
                next_lines = lines[i+1:i+5]
                if any(len(l.strip()) > 0 for l in next_lines):
                    job_indices.append(i)

    # Add end sentinel
    job_indices = sorted(set(job_indices))
    blocks = {}
    
    # For single job mode, only process the first job
    if single_job and job_indices:
        job_indices = job_indices[:1]
    
    for idx, start in enumerate(job_indices):
        end = job_indices[idx+1] if idx+1 < len(job_indices) else len(lines)
        chunk = "\n".join(lines[start:end]).strip()
        if not chunk:
            continue
        # Job title = first line
        job_title = lines[start]
        # Extract numbered sections
        def cap(pattern):
            m = re.search(pattern, chunk, re.S)
            return m.group(1).strip() if m else ""

        # More flexible pattern matching for sections
        ref_block      = cap(r"1\)\s*البيانات.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"البيانات.*?\n(.*?)(?=\n\d\)|\Z)")
        summary_block  = cap(r"2\)\s*الملخص.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"الملخص.*?\n(.*?)(?=\n\d\)|\Z)")
        channels_block = cap(r"3\)\s*قنوات التواصل.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"قنوات التواصل.*?\n(.*?)(?=\n\d\)|\Z)")
        levels_block   = cap(r"4\)\s*مستويات.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"مستويات.*?\n(.*?)(?=\n\d\)|\Z)")
        comp_block     = cap(r"5\)\s*الجدارات.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"الجدارات.*?\n(.*?)(?=\n\d\)|\Z)")
        kpis_block     = cap(r"6\)\s*إدارة الأداء.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"إدارة الأداء.*?\n(.*?)(?=\n\d\)|\Z)")
        tasks_block    = cap(r"7\)\s*المهام.*?\n(.*?)(?=\n\d\)|\Z)") or cap(r"المهام.*?\n(.*?)(?=\n\d\)|\Z)")

        blocks[job_title] = {
            "ref": ref_block,
            "summary": summary_block,
            "channels": channels_block,
            "levels": levels_block,
            "competencies": comp_block,
            "kpis": kpis_block,
            "tasks": tasks_block
        }

    return blocks

def zip_many(named_bytes: dict[str, bytes]) -> bytes:
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for fname, b in named_bytes.items():
            z.writestr(fname, b)
    bio.seek(0)
    return bio.read()

# ---------- main ----------
if st.button("إنشاء النماذج المملوءة / Generate Filled Forms", type="primary", disabled=(tmpl_file is None or src_file is None)):
    try:
        tmpl_bytes = tmpl_file.read()
        src_bytes  = src_file.read()

        # Show template structure
        st.write("**📋 Template Structure Created:**")
        template_structure = create_template_structure()
        st.json(template_structure)
        
        # Create template with placeholders
        st.write("**🔧 Creating template with placeholders...**")
        template_with_placeholders = create_template_with_placeholders(tmpl_bytes)
        
        # Show download for template with placeholders
        st.download_button(
            "📥 Download Template with Placeholders",
            data=template_with_placeholders,
            file_name="template_with_placeholders.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # parse jobs
        paras = read_docx_paragraphs(src_bytes)
        single_job_mode = processing_mode == "وظيفة واحدة / Single Job"
        jobs = slice_jobs_from_source(paras, single_job_mode)

        if not jobs:
            st.error("لم يتم اكتشاف أي وظائف. تأكد من أن ملف مصدر البيانات DOCX يحتوي على نصوص عربية مع أقسام مرقمة أو كلمات مفتاحية مثل 'البيانات'، 'الملخص'، 'المهام'.")
        else:
            if single_job_mode:
                st.success(f"تم اكتشاف وظيفة واحدة. إنشاء النموذج...")
            else:
                st.success(f"تم اكتشاف {len(jobs)} وظيفة(وظائف). إنشاء النماذج...")
            
            files = {}
            for job_title, data in jobs.items():
                doc_bytes = build_filled_docx_bytes(template_with_placeholders, job_title, data)
                safe_name = re.sub(r'[\\/*?:"<>|]', "-", job_title)
                files[f"{safe_name}.docx"] = doc_bytes
                st.download_button(f"تحميل: {job_title} / Download: {job_title}", data=doc_bytes, file_name=f"{safe_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

            # zip all (only for multi-job mode)
            if not single_job_mode and len(files) > 1:
                zip_bytes = zip_many(files)
                st.download_button("تحميل الكل (ZIP) / Download ALL (ZIP)", data=zip_bytes, file_name="filled_jobs.zip", mime="application/zip")

    except Exception as e:
        st.error(f"خطأ: {e}")

st.markdown("""
**ملاحظات مهمة / Important Notes**

## 🎯 **كيف يعمل التطبيق الآن / How the App Works Now:**

1. **يرفع العميل قالب** (أي قالب DOCX)
2. **التطبيق ينشئ قالب جديد** مع العناصر النائبة تلقائياً
3. **يرفع العميل ملف المصدر** مع معلومات الوظائف
4. **التطبيق يملأ القالب** ببيانات كل وظيفة
5. **يحصل العميل على ملفات مملوءة** جاهزة للاستخدام

## ✅ **الميزات الجديدة:**
- **إنشاء تلقائي للعناصر النائبة** - لا حاجة لإضافتها يدوياً
- **ملء جميع الجداول الفارغة** تلقائياً
- **دعم كامل للعربية**
- **معالجة عدة وظائف** في نفس الوقت
- **تحميل القالب مع العناصر النائبة** للاستخدام المستقبلي

## 🔧 **العملية:**
1. ارفع قالبك
2. احصل على قالب مع عناصر نائبة
3. ارفع مصدر البيانات
4. احصل على نماذج مملوءة جاهزة
""")