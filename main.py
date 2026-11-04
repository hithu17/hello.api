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
    # Cloud Run sets PORT; default to 8080 for local runs.
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
