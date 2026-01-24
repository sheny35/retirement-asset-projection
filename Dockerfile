FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for numba
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY retire.py .

# Expose the default port
EXPOSE 8050

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8050
ENV DEBUG=false

# Run the application
CMD ["python", "retire.py"]
