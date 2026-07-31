FROM python:3.10-slim

WORKDIR /app

# Layer Optimization: Copy dependencies first to leverage Docker build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose all network interfaces (0.0.0.0) inside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]