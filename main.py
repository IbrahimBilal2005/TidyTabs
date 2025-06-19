from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later restrict to your extension origin
    allow_methods=["*"],
    allow_headers=["*"],
)

class TabData(BaseModel):
    titles: list[str]

@app.get("/")
def root():
    return {"status": "TidyTabs backend is live"}

@app.post("/categorize")
async def categorize_tabs(data: TabData):
    prompt = build_prompt(data.titles)

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
        )

        content = response.choices[0].message.content.strip()
        return JSONResponse(content=json.loads(content))

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def build_prompt(titles: list[str]) -> str:
    return f"""
You are given a list of browser tab titles.

Your task is to group them into clear, high-level categories based on the **intent or purpose behind each tab**, not just the literal text of the title.

## 🧠 Categorization Rules:

1. Return only a **valid JSON object**.  
   - **Keys**: Category names (e.g. "Work", "Entertainment", "Shopping")  
   - **Values**: Arrays of tab titles (as-is from the list)

2. Group tabs under general, meaningful categories such as:
   - "Work", "Research", "Entertainment", "Education", "Shopping", "Social Media", "News", "Email", "Documentation", "Productivity", "Finance", "Travel", "Technology", "Weather", "Health", "Food", "New Tabs"
   - Avoid overly niche or uncommon category names

3. **NEVER** create a category called “Search” or any variation of it.
   - If a title contains “Google Search”, **infer the true intent** and categorize accordingly:
     - "netflix release dates - Google Search" → "Entertainment"
     - "weather in Toronto - Google Search" → "Weather"
     - "how to budget - Google Search" → "Finance"
     - "best burgers near me - Google Search" → "Food"

4. If the tab title is exactly **"New Tab"**, assign it to the category `"New Tabs"`.

5. Every tab must be assigned to a category.
   - If a tab could fit multiple, choose the **most directly relevant** one.

6. Do not return anything except the **JSON object**.

---

Here is the list of tab titles:

{json.dumps(titles, indent=2)}
""".strip()
