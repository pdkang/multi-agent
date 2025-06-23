from phi.agent import Agent
from phi.model.groq import Groq
from memvid import MemvidEncoder, MemvidChat
import os
from pathlib import Path
import shutil
import logging
from dotenv import load_dotenv

class FileChatAgent:
    def __init__(self):
        self.encoder = None
        self.chat = None
        self.document_path = None
        self.memory_dir = Path('data/memory')
        self.documents_dir = Path('data/documents')
        self.logger = logging.getLogger('multi_agent')
        
        # Load environment variables
        load_dotenv()
        
        # Check if API key is loaded
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        self.logger.info("GOOGLE_API_KEY loaded successfully")
        
    def load_document(self, file_path):
        """Load and process a document (PDF or memory file)"""
        # Convert to Path object
        file_path = Path(file_path)
        
        # Validate file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Handle different file types
        if file_path.suffix.lower() == '.pdf':
            self._process_pdf(file_path)
        elif file_path.suffix.lower() == '.mp4':
            self._load_memory_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}. Supported types: .pdf, .mp4")
            
    def _process_pdf(self, pdf_path):
        """Process a PDF file and create memory video"""
        # Validate file extension
        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF: {pdf_path}")
            
        # Create a copy in documents directory
        doc_name = pdf_path.name
        doc_path = self.documents_dir / doc_name
        shutil.copy2(pdf_path, doc_path)
        
        self.document_path = doc_path
        
        # Initialize encoder
        self.encoder = MemvidEncoder()
        
        # Process PDF
        print(f"Processing PDF: {doc_name}")
        self.encoder.add_pdf(str(doc_path))
        
        # Create memory video
        memory_name = f"{doc_path.stem}_memory"
        video_path = self.memory_dir / f"{memory_name}.mp4"
        index_path = self.memory_dir / f"{memory_name}_index.json"
        
        # Build memory video
        print("Creating memory video...")
        self.encoder.build_video(str(video_path), str(index_path))
        
        # Initialize chat
        self._initialize_chat(video_path, index_path)
        
    def _load_memory_file(self, video_path):
        """Load an existing memory video file"""
        # Validate file extension
        if video_path.suffix.lower() != '.mp4':
            raise ValueError(f"File must be an MP4: {video_path}")
            
        # Check for corresponding index file
        index_path = video_path.with_suffix('_index.json')
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
            
        # Set document path to the video file
        self.document_path = video_path
            
        # Initialize chat
        self._initialize_chat(video_path, index_path)
        
    def _initialize_chat(self, video_path, index_path):
        """Initialize the chat with memory video and index"""
        print("Initializing chat...")
        try:
            self.chat = MemvidChat(
                video_file=str(video_path),
                index_file=str(index_path),
                llm_provider='google',
                llm_model='gemini-2.0-flash-exp'
            )
            print("Document loaded successfully!")
        except Exception as e:
            self.logger.error(f"Error initializing chat: {str(e)}")
            raise ValueError(f"Failed to initialize chat: {str(e)}")
        
    def process_query(self, query):
        """Process a query against the loaded document"""
        if not self.chat:
            raise ValueError("No document loaded. Please load a document first.")
            
        try:
            # Get response from chat
            response = self.chat.chat(query, stream=False)
            
            # Check if LLM is available
            if "LLM not available" in response:
                self.logger.error("LLM service not available. Please check your GOOGLE_API_KEY.")
                raise ValueError("LLM service not available. Please check your GOOGLE_API_KEY in .env file.")
                
            # Add context to response
            if response and not response.startswith("I don't"):
                response = f"Based on the document content: {response}"
                
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            raise
        
    def get_document_info(self):
        """Get information about the loaded document"""
        if not self.document_path:
            return "No document loaded"
            
        return {
            "name": self.document_path.name,
            "size": f"{self.document_path.stat().st_size / 1024:.1f} KB",
            "path": str(self.document_path)
        } 