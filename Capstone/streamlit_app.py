import streamlit as st
import os
import logging
from pathlib import Path
import sys
from dotenv import load_dotenv

# Add the project's root directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import the FileChatAgent
from agents.file_chat_agent import FileChatAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Document Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .file-uploader {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
    }
    .status-success {
        color: #4caf50;
        font-weight: bold;
    }
    .status-error {
        color: #f44336;
        font-weight: bold;
    }
    .sidebar-content {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'agent' not in st.session_state:
        st.session_state.agent = None
    if 'document_loaded' not in st.session_state:
        st.session_state.document_loaded = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'document_info' not in st.session_state:
        st.session_state.document_info = None

def initialize_agent():
    """Initialize the FileChatAgent"""
    try:
        if st.session_state.agent is None:
            with st.spinner("Initializing agent..."):
                st.session_state.agent = FileChatAgent()
            st.success("Agent initialized successfully!")
        return True
    except ValueError as e:
        st.error(f"Failed to initialize agent: {e}")
        st.info("Please ensure your .env file is correctly set up with GOOGLE_API_KEY and GROQ_API_KEY.")
        return False

def load_document(uploaded_file):
    """Load a document from uploaded file"""
    try:
        if uploaded_file is None:
            return False
        
        # Save uploaded file temporarily
        temp_path = Path("temp_upload") / uploaded_file.name
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Load document using agent
        with st.spinner(f"Processing {uploaded_file.name}..."):
            st.session_state.agent.load_document(str(temp_path))
            st.session_state.document_loaded = True
            st.session_state.document_info = st.session_state.agent.get_document_info()
            st.session_state.chat_history = []
        
        # Clean up temp file
        temp_path.unlink()
        
        st.success(f"✅ Document loaded successfully: {uploaded_file.name}")
        return True
        
    except Exception as e:
        st.error(f"Error loading document: {e}")
        return False

def load_memory_by_path(memory_path):
    """Load an existing memory file by providing its path"""
    try:
        if not memory_path or not memory_path.strip():
            return False
        
        memory_path = Path(memory_path.strip())
        
        # Validate the path exists
        if not memory_path.exists():
            st.error(f"❌ File not found: {memory_path}")
            return False
        
        # Check if it's a supported video format
        if memory_path.suffix.lower() not in ['.mp4', '.mkv', '.avi']:
            st.error(f"❌ Unsupported file format: {memory_path.suffix}. Supported: .mp4, .mkv, .avi")
            return False
        
        # Check if corresponding index file exists
        index_path = memory_path.with_name(f"{memory_path.stem}_index.json")
        if not index_path.exists():
            st.error(f"❌ Index file not found: {index_path}")
            st.info("Memory files must have a corresponding index file with '_index.json' suffix.")
            return False
        
        # Load memory file using agent
        with st.spinner(f"Loading memory file: {memory_path.name}..."):
            st.session_state.agent.load_document(str(memory_path))
            st.session_state.document_loaded = True
            st.session_state.document_info = st.session_state.agent.get_document_info()
            st.session_state.chat_history = []
        
        st.success(f"✅ Memory file loaded successfully: {memory_path.name}")
        return True
        
    except Exception as e:
        st.error(f"Error loading memory file: {e}")
        return False

def list_memory_files():
    """List existing memory files in the data/memory directory"""
    memory_dir = Path("data/memory")
    if not memory_dir.exists():
        return []
    
    memory_files = []
    # Support multiple video formats
    for file_path in memory_dir.glob("*"):
        if file_path.suffix.lower() in ['.mp4', '.mkv', '.avi']:
            index_path = file_path.with_name(f"{file_path.stem}_index.json")
            if index_path.exists():
                # Get file creation/modification time
                stat = file_path.stat()
                memory_files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": f"{stat.st_size / (1024*1024):.1f} MB",
                    "modified": stat.st_mtime,
                    "index_size": f"{index_path.stat().st_size / 1024:.1f} KB"
                })
    
    # Sort by modification time (newest first)
    memory_files.sort(key=lambda x: x["modified"], reverse=True)
    return memory_files

