import io, zipfile, re
from pathlib import Path
import streamlit as st
from docxtpl import DocxTemplate  # For template filling
from docx import Document  # For reading source document

st.set_page_config(page_title="ملء النماذج (Multi-Job)", layout="centered")
st.title("ملء النماذج — متعدد الوظائف (DOCX → DOCX)")
st.caption("قم برفع قالب DOCX مع عناصر نائبة في الجداول ومصدر بيانات يحتوي على معلومات عدة وظائف. سيقوم التطبيق بملء الجداول الموجودة.")

# Add processing mode selection
processing_mode = st.radio(
    "وضع المعالجة / Processing Mode:",
    ["متعدد الوظائف / Multi-Job", "وظيفة واحدة / Single Job"],
    horizontal=True
)

tmpl_file = st.file_uploader("رفع القالب (DOCX) / Upload Template (DOCX)", type=["docx"])
st.info("💡 **هام**: يجب أن يحتوي القالب على عناصر نائبة مثل {{ref}}، {{summary}}، {{channels}} في خلايا الجداول")

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
        st.error("تأكد من أن الملف هو ملف DOCX صحيح")
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

def build_filled_docx_bytes(template_bytes: bytes, job_title: str, data: dict) -> bytes:
    """
    Build a filled DOCX using DocxTemplate to fill existing table cells with placeholders.
    This preserves the original table structure and fills the blanks instead of adding new content.
    """
    # Create DocxTemplate from the template bytes
    doc = DocxTemplate(io.BytesIO(template_bytes))
    
    # Prepare context data for template rendering
    # Add job_title to the context so it can be used in the template
    context = {
        "job_title": job_title,
        "ref": data.get("ref", ""),
        "summary": data.get("summary", ""),
        "channels": data.get("channels", ""),
        "levels": data.get("levels", ""),
        "competencies": data.get("competencies", ""),
        "kpis": data.get("kpis", ""),
        "tasks": data.get("tasks", "")
    }
    
    # Render the template with the context data
    # This will replace all {{placeholders}} in tables and paragraphs
    doc.render(context)
    
    # Save the rendered document to bytes
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.read()

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
                doc_bytes = build_filled_docx_bytes(tmpl_bytes, job_title, data)
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
- **يجب أن يحتوي القالب على عناصر نائبة** مثل `{{ref}}`، `{{summary}}`، `{{channels}}` في خلايا الجداول
- **لا يضيف محتوى جديد** في أسفل الصفحة، بل يملأ الخلايا الموجودة
- **يحافظ على تخطيط الجداول** الأصلي والتصميم
- **العناصر النائبة المتاحة**:
  - `{{job_title}}` - عنوان الوظيفة
  - `{{ref}}` - البيانات المرجعية
  - `{{summary}}` - الملخص العام
  - `{{channels}}` - قنوات التواصل
  - `{{levels}}` - المستويات
  - `{{competencies}}` - الجدارات
  - `{{kpis}}` - إدارة الأداء
  - `{{tasks}}` - المهام

**مثال على القالب**:
```
| القسم | المحتوى |
|-------|---------|
| عنوان الوظيفة | {{job_title}} |
| البيانات المرجعية | {{ref}} |
| الملخص | {{summary}} |
```
""")