import sys
import pypdf

# Read all incoming bytes from NiFi
pdf_data = sys.stdin.buffer.read()