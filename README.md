# lLearn

lLearn is a local AI learning and tutoring application. It combines a React/Vite frontend, a FastAPI backend, Postgres for application data, and Weaviate for vector search over uploaded course materials.

The app is designed around teacher-created classes, learning objectives, uploaded course materials, example problem extraction, student practice, tutoring chat, and performance tracking.

## Repository Structure

```text
.
├── AGENTS.md              # Instructions for coding agents working in this repo
├── PROJECT_IDEAS.md       # Product backlog and future project ideas
├── docker-compose.yml     # Local Postgres and Weaviate services
├── requirements.txt       # Backend Python dependencies
├── start-dev.sh           # Optional local helper for starting services and app servers
├── llearn-backend/        # FastAPI backend
└── llearn-frontend/       # React/Vite frontend
```

## Backend

The backend lives in `llearn-backend/` and uses FastAPI. It initializes configuration and database state on startup, then mounts route modules for the app's main domains:

- Authentication and user session management
- Admin teacher-access workflows
- Learning objective generation and management
- Student enrollment and rosters
- Course material upload, storage, and retrieval
- Example problem extraction, publishing, practice, and grading
- Student performance and chat logs
- Tutoring chat over WebSockets

Important backend folders:

```text
llearn-backend/
├── app.py                 # FastAPI app entrypoint
├── auth/                  # Auth config, services, and dependencies
├── assessment/            # Assessment evidence helpers
├── db/                    # SQLAlchemy models, CRUD, session, initialization
├── document_processing/   # Text and PDF extraction helpers
├── routers/               # API route modules
├── services/              # Application services
├── tests/                 # Backend tests
└── vector_db/             # Chunking, ingestion, pipeline, and Weaviate integration
```

Backend Python commands should be run with the Conda environment `llearn_env`.

## Frontend

The frontend lives in `llearn-frontend/` and uses React with Vite.

Important frontend files:

```text
llearn-frontend/
├── package.json
├── vite.config.js
└── src/
    ├── App.js
    ├── AuthContext.js
    ├── ChatPage.js
    ├── AdminDashboard.js
    ├── ClassPerformanceDashboard.js
    ├── LearningObjectivesForm.js
    └── ...
```

The frontend includes screens and components for login, chat tutoring, teacher/admin workflows, math rendering, and performance views. Teacher class management uses a single class setup screen with a left-side workflow toggle for AI generation, goals/objectives, existing classes, and class materials/examples.

## Local Services

Start Postgres and Weaviate from the repo root:

```bash
docker compose up -d postgres weaviate
```

Check service status:

```bash
docker compose ps
```

Stop services without deleting stored data:

```bash
docker compose stop
```

Avoid `docker compose down -v` unless you intentionally want to delete the local database and vector-store volumes.

## Environment

Create a `.env` file for local backend development with values like:

```txt
OPENAI_API_KEY=...
DATABASE_URL=postgresql+psycopg://llearn:llearn@localhost:5432/llearn
WEAVIATE_URL=http://localhost:8080
WEAVIATE_GRPC_PORT=50051
```

Auth-related settings may also be required depending on whether you are using local dev login or OAuth flows.

## Running Locally

Start the backend:

```bash
cd llearn-backend
conda run -n llearn_env python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend in another terminal:

```bash
cd llearn-frontend
npm install
npm run dev
```

Vite usually serves the frontend at `http://localhost:5173`.

If `start-dev.sh` is available and executable, it can be used from the repo root to start Docker services plus the backend and frontend together:

```bash
./start-dev.sh
```

## Useful Checks

Backend syntax check:

```bash
conda run -n llearn_env python -m py_compile llearn-backend/app.py llearn-backend/db/*.py llearn-backend/routers/*.py llearn-backend/vector_db/*.py
```

Backend tests:

```bash
cd llearn-backend
conda run -n llearn_env python -m unittest discover -s tests -v
```

Frontend build:

```bash
cd llearn-frontend
npm run build
```

Frontend tests:

```bash
cd llearn-frontend
npm test -- --run
```

## Inspecting Local Data

List Postgres tables:

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

## Documentation Expectations

Keep this README current as the project grows. Significant changes to app functionality, architecture, setup, local services, environment variables, or repository structure should be reflected here as part of the same change.
