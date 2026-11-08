# hello_api

A tiny FastAPI app with five endpoints:

| Method | Path          | Response                                                       |
|--------|---------------|----------------------------------------------------------------|
| GET    | `/hello`      | `{"message": "Hey there! 👋"}`                                 |
| GET    | `/goodbye`    | `{"message": "Catch you later! ✌️"}`                           |
| GET    | `/haiku`      | `{"haiku": "..."}`: a short DevOps haiku written by Gemini     |
| GET    | `/fortune`    | `{"fortune": "..."}`: a one-sentence software fortune by Gemini |
| GET    | `/ask?q=...`  | `{"answer": "..."}`: Gemini's short answer to your question    |

`/haiku`, `/fortune` and `/ask` call Google's Gemini model on Vertex AI through the [google-genai](https://pypi.org/project/google-genai/) SDK. `/haiku` and `/fortune` use prompts fixed in the code, take no input, and are capped at about 100 output tokens each. For `/ask`, see [The /ask endpoint](#the-ask-endpoint).

## Requirements

- Python 3.12 or newer
- [Poetry](https://python-poetry.org/) 2.x
- For `/haiku`, `/fortune` and `/ask`: a Google Cloud project with the Vertex AI API enabled, plus the [gcloud CLI](https://cloud.google.com/sdk/docs/install) for local credentials

## Install

```bash
poetry install
```

This creates a virtual environment in `.venv/` and installs the dependencies listed in `poetry.lock`.

## Configure

The app is configured through environment variables:

| Variable                | Required          | Default                 | Purpose                               |
|-------------------------|-------------------|-------------------------|---------------------------------------|
| `PORT`                  | no                | `8080`                  | Port to listen on (Cloud Run sets it) |
| `GOOGLE_CLOUD_PROJECT`  | yes, for Gemini   |                         | Google Cloud project for Vertex AI    |
| `GOOGLE_CLOUD_LOCATION` | no                | `global`                | Vertex AI location                    |
| `GEMINI_MODEL`          | no                | `gemini-3.1-flash-lite` | Gemini model to call                  |

### Authentication

The Gemini endpoints authenticate **only** with [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials). There are no API keys or key files, so don't add any. Any `GOOGLE_API_KEY` or `GEMINI_API_KEY` in the environment is ignored.

- **Locally:** run `gcloud auth application-default login` once.
- **On Cloud Run:** the service's service account is used automatically. Give it the **Vertex AI User** role (`roles/aiplatform.user`).

## Run

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
poetry run python main.py
```

The app listens on port **8080** by default. To use a different port, set `PORT`:

```bash
PORT=9000 poetry run python main.py
```

Try it:

```bash
curl http://localhost:8080/hello
curl http://localhost:8080/goodbye
curl http://localhost:8080/haiku
curl http://localhost:8080/fortune
curl "http://localhost:8080/ask?q=What%20is%20Kubernetes%3F"
```

Interactive API docs are at http://localhost:8080/docs.

`/hello` and `/goodbye` work without any Google Cloud setup.

### The /ask endpoint

`/ask` sends your question in the `q` query parameter to Gemini and returns `{"answer": "..."}`. The endpoint is meant to be public and every call costs money, so it's tightly limited:

- **Input:** `q` is required, can't be empty or only whitespace, and can be at most **200 characters** (surrounding whitespace is trimmed first). Otherwise you get **400** with a JSON error, and Gemini is never called:
  - `{"error": "Query parameter 'q' is required and must not be empty."}`
  - `{"error": "Query parameter 'q' must be 200 characters or fewer."}`
- **Output:** answers are capped at about **200 output tokens**, and a system instruction tells the model to answer in **three sentences or fewer**.

Remember to URL-encode the question (for example, spaces become `%20`).

### Gemini errors

If a Gemini call can't be made, `/haiku`, `/fortune` and `/ask` return JSON such as `{"error": "..."}` instead of crashing:

| Status | When                                                                          |
|--------|-------------------------------------------------------------------------------|
| 500    | `GOOGLE_CLOUD_PROJECT` is not set, or no Application Default Credentials found |
| 502    | Gemini returned an error (the upstream status is in the message) or an empty reply |
| 503    | Gemini is rate limiting requests (HTTP 429). Try again shortly                |

Full error details are written to the server log.

## requirements.txt

`requirements.txt` is generated from `poetry.lock` for deployment (for example, to Google Cloud Run). Regenerate it every time you change dependencies:

```bash
poetry export -f requirements.txt --output requirements.txt
```

Poetry 2 needs the `poetry-plugin-export` plugin for this command. The plugin is declared in `pyproject.toml`, so Poetry installs it automatically.
