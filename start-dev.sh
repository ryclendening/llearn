#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/llearn-backend"
FRONTEND_DIR="$ROOT_DIR/llearn-frontend"

CONDA_ENV="${CONDA_ENV:-llearn_env}"
CONDA_BIN="${CONDA_BIN:-/opt/miniconda3/bin/conda}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

backend_pid=""
frontend_pid=""

cleanup() {
  local exit_code=$?

  if [[ -n "${backend_pid}" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
  fi

  if [[ -n "${frontend_pid}" ]] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid" 2>/dev/null || true
  fi

  exit "$exit_code"
}

trap cleanup EXIT INT TERM

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but was not found on PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required but is not available." >&2
  exit 1
fi

if [[ ! -x "$CONDA_BIN" ]]; then
  if command -v conda >/dev/null 2>&1; then
    CONDA_BIN="$(command -v conda)"
  else
    echo "conda was not found. Set CONDA_BIN=/path/to/conda and try again." >&2
    exit 1
  fi
fi

echo "Starting Docker services..."
docker compose -f "$ROOT_DIR/docker-compose.yml" up -d

echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT} using conda env ${CONDA_ENV}..."
(
  cd "$BACKEND_DIR"
  exec "$CONDA_BIN" run --no-capture-output -n "$CONDA_ENV" \
    python -m uvicorn app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload
) &
backend_pid=$!

echo "Starting frontend on http://${FRONTEND_HOST}:${FRONTEND_PORT}..."
(
  cd "$FRONTEND_DIR"
  exec npm start -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
frontend_pid=$!

echo
echo "lLearn is starting:"
echo "  Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "  Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo
echo "Press Ctrl+C to stop the backend and frontend. Docker services will keep running."

while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do
  sleep 1
done

echo
echo "One of the app servers stopped. Shutting down the remaining app server..."

wait "$backend_pid" 2>/dev/null || true
wait "$frontend_pid" 2>/dev/null || true
exit 1
