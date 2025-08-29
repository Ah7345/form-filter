#!/usr/bin/env python3

def replace_function():
    """Replace the long generate_docx_report function with a simple wrapper"""
    
    # Read the file line by line
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_function = False
    skip_until_next_function = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def generate_docx_report('):
            # Start of the function we want to replace
            in_function = True
            new_lines.append(line)  # Keep the function definition
            new_lines.append('    """Generate a professional DOCX form template from form data"""\n')
            new_lines.append('    # DOCX generation is now handled by docx_generator.py module\n')
            new_lines.append('    try:\n')
            new_lines.append('        doc = generate_docx_from_module(form_data)\n')
            new_lines.append('        if doc:\n')
            new_lines.append('            # Save the document to bytes\n')
            new_lines.append('            docx_bytes = io.BytesIO()\n')
            new_lines.append('            doc.save(docx_bytes)\n')
            new_lines.append('            docx_bytes.seek(0)\n')
            new_lines.append('            return docx_bytes.getvalue()\n')
            new_lines.append('        else:\n')
            new_lines.append('            return None\n')
            new_lines.append('    except Exception as e:\n')
            new_lines.append('        st.error(f"خطأ في إنشاء التقرير DOCX: {str(e)}")\n')
            new_lines.append('        return None\n')
            new_lines.append('\n')
            skip_until_next_function = True
            continue
            
        elif skip_until_next_function and line.strip().startswith('def '):
            # We found the next function, stop skipping
            skip_until_next_function = False
            in_function = False
            new_lines.append(line)  # Add this function line
            
        elif skip_until_next_function:
            # Skip all lines until we find the next function
            continue
            
        else:
            # Add all other lines normally
            new_lines.append(line)
    
    # Write the new content
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("Function replaced successfully!")

if __name__ == "__main__":
    replace_function()
