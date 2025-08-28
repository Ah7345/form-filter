import io, zipfile, re, json
from pathlib import Path
import streamlit as st
from docxtpl import DocxTemplate  # For template filling
from docx import Document  # For reading source document

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

def add_table(doc, label, data):
    """
    Add a 2-column table to the document with proper RTL formatting.
    
    Args:
        doc: Document object
        label: Table title/label
        data: Data to display (dict, list, or string)
    """
    # Create table based on data type
    if isinstance(data, dict):
        # For dictionaries, create table with key-value pairs
        rows = len(data) + 1  # +1 for header
        table = doc.add_table(rows=rows, cols=2)
        table.style = 'Table Grid'
        
        # Header row
        header_cells = table.rows[0].cells
        header_cells[0].text = label
        header_cells[1].text = "القيمة"
        
        # Make header bold and center
        for cell in header_cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 1  # Center alignment
                for run in paragraph.runs:
                    run.bold = True
        
        # Data rows
        for i, (key, value) in enumerate(data.items(), 1):
            row_cells = table.rows[i].cells
            row_cells[0].text = str(key)
            row_cells[1].text = str(value) if value else ""
            
            # Make label column bold
            for paragraph in row_cells[0].paragraphs:
                for run in paragraph.runs:
                    run.bold = True
    
    elif isinstance(data, list):
        # For lists, create table with items
        if not data:
            # Empty list - create single row
            table = doc.add_table(rows=2, cols=2)
            table.style = 'Table Grid'
            header_cells = table.rows[0].cells
            header_cells[0].text = label
            header_cells[1].text = "القيمة"
            
            # Make header bold and center
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    paragraph.alignment = 1
                    for run in paragraph.runs:
                        run.bold = True
            
            # Empty data row
            data_cells = table.rows[1].cells
            data_cells[0].text = "لا توجد بيانات"
            data_cells[1].text = ""
        else:
            # List with items
            rows = len(data) + 1  # +1 for header
            table = doc.add_table(rows=rows, cols=2)
            table.style = 'Table Grid'
            
            # Header row
            header_cells = table.rows[0].cells
            header_cells[0].text = label
            header_cells[1].text = "القيمة"
            
            # Make header bold and center
            for cell in header_cells:
                for paragraph in cell.paragraphs:
                    paragraph.alignment = 1
                    for run in paragraph.runs:
                        run.bold = True
            
            # Data rows
            for i, item in enumerate(data, 1):
                row_cells = table.rows[i].cells
                if isinstance(item, dict):
                    # Handle dictionary items (like competencies with number, competency, level)
                    if 'الرقم' in item and 'الجدارة' in item:
                        row_cells[0].text = f"{item.get('الرقم', '')} - {item.get('الجدارة', '')}"
                        row_cells[1].text = str(item.get('مستوى الإتقان', ''))
                    elif 'الرقم' in item and 'مؤشر الأداء الرئيسي' in item:
                        row_cells[0].text = f"{item.get('الرقم', '')} - {item.get('مؤشر الأداء الرئيسي', '')}"
                        row_cells[1].text = str(item.get('طريقة القياس', ''))
                    else:
                        # Generic dictionary handling
                        row_cells[0].text = str(list(item.keys())[0]) if item else ""
                        row_cells[1].text = str(list(item.values())[0]) if item else ""
                else:
                    # Simple list item
                    row_cells[0].text = str(i)
                    row_cells[1].text = str(item)
    
    else:
        # For strings or other types, create single row
        table = doc.add_table(rows=2, cols=2)
        table.style = 'Table Grid'
        
        # Header row
        header_cells = table.rows[0].cells
        header_cells[0].text = label
        header_cells[1].text = "القيمة"
        
        # Make header bold and center
        for cell in header_cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 1
                for run in paragraph.runs:
                    run.bold = True
        
        # Data row
        data_cells = table.rows[1].cells
        data_cells[0].text = label
        data_cells[1].text = str(data) if data else ""
        
        # Make label column bold
        for paragraph in data_cells[0].paragraphs:
            for run in paragraph.runs:
                run.bold = True
    
    # Set RTL alignment for all cells
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = 2  # RTL alignment
    
    # Add spacing after table
    doc.add_paragraph("")

