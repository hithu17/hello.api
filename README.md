# hello_api

A tiny FastAPI app with two endpoints:

| Method | Path       | Response                                  |
|--------|------------|-------------------------------------------|
| GET    | `/hello`   | `{"message": "Hey there! 👋"}`            |
| GET    | `/goodbye` | `{"message": "Catch you later! ✌️"}`      |

## Requirements

- Python 3.12 or newer
- [Poetry](https://python-poetry.org/) 2.x

## Install

```bash
poetry install
```

This creates a virtual environment in `.venv/` and installs the dependencies listed in `poetry.lock`.

## Run

```bash
poetry run python main.py
```

The app listens on port **8080** by default. To use a different port, set the `PORT` environment variable (Cloud Run sets it automatically):

```bash
PORT=9000 poetry run python main.py
```

Try it:

```bash
curl http://localhost:8080/hello
curl http://localhost:8080/goodbye
```

Interactive API docs are at http://localhost:8080/docs.

## requirements.txt

`requirements.txt` is generated from `poetry.lock` for deployment (for example, to Google Cloud Run). Regenerate it every time you change dependencies:

```bash
poetry export -f requirements.txt --output requirements.txt
```

Poetry 2 needs the `poetry-plugin-export` plugin for this command. The plugin is declared in `pyproject.toml`, so Poetry installs it automatically.
