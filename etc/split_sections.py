import os

def extract_metadata_and_sections(text):
    text = text.replace('\r\n', '\n')
    lines = text.split('\n')
    
    metadata = {}
    content_lines = []
    metadata_keys = ['Document ID', 'Department', 'Author', 'Effective Date']
    
    for line in lines:
        stripped = line.strip()
        stripped = re.sub(r'^\\s*', '', stripped)
        
        matched_metadata = False
        for key in metadata_keys:
            pattern = rf'^(?:\*\*|\*\s*)?{key}(?:\*\*|:)?\s*:\s*(.*)$'
            match = re.match(pattern, stripped, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()
                matched_metadata = True
                break
        
        if not matched_metadata:
            cleaned_line = re.sub(r'^\\s*', '', line)
            content_lines.append(cleaned_line)

    body_text = "\n".join(content_lines).strip()
    raw_sections = re.split(r'\n(?=##? )', body_text)
    
    # Extract Document ID safely for the filename
    doc_id = metadata.get('Document ID', 'unknown_document').replace(' ', '_')
    
    meta_string = " | ".join([f"{k}: {v}" for k, v in metadata.items()])
    meta_header = f"[{meta_string}]\n"
    
    # Write each section directly to a file
    output_dir = "/tmp"
    for index, section in enumerate(raw_sections, start=1):
        section = section.strip()
        if section:
            # Combine metadata and section text
            full_content = meta_header + section
            
            # Create a unique filename: /tmp/COMP-REG-1031_section_1.md
            filename = os.path.join(output_dir, f"{doc_id}_section_{index}.md")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_content)
                
    return doc_id, len(raw_sections)

def main():
    input_text = sys.stdin.read()
    if not input_text.strip():
        return
    
    # Process and write files
    doc_id, count = extract_metadata_and_sections(input_text)
    
    # Send a success confirmation message downstream in NiFi
    sys.stdout.write(f"Successfully split {doc_id} into {count} markdown files in /tmp.")
    sys.stdout.flush()