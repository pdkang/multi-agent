from agents.orchestrator import OrchestratorAgent
from utils.logger import setup_logger
import os
from pathlib import Path

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = ['data/documents', 'data/memory']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    # Setup logging
    logger = setup_logger()
    
    # Create necessary directories
    setup_directories()
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent()
    
    print("\nWelcome to the Multi-Agent Document Chat System!")
    print("=" * 50)
    
    # Get PDF file path
    while True:
        pdf_path = input("\nEnter the path to your PDF file (or 'quit' to exit): ").strip()
        
        if pdf_path.lower() == 'quit':
            print("Exiting program...")
            break
            
        if not os.path.exists(pdf_path):
            print("File not found. Please enter a valid path.")
            continue
            
        if not pdf_path.lower().endswith('.pdf'):
            print("Please provide a PDF file.")
            continue
            
        try:
            # Process the PDF file
            print(f"\nProcessing {pdf_path}...")
            orchestrator.load_document(pdf_path)
            print("Document processed successfully!")
            
            # Start chat loop
            while True:
                query = input("\nEnter your question (or 'new' for new document, 'quit' to exit): ").strip()
                
                if query.lower() == 'quit':
                    print("Exiting program...")
                    return
                    
                if query.lower() == 'new':
                    break
                    
                if not query:
                    print("Please enter a valid question")
                    continue
                    
                try:
                    # Process query through orchestrator
                    response = orchestrator.process_query(query)
                    print(f"\nResponse: {response}")
                    
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    print("An error occurred. Please try again.")
                    
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            print("An error occurred while processing the document. Please try again.")

if __name__ == "__main__":
    main() 