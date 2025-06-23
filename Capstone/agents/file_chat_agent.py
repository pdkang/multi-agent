import os
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

# --- Local Imports ---
# Import the existing WebSearchAgent
from agents.web_search_agent import WebSearchAgent
from memvid import MemvidEncoder, MemvidChat

class FileChatAgent:
    def __init__(self):
        """Initializes the agent, its directories, and the web search agent."""
        self.encoder = None
        self.chat = None
        self.document_path = None
        self.memory_dir = Path('data/memory')
        self.documents_dir = Path('data/documents')
        self.logger = logging.getLogger('multi_agent')
        
        # Create directories if they don't exist
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)

        # Load environment variables from .env file
        load_dotenv()
        
        if not os.getenv('GOOGLE_API_KEY'):
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        if not os.getenv('GROQ_API_KEY'):
             raise ValueError("GROQ_API_KEY not found in .env file for the WebSearchAgent")
        self.logger.info("API keys loaded successfully.")
        
        try:
            self.web_searcher = WebSearchAgent()
            self.logger.info("WebSearchAgent initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSearchAgent: {e}")
            raise
        
    def load_document(self, file_path):
        """Load and process a document (PDF or memory file)"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_suffix = file_path.suffix.lower()
        if file_suffix == '.pdf':
            self._process_pdf(file_path)
        elif file_suffix in ['.mp4', '.mkv', '.avi']:
            self._load_memory_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}. Supported: .pdf, .mp4, .mkv, .avi")
            
    def _process_pdf(self, pdf_path):
        """Process a PDF file and create memory video"""
        doc_name = pdf_path.name
        doc_path = self.documents_dir / doc_name
        shutil.copy2(pdf_path, doc_path)
        self.document_path = doc_path
        
        self.encoder = MemvidEncoder()
        print(f"Processing PDF: {doc_name}")
        self.encoder.add_pdf(str(doc_path))
        
        memory_name = f"{doc_path.stem}_memory"
        video_path = self.memory_dir / f"{memory_name}.mp4"
        index_path = self.memory_dir / f"{memory_name}_index.json"
        
        print("Creating memory video...")
        self.encoder.build_video(str(video_path), str(index_path))
        self._initialize_chat(video_path, index_path)
        
    def _load_memory_file(self, video_path):
        """Load an existing memory video file"""
        index_path = video_path.with_name(f"{video_path.stem}_index.json")
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found for video. Looked for: {index_path}")
        self.document_path = video_path
        self._initialize_chat(video_path, index_path)
        
    def _initialize_chat(self, video_path, index_path):
        """Initialize the chat with memory video and index"""
        print(f"Initializing chat with video: {video_path} and index: {index_path}")
        try:
            self.chat = MemvidChat(
                video_file=str(video_path),
                index_file=str(index_path),
                llm_provider='google',
                llm_model='gemini-2.0-flash-exp'
            )
            print("Document loaded and chat initialized successfully!")
        except Exception as e:
            self.logger.error(f"Error initializing chat: {e}")
            raise ValueError(f"Failed to initialize chat: {e}")
        
    def process_query(self, query):
        """
        Process a query, first against the document, then with the WebSearchAgent if needed.
        """
        if not self.chat:
            raise ValueError("No document loaded. Please load a document first.")
        
        print("\nStep 1: Searching the loaded document...")
        doc_response = self.chat.chat(query, stream=False)

        # --- CORRECTED LOGIC ---
        # More robust list of phrases indicating the answer was not found.
        not_found_phrases = [
            "i'm sorry", "i am sorry", "i apologize",
            "does not contain information", "does not have any information",
            "no information found", "not mentioned in the context",
            "the context does not provide", "the provided context does not",
            "i don't know", "i cannot answer"
        ]

        doc_response_lower = str(doc_response).lower()
        
        # We now check if ANY of the 'not found' phrases are in the response.
        # This is more reliable than checking if ALL of them are absent.
        is_answer_missing = any(phrase in doc_response_lower for phrase in not_found_phrases)

        if is_answer_missing:
            print(f"-> Answer not in document. Original response: '{doc_response}'")
            print("\nStep 2: Delegating to Web Search Agent...")
            try:
                # Call the existing WebSearchAgent's process_query method
                web_response = self.web_searcher.process_query(query) 
                
                print("-> Web search complete.")
                return f"\nBased on a web search:\n{web_response}"

            except Exception as e:
                self.logger.error(f"Error during web search delegation: {e}", exc_info=True)
                return "I could not find an answer in the document, and the web search failed."
        else:
            # If no "not found" phrases were detected, we assume the answer is good.
            print("-> Answer found in the document.")
            return f"Based on the document content: {doc_response}"
        
    def get_document_info(self):
        """Get information about the loaded document"""
        if not self.document_path:
            return "No document loaded"
        return {
            "name": self.document_path.name,
            "size": f"{self.document_path.stat().st_size / 1024:.1f} KB",
            "path": str(self.document_path)
        }