def process_query(query):
    """Process a user query"""
    try:
        with st.spinner("Processing your question..."):
            response = st.session_state.agent.process_query(query)
        
        # Add to chat history
        st.session_state.chat_history.append({
            "role": "user",
            "content": query
        })
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": response
        })
        
        return response
    except Exception as e:
        error_msg = f"Error processing query: {e}"
        st.error(error_msg)
        return error_msg

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🤖 Multi-Agent Document Chat</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Upload documents and chat with AI agents about their content</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 📁 Document Management")
        
        # Check API keys
        if not os.getenv('GOOGLE_API_KEY') or not os.getenv('GROQ_API_KEY'):
            st.error("⚠️ Missing API Keys")
            st.info("Please set up your .env file with GOOGLE_API_KEY and GROQ_API_KEY")
            return
        
        # Initialize agent
        if not initialize_agent():
            return
        
        # Create tabs for different loading methods
        tab1, tab2 = st.tabs(["📤 Upload File", "📂 Load Memory"])
        
        with tab1:
            st.markdown("### Upload New Document")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'mp4', 'mkv', 'avi'],
                help="Supported formats: PDF, MP4, MKV, AVI"
            )
            
            if uploaded_file and st.button("Load Document", key="upload_btn"):
                load_document(uploaded_file)
        
        with tab2:
            st.markdown("### Load Existing Memory File")
            
            # Add refresh button and file count
            col_refresh, col_count = st.columns([1, 3])
            with col_refresh:
                if st.button("🔄 Refresh List", key="refresh_memory"):
                    st.rerun()
            
            # List existing memory files
            existing_files = list_memory_files()
            if existing_files:
                with col_count:
                    st.markdown(f"**📂 Available Memory Files ({len(existing_files)} found):**")
                st.markdown("*Files are sorted by modification date (newest first)*")
                
                for i, file_info in enumerate(existing_files):
                    # Create a container for each file
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([4, 1, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{file_info['name']}**")
                            # Show modification date
                            from datetime import datetime
                            mod_date = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M')
                            st.caption(f"Modified: {mod_date}")
                        
                        with col2:
                            st.markdown(f"**Size:** {file_info['size']}")
                        
                        with col3:
                            st.markdown(f"**Index:** {file_info['index_size']}")
                        
                        with col4:
                            if st.button("Load", key=f"load_{i}_{file_info['name']}", type="primary"):
                                load_memory_by_path(file_info["path"])
                        
                        with col5:
                            if st.button("Info", key=f"info_{i}_{file_info['name']}"):
                                st.info(f"""
                                **File Details:**
                                - **Name:** {file_info['name']}
                                - **Path:** {file_info['path']}
                                - **Size:** {file_info['size']}
                                - **Index Size:** {file_info['index_size']}
                                - **Modified:** {mod_date}
                                """)
                        
                        st.divider()
            else:
                st.info("📁 No memory files found in `data/memory/` directory.")
                st.markdown("""
                **To create memory files:**
                1. Upload a PDF file using the "Upload File" tab
                2. The system will automatically create memory files
                3. They will appear here for future use
                """)
            
            st.markdown("---")
            st.markdown("**🔍 Or enter a custom path:**")
            st.markdown("Enter the full path to an existing memory file (MP4, MKV, or AVI):")
            
            # Provide some example paths
            st.markdown("**Example paths:**")
            st.code("data/memory/ai-use-case_memory.mp4")
            st.code("C:/path/to/your/memory_file.mp4")
            
            memory_path = st.text_input(
                "Memory file path:",
                placeholder="Enter full path to memory file...",
                help="Path to existing memory file (must have corresponding _index.json file)"
            )
            
            if memory_path and st.button("Load Memory File", key="path_btn"):
                load_memory_by_path(memory_path)
        
        # Document info
        if st.session_state.document_loaded and st.session_state.document_info:
            st.markdown("### 📄 Current Document")
            doc_info = st.session_state.document_info
            st.info(f"""
            **Name:** {doc_info['name']}  
            **Size:** {doc_info['size']}  
            **Path:** {doc_info['path']}
            """)
        
        # Clear chat button
        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Chat interface
        if st.session_state.document_loaded:
            st.markdown("## 💬 Chat Interface")
            
            # Display chat history
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Assistant:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Query input
            with st.form("chat_form"):
                query = st.text_area(
                    "Ask a question about your document:",
                    placeholder="What would you like to know about the document?",
                    height=100
                )
                submit_button = st.form_submit_button("Send", type="primary")
                
                if submit_button and query.strip():
                    response = process_query(query.strip())
                    st.rerun()
        
        else:
            # Welcome message when no document is loaded
            st.markdown("## 👋 Welcome!")
            st.info("""
            **To get started:**
            1. **Upload a new document** using the "Upload File" tab in the sidebar
            2. **Or load an existing memory file** using the "Load Memory" tab
            3. Wait for the document to be processed
            4. Start asking questions about the content
            
            **Supported formats:**
            - **PDF files**: Will be converted to memory video for processing
            - **MP4/MKV/AVI files**: Memory video files (must have corresponding index files)
            
            **Loading options:**
            - **Upload**: Drag and drop or browse for new files
            - **Path**: Enter the full path to existing memory files
            """)
    
    with col2:
        # Features and help
        st.markdown("## 🚀 Features")
        st.markdown("""
        - **Document Processing:** Upload PDFs and video files
        - **Multi-Agent System:** Combines document search with web search
        - **Memory Video:** Advanced document understanding
        - **Real-time Chat:** Interactive Q&A interface
        """)
        
        st.markdown("## 💡 Tips")
        st.markdown("""
        - Ask specific questions for better answers
        - The system will search the document first
        - If not found, it will search the web
        - Clear chat history to start fresh
        """)
        
        # System status
        st.markdown("## 🔧 System Status")
        if st.session_state.agent:
            st.success("✅ Agent: Active")
        else:
            st.error("❌ Agent: Not initialized")
            
        if st.session_state.document_loaded:
            st.success("✅ Document: Loaded")
        else:
            st.info("ℹ️ Document: Not loaded")

if __name__ == "__main__":
    main() 