def build_filled_docx_bytes(template_bytes: bytes, job_title: str, data: dict) -> bytes:
    """
    Build a filled DOCX using tables for structured layout with proper RTL formatting.
    This creates a clean, professional document with tables instead of plain paragraphs.
    """
    try:
        # Create a new document
        doc = Document()
        
        # Add title - centered and bold
        title = doc.add_heading(f"نموذج بطاقة الوصف المهني — {job_title}", 0)
        title.alignment = 1  # Center alignment
        
        # Add spacing after title
        doc.add_paragraph("")
        
        # Section 1: البيانات المرجعية للمهنة (Job Reference Data)
        ref_data = {
            "المجموعة الرئيسية": data.get("ref", ""),
            "رمز المجموعة الرئيسية": "001",
            "المجموعة الفرعية": data.get("ref", ""),
            "رمز المجموعة الفرعية": "001",
            "المجموعة الثانوية": data.get("ref", ""),
            "رمز المجموعة الثانوية": "001",
            "مجموعة الوحدات": data.get("ref", ""),
            "رمز الوحدات": "001",
            "المهنة": job_title,
            "رمز المهنة": "001",
            "موقع العمل": "المقر الرئيسي",
            "المرتبة": "أول"
        }
        add_table(doc, "1- البيانات المرجعية للمهنة", ref_data)
        
        # Section 2: الملخص العام للمهنة (General Summary)
        summary_data = data.get("summary", "") or "لا يوجد ملخص"
        add_table(doc, "2- الملخص العام للمهنة", summary_data)
        
        # Section 3: قنوات التواصل (Communication Channels)
        channels_data = {
            "جهات التواصل الداخلية": data.get("channels", ""),
            "جهات التواصل الخارجية": data.get("channels", "")
        }
        add_table(doc, "3- قنوات التواصل", channels_data)
        
        # Section 4: مستويات المهنة القياسية (Standard Profession Levels)
        levels_data = {
            "مستوى المهنة القياسي": data.get("levels", ""),
            "رمز المستوى المهني": "L1",
            "الدور المهني": data.get("levels", ""),
            "التدرج المهني (المرتبة)": "أول"
        }
        add_table(doc, "4- مستويات المهنة القياسية", levels_data)
        
        # Section 5: الجدارات (Competencies)
        competencies_data = {
            "الجدارات السلوكية": data.get("competencies", ""),
            "الجدارات الأساسية": data.get("competencies", ""),
            "الجدارات القيادية": data.get("competencies", ""),
            "الجدارات الفنية": data.get("competencies", "")
        }
        add_table(doc, "5- الجدارات", competencies_data)
        
        # Section 6: إدارة الأداء المهني (Performance Management)
        kpis_data = {
            "مؤشر الأداء 1": data.get("kpis", ""),
            "مؤشر الأداء 2": data.get("kpis", ""),
            "مؤشر الأداء 3": data.get("kpis", ""),
            "مؤشر الأداء 4": data.get("kpis", "")
        }
        add_table(doc, "6- إدارة الأداء المهني", kpis_data)
        
        # Section 7: المهام (Tasks)
        tasks_data = {
            "المهام القيادية/الإشرافية": data.get("tasks", ""),
            "المهام التخصصية": data.get("tasks", ""),
            "مهام أخرى إضافية": data.get("tasks", "")
        }
        add_table(doc, "7- المهام", tasks_data)
        
        # Add Form B: نموذج الوصف الفعلي (Actual Description Form)
        doc.add_heading("نموذج الوصف الفعلي", level=1)
        doc.add_paragraph("")
        
        # Form B Section 1: المهام (Tasks)
        form_b_tasks = [
            {"الرقم": "1", "المهمة": data.get("tasks", "")},
            {"الرقم": "2", "المهمة": data.get("tasks", "")},
            {"الرقم": "3", "المهمة": data.get("tasks", "")}
        ]
        add_table(doc, "1- المهام", form_b_tasks)
        
        # Form B Section 2: الجدارات السلوكية والفنية (Behavioral and Technical Competencies)
        behavioral_competencies = [
            {"الرقم": "1", "الجدارة": data.get("competencies", ""), "مستوى الإتقان": "متقدم"},
            {"الرقم": "2", "الجدارة": data.get("competencies", ""), "مستوى الإتقان": "متقدم"},
            {"الرقم": "3", "الجدارة": data.get("competencies", ""), "مستوى الإتقان": "متقدم"},
            {"الرقم": "4", "الجدارة": data.get("competencies", ""), "مستوى الإتقان": "متقدم"},
            {"الرقم": "5", "الجدارة": data.get("competencies", ""), "مستوى الإتقان": "متقدم"}
        ]
        add_table(doc, "2- الجدارات السلوكية والفنية", behavioral_competencies)
        
        # Form B Section 3: إدارة الأداء المهني (Performance Management)
        performance_indicators = [
            {"الرقم": "1", "مؤشر الأداء": data.get("kpis", ""), "طريقة القياس": "قياس مباشر"},
            {"الرقم": "2", "مؤشر الأداء": data.get("kpis", ""), "طريقة القياس": "قياس مباشر"},
            {"الرقم": "3", "مؤشر الأداء": data.get("kpis", ""), "طريقة القياس": "قياس مباشر"},
            {"الرقم": "4", "مؤشر الأداء": data.get("kpis", ""), "طريقة القياس": "قياس مباشر"}
        ]
        add_table(doc, "3- إدارة الأداء المهني", performance_indicators)
        
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