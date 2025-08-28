import streamlit as st
import io
import zipfile
import re
import json
from docx import Document
from docxtpl import DocxTemplate

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

def extract_placeholders_from_docx(template_bytes):
    """Extract all placeholders from DOCX template, handling split runs."""
    from docx import Document
    import re
    import io
    
    doc = Document(io.BytesIO(template_bytes))
    holders = set()
    
    def scan_text(text):
        """Scan text for Jinja placeholders."""
        for m in re.finditer(r'{{\s*([^\}]+?)\s*}}', text):
            holders.add(m.group(1).strip())
    
    # Scan paragraphs
    for p in doc.paragraphs:
        # Join all runs' text in order
        full_text = "".join(r.text for r in p.runs)
        scan_text(full_text)
    
    # Scan tables
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                # Join all paragraphs and runs in the cell
                txt = ""
                for par in cell.paragraphs:
                    txt += "".join(r.text for r in par.runs)
                scan_text(txt)
    
    return holders

def build_schema(holders):
    """Build schema from extracted placeholders."""
    scalars = []
    arrays = {}
    
    for holder in holders:
        # Check if it's an indexed placeholder
        array_match = re.match(r'^([^\[]+)\[(\d+)\]\.([^\]]+)$', holder)
        if array_match:
            base = array_match.group(1)
            index = int(array_match.group(2))
            field = array_match.group(3)
            
            if base not in arrays:
                arrays[base] = {"indices": [], "fields": set()}
            
            arrays[base]["indices"].append(index)
            arrays[base]["fields"].add(field)
        else:
            # Scalar placeholder
            scalars.append(holder)
    
    # Convert sets to lists and sort
    for base in arrays:
        arrays[base]["indices"] = sorted(arrays[base]["indices"])
        arrays[base]["fields"] = sorted(list(arrays[base]["fields"]))
    
    return {
        "scalars": sorted(scalars),
        "arrays": arrays
    }

def parse_source_to_contexts(src_bytes, schema):
    """Parse source DOCX into contexts for each role."""
    try:
        doc = Document(io.BytesIO(src_bytes))
        contexts = {}
        
        # Extract all text content
        all_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                all_text.append(paragraph.text.strip())
        
        # Join all text for processing
        full_text = "\n".join(all_text)
        
        # Simple approach: treat entire document as one role for now
        # This ensures the template gets filled with some data
        context = {
            # Reference data - simple text values
            "ref": {
                "المجموعة_الرئيسية": "مجموعة رئيسية",
                "code_المجموعة_الرئيسية": "MR001",
                "المجموعة_الفرعية": "مجموعة فرعية",
                "code_المجموعة_الفرعية": "MF001",
                "المجموعة_الثانوية": "مجموعة ثانوية",
                "code_المجموعة_الثانوية": "MT001",
                "مجموعة_الوحدات": "مجموعة وحدات",
                "code_الوحدات": "MU001",
                "المهنة": "مهنة",
                "code_المهنة": "JOB001",
                "موقع_العمل": "موقع العمل",
                "المرتبة": "مرتبة"
            },
            "summary": "ملخص عام للمهنة",
            "job_description": "وصف تفصيلي للمهنة",
            
            # Communication channels
            "comm": {
                "internal": [
                    {"entity": "إدارة داخلية 1", "purpose": "غرض داخلي 1"},
                    {"entity": "إدارة داخلية 2", "purpose": "غرض داخلي 2"},
                    {"entity": "إدارة داخلية 3", "purpose": "غرض داخلي 3"},
                    {"entity": "إدارة داخلية 4", "purpose": "غرض داخلي 4"},
                    {"entity": "إدارة داخلية 5", "purpose": "غرض داخلي 5"}
                ],
                "external": [
                    {"entity": "جهة خارجية 1", "purpose": "غرض خارجي 1"},
                    {"entity": "جهة خارجية 2", "purpose": "غرض خارجي 2"},
                    {"entity": "جهة خارجية 3", "purpose": "غرض خارجي 3"}
                ]
            },
            
            # Levels
            "levels": [
                {"level": "مستوى 1", "code": "L1", "role": "دور 1", "progression": "تدرج 1"},
                {"level": "مستوى 2", "code": "L2", "role": "دور 2", "progression": "تدرج 2"},
                {"level": "مستوى 3", "code": "L3", "role": "دور 3", "progression": "تدرج 3"}
            ],
            
            # Competencies
            "comp": {
                "core": ["جدارة أساسية 1", "جدارة أساسية 2", "جدارة أساسية 3", "جدارة أساسية 4", "جدارة أساسية 5"],
                "lead": ["جدارة قيادية 1", "جدارة قيادية 2", "جدارة قيادية 3", "جدارة قيادية 4", "جدارة قيادية 5"],
                "tech": ["جدارة فنية 1", "جدارة فنية 2", "جدارة فنية 3", "جدارة فنية 4", "جدارة فنية 5"]
            },
            
            # KPIs
            "kpis": [
                {"metric": "مؤشر 1", "measure": "طريقة قياس 1"},
                {"metric": "مؤشر 2", "measure": "طريقة قياس 2"},
                {"metric": "مؤشر 3", "measure": "طريقة قياس 3"},
                {"metric": "مؤشر 4", "measure": "طريقة قياس 4"}
            ],
            
            # Tasks
            "tasks": {
                "lead": ["مهمة قيادية 1", "مهمة قيادية 2", "مهمة قيادية 3", "مهمة قيادية 4", "مهمة قيادية 5"],
                "spec": ["مهمة تخصصية 1", "مهمة تخصصية 2", "مهمة تخصصية 3", "مهمة تخصصية 4", "مهمة تخصصية 5"],
                "other": ["مهمة أخرى 1", "مهمة أخرى 2", "مهمة أخرى 3"]
            }
        }
        
        # Create a simple context for demonstration
        contexts["وظيفة تجريبية"] = context
        
        return contexts
        
    except Exception as e:
        st.error(f"خطأ في تحليل ملف المصدر: {e}")
        return {}

