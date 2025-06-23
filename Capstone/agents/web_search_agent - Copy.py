from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
import logging
import io
import sys

class WebSearchAgent:
    def __init__(self):
        """Initialize the web search agent with DuckDuckGo search tool"""
        self.logger = logging.getLogger('multi_agent')
        self.agent = Agent(
            name="Web Search Agent",
            role="Search the web for the information",
            model=Groq(id="llama-3.3-70b-versatile"),
            tools=[DuckDuckGo()],
            instructions=["Always include sources"],
            show_tool_calls=True,
            markdown=True
        )
        
    def process_query(self, query: str) -> str:
        """
        Process a query using web search
        
        Args:
            query (str): The search query
            
        Returns:
            str: The search results formatted as a response
        """
        try:
            # Capture the output of print_response with streaming
            buffer = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buffer
            self.agent.print_response(query, stream=True)
            sys.stdout = sys_stdout
            response = buffer.getvalue().strip()
            
            # Clean up the response to remove the message box formatting
            lines = response.split('\n')
            cleaned_lines = []
            in_message_box = False
            
            for line in lines:
                if line.startswith('┏') or line.startswith('┃') or line.startswith('┗'):
                    in_message_box = True
                    continue
                if not in_message_box and line.strip():
                    cleaned_lines.append(line)
                    
            response = '\n'.join(cleaned_lines).strip()
            return response
            
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}")
            return f"Error performing web search: {str(e)}"
            
    def _clean_response(self, response):
        """Clean up the web search response"""
        if not response:
            return "I apologize, but I couldn't find a relevant answer to your question."
            
        # Convert to string if not already
        response = str(response)
        
        # Remove any instruction lines and tool execution details
        lines = response.split('\n')
        cleaned_lines = []
        skip_line = False
        
        for line in lines:
            # Skip instruction lines and tool execution details
            if any(pattern in line for pattern in [
                'Running:', ' - ', 'Instructions:', 'Role:', 
                'Enter your question', 'Your role is', 
                '## Instructions', 'Search the web',
                'content_type=', 'event=', 'messages='
            ]):
                skip_line = True
                continue
                
            if skip_line and line.strip() == '':
                skip_line = False
                continue
                
            if not skip_line:
                cleaned_lines.append(line)
                
        response = '\n'.join(cleaned_lines)
        
        # Remove any empty lines at the start and end
        response = response.strip()
        
        # If the response is empty after cleaning, return a default message
        if not response:
            return "I apologize, but I couldn't find a relevant answer to your question."
            
        return response 