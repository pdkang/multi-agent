from phi.assistant import Assistant
from phi.llm.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
import logging

class WebSearchAgent:
    def __init__(self):
        """
        Initialize the web search agent with a strong prompt to ensure it uses the search tool.
        """
        self.logger = logging.getLogger('multi_agent')
        
        # --- CORRECTED AGENT INITIALIZATION ---
        # Using Assistant which is a more robust implementation than the base Agent.
        # The system prompt is now very explicit to force tool usage.
        self.agent = Assistant(
            name="Web Searcher",
            llm=Groq(model="llama-3.3-70b-versatile"), # Using the recommended model name
            tools=[DuckDuckGo()],
            show_tool_calls=True,
            # This is the key change: A direct command to use the tool.
            instructions=[
                "You are a world-class web researcher.",
                "You MUST use the `duckduckgo_search` tool to answer the user's question.",
                "Do not answer from your own knowledge. Your only job is to search.",
                "Provide a concise answer based on the search results and ALWAYS include the sources."
            ],
            markdown=True
        )
        
    def process_query(self, query: str) -> str:
        """
        Process a query using the web search agent. This method now uses the more
        reliable .run() method which directly returns the final response.
        
        Args:
            query (str): The search query
            
        Returns:
            str: The search results formatted as a response
        """
        try:
            # --- SIMPLIFIED AND MORE RELIABLE METHOD ---
            # The .run() method handles the entire interaction and returns the final string.
            # This avoids complex stdout capturing and parsing.
            response = ""
            for chunk in self.agent.run(query, stream=True):
                response += chunk
            
            if not response:
                return "I could not find an answer during the web search."
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}", exc_info=True)
            return f"An error occurred while performing the web search: {str(e)}"
