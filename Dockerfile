FROM python:3.13-slim

WORKDIR /app

# Create /data directory for persistent storage on Hugging Face Spaces
RUN mkdir -p /data

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
