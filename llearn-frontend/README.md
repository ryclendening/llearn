# Llearn Local Development

Llearn has a React/Vite frontend, a FastAPI backend, Postgres for app data, and Weaviate for uploaded course-material vectors.

## Start Docker Services

From the repo root:

```bash
cd /Users/ryanclendening/Development/llearn/llearn
docker compose up -d postgres weaviate
```

Check status:

```bash
docker compose ps
```

Stop services without deleting stored data:

```bash
docker compose stop
```

Avoid `docker compose down -v` unless you intentionally want to delete the database volumes.

## Backend

Make sure `.env` contains:

```txt
OPENAI_API_KEY=...
DATABASE_URL=postgresql+psycopg://llearn:llearn@localhost:5432/llearn
WEAVIATE_URL=http://localhost:8080
WEAVIATE_GRPC_PORT=50051
```

Start the backend:

```bash
conda activate llearn_env
cd /Users/ryanclendening/Development/llearn/llearn/llearn-backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend

In another terminal:

```bash
cd /Users/ryanclendening/Development/llearn/llearn/llearn-frontend
npm install
npm run dev
```

Vite will print the local frontend URL, usually `http://localhost:5173`.

## Inspect Postgres

List tables:

```bash
docker compose exec postgres psql -U llearn -d llearn -c "\dt"
```

View recent uploaded materials:

```bash
docker compose exec postgres psql -U llearn -d llearn -c "SELECT id, lesson_id, filename, status, chunk_count FROM course_materials ORDER BY id DESC LIMIT 10;"
```

Open interactive `psql`:

```bash
docker compose exec postgres psql -U llearn -d llearn
```

Exit interactive `psql` with:

```sql
\q
```

## Useful Checks

Backend syntax check:

```bash
conda run -n llearn_env python -m py_compile llearn-backend/app.py llearn-backend/db/*.py llearn-backend/routers/*.py llearn-backend/vector_db/*.py
```

Frontend build and tests:

```bash
cd llearn-frontend
npm run build
npm test -- --run
```
