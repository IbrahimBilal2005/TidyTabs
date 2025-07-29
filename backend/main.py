from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ml.predict import predict_categories

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TabData(BaseModel):
    titles: list[str]

@app.get("/")
def root():
    return {"status": "TidyTabs local backend is live"}

@app.post("/categorize_local")
def categorize_local(data: TabData):
    try:
        return {"categories": predict_categories(data.titles)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
