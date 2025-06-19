from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your extension origin later
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

        # Return the raw GPT content string
        content = response.choices[0].message.content.strip()
        return { "categories": content }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def build_prompt(titles: list[str]) -> str:
    return f"""
You are given a list of browser tab titles.

Your task is to group them into categories based on the **actual purpose or intent** behind each tab — not the exact text.

You must return a **valid JSON object only**, structured like this:

{{
  "Category 1": ["Title A", "Title B"],
  "Category 2": ["Title C", "Title D"]
}}

---

### Strict Rules:

1. Choose categories **only** from this approved list:
   - "Work", "Research", "Entertainment", "Education", "Shopping", "Social Media", "News", "Email", "Documentation", "Productivity", "Finance", "Travel", "Technology", "Weather", "Health", "Food", "New Tabs"

2. If a tab is **'New Tab'**, assign it to `"New Tabs"`.

3. NEVER use categories like "Search", "Other", "Miscellaneous", or create new ones.

4. If a tab includes "Google Search", classify it by the actual topic searched:
   - "weather in Paris - Google Search" → "Weather"
   - "how to get a scholarship - Google Search" → "Education"

5. Each tab must be assigned to **exactly one** of the approved categories.

---

Here is the list of tab titles:

{json.dumps(titles, indent=2)}
""".strip()
