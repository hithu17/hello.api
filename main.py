import logging
import os
from functools import cache

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google import genai
from google.auth.exceptions import GoogleAuthError
from google.genai import errors, types

logger = logging.getLogger(__name__)

HAIKU_PROMPT = (
    "Write a short haiku about DevOps. "
    "Reply with only the three lines of the haiku, no title."
)
FORTUNE_PROMPT = (
    "Write a one-sentence, software-themed fortune-cookie message. "
    "Reply with only that sentence."
)
ASK_SYSTEM_INSTRUCTION = (
    "You answer questions from the public. "
    "Answer in three sentences or fewer, in plain text."
)
ASK_MAX_QUESTION_LENGTH = 200

app = FastAPI()


class GeminiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


@app.exception_handler(GeminiError)
def gemini_error_handler(request: Request, exc: GeminiError):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@cache
def gemini_client() -> genai.Client:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise GeminiError(500, "GOOGLE_CLOUD_PROJECT is not set.")
    # Passing project/location (and no api_key) means Vertex AI with
    # Application Default Credentials; any API key in the environment is ignored.
    return genai.Client(
        vertexai=True,
        project=project,
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        http_options=types.HttpOptions(timeout=30_000),
    )


def ask_gemini(
    prompt: str, max_output_tokens: int = 100, system_instruction: str | None = None
) -> str:
    client = gemini_client()
    try:
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                system_instruction=system_instruction,
            ),
        )
    except GoogleAuthError:
        logger.exception("Gemini call failed: no usable credentials")
        raise GeminiError(500, "No Google Cloud credentials found (Application Default Credentials).")
    except errors.APIError as e:
        logger.exception("Gemini call failed")
        if e.code == 429:
            raise GeminiError(503, "Gemini is rate limited right now. Try again shortly.")
        raise GeminiError(502, f"Gemini request failed (status {e.code}).")
    except Exception:
        logger.exception("Gemini call failed")
        raise GeminiError(502, "Gemini request failed.")

    if not response.text:
        raise GeminiError(502, "Gemini returned an empty response.")
    return response.text.strip()


@app.get("/hello")
def hello():
    return {"message": "Hey there! 👋"}


@app.get("/goodbye")
def goodbye():
    return {"message": "Catch you later! ✌️"}


@app.get("/haiku")
def haiku():
    return {"haiku": ask_gemini(HAIKU_PROMPT)}


@app.get("/fortune")
def fortune():
    return {"fortune": ask_gemini(FORTUNE_PROMPT)}


@app.get("/ask")
def ask(q: str | None = None):
    # Validate before touching Gemini: bad input must never cost money.
    question = (q or "").strip()
    if not question:
        return JSONResponse(
            status_code=400,
            content={"error": "Query parameter 'q' is required and must not be empty."},
        )
    if len(question) > ASK_MAX_QUESTION_LENGTH:
        return JSONResponse(
            status_code=400,
            content={"error": f"Query parameter 'q' must be {ASK_MAX_QUESTION_LENGTH} characters or fewer."},
        )
    answer = ask_gemini(
        question, max_output_tokens=200, system_instruction=ASK_SYSTEM_INSTRUCTION
    )
    return {"answer": answer}


if __name__ == "__main__":
    # Cloud Run sets PORT; default to 8080 for local runs.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
