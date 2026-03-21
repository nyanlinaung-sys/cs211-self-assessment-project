# 1. Use an official Python image
FROM python:3.9-slim

# 2. Set the folder inside the cloud where your code will live
WORKDIR /app

# 3. Install necessary system tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install them
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# 5. Copy all your project files (app.py, logic.py, questions.json, etc.)
COPY . .

# 6. Tell AWS to open the port Streamlit uses
EXPOSE 8080

# 7. The command to start your app
ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]