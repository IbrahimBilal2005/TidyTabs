from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your extension later
    allow_methods=["*"],
    allow_headers=["*"],
)

class TabData(BaseModel):
    titles: list[str]

@app.post("/categorize")
async def categorize_tabs(data: TabData):
    prompt = build_prompt(data.titles)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that categorizes browser tabs."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    content = response.choices[0].message["content"]
    return {"categories": content}

def build_prompt(titles: list[str]) -> str:
    return f"""
You are given a list of browser tab titles. Group them into meaningful high-level categories based on the purpose of each tab.

Rules:
- If a title contains “Google Search”, categorize it based on the actual search query.
- Use categories like: "Entertainment", "Education", "Productivity", "Technology", "News", "Travel", etc.
- Do not skip any.
- Return a valid JSON object: keys are category names, values are arrays of titles.

Titles:
{chr(10).join(titles)}
""".strip()
