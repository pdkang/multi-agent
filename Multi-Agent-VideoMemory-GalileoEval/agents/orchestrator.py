from .file_chat_agent import FileChatAgent
from .web_search_agent import WebSearchAgent
from evaluation.galileo_evaluator import GalileoEvaluator
import logging
import time

class OrchestratorAgent:
    def __init__(self):
        self.file_chat_agent = FileChatAgent()
        self.web_search_agent = WebSearchAgent()
        self.galileo_evaluator = GalileoEvaluator()
        self.logger = logging.getLogger('multi_agent')
        
        # Start Galileo context
        self.galileo_evaluator.start_context()
        
    def load_document(self, pdf_path):
        """Load document into file chat agent"""
        self.file_chat_agent.load_document(pdf_path)
    
    def flush_galileo_logs(self):
        """Manually flush Galileo logs"""
        try:
            if self.galileo_evaluator:
                return self.galileo_evaluator.flush_context()
            return False
        except Exception as e:
            self.logger.error(f"Error flushing Galileo logs: {str(e)}")
            return False
    
    def get_document_info(self):
        """Get information about the currently loaded document"""
        try:
            if hasattr(self.file_chat_agent, 'get_document_info'):
                return self.file_chat_agent.get_document_info()
            else:
                # Fallback if file_chat_agent doesn't have this method
                return {
                    'name': 'Unknown Document',
                    'size': 'Unknown',
                    'path': 'Unknown'
                }
        except Exception as e:
            self.logger.error(f"Error getting document info: {str(e)}")
            return {
                'name': 'Error loading document info',
                'size': 'Unknown',
                'path': 'Unknown'
            }
        
    def process_query(self, query):
        """Process a query using the appropriate agent with Galileo tracking"""
        start_time = time.time()
        
        try:
            # Step 1: Try file chat first
            file_start_time = time.time()
            file_response = self.file_chat_agent.process_query(query)
            file_processing_time = time.time() - file_start_time
            
            # Log file chat span using decorated method
            file_response = self.galileo_evaluator.log_agent_span(
                agent_name="file_chat",
                input_data=query,
                output_data=file_response,
                metrics={
                    "processing_time": file_processing_time,
                    "response_length": len(str(file_response)),
                    "agent_type": "document_retrieval"
                }
            )
            
            # Step 2: Check if the response indicates no answer was found or web search was used
            if self._is_no_answer(file_response):
                # Check if file_chat_agent already used web search
                if "Based on a web search:" in file_response:
                    self.logger.info("File chat agent already used web search fallback")
                    
                    # Log fallback decision using decorated method
                    fallback_info = self.galileo_evaluator.log_fallback_decision(
                        from_agent="file_chat",
                        to_agent="web_search",
                        reason="No answer found in document (fallback handled by file_chat_agent)"
                    )
                    
                    final_response = self._format_response(file_response)
                    agent_used = "web_search"
                    
                else:
                    self.logger.info("No answer found in document, falling back to web search")
                    
                    # Log fallback decision using decorated method
                    fallback_info = self.galileo_evaluator.log_fallback_decision(
                        from_agent="file_chat",
                        to_agent="web_search",
                        reason="No answer found in document"
                    )
                    
                    # Step 3: Fall back to web search
                    web_start_time = time.time()
                    web_response = self.web_search_agent.process_query(query)
                    web_processing_time = time.time() - web_start_time
                    
                    # Log web search span using decorated method
                    web_response = self.galileo_evaluator.log_agent_span(
                        agent_name="web_search",
                        input_data=query,
                        output_data=web_response,
                        metrics={
                            "processing_time": web_processing_time,
                            "response_length": len(str(web_response)),
                            "agent_type": "web_search",
                            "fallback_used": True
                        }
                    )
                    
                    final_response = self._format_response(web_response)
                    agent_used = "web_search"
                
            else:
                final_response = self._format_response(file_response)
                agent_used = "file_chat"
            
            # Calculate overall metrics
            total_processing_time = time.time() - start_time
            overall_metrics = {
                "total_processing_time": total_processing_time,
                "final_agent_used": agent_used,
                "fallback_triggered": agent_used == "web_search",
                "final_response_length": len(str(final_response))
            }
            
            # Log the complete query using decorated method
            final_response = self.galileo_evaluator.log_query(
                query=query,
                response=final_response,
                metrics=overall_metrics
            )
            
            # Strategic flush after complete query processing
            self.galileo_evaluator.flush_after_query()
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            
            # Log error span using decorated method
            error_response = self.galileo_evaluator.log_agent_span(
                agent_name="error_handler",
                input_data=query,
                output_data=f"Error: {str(e)}",
                metrics={
                    "error_type": type(e).__name__,
                    "processing_time": time.time() - start_time
                }
            )
            
            # If file chat fails, try web search
            try:
                web_start_time = time.time()
                web_response = self.web_search_agent.process_query(query)
                web_processing_time = time.time() - web_start_time
                
                # Log web search span (fallback due to error) using decorated method
                web_response = self.galileo_evaluator.log_agent_span(
                    agent_name="web_search_error_fallback",
                    input_data=query,
                    output_data=web_response,
                    metrics={
                        "processing_time": web_processing_time,
                        "response_length": len(str(web_response)),
                        "agent_type": "web_search",
                        "fallback_reason": "file_chat_error"
                    }
                )
                
                final_response = self._format_response(web_response)
                
                # Log the complete query with error recovery using decorated method
                overall_metrics = {
                    "total_processing_time": time.time() - start_time,
                    "final_agent_used": "web_search_error_fallback",
                    "fallback_triggered": True,
                    "error_recovered": True,
                    "final_response_length": len(str(final_response))
                }
                
                final_response = self.galileo_evaluator.log_query(
                    query=query,
                    response=final_response,
                    metrics=overall_metrics
                )
                
                # Strategic flush after complete query processing (error recovery)
                self.galileo_evaluator.flush_after_query()
                
                return final_response
                
            except Exception as web_error:
                self.logger.error(f"Web search also failed: {str(web_error)}")
                
                # Log complete failure using decorated method
                error_response = "I apologize, but I'm unable to process your query at the moment. Please try again later."
                
                overall_metrics = {
                    "total_processing_time": time.time() - start_time,
                    "final_agent_used": "none",
                    "fallback_triggered": False,
                    "error_recovered": False,
                    "complete_failure": True
                }
                
                error_response = self.galileo_evaluator.log_query(
                    query=query,
                    response=error_response,
                    metrics=overall_metrics
                )
                
                # Strategic flush after complete query processing (complete failure)
                self.galileo_evaluator.flush_after_query()
                
                return error_response
                
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
            "Based on the context provided, I don't have specific details about",
            "Based on the provided contexts, there are no specific examples",
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
        
        # Check if this is a web search response (indicating fallback was used)
        web_search_indicators = [
            "Based on a web search:",
            "Based on web search:",
            "According to web search:",
            "Web search results:",
            "From web search:"
        ]
        
        # Convert response to lowercase for case-insensitive matching
        response_lower = response.lower()
        
        # Check for any of the no-answer phrases
        is_no_answer = any(phrase.lower() in response_lower for phrase in no_answer_phrases)
        
        # Check if this is a web search response (indicating fallback was used)
        is_web_search_response = any(indicator.lower() in response_lower for indicator in web_search_indicators)
        
        # Log the decision for debugging
        if is_no_answer:
            self.logger.info(f"Detected no-answer response: {response}")
        elif is_web_search_response:
            self.logger.info(f"Detected web search response (fallback used): {response}")
        else:
            self.logger.info(f"Detected valid answer response: {response}")
            
        # Return True if either no answer OR web search response (indicating fallback was needed)
        return is_no_answer or is_web_search_response

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