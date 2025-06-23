import logging
from pathlib import Path
import sys

# --- Path Correction ---
# Add the project's root directory to the Python path.
# This ensures that modules in subdirectories (like 'agents') can be found.
# Assumes this script is run from the project root.
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# --- Corrected Import ---
# Import FileChatAgent from its location within the 'agents' directory.
from agents.file_chat_agent import FileChatAgent


# --- Configuration ---
# Set up basic logging to see informational messages and errors.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_welcome_message():
    """Prints a welcome message and instructions to the user."""
    print("==================================================")
    print("Welcome to the Multi-Agent Document Chat System!")
    print("==================================================")
    print("You can load a document by providing its full path.")
    print("Supported formats: .pdf, .mp4, .mkv, .avi")
    print("\nOnce a document is loaded, you can ask questions about it.")
    print("Type 'new' to load a new document, or 'quit' to exit the system.")
    print("--------------------------------------------------\n")

def main():
    """Main function to run the chat application."""
    print_welcome_message()
    
    try:
        # Initialize the agent. This will also check for the GOOGLE_API_KEY.
        agent = FileChatAgent()
    except ValueError as e:
        logging.error(f"Failed to initialize agent: {e}")
        print(f"\nError: {e}")
        print("Please ensure your .env file is correctly set up next to this script.")
        return

    while True:
        # --- Document Loading Loop ---
        try:
            # Get the path to the document from the user.
            doc_path_str = input("Enter the path to your document (or 'quit' to exit): ").strip()

            if doc_path_str.lower() == 'quit':
                print("Goodbye!")
                break
            
            # Use the agent to load the document. The agent itself handles file validation.
            agent.load_document(doc_path_str)
            logging.info(f"Successfully loaded document: {agent.get_document_info().get('name')}")
            print(f"\n✅ Document loaded: {Path(doc_path_str).name}")

            # --- Chatting Loop ---
            while True:
                try:
                    query = input("\nAsk a question (or 'new'/'quit'): ").strip()

                    if query.lower() == 'quit':
                        print("Goodbye!")
                        return # Exit the entire application
                    
                    if query.lower() == 'new':
                        print("\nLoading a new document...")
                        break # Exit the chatting loop to go back to the document loading loop
                    
                    if not query:
                        continue
                        
                    # Process the query using the agent
                    print("\nThinking...")
                    response = agent.process_query(query)
                    print(f"\nAssistant: {response}")

                except Exception as e:
                    logging.error(f"An error occurred during chat: {e}")
                    print(f"\nAn error occurred: {e}. Let's try again.")

        except (FileNotFoundError, ValueError) as e:
            # Catch errors from agent.load_document (e.g., file not found, unsupported type)
            logging.error(f"Error loading document: {e}")
            print(f"\nError: {e}\nPlease check the file path and try again.")
        except Exception as e:
            # Catch other potential errors during document loading.
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"\nAn unexpected error occurred. Please try again.")


if __name__ == "__main__":
    main()
