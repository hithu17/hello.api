# Plan 03: `/ask` endpoint

## Context
`/haiku` and `/fortune` (Plan 02, now merged to `main`) call Gemini with fixed prompts. We want a public `GET /ask?q=...` that sends a user's question to Gemini, using the same client and settings, and returns the answer as JSON. Every call costs money and the endpoint will be on the internet, so:
- bad input is rejected before Gemini is called
- the answer is capped at about 200 output tokens
- a system instruction keeps answers to three sentences or fewer

## Steps

1. **Housekeeping (CLAUDE.md).** `main` is checked out and is up to date with the merged PR #1.
   - Run `git checkout -b feature_ask_endpoint` and confirm with `git branch --show-current` that we're off `main`.
   - Log this prompt word for word in `PROMPTS.md` under `## 2026-11-08 04:51`.
   - Save this plan, unchanged, as `plans/03_ask_endpoint.md`.

2. **Extend `ask_gemini`** ([main.py:52](../main.py)). Add two optional parameters and keep the defaults, so `/haiku` and `/fortune` behave exactly as before:
   ```python
   def ask_gemini(prompt: str, max_output_tokens: int = 100, system_instruction: str | None = None) -> str:
       ...
       config=types.GenerateContentConfig(
           max_output_tokens=max_output_tokens,
           system_instruction=system_instruction,
       ),
   ```
   The client (`gemini_client()`), the model, location and project settings, and all the existing error handling (500/502/503) are reused unchanged.

3. **Add `/ask`** to `main.py`, next to the other Gemini endpoints:
   ```python
   ASK_SYSTEM_INSTRUCTION = (
       "You answer questions from the public. "
       "Answer in three sentences or fewer, in plain text."
   )
   ASK_MAX_QUESTION_LENGTH = 200

   @app.get("/ask")
   def ask(q: str | None = None):
       question = (q or "").strip()
       if not question:
           return JSONResponse(status_code=400, content={"error": "Query parameter 'q' is required and must not be empty."})
       if len(question) > ASK_MAX_QUESTION_LENGTH:
           return JSONResponse(status_code=400, content={"error": f"Query parameter 'q' must be {ASK_MAX_QUESTION_LENGTH} characters or fewer."})
       return {"answer": ask_gemini(question, max_output_tokens=200, system_instruction=ASK_SYSTEM_INSTRUCTION)}
   ```
   - **Why I validate by hand.** FastAPI's `Query(min_length=..., max_length=...)` would return a 422 with FastAPI's nested `{"detail": [...]}` format, and it lets whitespace-only input through. Checking by hand gives the same `{"error": "..."}` shape as the other endpoints and treats `q=%20%20` as empty.
   - **Validation runs before the Gemini client is created.** Bad input never costs money, and it gets a 400 even when `GOOGLE_CLOUD_PROJECT` isn't set.
   - **Length is measured after stripping whitespace.** Leading and trailing spaces aren't sent to Gemini.
   - **Logging.** The question text isn't logged. Existing logging only records exceptions.

4. **`README.md`**:
   - Add `/ask` to the endpoints table.
   - Add an `/ask` section: the `q` rules (required, non-empty, at most 200 characters), the 400 errors, the 200-token and three-sentence limits, and a curl example (`curl "http://localhost:8080/ask?q=What%20is%20Kubernetes%3F"`).
   - Mention in the Gemini errors section that `/ask` uses the same 500/502/503 codes.

5. **No new dependencies.** `pyproject.toml`, `poetry.lock` and `requirements.txt` don't change, which `poetry check --lock` will confirm. No commits, pushes or PRs.

## Out of scope (I recommend it before going public)
The input and token limits cap the cost of each call, but nothing limits how *many* calls come in. Before exposing `/ask`, consider at least setting Cloud Run `--max-instances` and a Vertex AI quota or budget alert. A rate limiter or API Gateway could come later. None of this needs code changes now.

## Verification
Use a throwaway `TestClient` script in the scratchpad. `httpx` is already installed, so no new packages are needed.
- **Without `GOOGLE_CLOUD_PROJECT`:**
  - Missing `q`, `q=`, whitespace-only `q` and a 201-character `q` each return **400** with a clear `{"error": ...}`. This also proves validation happens before any Gemini call.
  - A valid `q` returns 500 (project not set).
- **With the project and ADC:**
  - `/ask?q=What is Kubernetes?` returns 200 with `{"answer": "..."}` in three sentences or fewer.
  - A `q` of exactly 200 characters is accepted.
  - `/haiku` and `/fortune` still return 200.
- `GEMINI_MODEL=no-such-model` makes `/ask` return 502.
- `poetry check --lock` passes, and `git status` shows only `main.py`, `README.md`, `PROMPTS.md` and `plans/03_ask_endpoint.md` changed or added, on `feature_ask_endpoint`.
