import streamlit as st
import os
from pathlib import Path
from document_processor import DocumentProcessor
from router import QueryRouter
from semantic_cache import SemanticCache
import logging
import openai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_components():
    """Initialize all components."""
    if 'processor' not in st.session_state:
        st.session_state.processor = DocumentProcessor()
        # Try to load the vector database if it exists
        index_path = "data/vector_store/10k_index.faiss"
        docs_path = "data/vector_store/10k_documents.json"
        if os.path.exists(index_path) and os.path.exists(docs_path):
            st.session_state.processor.load_index(index_path, docs_path)
    if 'router' not in st.session_state:
        st.session_state.router = QueryRouter()
    if 'cache' not in st.session_state:
        st.session_state.cache = SemanticCache()

def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk."""
    try:
        # Create directory if it doesn't exist
        os.makedirs("10-K", exist_ok=True)
        
        # Save file
        file_path = os.path.join("10-K", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return None

def process_document(file_path):
    """Process a document with progress updates."""
    try:
        # Create a placeholder for progress
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        def update_progress(message, progress):
            progress_placeholder.progress(progress)
            status_placeholder.text(message)
        
        # Process document with progress updates
        st.session_state.processor.process_document(file_path, progress_callback=update_progress)
        
        # Save the updated index
        st.session_state.processor.save_index(
            "data/vector_store/10k_index.faiss",
            "data/vector_store/10k_documents.json"
        )
        
        # Clear progress indicators
        progress_placeholder.empty()
        status_placeholder.empty()
        
        return True
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return False

def display_cache_stats():
    """Display cache statistics."""
    stats = st.session_state.cache.get_stats()
    st.sidebar.markdown("### Cache Statistics")
    st.sidebar.markdown(f"""
    - **Total Queries**: {stats['total_queries']}
    - **Cache Hits**: {stats['cache_hits']}
    - **Hit Rate**: {stats['hit_rate']:.1%}
    - **Memory Usage**: {stats.get('memory_usage', 0.0):.1f}MB
    """)

def main():
    st.title("10-K Document Search")
    
    # Initialize components
    init_components()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("Document Upload")
        similarity_threshold = st.sidebar.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.85,
            step=0.01
        )
        # Set the threshold in the cache (if needed)
        if hasattr(st.session_state.cache, 'similarity_threshold'):
            st.session_state.cache.similarity_threshold = similarity_threshold
        uploaded_file = st.file_uploader("Upload a 10-K PDF", type=['pdf'])
        
        if uploaded_file:
            if st.button("Process Document"):
                file_path = save_uploaded_file(uploaded_file)
                if file_path:
                    if process_document(file_path):
                        st.success(f"Successfully processed {uploaded_file.name}")
                    else:
                        st.error(f"Failed to process {uploaded_file.name}")
                else:
                    st.error("Failed to save uploaded file")
        # Add button to show all file names in the vector database
        if st.button("Show All Stored Files"):
            if hasattr(st.session_state.processor, 'documents') and st.session_state.processor.documents:
                file_names = sorted(set(doc['source'] for doc in st.session_state.processor.documents if 'source' in doc))
                st.markdown("### Files in Vector Database:")
                for fname in file_names:
                    st.write(f"- {fname}")
            else:
                st.info("No files are currently stored in the vector database.")
        # Add a Refresh button that only refreshes the UI
        if st.button("Refresh"):
            st.session_state.submitted_query = ""
            st.session_state.query_input = ""
            st.rerun()
        # Add a Reset Vector Database button
        if st.button("Reset Vector Database"):
            index_path = "data/vector_store/10k_index.faiss"
            docs_path = "data/vector_store/10k_documents.json"
            # Remove files if they exist
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(docs_path):
                os.remove(docs_path)
            # Reset in-memory processor state
            if hasattr(st.session_state, 'processor'):
                st.session_state.processor.index.reset()
                st.session_state.processor.documents = []
                st.session_state.processor.current_index = 0
            st.success("Vector database has been reset. Please re-upload your documents.")
        # Add a Clear Cache button
        if st.button("Clear Cache"):
            if hasattr(st.session_state, 'cache'):
                st.session_state.cache.clear()
                st.success("Semantic cache has been cleared.")
        st.sidebar.markdown(f"**# Documents:** {len(st.session_state.processor.documents)}")
        if hasattr(st.session_state.processor, 'index'):
            try:
                st.sidebar.markdown(f"**# Vectors in Index:** {st.session_state.processor.index.ntotal}")
            except Exception as e:
                st.sidebar.markdown(f"Could not get FAISS index size: {e}")
    
    # Main content area
    query = st.text_input("Enter your query:", key="query_input")
    if "submitted_query" not in st.session_state:
        st.session_state.submitted_query = ""
    if st.button("Submit Query"):
        st.session_state.submitted_query = query
    use_web_search = st.checkbox("Include web search results")
    
    if st.session_state.submitted_query:
        # Check if we have any documents
        if not st.session_state.processor.documents:
            st.warning("No documents available for search. Please upload some 10-K documents first.")
        else:
            # Route query (for intent/confidence, but always search local first)
            classification = st.session_state.router.classify_intent(st.session_state.submitted_query)
            intent = classification["intent"]
            confidence = classification["confidence"]
            # Check cache
            cached_result, is_hit = st.session_state.cache.get(st.session_state.submitted_query)
            print("Cached result for query:", cached_result, "is_hit:", is_hit)
            if is_hit and cached_result:
                st.info("Retrieved from cache")
                results = cached_result
            else:
                # Always search local documents first
                st.info("Searching local documents...")
                results = st.session_state.processor.search(st.session_state.submitted_query)
                if results and isinstance(results, list) and any((isinstance(r, dict) and ('doc' in r or 'text' in r)) for r in results):
                    st.session_state.cache.put(st.session_state.submitted_query, results)
                else:
                    # If no results and user wants web search, do web search
                    if use_web_search:
                        st.info("No local results found. Performing web search...")
                        results = st.session_state.router.route_query(st.session_state.submitted_query)
                        print("Web search results:", results)
                        if results and isinstance(results, list) and any((isinstance(r, dict) and ('doc' in r or 'text' in r)) for r in results):
                            st.session_state.cache.put(st.session_state.submitted_query, results)
                        else:
                            st.warning("No results found in local documents. Enable web search to search the internet.")
                            results = []
                    else:
                        st.warning("No results found in local documents. Enable web search to search the internet.")
                        results = []
            # Display results
            st.subheader("Search Results")
            if results:
                # Prepare context for LLM
                top_chunks = [result['doc']['text'] for result in results if 'doc' in result and 'text' in result['doc']]
                context = "\n\n".join(top_chunks)
                llm_prompt = f"""You are an expert assistant. Use the following context to answer the user's question.\n\nContext:\n{context}\n\nQuestion:\n{st.session_state.submitted_query}\n\nAnswer:"""
                # Call GPT-4.1 using new OpenAI API
                try:
                    client = openai.OpenAI()  # Uses env variable for API key
                    response = client.chat.completions.create(
                        model="gpt-4.1",
                        messages=[
                            {"role": "system", "content": "You are an expert assistant."},
                            {"role": "user", "content": llm_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=512
                    )
                    final_answer = response.choices[0].message.content
                    st.subheader("LLM-Generated Answer")
                    st.write(final_answer)
                except Exception as e:
                    st.error(f"Error calling GPT-4.1: {e}")
                for i, result in enumerate(results, 1):
                    # Skip invalid results (not dict, or missing keys)
                    if not isinstance(result, dict) or ('doc' not in result and ('source' not in result or 'text' not in result)):
                        continue  # skip invalid results
                    doc = result['doc'] if 'doc' in result else result
                    score = result.get('score', None)
                    if not isinstance(doc, dict) or 'source' not in doc or 'text' not in doc:
                        continue  # skip invalid results
                    header = f"Result {i} - {doc['source']}"
                    if score is not None:
                        header += f" (Cosine similarity: {score:.3f})"
                    with st.expander(header):
                        st.write(doc['text'])
                        st.caption(f"Source: {doc['source']}")
                        if 'metadata' in doc:
                            st.caption(f"Processed: {doc['metadata'].get('processed_date', 'N/A')}")
            else:
                st.info("No results to display.")
    
    # Display cache statistics
    display_cache_stats()

if __name__ == "__main__":
    main() 