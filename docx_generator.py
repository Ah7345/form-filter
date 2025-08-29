from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

def generate_docx_report(form_data):
    """
    Generate a professional DOCX report based on the form data.
    Creates a form template with structured tables and blank spaces for manual entry.
    """
    doc = Document()
    
    # Set document title
    title = doc.add_heading("نظام بطاقة الوصف المهني", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add timestamp
    from datetime import datetime
    timestamp = doc.add_paragraph(f"تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    timestamp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # Add spacing
    
    # Part A: Professional Job Description Card Template
    doc.add_heading("أ- نموذج بطاقة الوصف المهني", level=1)
    
    # 1. Reference Data Section - 3-column table as per client design
    doc.add_heading("1. البيانات المرجعية للمهنة", level=2)
    ref_data = form_data.get('ref_data', {})
    
    # Create reference data table with 3 columns: Empty | Code | Main
    ref_table = doc.add_table(rows=7, cols=3)
    ref_table.style = 'Table Grid'
    
    # Set column headers (right to left for Arabic)
    ref_table.rows[0].cells[2].text = "المجموعة الرئيسية"
    ref_table.rows[1].cells[2].text = "المجموعة الفرعية"
    ref_table.rows[2].cells[2].text = "المجموعة الثانوية"
    ref_table.rows[3].cells[2].text = "مجموعة الوحدات"
    ref_table.rows[4].cells[2].text = "المهنة"
    ref_table.rows[5].cells[2].text = "موقع العمل"
    ref_table.rows[6].cells[2].text = "المرتبة"
    
    # Set code labels in middle column
    ref_table.rows[0].cells[1].text = "رمز المجموعة الرئيسية"
    ref_table.rows[1].cells[1].text = "رمز المجموعة الفرعية"
    ref_table.rows[2].cells[1].text = "رمز المجموعة الثانوية"
    ref_table.rows[3].cells[1].text = "رمز الوحدات"
    ref_table.rows[4].cells[1].text = "رمز المهنة"
    ref_table.rows[5].cells[1].text = ""
    ref_table.rows[6].cells[1].text = ""
    
    # Fill data in left column (empty cells for input)
    for i in range(7):
        ref_table.rows[i].cells[0].text = ref_data.get([
            'main_group', 'sub_group', 'secondary_group', 
            'unit_group', 'job', 'work_location', 'grade'
        ][i], '') or "_________________"
    
    doc.add_paragraph()  # Add spacing
    
    # 2. General Summary Section - large empty space for manual entry
    doc.add_heading("2. الملخص العام للمهنة", level=2)
    summary = form_data.get('summary', '')
    if summary:
        doc.add_paragraph(summary)
    else:
        # Add blank lines for manual entry
        for i in range(8):
            doc.add_paragraph("_________________")
    
    doc.add_paragraph()  # Add spacing
    
    # 3. Communication Channels Section - Single 3-column table as per client design
    doc.add_heading("3. قنوات التواصل", level=2)
    
    # Create single table with 3 columns: Empty | Purpose | Communication Parties
    comm_table = doc.add_table(rows=3, cols=3)
    comm_table.style = 'Table Grid'
    
    # Set headers (right to left for Arabic)
    comm_table.rows[0].cells[2].text = "جهات التواصل الداخلية"
    comm_table.rows[1].cells[2].text = "جهات التواصل الخارجية"
    comm_table.rows[2].cells[2].text = ""
    
    comm_table.rows[0].cells[1].text = "الغرض من التواصل"
    comm_table.rows[1].cells[1].text = "الغرض من التواصل"
    comm_table.rows[2].cells[1].text = ""
    
    # Fill data in left column (empty cells for input)
    internal_comms = form_data.get('internal_communications', [])
    external_comms = form_data.get('external_communications', [])
    
    if internal_comms and any(any(comm.values()) for comm in internal_comms):
        comm_table.rows[0].cells[0].text = internal_comms[0].get('entity', '') or "_________________"
    else:
        comm_table.rows[0].cells[0].text = "_________________"
        
    if external_comms and any(any(comm.values()) for comm in external_comms):
        comm_table.rows[1].cells[0].text = external_comms[0].get('entity', '') or "_________________"
    else:
        comm_table.rows[1].cells[0].text = "_________________"
        
    comm_table.rows[2].cells[0].text = "_________________"
    
    doc.add_paragraph()  # Add spacing
    
    # 4. Job Standard Levels Section - 2-column table as per client design
    doc.add_heading("4. مستويات المهنة القياسية", level=2)
    job_levels = form_data.get('job_levels', [])
    
    # Create table with 2 columns: Empty | Level descriptions
    level_table = doc.add_table(rows=5, cols=2)
    level_table.style = 'Table Grid'
    
    # Set level descriptions (right to left for Arabic)
    level_table.rows[0].cells[1].text = "مستوى المهنة القياسي"
    level_table.rows[1].cells[1].text = "رمز المستوى المهني"
    level_table.rows[2].cells[1].text = "الدور المهني"
    level_table.rows[3].cells[1].text = "التدرج المهني (المرتبة)"
    level_table.rows[4].cells[1].text = ""
    
    # Fill data in left column (empty cells for input)
    if job_levels and any(any(level.values()) for level in job_levels):
        level_table.rows[0].cells[0].text = job_levels[0].get('level', '') or "_________________"
        level_table.rows[1].cells[0].text = job_levels[0].get('code', '') or "_________________"
        level_table.rows[2].cells[0].text = job_levels[0].get('role', '') or "_________________"
        level_table.rows[3].cells[0].text = job_levels[0].get('progression', '') or "_________________"
    else:
        level_table.rows[0].cells[0].text = "_________________"
        level_table.rows[1].cells[0].text = "_________________"
        level_table.rows[2].cells[0].text = "_________________"
        level_table.rows[3].cells[0].text = "_________________"
        
    level_table.rows[4].cells[0].text = "_________________"
    
    doc.add_paragraph()  # Add spacing
    
    # 5. Competencies Section - Single table as per client design
    doc.add_heading("5. الجدارات", level=2)
    
    # Create single table with 3 columns: Empty | Competency types | Behavioral competencies
    comp_table = doc.add_table(rows=4, cols=3)
    comp_table.style = 'Table Grid'
    
    # Set competency types (right to left for Arabic)
    comp_table.rows[0].cells[1].text = "الجدارات الأساسية"
    comp_table.rows[1].cells[1].text = "الجدارات القيادية"
    comp_table.rows[2].cells[1].text = "الجدارات الفنية"
    comp_table.rows[3].cells[1].text = ""
    
    # Set behavioral competencies header (spans vertically)
    comp_table.rows[0].cells[2].text = "الجدارات السلوكية"
    comp_table.rows[1].cells[2].text = ""
    comp_table.rows[2].cells[2].text = ""
    comp_table.rows[3].cells[2].text = ""
    
    # Fill data in left column (empty cells for input)
    core_comp = form_data.get('core_competencies', [])
    leadership_comp = form_data.get('leadership_competencies', [])
    technical_comp = form_data.get('technical_competencies', [])
    
    if core_comp and any(any(comp.values()) for comp in core_comp):
        comp_table.rows[0].cells[0].text = core_comp[0].get('name', '') or "_________________"
    else:
        comp_table.rows[0].cells[0].text = "_________________"
        
    if leadership_comp and any(any(comp.values()) for comp in leadership_comp):
        comp_table.rows[1].cells[0].text = leadership_comp[0].get('name', '') or "_________________"
    else:
        comp_table.rows[1].cells[0].text = "_________________"
        
    if technical_comp and any(any(comp.values()) for comp in technical_comp):
        comp_table.rows[2].cells[0].text = technical_comp[0].get('name', '') or "_________________"
    else:
        comp_table.rows[2].cells[0].text = "_________________"
        
    comp_table.rows[3].cells[0].text = "_________________"
    
    doc.add_page_break()
    
    # Part B: Actual Job Description Template
    doc.add_heading("ب- نموذج الوصف الفعلي", level=1)
    
    # 1. Tasks Section - blank lines for manual entry as per client design
    doc.add_heading("1. المهام", level=2)
    
    # Leadership Tasks
    doc.add_heading("المهام القيادية / الإشرافية", level=3)
    leadership_tasks = form_data.get('leadership_tasks', [])
    if leadership_tasks:
        for task in leadership_tasks:
            if task:
                doc.add_paragraph(f"• {task}")
    else:
        # Add blank lines for manual entry
        for i in range(5):
            doc.add_paragraph("• _________________")
    
    # Specialized Tasks
    doc.add_heading("المهام التخصصية", level=3)
    specialized_tasks = form_data.get('specialized_tasks', [])
    if specialized_tasks:
        for task in specialized_tasks:
            if task:
                doc.add_paragraph(f"• {task}")
    else:
        # Add blank lines for manual entry
        for i in range(5):
            doc.add_paragraph("• _________________")
    
    # Other Tasks
    doc.add_heading("مهام أخرى إضافية", level=3)
    other_tasks = form_data.get('other_tasks', [])
    if other_tasks:
        for task in other_tasks:
            if task:
                doc.add_paragraph(f"• {task}")
    else:
        # Add blank lines for manual entry
        for i in range(5):
            doc.add_paragraph("• _________________")
    
    doc.add_paragraph()  # Add spacing
    
    # 2. Competency Tables Section - 3-column tables as per client design
    doc.add_heading("2. الجدارات السلوكية والفنية", level=2)
    
    # Behavioral Competencies Table - 3 columns, 5 rows minimum
    doc.add_heading("الجدارات السلوكية", level=3)
    behavioral_table = doc.add_table(rows=1, cols=3)
    behavioral_table.style = 'Table Grid'
    behavioral_table.rows[0].cells[0].text = "الرقم"
    behavioral_table.rows[0].cells[1].text = "الجدارات السلوكية"
    behavioral_table.rows[0].cells[2].text = "مستوى الإتقان"
    
    # Style header row - bold, no shading
    for cell in behavioral_table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    behavioral_data = form_data.get('behavioral_table', [])
    if behavioral_data:
        for comp in behavioral_data:
            if comp.get('name') or comp.get('level'):
                row = behavioral_table.add_row()
                row.cells[0].text = str(comp.get('number', '')) or "_________________"
                row.cells[1].text = comp.get('name', '') or "_________________"
                row.cells[2].text = comp.get('level', '') or "_________________"
    
    # Add blank rows for manual entry - 5 rows minimum as specified
    for i in range(5):
        row = behavioral_table.add_row()
        row.cells[0].text = str(i + 1)
        row.cells[1].text = "_________________"
        row.cells[2].text = "_________________"
    
    doc.add_paragraph()  # Add spacing
    
    # Technical Competencies Table - 3 columns, 5 rows minimum
    doc.add_heading("الجدارات الفنية", level=3)
    technical_table = doc.add_table(rows=1, cols=3)
    technical_table.style = 'Table Grid'
    technical_table.rows[0].cells[0].text = "الرقم"
    technical_table.rows[0].cells[1].text = "الجدارات الفنية"
    technical_table.rows[0].cells[2].text = "مستوى الإتقان"
    
    # Style header row - bold, no shading
    for cell in technical_table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    technical_data = form_data.get('technical_table', [])
    if technical_data:
        for comp in technical_data:
            if comp.get('name') or comp.get('level'):
                row = technical_table.add_row()
                row.cells[0].text = str(comp.get('number', '')) or "_________________"
                row.cells[1].text = comp.get('name', '') or "_________________"
                row.cells[2].text = comp.get('level', '') or "_________________"
    
    # Add blank rows for manual entry - 5 rows minimum as specified
    for i in range(5):
        row = technical_table.add_row()
        row.cells[0].text = str(i + 1)
        row.cells[1].text = "_________________"
        row.cells[2].text = "_________________"
    
    doc.add_paragraph()  # Add spacing
    
    # 3. Performance Management Section - KPIs table
    doc.add_heading("3. إدارة الأداء المهني", level=2)
    
    # Create KPIs table with 3 columns: Number | KPI | Measurement Method
    kpi_table = doc.add_table(rows=1, cols=3)
    kpi_table.style = 'Table Grid'
    kpi_table.rows[0].cells[0].text = "الرقم"
    kpi_table.rows[0].cells[1].text = "مؤشرات الأداء الرئيسية"
    kpi_table.rows[0].cells[2].text = "طريقة القياس"
    
    # Style header row - bold, no shading
    for cell in kpi_table.rows[0].cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    kpis = form_data.get('kpis', [])
    if kpis:
        for kpi in kpis:
            if kpi.get('metric') or kpi.get('measure'):
                row = kpi_table.add_row()
                row.cells[0].text = str(kpi.get('number', '')) or "_________________"
                row.cells[1].text = kpi.get('metric', '') or "_________________"
                row.cells[2].text = kpi.get('measure', '') or "_________________"
    
    # Add blank rows for manual entry - 4 rows minimum as specified
    for i in range(4):
        row = kpi_table.add_row()
        row.cells[0].text = str(i + 1)
        row.cells[1].text = "_________________"
        row.cells[2].text = "_________________"
    
    # Add footer
    doc.add_paragraph()
    footer = doc.add_paragraph("Powered by AI-Powered Job Description System")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    return doc
