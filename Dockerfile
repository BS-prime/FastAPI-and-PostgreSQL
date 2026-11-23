FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.21 /uv /uvx /bin/

# Switch to /app (creates it if missing); otherwise Docker drops all your files into the Linux root directory (/), mixing your project files directly with core OS system folders (/bin, /etc, /usr). Using /app (or /code) keeps your project isolated and clean.
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Runs uv sync inside /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project 

# Copies your code into /app/src/FastAPI_PostgreSQL/main.py
COPY src/FastAPI_PostgreSQL ./src/FastAPI_PostgreSQL
RUN uv sync --frozen --no-dev --no-install-project

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "src.FastAPI_PostgreSQL.main:app", "--host", "0.0.0.0", "--port", "8000"]