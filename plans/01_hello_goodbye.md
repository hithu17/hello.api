# Plan: Hello/Goodbye FastAPI app

## Context
The repo has only `CLAUDE.md` and is on `main`. We need a small FastAPI app (managed with Poetry) with `GET /hello` and `GET /goodbye` returning casual JSON messages. It will later be deployed to Google Cloud Run from GitHub, so it must listen on `$PORT` (default 8080) and ship a `requirements.txt` exported from Poetry. Tools on the machine: Poetry 2.5.1, Python 3.14.

## Steps

1. **Housekeeping (CLAUDE.md rules). This happens first, before any other file is created or changed.**
   - Run `git checkout -b feature_hello_goodbye`, then confirm with `git branch --show-current` that we're no longer on `main`.
   - Create `PROMPTS.md` and log each prompt word for word, each with its own timestamp (`YYYY-MM-DD HH:MM` from `date`):
     1. the original API prompt
     2. the follow-up asking me to check this plan against CLAUDE.md
   - Save the complete, approved plan (this whole file, unchanged) as `plans/01_hello_goodbye.md`.

2. **`pyproject.toml`** (written by hand, Poetry 2 / PEP 621 format)
   - `requires-python = ">=3.12"`, dependencies: `fastapi`, `uvicorn` (nothing else).
   - `[tool.poetry] package-mode = false`, since this is an app, not a library.
   - `[tool.poetry.requires-plugins] poetry-plugin-export = ">=1.8"`. Poetry 2 no longer includes `poetry export`. Declaring the plugin here makes Poetry install it for this project only, so your global Poetry setup stays unchanged.
   - Run `poetry lock` and `poetry install` to create `poetry.lock` and `.venv`.

3. **`main.py`** (at the repo root)
   ```python
   import os
   import uvicorn
   from fastapi import FastAPI

   app = FastAPI()

   @app.get("/hello")
   def hello():
       return {"message": "Hey there! 👋"}

   @app.get("/goodbye")
   def goodbye():
       return {"message": "Catch you later! ✌️"}

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
   ```
   It binds to `0.0.0.0` because Cloud Run needs that.

4. **`requirements.txt`**: `poetry export -f requirements.txt --output requirements.txt` (with hashes).

5. **`.gitignore`**: `.venv/`, `__pycache__/`, `*.pyc`, `.env`.

6. **`README.md`**: prerequisites, `poetry install`, `poetry run python main.py`, the `PORT` env var, example curl calls and their responses, and how to regenerate `requirements.txt` after dependency changes.

No commits, pushes or PRs. You'll do those.

## Requirements checklist
| # | Requirement | Where |
|---|---|---|
| 1 | Create a branch other than `main` before any code changes | Step 1 (first action) |
| 2 | Create `PROMPTS.md` and log the original prompt with a timestamp | Step 1 |
| 3 | Save the complete plan to `plans/01_hello_goodbye.md` after approval | Step 1 |
| 4 | FastAPI app with `GET /hello` and `GET /goodbye` | Step 3 |
| 5 | Poetry for dependency management (only `fastapi` and `uvicorn`) | Step 2 |
| 6 | Generate `requirements.txt` from Poetry | Step 4 |
| 7 | Read `PORT`, defaulting to 8080 | Step 3 |
| 8 | Write `README.md` with install and run steps, and keep it updated | Step 6 |
| 9 | No commit, push, merge or PR | Steps section, Verification |
| – | Underscores in the names I choose (`feature_hello_goodbye`, `01_hello_goodbye.md`) | Steps 1 and 2 |
| – | No secrets in any file (none are needed, and `.env` is gitignored) | Step 5 |

## Out of scope (for the deploy step later)
Cloud Run's Python buildpack defaults to gunicorn (WSGI), so the deploy step will need a `Procfile` (`web: python main.py`) or a Dockerfile. I'm leaving that out for now, as you asked.

## Verification
- `poetry run python main.py`, then `curl localhost:8080/hello` and `curl localhost:8080/goodbye` should return the JSON messages.
- `PORT=9000 poetry run python main.py`, then curl on 9000, confirms the port override works.
- In a throwaway venv in the scratchpad, `pip install -r requirements.txt` succeeds.
- `git status` shows the expected new files on `feature_hello_goodbye`, and nothing is committed.