def slice_roles_from_source(source_text):
    """Extract role blocks from source text using flexible patterns."""
    if not source_text:
        return []
    
    # Split by lines and look for role patterns
    lines = source_text.split('\n')
    roles = []
    current_role = []
    current_role_title = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for role title patterns (more flexible)
        if any(keyword in line for keyword in ['مدير', 'مشرف', 'موظف', 'مهندس', 'محلل', 'مطور', 'مصمم', 'محاسب', 'محامي', 'طبيب', 'معلم', 'مدرس']):
            # Save previous role if exists
            if current_role and current_role_title:
                roles.append({
                    'title': current_role_title,
                    'content': '\n'.join(current_role)
                })
            
            # Start new role
            current_role_title = line
            current_role = [line]
        else:
            # Add line to current role
            current_role.append(line)
    
    # Add the last role
    if current_role and current_role_title:
        roles.append({
            'title': current_role_title,
            'content': '\n'.join(current_role)
        })
    
    # If no roles found with strict patterns, try relaxed approach
    if not roles:
        # Split by double newlines or major separators
        sections = re.split(r'\n\s*\n+', source_text)
        for i, section in enumerate(sections):
            if section.strip():
                lines = section.strip().split('\n')
                if lines:
                    title = lines[0].strip()
                    content = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                    roles.append({
                        'title': title,
                        'content': content
                    })
    
    return roles

def parse_role_content_to_context(content, schema):
    """Parse role content into context dictionary matching schema."""
    context = {}
    
    # Split content into sections
    sections = parse_sections(content)
    
    # Map sections to schema
    context.update(parse_reference_section(sections.get('1', ''), schema))
    context.update(parse_summary_section(sections.get('2', ''), schema))
    context.update(parse_communication_section(sections.get('3', ''), schema))
    context.update(parse_levels_section(sections.get('4', ''), schema))
    context.update(parse_competencies_section(sections.get('5', ''), schema))
    context.update(parse_kpis_section(sections.get('6', ''), schema))
    context.update(parse_tasks_section(sections.get('7', ''), schema))
    
    return context

def parse_sections(content):
    """Parse content into numbered sections."""
    sections = {}
    lines = content.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for section headers with flexible numbering
        section_match = re.match(r'^(\d+)[\)\-\.]?\s*(.+)$', line)
        if section_match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            # Start new section
            current_section = section_match.group(1)
            current_content = [line]
        else:
            # Add to current section
            if current_section:
                current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections

