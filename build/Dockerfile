FROM python:3.11-slim

WORKDIR /app

COPY build/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

WORKDIR /app/src/validation_service

ENTRYPOINT ["python", "main.py"]