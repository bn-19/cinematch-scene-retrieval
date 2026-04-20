FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    ANONYMIZED_TELEMETRY=False \
    PORT=7860

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY . .

RUN rm -rf data/chromadb_store \
    && python -m backend.ingest

EXPOSE 7860

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
