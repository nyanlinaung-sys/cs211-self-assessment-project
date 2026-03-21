FROM python:3.9-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy everything
COPY . .

# Install Python deps (IMPORTANT: after copy)
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8080

# Run Streamlit
CMD ["python3", "-m", "streamlit", "run", "app.py"]