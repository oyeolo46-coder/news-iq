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
    twilio python-dateutil ffmpeg-python \
    numpy \
    psycopg2-binary

RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir sentence-transformers

COPY python_nodes/ ./python_nodes/
COPY config/ ./config/

WORKDIR /app/python_nodes

EXPOSE 8001

CMD ["uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8001"]