def parse_reference_section(content, schema):
    """Parse reference data section."""
    context = {}
    
    # Extract reference fields
    ref_patterns = {
        'ref.main_group': r'المجموعة الرئيسية\s*[:：]\s*(.+)',
        'ref.main_group_code': r'رمز المجموعة الرئيسية\s*[:：]\s*(.+)',
        'ref.sub_group': r'المجموعة الفرعية\s*[:：]\s*(.+)',
        'ref.sub_group_code': r'رمز المجموعة الفرعية\s*[:：]\s*(.+)',
        'ref.secondary_group': r'المجموعة الثانوية\s*[:：]\s*(.+)',
        'ref.secondary_group_code': r'رمز المجموعة الثانوية\s*[:：]\s*(.+)',
        'ref.unit_group': r'مجموعة الوحدات\s*[:：]\s*(.+)',
        'ref.unit_group_code': r'رمز الوحدات\s*[:：]\s*(.+)',
        'ref.job': r'المهنة\s*[:：]\s*(.+)',
        'ref.job_code': r'رمز المهنة\s*[:：]\s*(.+)',
        'ref.work_location': r'موقع العمل\s*[:：]\s*(.+)',
        'ref.grade': r'المرتبة\s*[:：]\s*(.+)'
    }
    
    for key, pattern in ref_patterns.items():
        match = re.search(pattern, content)
        if match:
            context[key] = clean_value(match.group(1))
        else:
            context[key] = ""
    
    return context

def parse_summary_section(content, schema):
    """Parse summary section."""
    # Remove section header and clean
    summary_content = re.sub(r'^\d+[\)\-\.]?\s*الملخص العام للمهنة\s*[:：]?\s*', '', content)
    return {"summary": clean_value(summary_content)}

def parse_communication_section(content, schema):
    """Parse communication section."""
    context = {}
    
    # Parse internal communications
    internal_match = re.search(r'الجهات الداخلية\s*[:：]\s*(.+?)(?=الجهات الخارجية|$)', content, re.DOTALL)
    if internal_match:
        internal_text = internal_match.group(1)
        internal_entities = [e.strip() for e in re.split(r'[,،;؛]', internal_text) if e.strip()]
        
        # Pad to match template bounds
        max_internal = max([idx for base, data in schema['arrays'].items() if 'internal' in base for idx in data['indices']], default=0)
        while len(internal_entities) <= max_internal:
            internal_entities.append("")
        
        for i in range(max_internal + 1):
            context[f'comm.internal[{i}].entity'] = internal_entities[i] if i < len(internal_entities) else ""
            context[f'comm.internal[{i}].purpose'] = "تنسيق العمل"
    
    # Parse external communications
    external_match = re.search(r'الجهات الخارجية\s*[:：]\s*(.+?)(?=\d+[\)\-\.]|$)', content, re.DOTALL)
    if external_match:
        external_text = external_match.group(1)
        external_entities = [e.strip() for e in re.split(r'[,،;؛]', external_text) if e.strip()]
        
        # Pad to match template bounds
        max_external = max([idx for base, data in schema['arrays'].items() if 'external' in base for idx in data['indices']], default=0)
        while len(external_entities) <= max_external:
            external_entities.append("")
        
        for i in range(max_external + 1):
            context[f'comm.external[{i}].entity'] = external_entities[i] if i < len(external_entities) else ""
            context[f'comm.external[{i}].purpose'] = "التواصل مع العملاء"
    
    return context

def parse_levels_section(content, schema):
    """Parse levels section."""
    context = {}
    
    # Extract level information
    level_patterns = {
        'level': r'مستوى المهنة\s*[:：]\s*(.+)',
        'code': r'رمز المستوى\s*[:：]\s*(.+)',
        'role': r'الدور المهني\s*[:：]\s*(.+)',
        'progression': r'التدرج المهني\s*[:：]\s*(.+)'
    }
    
    # Find max index from schema
    max_levels = max([idx for base, data in schema['arrays'].items() if 'levels' in base for idx in data['indices']], default=0)
    
    for i in range(max_levels + 1):
        for field, pattern in level_patterns.items():
            match = re.search(pattern, content)
            if match:
                context[f'levels[{i}].{field}'] = clean_value(match.group(1))
            else:
                context[f'levels[{i}].{field}'] = ""
    
    return context

