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
