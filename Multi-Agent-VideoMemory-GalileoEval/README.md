# 🤖 Multi-Agent Document Chat System

A powerful AI-powered document chat system that combines advanced document processing with intelligent web search capabilities. Upload documents, ask questions, and get comprehensive answers using multiple AI agents working together.

## 🎯 What It Does

This system allows you to:
- **Upload PDF documents** and chat with them using AI
- **Ask questions** about document content and get intelligent responses
- **Automatic web search fallback** when document doesn't contain answers
- **Memory video technology** for advanced document understanding
- **Real-time performance monitoring** with Galileo tracing
- **Beautiful web interface** for easy interaction

## 🚀 Key Features

- **📄 Document Processing**: Upload PDFs and video files for AI analysis
- **🧠 Multi-Agent Intelligence**: Combines document search + web search agents
- **🔄 Smart Fallback**: Automatically searches the web when document lacks answers
- **📊 Performance Monitoring**: Galileo integration for tracing and analytics
- **💬 Interactive Chat**: Real-time Q&A with chat history
- **🎥 Memory Video**: Advanced document understanding technology
- **📱 Modern UI**: Beautiful Streamlit web interface

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.8+** - Main programming language
- **Streamlit** - Web interface framework
- **Custom Multi-Agent Architecture** - Orchestrated agent system
- **Memory Video Technology** - Advanced document processing and vector search

### AI Services
- **Google Gemini** - Document processing and chat
- **Groq** - Fast LLM inference for web search
- **Galileo** - Performance monitoring and tracing

### Document Processing
- **Memory Video Technology** - Advanced document understanding
- **PDF Processing** - Automatic conversion to searchable format
- **Vector Search** - Semantic document retrieval

### Supported File Formats

- **PDF**: Will be converted to memory video for processing
- **MP4/MKV/AVI**: Memory video files (must have corresponding index files)- 

## 📋 Prerequisites

- Python 3.8 or higher
- Google API Key (for Gemini AI)
- Groq API Key (for web search)
- Galileo API Key (for monitoring - optional)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd demo
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create a `.env` file in the project root:
```bash
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GALILEO_API_KEY=your_galileo_api_key_here
GALILEO_PROJECT_ID=your_project_id
GALILEO_LOG_STREAM=your_log_stream
```

### 5. Run the Application
```bash
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📖 How to Use

### 1. Upload a Document
- Use the sidebar to upload a PDF file
- The system automatically converts it to a memory video for processing
- Wait for the "Document loaded successfully" message

### 2. Start Chatting
- Type your questions in the chat interface
- The system will search the document first
- If no answer is found, it automatically searches the web
- View your chat history and responses

### 3. Load Existing Files
- Browse available memory files in the sidebar
- Load previously processed documents
- View file details and modification dates
- **Load PDF file**: `.\data\ai-use-case.pdf`
- **Load video memory**: `.\data\memory\ai-use-case_memory.mp4`

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Orchestrator   │    │  Galileo Trace  │
│                 │◄──►│     Agent       │◄──►│    Monitor      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼──────┐    ┌───────▼──────┐
            │ File Chat    │    │ Web Search   │
            │   Agent      │    │   Agent      │
            └──────────────┘    └──────────────┘
```

### Core Components

- **OrchestratorAgent**: Coordinates between file chat and web search
- **FileChatAgent**: Processes documents and answers questions
- **WebSearchAgent**: Searches the web when document lacks answers
- **GalileoEvaluator**: Monitors performance and creates traces

## 📊 Performance Monitoring

The system includes comprehensive performance monitoring with Galileo:

- **Query Processing Traces**: Track how long queries take
- **Agent Performance**: Monitor file chat vs web search usage
- **Fallback Analysis**: See when and why web search is triggered
- **Error Tracking**: Identify and debug issues
- **Session Management**: Track user interactions over time

## 🔧 Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key

# Optional (for monitoring)
GALILEO_API_KEY=your_galileo_api_key
GALILEO_PROJECT_ID=your_project_id
GALILEO_LOG_STREAM=your_log_stream
```

### File Structure
```
demo/
├── agents/                    # AI agent implementations
│   ├── orchestrator.py       # Main orchestrator
│   ├── file_chat_agent.py    # Document processing
│   └── web_search_agent.py   # Web search
├── evaluation/               # Performance monitoring
│   └── galileo_evaluator.py  # Galileo integration
├── utils/                    # Utilities
│   └── logger.py            # Logging
├── data/                     # Data storage
│   ├── documents/           # Uploaded files
│   └── memory/              # Processed memory files
├── streamlit_app.py         # Main web application
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
- Verify all API keys are set in `.env` file
- Check API key permissions and credits

**Document Processing**
- Ensure PDF files are not corrupted
- Check file size (large files may take time)
- Verify sufficient disk space

**Streamlit Issues**
- Try different port: `streamlit run streamlit_app.py --server.port 8502`
- Check if port 8501 is already in use

**Galileo Integration**
- Galileo is optional - app works without it
- Check Galileo API key and project settings
- View console logs for trace information

### Getting Help

1. Check the `logs/app.log` file for detailed errors
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure Python version is 3.8 or higher
4. Check API key permissions and quotas

## 🎯 Use Cases

- **Document Analysis**: Upload research papers and ask questions
- **Knowledge Base**: Create searchable document repositories
- **Customer Support**: Process manuals and answer user questions
- **Research**: Analyze large documents quickly
- **Education**: Interactive learning with document content

## 🔮 Future Enhancements

- [ ] Support for more document formats (Word, PowerPoint)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] API endpoints for integration
- [ ] Batch document processing
- [ ] Custom agent training

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

**Built with ❤️ using modern AI technologies** 
