# -*- coding: utf-8 -*-
"""
Created on Sun Jul 12 13:21:04 2026

@author: moham
"""

import os
import random
import requests
from faker import Faker
from fpdf import FPDF

# 1. Initialize generators
fake = Faker()

# 2. Directory setup (Resume logic will apply here too!)
output_dir = "./corporate_documents"
os.makedirs(output_dir, exist_ok=True)

departments = {
    "HR": "HR-POLICY",
    "Architecture": "TECH-ARCH",
    "Compliance": "COMP-REG"
}

TOTAL_DOCUMENTS = 1000
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"

print(f"Starting mixed-format generation loop...")

for i in range(1, TOTAL_DOCUMENTS + 1):
    dept_name, prefix = random.choice(list(departments.items()))
    doc_id = f"{prefix}-{fake.random_int(1000, 9999)}"
    author_name = fake.name()
    effective_date = fake.date_this_decade()
    
    # Randomly choose the file extension for this iteration
    extension = random.choice([".md", ".pdf"])
    file_name = f"{output_dir}/{doc_id}{extension}"
    
    # Skip if THIS specific format already exists
    if os.path.exists(file_name):
        continue
        
    prompt = f"""
    You are an expert enterprise corporate writer. Write a comprehensive corporate document for the {dept_name} department.
    Use professional corporate jargon, realistic procedures, and edge cases.
    
    CRITICAL: Output the document strictly in Markdown format using '#' and '##' headers.
    Do not include any chat conversational filler before or after the document.
    
    Document Metadata to display at the top:
    - Document ID: {doc_id}
    - Department: {dept_name}
    - Author: {author_name}
    - Effective Date: {effective_date}
    
    Structure the document body with these sections:
    # {dept_name} Reference Document: {doc_id}
    ## 1. Document Scope and Executive Summary
    ## 2. Core Policies and Standard Operating Procedures
    ## 3. Compliance Monitoring, Penalties, and Operational Governance
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        markdown_content = response.json().get("response", "").strip()
        
        # Save strategy based on the chosen format
        if extension == ".md":
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                
        elif extension == ".pdf":
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            
            # Write line by line to the PDF binary format
            for line in markdown_content.split('\n'):
                # Clean up encoding characters for the standard PDF fonts
                clean_line = line.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 5, txt=clean_line, ln=1)
                
            pdf.output(file_name)
            
        if i % 10 == 0:
            print(f"Iteration {i}/{TOTAL_DOCUMENTS} processed...")
            
    except Exception as e:
        print(f" Error at iteration {i}: {str(e)}")

print(f" Success! Mixed dataset ready in '{output_dir}'.")