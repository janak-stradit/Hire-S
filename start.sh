#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

cd "$PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install/update dependencies if requirements.git config --get remote.origin.urltxt changed
REQUIREMENTS_HASH_FILE="$VENV_DIR/.requirements_hash"
CURRENT_HASH=$(md5sum requirements.txt 2>/dev/null | cut -d' ' -f1 || echo "none")
STORED_HASH=$(cat "$REQUIREMENTS_HASH_FILE" 2>/dev/null || echo "")

if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
    echo "[setup] Installing dependencies..."
    pip install --upgrade pip -q
    pip install \
        "fastapi>=0.111.0" \
        "uvicorn[standard]>=0.30.0" \
        "sqlalchemy>=2.0.30" \
        "asyncpg>=0.29.0" \
        "psycopg2-binary>=2.9.9" \
        "alembic>=1.13.0" \
        "pydantic>=2.7.0" \
        "pydantic-settings>=2.2.0" \
        "python-dotenv>=1.0.1" \
        "python-jose[cryptography]>=3.3.0" \
        "passlib[bcrypt]>=1.7.4" \
        "python-multipart>=0.0.9" \
        "email-validator>=2.1.0" \
        "greenlet>=3.0.3" \
        "sqlalchemy-utils>=0.41.2" \
        "aiofiles>=23.2.1" \
        "PyPDF2>=3.0.1" \
        "pdfplumber>=0.11.0" \
        "python-docx>=1.1.2" \
        "docx2txt>=0.8" \
        "nltk>=3.8.1" \
        "rapidfuzz>=3.9.0" \
        "scikit-learn>=1.4.0" \
        "pandas>=2.2.0" \
        "numpy>=1.26.0" \
        "openpyxl>=3.1.0" \
        "httpx>=0.27.0" \
        "requests>=2.32.0" \
        "aiosqlite>=0.20.0" \
        "pytest>=8.2.0" \
        "pytest-asyncio>=0.23.0" -q
    echo "$CURRENT_HASH" > "$REQUIREMENTS_HASH_FILE"
    echo "[setup] Dependencies installed."
else
    echo "[setup] Dependencies up to date."
fi

# Copy .env from example if .env doesn't exist
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "[setup] Creating .env from .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "[setup] Please update .env with your database credentials before continuing."
    exit 1
fi

# Run Alembic migrations
echo "[db] Running database migrations..."
alembic upgrade head

# Bootstrap storage directories and seed workbooks if missing
echo "[setup] Checking storage..."
python3 - <<'PYEOF'
from pathlib import Path
from backend.excel_intake.workbooks import create_requirement_template

root = Path(__file__).resolve().parent if False else Path(".")

jd_path = root / "storage/job_requirements/jd_input.xlsx"
if not jd_path.exists():
    print("[setup] Creating seed job requirements workbook...")
    create_requirement_template(jd_path)

# Create candidate pool directories so the app doesn't 500 on missing paths
for sub in [
    "storage/candidate_pool",
    "storage/candidate_pool/freshness_cycles",
    "storage/resumes",
    "storage/exports",
]:
    (root / sub).mkdir(parents=True, exist_ok=True)
PYEOF

# Start FastAPI server
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8002}"

# Kill anything already on the port
echo "[setup] Freeing port $PORT..."
fuser -k "${PORT}/tcp" 2>/dev/null || true
if lsof -ti :"$PORT" &>/dev/null 2>&1; then
    lsof -ti :"$PORT" | xargs kill -9 2>/dev/null || true
fi
sleep 1

echo ""
echo "  HireX API starting..."
echo "  Docs:  http://localhost:$PORT/docs"
echo "  ReDoc: http://localhost:$PORT/redoc"
echo ""

exec uvicorn backend.main:app --reload --host "$HOST" --port "$PORT"
