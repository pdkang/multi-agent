from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo
import logging
import io
import sys
import re
import time
import random

class WebSearchAgent:
    def __init__(self):
        """Initialize the web search agent with DuckDuckGo search tool"""
        self.logger = logging.getLogger('multi_agent')
        self.agent = Agent(
            name="Web Search Agent",
            role="Search the web for the information",
            model=Groq(id="llama3-70b-8192"),
            tools=[DuckDuckGo()],
            instructions=["Always include sources"],
            show_tool_calls=True,
            markdown=True
        )
        self.last_search_time = 0
        self.min_delay = 2  # Minimum delay between searches in seconds
        
    def process_query(self, query: str) -> str:
        """
        Process a query using web search with rate limiting protection
        
        Args:
            query (str): The search query
            
        Returns:
            str: The search results formatted as a response
        """
        try:
            # Add delay to prevent rate limiting
            current_time = time.time()
            time_since_last_search = current_time - self.last_search_time
            if time_since_last_search < self.min_delay:
                delay_needed = self.min_delay - time_since_last_search
                self.logger.info(f"Adding delay of {delay_needed:.2f}s to prevent rate limiting")
                time.sleep(delay_needed)
            
            # Capture the output of print_response with streaming
            buffer = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buffer
            self.agent.print_response(query, stream=True)
            sys.stdout = sys_stdout
            response = buffer.getvalue().strip()
            
            # Update last search time
            self.last_search_time = time.time()
            
            # Debug: Log the full raw response
            self.logger.info(f"Raw web search response length: {len(response)}")
            self.logger.info(f"Raw web search response: {response}")
            
            # Check for rate limit error in response
            if "Ratelimit" in response or "202" in response:
                self.logger.warning("Rate limit detected, returning fallback response")
                return self._get_fallback_response(query)
            
            # Clean up the response to remove the message box formatting and escape codes
            cleaned_response = self._clean_response(response)
            
            # Debug: Log the cleaned response
            self.logger.info(f"Cleaned web search response length: {len(cleaned_response)}")
            self.logger.info(f"Cleaned web search response: {cleaned_response}")
            
            # If cleaning removed everything, try a simpler approach
            if not cleaned_response or cleaned_response == "I apologize, but I couldn't find a relevant answer to your question.":
                self.logger.info("Cleaning removed all content, trying simple extraction...")
                simple_response = self._simple_clean_response(response)
                if simple_response:
                    return simple_response
            
            return cleaned_response
            
        except Exception as e:
            self.logger.error(f"Error in web search: {str(e)}")
            # Check if it's a rate limit error
            if "Ratelimit" in str(e) or "202" in str(e):
                return self._get_fallback_response(query)
            return f"Error performing web search: {str(e)}"
            
    def _clean_response(self, response):
        """Clean up the web search response"""
        if not response:
            return "I apologize, but I couldn't find a relevant answer to your question."
            
        # Convert to string if not already
        response = str(response)
        
        # Remove ANSI escape codes (colors, formatting)
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        response = ansi_escape.sub('', response)
        
        # Remove the message box formatting and extract content
        lines = response.split('\n')
        cleaned_lines = []
        in_message_box = False
        in_response_box = False
        found_content = False
        
        for line in lines:
            # Skip message box border lines
            if line.startswith('┏') or line.startswith('┗'):
                continue
                
            # Detect message box start
            if line.startswith('┃') and 'Message' in line:
                in_message_box = True
                continue
                
            # Detect response box start
            if line.startswith('┃') and 'Response' in line:
                in_message_box = False
                in_response_box = True
                continue
                
            # Skip empty lines in message box
            if in_message_box and not line.strip():
                continue
                
            # If we're in message box and find content, skip it
            if in_message_box and line.strip():
                in_message_box = False
                continue
                
            # If we're in response box, collect content
            if in_response_box:
                # Skip border lines
                if line.startswith('┃'):
                    continue
                    
                # Skip metadata lines
                if any(pattern in line for pattern in [
                    'No tools were used in this response',
                    'content_type=',
                    'event=',
                    'messages='
                ]):
                    continue
                    
                # Add the line if it has content
                if line.strip():
                    cleaned_lines.append(line.strip())
                    found_content = True
        
        # If we didn't find content in response box, try to extract from the whole response
        if not found_content:
            # Look for content after removing formatting
            lines = response.split('\n')
            for line in lines:
                # Skip formatting and metadata
                if any(pattern in line for pattern in [
                    '┏', '┃', '┗', 'Message', 'Response', 'Running:', ' - ',
                    'Instructions:', 'Role:', 'Enter your question', 'Your role is',
                    '## Instructions', 'Search the web', 'content_type=', 'event=',
                    'messages=', 'No tools were used in this response'
                ]):
                    continue
                    
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Add content lines
                cleaned_lines.append(line.strip())
        
        response = '\n'.join(cleaned_lines)
        
        # Remove any empty lines at the start and end
        response = response.strip()
        
        # If the response is empty after cleaning, return a default message
        if not response:
            return "I apologize, but I couldn't find a relevant answer to your question."
            
        return response

    def _simple_clean_response(self, response):
        """Simple fallback cleaning method"""
        if not response:
            return ""
            
        # Remove ANSI escape codes
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        response = ansi_escape.sub('', response)
        
        # Remove URL formatting codes that appear in the output
        response = re.sub(r'\]8;id=\d+;[^]]*\[', '', response)
        response = re.sub(r'\]8;;', '', response)
        
        # Split into lines and extract content from response box
        lines = response.split('\n')
        content_lines = []
        in_response_box = False
        
        for line in lines:
            # Detect response box start
            if 'Response' in line and '┃' in line:
                in_response_box = True
                continue
                
            # Detect response box end
            if in_response_box and line.startswith('┗'):
                break
                
            # If we're in response box, collect content
            if in_response_box:
                # Skip border lines that are just formatting
                if line.startswith('┃') and not line.strip().replace('┃', '').strip():
                    continue
                    
                # Skip metadata lines
                if any(pattern in line for pattern in [
                    'No tools were used in this response',
                    'content_type=',
                    'event=',
                    'messages='
                ]):
                    continue
                    
                # Extract content from border lines
                if line.startswith('┃'):
                    # Remove the border characters and get the content
                    content = line.replace('┃', '').strip()
                    if content:
                        content_lines.append(content)
                else:
                    # Regular content line
                    if line.strip():
                        content_lines.append(line.strip())
        
        result = '\n'.join(content_lines).strip()
        
        # If we still don't have content, try a more aggressive approach
        if not result:
            # Look for any content that's not formatting
            for line in lines:
                # Skip obvious formatting
                if any(pattern in line for pattern in [
                    '┏', '┗', 'Message', 'Running:', ' - ',
                    'Instructions:', 'Role:', 'Enter your question', 'Your role is',
                    '## Instructions', 'Search the web', 'content_type=', 'event=',
                    'messages=', 'No tools were used in this response'
                ]):
                    continue
                    
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # Add content lines
                content_lines.append(line.strip())
            
            result = '\n'.join(content_lines).strip()
        
        # Final cleanup: remove any remaining border characters and extra whitespace
        if result:
            # Remove any remaining border characters
            result = re.sub(r'┃\s*', '', result)
            # Clean up multiple spaces
            result = re.sub(r'\s+', ' ', result)
            # Clean up multiple newlines
            result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
            
            # Clean up the sources section to make it more readable
            if 'Sources:' in result:
                # Split into content and sources
                parts = result.split('Sources:')
                content = parts[0].strip()
                sources = parts[1].strip() if len(parts) > 1 else ""
                
                # Clean up sources formatting
                if sources:
                    # Remove URL formatting codes and clean up source links
                    sources = re.sub(r'8;id=\d+;', '', sources)
                    sources = re.sub(r'8;;', '', sources)
                    sources = re.sub(r'https?://[^\s]+', '', sources)  # Remove raw URLs
                    sources = re.sub(r'\s+', ' ', sources)  # Clean up whitespace
                    
                    # Format sources nicely
                    source_list = []
                    for source in sources.split('•'):
                        if source.strip():
                            source_list.append(f"• {source.strip()}")
                    
                    sources = '\n'.join(source_list)
                    
                    # Reconstruct the response with better formatting
                    result = f"{content}\n\n**Sources:**\n{sources}"
                else:
                    result = content
            else:
                result = result.strip()
        
        return result

    def _get_fallback_response(self, query):
        """Provide a fallback response when rate limited"""
        return ("I'm currently unable to perform a web search due to rate limiting. "
                "Please try again in a few minutes, or I can help you with information from your loaded documents.")
