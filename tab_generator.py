import os
import json
import re
from typing import Dict, Any, List
from urllib.parse import quote

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_community.utilities import SerpAPIWrapper


class TabGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.search = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))

    def generate_tabs(self, user_prompt: str) -> Dict[str, Any]:
        """Generate tabs based on user intent using real search results"""
        try:
            # Step 1: Generate search queries for different aspects
            search_queries = self._generate_search_queries(user_prompt)
            
            # Step 2: Get real URLs from search results
            search_results = self._get_search_results(search_queries)
            
            # Step 3: Have LLM organize the results into tabs
            return self._organize_into_tabs(user_prompt, search_results)
            
        except Exception as e:
            print(f"Error: {e}")
            return self._basic_fallback(user_prompt)

    def _generate_search_queries(self, user_prompt: str) -> List[str]:
        """Generate specific search queries for different aspects"""
        prompt = f"""
User request: "{user_prompt}"

Generate 4-6 specific search queries that would help someone with this request. 
Think about different aspects they might need:
- Main topic research
- Practical tools/resources
- Reviews/recommendations
- How-to guides
- Location-specific info (if relevant)
- Shopping/booking (if relevant)

Return ONLY a JSON array of search query strings:
["query1", "query2", "query3", ...]

Examples:
For "plan a trip to Tokyo": ["Tokyo travel guide", "Tokyo hotels booking", "Tokyo restaurants", "Tokyo attractions", "Tokyo weather"]
For "learn Python": ["Python tutorial beginners", "Python documentation", "Python practice exercises", "Python IDE", "Python projects"]
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            queries = json.loads(response.content)
            return queries[:6] if isinstance(queries, list) else [user_prompt]
        except:
            # Fallback to basic queries
            return [
                user_prompt,
                f"{user_prompt} guide",
                f"{user_prompt} reviews",
                f"best {user_prompt}"
            ]

    def _get_search_results(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Get actual search results from SerpAPI"""
        all_results = []
        
        for query in queries:
            try:
                results = self.search.results(query)
                
                # Extract organic results
                organic_results = results.get("organic_results", [])
                
                for result in organic_results[:3]:  # Top 3 results per query
                    url = result.get("link")
                    title = result.get("title")
                    snippet = result.get("snippet", "")
                    
                    if url and title and self._is_valid_url(url):
                        all_results.append({
                            "query": query,
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                        
            except Exception as e:
                print(f"Search failed for query '{query}': {e}")
                continue
        
        return all_results

    def _organize_into_tabs(self, user_prompt: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Have LLM organize search results into useful tabs"""
        
        # Format search results for the LLM
        formatted_results = []
        for result in search_results:
            formatted_results.append(
                f"Title: {result['title']}\n"
                f"URL: {result['url']}\n"
                f"Description: {result['snippet']}\n"
                f"From query: {result['query']}\n"
            )
        
        results_text = "\n---\n".join(formatted_results)
        
        prompt = f"""
User request: "{user_prompt}"

Here are real search results from the web:

{results_text}

Your task:
1. Select the 5-8 most useful URLs from these results
2. Organize them into a logical tab group
3. Give each tab a clear, descriptive title
4. Explain why each tab is useful

Return ONLY valid JSON in this exact format:
{{
  "group_name": "Short descriptive title for the tab group",
  "tabs": [
    {{
      "title": "Clear, descriptive tab title",
      "url": "EXACT URL from the search results above",
      "description": "Why this tab is useful for the user's request"
    }}
  ]
}}

Important:
- Use ONLY URLs that appear in the search results above
- Choose the most relevant and useful sites
- Avoid duplicate or very similar sites
- Make tab titles descriptive and specific
"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Try to parse JSON
            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise Exception("No valid JSON found")
            
            # Validate result
            if self._validate_result(result, search_results):
                return result
            else:
                raise Exception("Invalid result structure")
                
        except Exception as e:
            print(f"LLM organization failed: {e}")
            # Create simple tabs from search results
            return self._create_simple_tabs(user_prompt, search_results)

    def _validate_result(self, result: Dict[str, Any], search_results: List[Dict[str, Any]]) -> bool:
        """Validate that the result uses only real URLs from search results"""
        if not isinstance(result, dict) or "group_name" not in result or "tabs" not in result:
            return False
        
        if not isinstance(result["tabs"], list) or len(result["tabs"]) == 0:
            return False
        
        # Get all valid URLs from search results
        valid_urls = {r["url"] for r in search_results}
        
        # Check each tab
        valid_tabs = []
        for tab in result["tabs"]:
            if (isinstance(tab, dict) and 
                "title" in tab and "url" in tab and "description" in tab and
                tab["url"] in valid_urls):
                valid_tabs.append(tab)
        
        if len(valid_tabs) == 0:
            return False
        
        result["tabs"] = valid_tabs
        return True

    def _create_simple_tabs(self, user_prompt: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create simple tabs directly from search results"""
        tabs = []
        seen_urls = set()
        
        for result in search_results[:8]:  # Max 8 tabs
            url = result["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                tabs.append({
                    "title": result["title"],
                    "url": url,
                    "description": result["snippet"][:100] + "..." if len(result["snippet"]) > 100 else result["snippet"]
                })
        
        return {
            "group_name": f"Research: {user_prompt}",
            "tabs": tabs
        }

    def _basic_fallback(self, user_prompt: str) -> Dict[str, Any]:
        """Last resort fallback with guaranteed working URLs"""
        safe_query = quote(user_prompt)
        return {
            "group_name": f"Search: {user_prompt}",
            "tabs": [
                {
                    "title": f"Google Search - {user_prompt}",
                    "url": f"https://www.google.com/search?q={safe_query}",
                    "description": "Search Google for your request"
                },
                {
                    "title": f"YouTube - {user_prompt}",
                    "url": f"https://www.youtube.com/results?search_query={safe_query}",
                    "description": "Find videos related to your request"
                },
                {
                    "title": f"Wikipedia - {user_prompt}",
                    "url": f"https://en.wikipedia.org/w/index.php?search={safe_query}",
                    "description": "Encyclopedia information"
                }
            ]
        }

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and not from unwanted domains"""
        if not url or not isinstance(url, str):
            return False
        
        # Basic URL pattern check
        pattern = re.compile(
            r'^https?://'
            r'(([A-Z0-9-]+\.)+[A-Z]{2,6}|localhost|\d{1,3}(\.\d{1,3}){3})'
            r'(:\d+)?(/.*)?$', re.IGNORECASE)
        
        if not pattern.match(url):
            return False
        
        # Filter out unwanted domains
        unwanted_domains = [
            "example.com", "test.com", "placeholder.com",
            "facebook.com", "twitter.com", "instagram.com",  # Social media can be less useful
            "linkedin.com", "pinterest.com"
        ]
        
        url_lower = url.lower()
        return not any(domain in url_lower for domain in unwanted_domains)


# Usage example
if __name__ == "__main__":
    generator = TabGenerator()
    result = generator.generate_tabs("learn machine learning")
    print(json.dumps(result, indent=2))