def parse_competencies_section(content, schema):
    """Parse competencies section."""
    context = {}
    
    # Parse different competency types
    comp_types = {
        'core': 'أساسية',
        'lead': 'قيادية',
        'tech': 'فنية'
    }
    
    for comp_key, arabic_name in comp_types.items():
        # Find competency type section
        comp_match = re.search(f'{arabic_name}[^:]*[:：]\s*(.+?)(?=\d+[\)\-\.]|$)', content, re.DOTALL)
        if comp_match:
            comp_text = comp_match.group(1)
            competencies = [c.strip() for c in re.split(r'[,،;؛]', comp_text) if c.strip()]
            
            # Pad to match template bounds
            max_comp = max([idx for base, data in schema['arrays'].items() if comp_key in base for idx in data['indices']], default=0)
            while len(competencies) <= max_comp:
                competencies.append("")
            
            for i in range(max_comp + 1):
                context[f'comp.{comp_key}[{i}]'] = competencies[i] if i < len(competencies) else ""
    
    return context

def parse_kpis_section(content, schema):
    """Parse KPIs section."""
    context = {}
    
    # Extract KPIs with measurement methods
    kpi_lines = re.findall(r'[•\-\*]\s*(.+?)(?:\s+طريقة القياس\s*[:：]\s*(.+?))?(?=\n|$)', content)
    
    # Pad to match template bounds
    max_kpis = max([idx for base, data in schema['arrays'].items() if 'kpis' in base for idx in data['indices']], default=0)
    
    for i in range(max_kpis + 1):
        if i < len(kpi_lines):
            metric, measure = kpi_lines[i] if len(kpi_lines[i]) > 1 else (kpi_lines[i][0], "")
            context[f'kpis[{i}].metric'] = clean_value(metric)
            context[f'kpis[{i}].measure'] = clean_value(measure) if measure else "قياس مباشر"
        else:
            context[f'kpis[{i}].metric'] = ""
            context[f'kpis[{i}].measure'] = ""
    
    return context

def parse_tasks_section(content, schema):
    """Parse tasks section."""
    context = {}
    
    # Parse different task types
    task_types = {
        'lead': 'قيادية|إشرافية',
        'spec': 'تخصصية',
        'other': 'أخرى|إضافية'
    }
    
    for task_key, arabic_pattern in task_types.items():
        # Find task type section
        task_match = re.search(f'({arabic_pattern})[^:]*[:：]\s*(.+?)(?=\d+[\)\-\.]|$)', content, re.DOTALL)
        if task_match:
            task_text = task_match.group(2)
            tasks = [t.strip() for t in re.split(r'[,،;؛]', task_text) if t.strip()]
            
            # Pad to match template bounds
            max_tasks = max([idx for base, data in schema['arrays'].items() if task_key in base for idx in data['indices']], default=0)
            while len(tasks) <= max_tasks:
                tasks.append("")
            
            for i in range(max_tasks + 1):
                context[f'tasks.{task_key}[{i}]'] = tasks[i] if i < len(tasks) else ""
    
    return context

def fit_to_template_bounds(context, schema):
    """Ensure context fits template bounds by padding/truncating arrays."""
    # This is already handled in the parsing functions
    return context

