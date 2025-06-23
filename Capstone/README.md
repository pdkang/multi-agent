# Multi-Agent Document Chat System

A powerful document chat system that combines document processing with web search capabilities using multiple AI agents.

## 🚀 Features

- **Document Processing**: Upload and process PDF files and video files
- **Smart Memory File Management**: Browse, list, and load existing memory files with detailed information
- **Multi-Agent System**: Combines document search with web search for comprehensive answers
- **Memory Video**: Advanced document understanding using memory video technology
- **Web UI**: Beautiful Streamlit interface for easy interaction
- **Real-time Chat**: Interactive Q&A interface with chat history

## 📋 Prerequisites

- Python 3.8 or higher
- Google API Key (for Gemini AI)
- Groq API Key (for web search functionality)

## 🛠️ Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd demo
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API keys**
   Create a `.env` file in the project root with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   ```

## 🎯 Usage

### Option 1: Web Interface (Recommended)

Run the Streamlit web interface:

```bash
python run_streamlit.py
```

Or directly with Streamlit:

```bash
streamlit run streamlit_app.py
```

The web interface will open at `http://localhost:8501`

### Option 2: Command Line Interface

Run the command-line version:

```bash
python main.py
```

## 📱 Web Interface Guide

### Getting Started

1. **Open the app**: Navigate to `http://localhost:8501` in your browser
2. **Upload a document**: Use the sidebar to upload a PDF, MP4, MKV, or AVI file
3. **Wait for processing**: The system will process your document (PDFs are converted to memory videos)
4. **Start chatting**: Ask questions about your document in the chat interface

### Features

- **Document Upload**: Drag and drop or browse for files
- **Memory File Loading**: Load existing memory files by path or from available list
- **Real-time Chat**: Interactive Q&A with your documents
- **Multi-Agent Responses**: Automatic fallback to web search when document doesn't contain answers
- **Chat History**: View your conversation history
- **System Status**: Monitor agent and document status
- **Clear Chat**: Reset conversation history

### Supported File Formats

- **PDF**: Will be converted to memory video for processing
- **MP4/MKV/AVI**: Memory video files (must have corresponding index files)

### Loading Options

1. **Upload New Documents**: 
   - Upload PDF files (will be processed into memory videos)
   - Upload existing memory video files

2. **Load Existing Memory Files**:
   - Browse available memory files in the data/memory directory
   - View file details: name, size, modification date, and index file size
   - One-click loading with automatic validation
   - Refresh button to update the file list
   - Enter custom file paths for memory files stored elsewhere
   - Automatic validation of index files

## 🔧 Technical Details

### Architecture

- **FileChatAgent**: Main agent for document processing and chat
- **WebSearchAgent**: Handles web search when document doesn't contain answers
- **MemvidEncoder**: Converts PDFs to memory videos
- **MemvidChat**: Handles chat interactions with memory videos

### File Structure

```
demo/
├── agents/
│   ├── file_chat_agent.py      # Main document chat agent
│   ├── web_search_agent.py     # Web search functionality
│   └── orchestrator.py         # Agent coordination
├── data/
│   ├── documents/              # Stored documents
│   └── memory/                 # Memory video files and indexes
├── utils/
│   └── logger.py               # Logging utilities
├── streamlit_app.py            # Web interface
├── main.py                     # Command-line interface
├── run_streamlit.py            # Streamlit launcher
└── requirements.txt            # Dependencies
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your `.env` file is in the project root
   - Verify API keys are correct and have sufficient credits

2. **Document Processing Errors**
   - Check file format is supported
   - Ensure file is not corrupted
   - For video files, ensure index file exists

3. **Streamlit Issues**
   - Make sure Streamlit is installed: `pip install streamlit`
   - Check port 8501 is not in use
   - Try running with: `streamlit run streamlit_app.py --server.port 8502`

4. **Memory Issues**
   - Large PDFs may take time to process
   - Ensure sufficient disk space for memory videos

### Logs

Check the `logs/app.log` file for detailed error information.

## 📝 API Reference

### FileChatAgent

```python
from agents.file_chat_agent import FileChatAgent

# Initialize agent
agent = FileChatAgent()

# Load document
agent.load_document("path/to/document.pdf")

# Process query
response = agent.process_query("What is this document about?")

# Get document info
info = agent.get_document_info()
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Streamlit for the web interface
- Uses Memvid for document processing
- Powered by Google Gemini and Groq APIs 