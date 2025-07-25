import os
import json
import logging
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SerpAPIWrapper
from langchain import hub

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("tab_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TabGeneratorAgent:
    def __init__(self):
        logger.info("Initializing TabGeneratorAgent...")

        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        logger.info("ChatOpenAI initialized with model gpt-4")

        self.search_tool = SerpAPIWrapper(serpapi_api_key=os.getenv("SERPAPI_API_KEY"))
        logger.info("SerpAPIWrapper initialized")

        self.tools = [
            Tool(
                name="search_web",
                description="Search the web for relevant URLs based on a query. Returns search results with titles, URLs, and descriptions.",
                func=self.search_tool.run
            )
        ]

        # Create the prompt template with proper format for structured chat agent
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an assistant that helps users by creating useful browser tabs.

When given a request like "learn Python" or "plan trip to Japan", do the following:
1. Figure out useful web search queries.
2. Use the `search_web` tool to get results.
3. Pick 5–8 of the most useful URLs and organize them into tabs.
4. For each tab, include a title, url, and description.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Your Final Answer MUST be ONLY valid JSON in this exact format:
{{
  "group_name": "Brief descriptive name",
  "tabs": [
    {{"title": "Tab title", "url": "https://example.com", "description": "Brief description"}}
  ]
}}

Do not include any explanation or other text in the Final Answer. Only return the JSON."""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Use a simpler agent approach that works more reliably
        
        # Create a custom ReAct prompt template
        react_prompt = ChatPromptTemplate.from_template("""You are an assistant that helps users by creating useful browser tabs.

When given a request like "learn Python" or "plan trip to Japan", do the following:
1. Figure out useful web search queries.
2. Use the `search_web` tool to get results.
3. Pick 5–8 of the most useful URLs and organize them into tabs.
4. For each tab, include a title, url, and description.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Your Final Answer MUST be ONLY valid JSON in this exact format:
{{
  "group_name": "Brief descriptive name",
  "tabs": [
    {{"title": "Tab title", "url": "https://example.com", "description": "Brief description"}}
  ]
}}

Do not include any explanation or other text in the Final Answer. Only return the JSON.

Begin!

Question: {input}
Thought: {agent_scratchpad}""")

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt
        )
        logger.info("ReAct agent created")

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=5
        )
        logger.info("AgentExecutor initialized")

    def generate_tabs(self, user_prompt: str) -> dict:
        logger.info(f"Generating tabs for prompt: {user_prompt}")
        try:
            result = self.executor.invoke({"input": user_prompt})
            raw_output = result.get("output", "")
            logger.info(f"Raw output from agent:\n{raw_output}")

            # Try to parse the JSON response
            parsed_output = self._parse_json_response(raw_output)
            if parsed_output:
                logger.info("Successfully parsed agent output to JSON")
                return self._validate_and_clean_result(parsed_output)
            else:
                logger.warning("Failed to parse agent output, using fallback")
                return self._create_fallback_response(user_prompt)

        except Exception as e:
            logger.error(f"[Agent Error] {e}", exc_info=True)
            return self._create_fallback_response(user_prompt)

    def _parse_json_response(self, response: str) -> dict:
        """Extract and parse JSON from the agent response"""
        if not response or not response.strip():
            return None
        
        # Try direct JSON parsing first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON using regex
        import re
        
        # Look for JSON patterns
        patterns = [
            r'\{[^{}]*"group_name"[^{}]*"tabs"[^{}]*\[[^\]]*\][^{}]*\}',
            r'\{.*?"group_name".*?"tabs".*?\[.*?\].*?\}',
            r'```(?:json)?\s*(\{.*?\})\s*```',
            r'(\{.*\})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    if "group_name" in result and "tabs" in result:
                        return result
                except json.JSONDecodeError:
                    continue
        
        return None

    def _validate_and_clean_result(self, result: dict) -> dict:
        """Validate and clean the parsed result"""
        try:
            cleaned_tabs = []
            for tab in result.get("tabs", []):
                if isinstance(tab, dict) and "title" in tab and "url" in tab:
                    url = tab["url"]
                    if not url.startswith("http"):
                        url = f"https://{url}"
                    
                    cleaned_tabs.append({
                        "title": str(tab["title"])[:100],
                        "url": url,
                        "description": str(tab.get("description", ""))[:200]
                    })
            
            return {
                "group_name": str(result.get("group_name", "Generated Tabs"))[:50],
                "tabs": cleaned_tabs[:8]
            }
        except Exception as e:
            logger.error(f"Result validation failed: {e}")
            return None

    def _create_fallback_response(self, user_prompt: str) -> dict:
        """Create a fallback response when the agent fails"""
        return {
            "group_name": f"Search: {user_prompt}",
            "tabs": [
                {
                    "title": "Google Search",
                    "url": f"https://www.google.com/search?q={user_prompt.replace(' ', '+')}",
                    "description": "Search results from Google"
                },
                {
                    "title": "YouTube Search", 
                    "url": f"https://www.youtube.com/results?search_query={user_prompt.replace(' ', '+')}",
                    "description": "Video content on YouTube"
                },
                {
                    "title": "Wikipedia Search",
                    "url": f"https://en.wikipedia.org/wiki/Special:Search?search={user_prompt.replace(' ', '+')}",
                    "description": "Encyclopedia articles on Wikipedia"
                }
            ]
        }

    def test_search(self, query: str) -> str:
        """Test method to check if SerpAPI is working"""
        try:
            return self.search_tool.run(query)
        except Exception as e:
            return f"Search error: {e}"

    def test_simple_generation(self, prompt: str) -> dict:
        """Simple test without agent - just direct LLM call"""
        try:
            test_prompt = f"""Create browser tabs for: {prompt}

Return only JSON in this format:
{{
  "group_name": "Learning Python",
  "tabs": [
    {{"title": "Python.org", "url": "https://python.org", "description": "Official Python website"}},
    {{"title": "Python Tutorial", "url": "https://docs.python.org/3/tutorial/", "description": "Official Python tutorial"}}
  ]
}}"""
            
            response = self.llm.invoke(test_prompt)
            return self._parse_json_response(response.content)
        except Exception as e:
            logger.error(f"Simple test failed: {e}")
            return None