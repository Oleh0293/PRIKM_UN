"""
TaskTracker — мінімальний REST API мікросервіс для демонстрації
наскрізного DevOps-конвеєра у курсовій роботі.

Особливості:
- /api/tasks      — CRUD-операції з задачами (PostgreSQL).
- /health         — liveness/readiness ендпоінт.
- /metrics        — Prometheus exposition format.
- /version        — версія застосунку (читається з ENV VERSION).
- /color          — колір "слота" (blue / green) — використовується
                    pipeline-ом для blue-green розгортання.
"""

import os
import time
import logging
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
)

# ─── конфігурація ────────────────────────────────────────────────────
APP_VERSION = os.environ.get("VERSION", "1.0.0")
APP_COLOR   = os.environ.get("COLOR",   "blue")
DB_HOST     = os.environ.get("DB_HOST", "postgres")
DB_PORT     = int(os.environ.get("DB_PORT", "5432"))
DB_NAME     = os.environ.get("DB_NAME", "tasktracker")
DB_USER     = os.environ.get("DB_USER", "tt")
DB_PASS     = os.environ.get("DB_PASS", "tt_pass")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("tasktracker")

# ─── метрики Prometheus ──────────────────────────────────────────────
REQ_COUNT = Counter(
    "tasktracker_requests_total",
    "HTTP requests count",
    ["method", "endpoint", "status"],
)
REQ_LATENCY = Histogram(
    "tasktracker_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
TASKS_GAUGE = Gauge(
    "tasktracker_tasks_total",
    "Total number of tasks currently stored",
)
BUILD_INFO = Gauge(
    "tasktracker_build_info",
    "Build info (always 1)",
    ["version", "color"],
)
BUILD_INFO.labels(version=APP_VERSION, color=APP_COLOR).set(1)

app = Flask(__name__)


# ─── допоміжне ───────────────────────────────────────────────────────
@contextmanager
def db_conn():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        connect_timeout=3,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Створює таблицю tasks, якщо вона ще не існує."""
    for attempt in range(20):
        try:
            with db_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id           SERIAL PRIMARY KEY,
                        title        TEXT NOT NULL,
                        done         BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at   TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
            log.info("DB initialised")
            return
        except Exception as exc:
            log.warning("DB not ready (attempt %d): %s", attempt + 1, exc)
            time.sleep(2)
    raise RuntimeError("DB unavailable after 20 attempts")


def refresh_tasks_gauge():
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tasks")
            TASKS_GAUGE.set(cur.fetchone()[0])
    except Exception as exc:
        log.warning("gauge refresh failed: %s", exc)


# ─── middleware вимірювання ──────────────────────────────────────────
@app.before_request
def _start_timer():
    request._start = time.perf_counter()


@app.after_request
def _record_metrics(response):
    elapsed = time.perf_counter() - getattr(request, "_start", time.perf_counter())
    REQ_LATENCY.labels(endpoint=request.path).observe(elapsed)
    REQ_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=str(response.status_code),
    ).inc()
    return response


# ─── наочна HTML-сторінка для демонстрації Blue/Green ────────────────
_UI_TEMPLATE = """<!doctype html>
<html lang="uk"><head><meta charset="utf-8">
<title>TaskTracker — {color}</title>
<style>
  body { margin: 0; height: 100vh; display: flex; flex-direction: column;
         align-items: center; justify-content: center;
         font-family: -apple-system, sans-serif; color: #fff;
         background: __BG__; }
  h1 { font-size: 64px; margin: 0; letter-spacing: 2px; }
  h2 { font-size: 28px; font-weight: 300; opacity: 0.85; margin: 16px 0 8px; }
  .card { background: rgba(0,0,0,0.25); padding: 30px 50px; border-radius: 18px;
          backdrop-filter: blur(8px); box-shadow: 0 10px 40px rgba(0,0,0,0.3); }
  .badge { display: inline-block; padding: 6px 16px; border-radius: 20px;
           background: rgba(255,255,255,0.2); font-size: 14px; margin-top: 12px; }
</style></head>
<body>
  <div class="card">
    <h1>__COLOR_UP__ SLOT</h1>
    <h2>TaskTracker · version __VERSION__</h2>
    <div class="badge">host: __HOST__</div>
  </div>
</body></html>"""

_BG_BY_COLOR = {
    "blue":  "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)",
    "green": "linear-gradient(135deg, #14532d 0%, #22c55e 100%)",
}


@app.route("/ui")
def ui():
    import socket
    bg = _BG_BY_COLOR.get(APP_COLOR, "#444")
    html = (_UI_TEMPLATE
            .replace("__BG__",       bg)
            .replace("__COLOR_UP__", APP_COLOR.upper())
            .replace("__VERSION__",  APP_VERSION)
            .replace("__HOST__",     socket.gethostname()))
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


# ─── маршрути ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "service": "TaskTracker",
        "version": APP_VERSION,
        "color":   APP_COLOR,
        "endpoints": [
            "GET  /api/tasks",
            "POST /api/tasks",
            "PATCH /api/tasks/<id>",
            "DELETE /api/tasks/<id>",
            "GET  /health",
            "GET  /metrics",
            "GET  /version",
            "GET  /color",
        ],
    })


@app.route("/health")
def health():
    try:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return jsonify({"status": "ok", "db": "ok"}), 200
    except Exception as exc:
        return jsonify({"status": "fail", "db": str(exc)}), 503


@app.route("/version")
def version():
    return jsonify({"version": APP_VERSION, "color": APP_COLOR})


@app.route("/color")
def color():
    return jsonify({"color": APP_COLOR})


@app.route("/metrics")
def metrics():
    refresh_tasks_gauge()
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    with db_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY id")
        rows = cur.fetchall()
    return jsonify(rows)


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    with db_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done, created_at",
            (title,),
        )
        task = cur.fetchone()
    return jsonify(task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    fields, values = [], []
    if "title" in data:
        fields.append("title = %s")
        values.append(data["title"])
    if "done" in data:
        fields.append("done = %s")
        values.append(bool(data["done"]))
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    values.append(task_id)
    with db_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            f"UPDATE tasks SET {', '.join(fields)} "
            f"WHERE id = %s RETURNING id, title, done, created_at",
            values,
        )
        task = cur.fetchone()
    if not task:
        return jsonify({"error": "not found"}), 404
    return jsonify(task)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
        deleted = cur.fetchone()
    if not deleted:
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": task_id})


# Виконується як при запуску через gunicorn, так і при прямому запуску
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
