import sys
import fitz  # PyMuPDF
import pymupdf4llm

def convert_pdf_stream():
    try:
        # Read raw PDF binary data directly from NiFi's flowfile stream (stdin)
        pdf_data = sys.stdin.buffer.read()
        
        if not pdf_data:
            sys.stderr.write("Error: Received empty stream from NiFi.\n")
            sys.exit(1)
            
        # Open PDF document directly from the memory buffer
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        
        # Convert to clean, LLM-ready markdown
        md_text = pymupdf4llm.to_markdown(doc)
        
        # Output the markdown text back to NiFi (stdout)
        sys.stdout.write(md_text)
        
    except Exception as e:
        sys.stderr.write(f"Conversion error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    convert_pdf_stream()