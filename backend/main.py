# main.py: FastAPI backend for TidyTabs AI extension (local model only)

import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ml.predict import predict_categories

app = FastAPI()

# Middleware to handle CORS, allowing requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your extension origin later
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Request model ===
class TabData(BaseModel):
    titles: list[str]

@app.get("/")
def root():
    return {"status": "TidyTabs local backend is live"}

@app.post("/categorize_local")
def categorize_local(data: TabData):
    try:
        categories = predict_categories(data.titles)
        return {"categories": categories}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
