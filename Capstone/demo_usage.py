#!/usr/bin/env python3
"""
Demo script showing how to use the enhanced Multi-Agent Document Chat System
with both upload and path-based loading functionality.
"""

import sys
from pathlib import Path

# Add the project's root directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from agents.file_chat_agent import FileChatAgent

def demo_upload_and_path_loading():
    """Demonstrate both upload and path-based loading functionality"""
    
    print("🤖 Multi-Agent Document Chat System - Demo")
    print("=" * 50)
    
    try:
        # Initialize the agent
        print("1. Initializing agent...")
        agent = FileChatAgent()
        print("✅ Agent initialized successfully!")
        
        # Demo 1: Load existing memory file by path
        print("\n2. Loading existing memory file by path...")
        memory_path = "data/memory/ai-use-case_memory.mp4"
        
        if Path(memory_path).exists():
            agent.load_document(memory_path)
            doc_info = agent.get_document_info()
            print(f"✅ Memory file loaded: {doc_info['name']}")
            
            # Test a query
            print("\n3. Testing query on loaded memory file...")
            query = "What is this document about?"
            response = agent.process_query(query)
            print(f"Q: {query}")
            print(f"A: {response[:200]}...")
        else:
            print(f"❌ Memory file not found: {memory_path}")
        
        # Demo 2: Load PDF file (if available)
        print("\n4. Loading PDF file...")
        pdf_path = "data/ai-use-case.PDF"
        
        if Path(pdf_path).exists():
            agent.load_document(pdf_path)
            doc_info = agent.get_document_info()
            print(f"✅ PDF loaded and processed: {doc_info['name']}")
            
            # Test a query
            print("\n5. Testing query on processed PDF...")
            query = "What are the main topics discussed?"
            response = agent.process_query(query)
            print(f"Q: {query}")
            print(f"A: {response[:200]}...")
        else:
            print(f"❌ PDF file not found: {pdf_path}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo use the web interface:")
        print("1. Run: python run_streamlit.py")
        print("2. Open: http://localhost:8501")
        print("3. Use the 'Upload File' tab for new documents")
        print("4. Use the 'Load Memory' tab for existing memory files")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        print("Make sure your .env file is set up with API keys.")

if __name__ == "__main__":
    demo_upload_and_path_loading() 