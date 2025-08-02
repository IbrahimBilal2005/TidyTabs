import os
import json
import logging
from dotenv import load_dotenv
from google import genai
import re


dotenv = load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    handlers=[logging.FileHandler("tab_generator.log"), logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


def generate_content(model, query):
    """
    Return the response returned by the Gemini API given a model and query
    """
    response = client.models.generate_content(model=model, contents=query)
    return response.text


class TabGeneratorAgent:
    def __init__(self):
        logger.info("Initialized TabGeneratorAgent using Gemini")

    def generate_tabs(self, user_prompt: str) -> dict:
        logger.info(f"Generating tabs for prompt: {user_prompt}")

        prompt = f"""
                    You are an assistant that helps users by creating useful browser tabs.

                    When given a request like "learn Python" or "plan trip to Japan", do the following:
                    1. Figure out useful search queries.
                    2. Find 5–8 helpful websites related to it.
                    3. Return ONLY valid JSON in the following format:
                    {{
                    "group_name": "Brief descriptive name",
                    "tabs": [
                        {{
                        "title": "Tab title",
                        "url": "https://example.com",
                        "description": "Short helpful description"
                        }},
                        ...
                    ]
                    }}

                    Do not add any other text. No commentary. Only JSON.

                    Now respond for this request: {user_prompt}
                    """

        try:
            response = generate_content(MODEL, prompt)
            text = response.strip()
            logger.info("Raw Gemini response:\n" + text)
            parsed = self._parse_json_response(text)

            if parsed:
                return self._validate_and_clean_result(parsed)

        except Exception as e:
            logger.error(f"[Gemini Error] {e}", exc_info=True)

        return self._create_fallback_response(user_prompt)

    def _parse_json_response(self, response: str) -> dict:
        """Extract and parse JSON from Gemini response"""
        
        if not response.strip():
            return None

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        patterns = [
            r'\{[^{}]*"group_name"[^{}]*"tabs"[^{}]*\[[^\]]*\][^{}]*\}',
            r'```(?:json)?\s*(\{.*?\})\s*```',
            r'(\{.*\})'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if "group_name" in data and "tabs" in data:
                        return data
                except json.JSONDecodeError:
                    continue
        return None

    def _validate_and_clean_result(self, result: dict) -> dict:
        try:
            cleaned = []
            for tab in result.get("tabs", []):
                if "title" in tab and "url" in tab:
                    url = tab["url"]
                    if not url.startswith("http"):
                        url = f"https://{url}"
                    cleaned.append({
                        "title": tab["title"][:100],
                        "url": url,
                        "description": tab.get("description", "")[:200]
                    })
            return {
                "group_name": result.get("group_name", "Generated Tabs")[:50],
                "tabs": cleaned[:8]
            }
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return None

    def _create_fallback_response(self, user_prompt: str) -> dict:
        query = user_prompt.replace(" ", "+")
        return {
            "group_name": f"Search: {user_prompt}",
            "tabs": [
                {"title": "Google Search", "url": f"https://www.google.com/search?q={query}", "description": "Search results from Google"},
                {"title": "YouTube", "url": f"https://www.youtube.com/results?search_query={query}", "description": "YouTube videos related to the topic"},
                {"title": "Wikipedia", "url": f"https://en.wikipedia.org/wiki/Special:Search?search={query}", "description": "Encyclopedia articles"}
            ]
        }