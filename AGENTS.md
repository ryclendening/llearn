# Repository Instructions

## Backend Python Environment

- Always run backend Python commands using the Conda environment `llearn_env`.
- Prefer `conda run -n llearn_env <command>` for non-interactive commands.
- This applies to backend tests, scripts, compilation, dependency checks, and server startup.
- Do not use the system Python or another Conda environment for backend verification.

Examples:

```bash
conda run -n llearn_env python -m unittest discover -s tests -v
conda run -n llearn_env python -m compileall -q .
conda run -n llearn_env python -m uvicorn app:app --reload
```

## Project Documentation

- Keep the root `README.md` current as the project grows.
- When making significant changes to app functionality, architecture, setup steps, local services, environment variables, or repository structure, update `README.md` in the same change.
- Keep `AGENTS.md` focused on coding-agent instructions and operational conventions; put human-facing project documentation in `README.md`.
