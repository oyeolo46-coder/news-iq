FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --no-cache-dir \
    fastapi uvicorn python-dotenv pydantic \
    requests anthropic \
    google-cloud-texttospeech \
    google-api-python-client google-auth-oauthlib \
    google-auth-httplib2 google-auth \
    twilio python-dateutil ffmpeg-python

RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    torch --index-url https://download.pytorch.org/whl/cpu \
    sentence-transformers==3.0.1 \
    psycopg2-binary==2.9.9

COPY python_nodes/ ./python_nodes/
COPY config/ ./config/

WORKDIR /app/python_nodes

EXPOSE 8001

CMD ["uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8001"]