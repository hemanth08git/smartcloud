FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY app ./app
COPY food_quality_analyzer ./food_quality_analyzer
COPY requirements.txt .

# Copy frontend into the image
COPY frontend ./frontend

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