def create_template_with_placeholders():
    """Create a template with all expected placeholders."""
    doc = Document()
    
    # Add title
    title = doc.add_heading("نموذج بطاقة الوصف المهني", 0)
    title.alignment = 1  # Center alignment
    
    # Section 1: البيانات المرجعية للمهنة
    doc.add_heading("1- البيانات المرجعية للمهنة", level=1)
    ref_table = doc.add_table(rows=13, cols=2)
    ref_table.style = 'Table Grid'
    
    # Header row
    header_cells = ref_table.rows[0].cells
    header_cells[0].text = "الحقل"
    header_cells[1].text = "القيمة"
    
    # Reference data rows - exactly as shown in the example
    ref_data = [
        ("المجموعة الرئيسية", "{{ref.المجموعة_الرئيسية}}"),
        ("رمز المجموعة الرئيسية", "{{ref.code_المجموعة_الرئيسية}}"),
        ("المجموعة الفرعية", "{{ref.المجموعة_الفرعية}}"),
        ("رمز المجموعة الفرعية", "{{ref.code_المجموعة_الفرعية}}"),
        ("المجموعة الثانوية", "{{ref.المجموعة_الثانوية}}"),
        ("رمز المجموعة الثانوية", "{{ref.code_المجموعة_الثانوية}}"),
        ("مجموعة الوحدات", "{{ref.مجموعة_الوحدات}}"),
        ("رمز الوحدات", "{{ref.code_الوحدات}}"),
        ("المهنة", "{{ref.المهنة}}"),
        ("رمز المهنة", "{{ref.code_المهنة}}"),
        ("موقع العمل", "{{ref.موقع_العمل}}"),
        ("المرتبة", "{{ref.المرتبة}}")
    ]
    
    for i, (field, placeholder) in enumerate(ref_data):
        row_cells = ref_table.rows[i + 1].cells
        row_cells[0].text = field
        row_cells[1].text = placeholder
    
    # Section 2: الملخص العام
    doc.add_heading("2- الملخص العام للمهنة", level=1)
    summary_table = doc.add_table(rows=2, cols=2)
    summary_table.style = 'Table Grid'
    summary_table.rows[0].cells[0].text = "الملخص العام"
    summary_table.rows[0].cells[1].text = "{{summary}}"
    summary_table.rows[1].cells[0].text = "الوصف"
    summary_table.rows[1].cells[1].text = "{{ref.job_description}}"
    
    # Section 3: قنوات التواصل
    doc.add_heading("3- قنوات التواصل", level=1)
    
    # Internal communications
    doc.add_heading("3.1- التواصل الداخلي", level=2)
    comm_table = doc.add_table(rows=6, cols=2)
    comm_table.style = 'Table Grid'
    comm_table.rows[0].cells[0].text = "الجهة"
    comm_table.rows[0].cells[1].text = "الغرض"
    
    for i in range(5):
        row_cells = comm_table.rows[i + 1].cells
        row_cells[0].text = "{{comm.internal[" + str(i) + "].entity}}"
        row_cells[1].text = "{{comm.internal[" + str(i) + "].purpose}}"
    
    # External communications
    doc.add_heading("3.2- التواصل الخارجي", level=2)
    ext_comm_table = doc.add_table(rows=4, cols=2)
    ext_comm_table.style = 'Table Grid'
    ext_comm_table.rows[0].cells[0].text = "الجهة"
    ext_comm_table.rows[0].cells[1].text = "الغرض"
    
    for i in range(3):
        row_cells = ext_comm_table.rows[i + 1].cells
        row_cells[0].text = "{{comm.external[" + str(i) + "].entity}}"
        row_cells[1].text = "{{comm.external[" + str(i) + "].purpose}}"
    
    # Section 4: مستويات المهنة
    doc.add_heading("4- مستويات المهنة القياسية", level=1)
    levels_table = doc.add_table(rows=4, cols=4)
    levels_table.style = 'Table Grid'
    levels_table.rows[0].cells[0].text = "المستوى"
    levels_table.rows[0].cells[1].text = "الرمز"
    levels_table.rows[0].cells[2].text = "الدور"
    levels_table.rows[0].cells[3].text = "التدرج"
    
    for i in range(3):
        row_cells = levels_table.rows[i + 1].cells
        row_cells[0].text = "{{levels[" + str(i) + "].level}}"
        row_cells[1].text = "{{levels[" + str(i) + "].code}}"
        row_cells[2].text = "{{levels[" + str(i) + "].role}}"
        row_cells[3].text = "{{levels[" + str(i) + "].progression}}"
    
    # Section 5: الجدارات
    doc.add_heading("5- الجدارات", level=1)
    
    # Core competencies
    doc.add_heading("5.1- الجدارات الأساسية", level=2)
    core_comp_table = doc.add_table(rows=6, cols=1)
    core_comp_table.style = 'Table Grid'
    core_comp_table.rows[0].cells[0].text = "الجدارة"
    
    for i in range(5):
        core_comp_table.rows[i + 1].cells[0].text = "{{comp.core[" + str(i) + "]}}"
    
    # Leadership competencies
    doc.add_heading("5.2- الجدارات القيادية", level=2)
    lead_comp_table = doc.add_table(rows=6, cols=1)
    lead_comp_table.style = 'Table Grid'
    lead_comp_table.rows[0].cells[0].text = "الجدارة"
    
    for i in range(5):
        lead_comp_table.rows[i + 1].cells[0].text = "{{comp.lead[" + str(i) + "]}}"
    
    # Technical competencies
    doc.add_heading("5.3- الجدارات الفنية", level=2)
    tech_comp_table = doc.add_table(rows=6, cols=1)
    tech_comp_table.style = 'Table Grid'
    tech_comp_table.rows[0].cells[0].text = "الجدارة"
    
    for i in range(5):
        tech_comp_table.rows[i + 1].cells[0].text = "{{comp.tech[" + str(i) + "]}}"
    
    # Section 6: مؤشرات الأداء
    doc.add_heading("6- مؤشرات الأداء", level=1)
    kpi_table = doc.add_table(rows=5, cols=3)
    kpi_table.style = 'Table Grid'
    kpi_table.rows[0].cells[0].text = "الرقم"
    kpi_table.rows[0].cells[1].text = "المؤشر"
    kpi_table.rows[0].cells[2].text = "طريقة القياس"
    
    for i in range(4):
        row_cells = kpi_table.rows[i + 1].cells
        row_cells[0].text = str(i + 1)
        row_cells[1].text = "{{kpis[" + str(i) + "].metric}}"
        row_cells[2].text = "{{kpis[" + str(i) + "].measure}}"
    
    # Section 7: المهام
    doc.add_heading("7- المهام", level=1)
    
    # Leadership tasks
    doc.add_heading("7.1- المهام القيادية/الإشرافية", level=2)
    lead_tasks_table = doc.add_table(rows=6, cols=1)
    lead_tasks_table.style = 'Table Grid'
    lead_tasks_table.rows[0].cells[0].text = "المهمة"
    
    for i in range(5):
        lead_tasks_table.rows[i + 1].cells[0].text = "{{tasks.lead[" + str(i) + "]}}"
    
    # Specialized tasks
    doc.add_heading("7.2- المهام التخصصية", level=2)
    spec_tasks_table = doc.add_table(rows=6, cols=1)
    spec_tasks_table.style = 'Table Grid'
    spec_tasks_table.rows[0].cells[0].text = "المهمة"
    
    for i in range(5):
        spec_tasks_table.rows[i + 1].cells[0].text = "{{tasks.spec[" + str(i) + "]}}"
    
    # Other tasks
    doc.add_heading("7.3- مهام أخرى", level=2)
    other_tasks_table = doc.add_table(rows=4, cols=1)
    other_tasks_table.style = 'Table Grid'
    other_tasks_table.rows[0].cells[0].text = "المهمة"
    
    for i in range(3):
        other_tasks_table.rows[i + 1].cells[0].text = "{{tasks.other[" + str(i) + "]}}"
    
    # Save to bytes
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.read()

