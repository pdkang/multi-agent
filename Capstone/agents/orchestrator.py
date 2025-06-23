from .file_chat_agent import FileChatAgent
from .web_search_agent import WebSearchAgent
import logging

class OrchestratorAgent:
    def __init__(self):
        self.file_chat_agent = FileChatAgent()
        self.web_search_agent = WebSearchAgent()
        self.logger = logging.getLogger('multi_agent')
        
    def load_document(self, pdf_path):
        """Load document into file chat agent"""
        self.file_chat_agent.load_document(pdf_path)
        
    def process_query(self, query):
        """Process a query using the appropriate agent"""
        try:
            # Try file chat first
            file_response = self.file_chat_agent.process_query(query)
            
            # Check if the response indicates no answer was found
            if self._is_no_answer(file_response):
                self.logger.info("No answer found in document, falling back to web search")
                # Fall back to web search
                web_response = self.web_search_agent.process_query(query)
                return self._format_response(web_response)
            
            return self._format_response(file_response)
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            # If file chat fails, try web search
            try:
                web_response = self.web_search_agent.process_query(query)
                return self._format_response(web_response)
            except Exception as web_error:
                self.logger.error(f"Web search also failed: {str(web_error)}")
                return "I apologize, but I'm unable to process your query at the moment. Please try again later."
                
    def _is_no_answer(self, response):
        """Check if the response indicates no answer was found"""
        no_answer_phrases = [
            "I'm sorry, but I did not find any information",
            "I'm sorry, but the provided context does not contain information",
            "I am sorry, but the context provided does not have information",
            "I'm sorry, but the context provided does not include information",
            "the context provided does not have information",
            "the provided context does not have information",
            "the context provided does not include information",
            "the provided context does not include information",
            "I don't have enough information",
            "I cannot find any information",
            "I don't have access to that information",
            "I don't have any information about",
            "I don't have any context about",
            "I don't have any knowledge about",
            "I don't have any data about",
            "I don't have any details about",
            "I don't have any specifics about",
            "I don't have any information in the provided contexts",
            "I don't have any information in the document",
            "I don't have any information in the file",
            "I don't have any information in the PDF",
            "I don't have any information in the content",
            "I don't have any information in the text",
            "I don't have any information in the material",
            "I don't have any information in the data",
            "I don't have any information in the resources",
            "I don't have any information in the sources",
            "the provided context does not contain",
            "the context does not contain",
            "no information about",
            "no details about",
            "no data about",
            "no context about",
            "no knowledge about",
            "no specifics about",
            "no information in the provided",
            "no information in the document",
            "no information in the file",
            "no information in the PDF",
            "no information in the content",
            "no information in the text",
            "no information in the material",
            "no information in the data",
            "no information in the resources",
            "no information in the sources",
            "does not have information",
            "does not contain information",
            "does not include information",
            "does not have any information",
            "does not contain any information",
            "does not include any information",
            "does not have the information",
            "does not contain the information",
            "does not include the information",
            "I'm sorry, but the documents provided do not contain information",
            "I'm sorry, but the documents provided do not have information",
            "I'm sorry, but the documents provided do not include information",
            "the documents provided do not contain information",
            "the documents provided do not have information",
            "the documents provided do not include information",
            "the documents do not contain information",
            "the documents do not have information",
            "the documents do not include information",
            "the document does not contain information",
            "the document does not have information",
            "the document does not include information",
            "the provided documents do not contain information",
            "the provided documents do not have information",
            "the provided documents do not include information",
            "the provided document does not contain information",
            "the provided document does not have information",
            "the provided document does not include information"
        ]
        
        # Convert response to lowercase for case-insensitive matching
        response_lower = response.lower()
        
        # Check for any of the no-answer phrases
        is_no_answer = any(phrase.lower() in response_lower for phrase in no_answer_phrases)
        
        # Log the decision for debugging
        if is_no_answer:
            self.logger.info(f"Detected no-answer response: {response}")
        else:
            self.logger.info(f"Detected valid answer response: {response}")
            
        return is_no_answer

    def _format_response(self, response):
        """Format the response to be clean and readable"""
        # If response is None or empty, return a default message
        if not response:
            return "I apologize, but I couldn't find a relevant answer to your question."
            
        # If response is a string, try to clean it up
        if isinstance(response, str):
            # Remove any content_type, event, messages, metrics, etc. metadata
            if "content=" in response:
                # Extract just the content part
                content_start = response.find('content="') + 9
                content_end = response.find('"', content_start)
                if content_start > 8 and content_end > content_start:
                    response = response[content_start:content_end]
            
            # Clean up any escaped newlines and quotes
            response = response.replace('\\n', '\n').replace('\\"', '"')
            
            # Remove any leading/trailing whitespace
            response = response.strip()
            
            # If the response starts with "Response:", remove it
            if response.startswith("Response:"):
                response = response[9:].strip()
                
            # If the response starts with "Based on the document content:", remove it
            if response.startswith("Based on the document content:"):
                response = response[31:].strip()
            
            # Remove any function call details
            if "<function=" in response:
                # Skip the function call part
                function_end = response.find("</function>")
                if function_end > 0:
                    response = response[function_end + 11:].strip()
            
            # Remove any "Running:" lines and tool execution details
            lines = response.split('\n')
            cleaned_lines = []
            skip_line = False
            for line in lines:
                # Skip function call lines
                if "<function=" in line or "</function>" in line:
                    continue
                # Skip tool execution lines
                if line.startswith('Running:') or line.startswith(' - '):
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
            
            # Remove duplicate content if it exists
            if "Based on the context provided" in response:
                # Find the second occurrence
                first_occurrence = response.find("Based on the context provided")
                second_occurrence = response.find("Based on the context provided", first_occurrence + 1)
                if second_occurrence > 0:
                    response = response[:second_occurrence].strip()
            
            # Remove any remaining "Based on the document content:" prefix
            if response.startswith("Based on the document content:"):
                response = response[31:].strip()
            
            # Remove any remaining "Response:" prefix
            if response.startswith("Response:"):
                response = response[9:].strip()
            
            # Remove any remaining "Based on the context provided" prefix
            if response.startswith("Based on the context provided"):
                response = response[31:].strip()
            
            return response
            
        return str(response) 