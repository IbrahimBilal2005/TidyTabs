#main.py
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
@app.head("/")
def root():
    return {"status": "TidyTabs local backend is live"}

@app.post("/categorize_local")
def categorize_local(data: TabData):
    try:
        result = predict_categories(data.titles)

        # Log which titles went to "Other"
        if "Other" in result:
            print("\n=== Tabs categorized as 'Other' ===")
            for title in result["Other"]:
                print(f"- {title}")
            print("=== End of 'Other' ===\n")
        

        return {"categories": result}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


