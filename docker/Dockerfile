FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Create required directories
RUN mkdir -p input_designs generated_uvm test_plans logs chromadb_store

# Environment defaults
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV PYTHONPATH=/app
ENV PYTHONIOENCODING=utf-8

# Expose Streamlit port
EXPOSE 8501

# Default command: run dashboard
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
