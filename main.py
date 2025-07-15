import os
import json

from dotenv import load_dotenv
load_dotenv()  

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from ml.predict import predict_categories

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# Middleware to handle CORS, allowing requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your extension origin later
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the data model for the incoming request
class TabData(BaseModel):
    titles: list[str]

@app.get("/")
def root():
    return {"status": "TidyTabs backend is live"}

@app.post("/categorize_local")
def categorize_local(data: TabData):
    try:
        categories = predict_categories(data.titles)
        return {"categories": categories}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.post("/categorize")
def categorize_tabs(data: TabData):
    prompt = build_prompt(data.titles)

    try:
        response = client.chat.completions.create( # Asynchronous call to OpenAI API
            model="gpt-3.5-turbo", 
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4, # Lower temperature for more deterministic output
        )

        # Return the raw GPT content string
        content = response.choices[0].message.content.strip() # Extract the content from the response
        return {"categories": json.loads(content)} # Parse the content as JSON


    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

""" Builds the prompt for the OpenAI API using a base template and the provided titles."""
def build_prompt(titles: list[str]) -> str:
    with open("prompt.txt", "r") as f:
        base_prompt = f.read()
    return base_prompt + "\n\n" + json.dumps(titles, indent=2)
