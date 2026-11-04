# Plan 02: Gemini endpoints (retrospective)

> **Retrospective plan.** This documents work that was already implemented on 2026-11-04, on the `feature_gemini_endpoints` branch, before any plan was written. CLAUDE.md asks for a saved plan for each piece of work, so this one is being written and approved after the fact. Applying it changes documentation only. No application code changes.

## Context
The original request (logged in `PROMPTS.md` at 2026-11-04 20:56) was to add two GET endpoints, `/haiku` and `/fortune`, that call Gemini on Vertex AI through the `google-genai` SDK. They were to authenticate with Application Default Credentials (ADC) only, read their settings from environment variables, use fixed prompts, cap output at about 100 tokens, and return JSON errors instead of crashing. That work skipped the plan step, so `plans/` has no record of it.

## What was implemented

### 1. Endpoints ([main.py](../main.py))
| Endpoint | Response | Fixed prompt |
|---|---|---|
| `GET /haiku` | `{"haiku": "<three lines>"}` | "Write a short haiku about DevOps. Reply with only the three lines of the haiku, no title." |
| `GET /fortune` | `{"fortune": "<one sentence>"}` | "Write a one-sentence, software-themed fortune-cookie message. Reply with only that sentence." |

- Neither endpoint takes input. Both call a shared helper, `ask_gemini(prompt)`, which sends `GenerateContentConfig(max_output_tokens=100)` and returns the stripped response text.
- `/hello` and `/goodbye` are unchanged. They work without any Google Cloud setup.

### 2. Vertex AI authentication and configuration
- `gemini_client()` builds `genai.Client(vertexai=True, project=..., location=..., http_options=HttpOptions(timeout=30_000))`. It's cached with `functools.cache`, so it's created once, on the first Gemini request rather than at startup.
- **ADC only.** The code passes no `api_key` and no credentials. With `project` and `location` passed explicitly, the SDK ignores any `GOOGLE_API_KEY` or `GEMINI_API_KEY` in the environment (checked in the SDK source, `_api_client.py`).
  - Locally: `gcloud auth application-default login`.
  - On Cloud Run: the service account, which needs `roles/aiplatform.user`.

| Variable | Required | Default |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | yes (for Gemini) | none |
| `GOOGLE_CLOUD_LOCATION` | no | `global` |
| `GEMINI_MODEL` | no | `gemini-3.1-flash-lite` |

### 3. Error handling
`GeminiError(status_code, message)` plus an exception handler return `{"error": "..."}`. Full details go to the server log only.

| Status | Cause |
|---|---|
| 500 | `GOOGLE_CLOUD_PROJECT` not set, or `GoogleAuthError` (no ADC) |
| 503 | Gemini `APIError` with code 429 (rate limited) |
| 502 | Any other `APIError` (upstream code in the message), an unexpected exception or timeout, or an empty reply |

### 4. Dependencies and docs
- `poetry add google-genai`: the only new package, `google-genai (>=2.34.0,<3.0.0)`. `poetry.lock` was updated.
- `pyproject.toml`: the description now mentions `/haiku` and `/fortune`.
- `requirements.txt`: re-exported with `poetry export -f requirements.txt --output requirements.txt`. It pins 31 packages, including `google-genai==2.34.0` and `google-auth==2.62.1`.
- `README.md`: added the endpoints table, the configuration table, an authentication section (ADC locally and on Cloud Run, API keys ignored), Gemini curl examples and the Gemini error table.

### 5. Verification already done
- Real calls through ADC returned 200 for both endpoints.
- Without `GOOGLE_CLOUD_PROJECT`: both endpoints returned 500 with `"GOOGLE_CLOUD_PROJECT is not set."`, and `/hello` and `/goodbye` still returned 200.
- `GEMINI_MODEL=no-such-model`: both returned 502 with `"Gemini request failed (status 404)."`.
- `requirements.txt` installed cleanly in a fresh venv, and `poetry check --lock` passed.
- A secret scan found no keys, credential files or `.env` files in the project.

## Documentation steps to apply after approval (no application code changes)
1. Stay on `feature_gemini_endpoints`. Confirm with `git branch --show-current` that it isn't `main`.
2. **`PROMPTS.md`**:
   - Confirm the original Gemini prompt is present, word for word, under `## 2026-11-04 20:56`. It already is, so no edit is needed there.
   - Append the two prompts that are still missing, word for word:
     - the verification request, timestamped `2026-11-04 21:00 (approximate; logged retroactively)`
     - this retrospective-plan request, timestamped `2026-11-04 21:06`
3. **`plans/02_gemini_endpoints.md`**: save this whole plan, unchanged.
4. Don't touch `main.py`, `pyproject.toml`, `poetry.lock`, `requirements.txt` or `README.md`. Don't commit, push or open a PR.

## Verification of these doc changes
- `git diff --stat` shows changes only in `PROMPTS.md` (relative to the pre-existing uncommitted Gemini changes) and the new untracked `plans/02_gemini_endpoints.md`.
- `grep -n '^## ' PROMPTS.md` lists the 20:56, 21:00 and 21:06 entries.
- `ls plans/` shows `01_hello_goodbye.md` and `02_gemini_endpoints.md`.
