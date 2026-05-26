# ── stage 1: збираємо залежності у віртуальне середовище ──────────────
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── stage 2: фінальний легкий образ ────────────────────────────────────
FROM python:3.11-slim

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv

WORKDIR /srv
COPY app.py .

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).status==200 else 1)"

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--access-logfile", "-", "app:app"]