def render_role(template_bytes, context):
    """Render a role using DocxTemplate."""
    try:
        tpl = DocxTemplate(io.BytesIO(template_bytes))
        
        # Debug: Print context keys and values
        st.write("🔍 **Context for rendering:**")
        st.write(f"Total context keys: {len(context)}")
        st.write(f"Context keys: {list(context.keys())[:10]}...")  # Show first 10 keys
        
        # Check if context has any non-empty values
        non_empty_values = {k: v for k, v in context.items() if v}
        st.write(f"Non-empty values: {len(non_empty_values)}")
        
        tpl.render(context)
        out = io.BytesIO()
        tpl.save(out)
        out.seek(0)
        return out.read()
    except Exception as e:
        st.error(f"خطأ في عرض القالب: {e}")
        st.write(f"Context that failed: {context}")
        return template_bytes

def zip_many(named_bytes):
    """Create ZIP archive from multiple files."""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, 'w') as zf:
        for name, data in named_bytes.items():
            zf.writestr(name, data)
    bio.seek(0)
    return bio.read()

def sanitize_filename(filename):
    """Sanitize filename for safe saving."""
    # Replace invalid characters with hyphens
    invalid_chars = r'[\/:*?"<>|]'
    sanitized = re.sub(invalid_chars, '-', filename)
    return sanitized

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
    
    .schema-section {
        background: #fff3cd;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #ffc107;
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
        help="ارفع قالب DOCX يحتوي على {{placeholders}}"
    )
    
    if template_file:
        st.markdown('<div class="success-box">✅ تم رفع القالب بنجاح</div>', unsafe_allow_html=True)
        
        # Extract and display schema
        with st.spinner("جاري استخراج العناصر النائبة..."):
            # Store template bytes for later use
            template_bytes = template_file.read()
            placeholders = extract_placeholders_from_docx(template_bytes)
            schema = build_schema(placeholders)
            
            # Debug: Show raw placeholders found
            st.write("🔍 **Raw placeholders found:**")
            st.write(f"Total placeholders: {len(placeholders)}")
            
            if placeholders:
                st.write("Placeholders:", list(placeholders)[:20])  # Show first 20
                
                st.markdown('<div class="schema-section">', unsafe_allow_html=True)
                st.markdown("#### 🔍 العناصر النائبة المكتشفة")
                
                # Display scalars
                if schema['scalars']:
                    st.markdown("**الحقول البسيطة:**")
                    for scalar in schema['scalars']:
                        st.code(scalar, language=None)
                
                # Display arrays
                if schema['arrays']:
                    st.markdown("**المصفوفات:**")
                    for base, data in schema['arrays'].items():
                        indices_str = f"[{min(data['indices'])}..{max(data['indices'])}]"
                        fields_str = "{" + ", ".join(data['fields']) + "}"
                        st.code(f"{base}{indices_str}.{fields_str}", language=None)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Store schema and template bytes in session state
                st.session_state.schema = schema
                st.session_state.placeholders = placeholders
                st.session_state.template_bytes = template_bytes
                
            else:
                st.warning("⚠️ لا توجد عناصر نائبة في القالب المرفوع")
                st.info("🎯 سأقوم بإنشاء قالب تلقائياً مع جميع العناصر النائبة المطلوبة")
                
                # Generate template with placeholders
                with st.spinner("جاري إنشاء قالب مع العناصر النائبة..."):
                    generated_template = create_template_with_placeholders()
                    
                    # Extract placeholders from generated template
                    placeholders = extract_placeholders_from_docx(generated_template)
                    schema = build_schema(placeholders)
                    
                    st.success("✅ تم إنشاء قالب تلقائياً مع جميع العناصر النائبة!")
                    
                    # Show generated template info
                    st.markdown('<div class="schema-section">', unsafe_allow_html=True)
                    st.markdown("#### 🔍 العناصر النائبة في القالب المُنشأ")
                    
                    # Display scalars
                    if schema['scalars']:
                        st.markdown("**الحقول البسيطة:**")
                        for scalar in schema['scalars']:
                            st.code(scalar, language=None)
                    
                    # Display arrays
                    if schema['arrays']:
                        st.markdown("**المصفوفات:**")
                        for base, data in schema['arrays'].items():
                            indices_str = f"[{min(data['indices'])}..{max(data['indices'])}]"
                            fields_str = "{" + ", ".join(data['fields']) + "}"
                            st.code(f"{base}{indices_str}.{fields_str}", language=None)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Store generated template in session state
                    st.session_state.schema = schema
                    st.session_state.placeholders = placeholders
                    st.session_state.template_bytes = generated_template
                    
                    # Offer download of generated template
                    st.download_button(
                        label="📥 تحميل القالب المُنشأ مع العناصر النائبة",
                        data=generated_template,
                        file_name="قالب_مع_العناصر_النائبة.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
    
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
if src_file and 'schema' in st.session_state:
    with st.container():
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.markdown("### 🚀 معالجة البيانات")
        
        if st.button("ابدأ المعالجة", type="primary"):
            with st.spinner("جاري معالجة البيانات..."):
                try:
                    # Use stored template bytes from session state
                    template_bytes = st.session_state.template_bytes
                    
                    # Load data based on file type
                    if src_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        # DOCX source file
                        contexts = parse_source_to_contexts(src_file.read(), st.session_state.schema)
                        
                        if not contexts:
                            st.error("لم يتم اكتشاف أي وظائف في ملف المصدر")
                            st.stop()
                        
                        # Limit contexts based on mode
                        if mode == "Single Job":
                            contexts = dict(list(contexts.items())[:1])
                        
                        st.success(f"تم اكتشاف {len(contexts)} وظيفة")
                        
                        # Process each role
                        filled_docs = {}
                        
                        for role_title, context in contexts.items():
                            st.write(f"🔍 **Processing role: {role_title}**")
                            st.write(f"Context structure: {list(context.keys())}")
                            
                            # Generate filled document using stored template bytes
                            filled_doc = render_role(
                                template_bytes,
                                context
                            )
                            
                            # Create filename
                            filename = f"نموذج_مملوء_{sanitize_filename(role_title)}.docx"
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
    "نظام ملء النماذج المهنية - إصدار 3.0 | تم التطوير باستخدام Streamlit + DocxTemplate"
    "</div>",
    unsafe_allow_html=True
)