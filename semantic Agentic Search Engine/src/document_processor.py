import fitz  # PyMuPDF
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import re
import torch
from tqdm import tqdm
import concurrent.futures

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        """
        Initialize the document processor with Nomic's embedding model.
        
        Args:
            model_name: Name of the sentence transformer model to use.
        """
        logger.info(f"Loading embedding model: {model_name}")
        
        # Check for GPU availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device=self.device
        )
        self.vector_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.vector_dim}")
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.vector_dim)
        self.documents: List[Dict[str, Any]] = []
        self.current_index = 0

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF while maintaining structure."""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text("text")
                
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def get_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF."""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            return {
                "filename": os.path.basename(pdf_path),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "creation_date": metadata.get("creationDate", ""),
                "page_count": len(doc),
                "processed_date": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {str(e)}")
            raise Exception(f"Failed to extract metadata from PDF: {str(e)}")

    def split_text(self, text: str, chunk_size: int = 300, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks in parallel."""
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text).strip()
        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Helper to build chunks from a slice of sentences
        def build_chunks(sent_slice):
            chunks = []
            current_chunk = []
            current_length = 0
            for sentence in sent_slice:
                sentence_length = len(sentence)
                if current_length + sentence_length > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    overlap_start = max(0, len(current_chunk) - overlap)
                    current_chunk = current_chunk[overlap_start:]
                    current_length = sum(len(s) for s in current_chunk)
                current_chunk.append(sentence)
                current_length += sentence_length
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            return chunks
        
        # Parallelize chunking by splitting sentences into N parts
        num_workers = min(8, os.cpu_count() or 1)
        if len(sentences) < num_workers * 10:
            # Not enough work to parallelize
            return build_chunks(sentences)
        chunk_size_per_worker = len(sentences) // num_workers
        slices = [sentences[i*chunk_size_per_worker:(i+1)*chunk_size_per_worker] for i in range(num_workers)]
        if len(sentences) % num_workers:
            slices[-1].extend(sentences[num_workers*chunk_size_per_worker:])
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            results = list(executor.map(build_chunks, slices))
        # Flatten and merge overlapping chunks
        all_chunks = []
        for chunk_list in results:
            all_chunks.extend(chunk_list)
        return all_chunks

    def _normalize(self, vectors):
        """Normalize vectors to unit length for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / (norms + 1e-10)

    def process_document(self, pdf_path: str, progress_callback=None) -> None:
        """Process a PDF document and add it to the vector store."""
        if not os.path.exists(pdf_path):
            raise Exception(f"File not found: {pdf_path}")
        try:
            # Extract text and metadata
            if progress_callback:
                progress_callback("Extracting text and metadata...", 0.1)
            text = self.extract_text(pdf_path)
            if not text.strip():
                raise Exception(f"No text content found in PDF: {pdf_path}")
            metadata = self.get_metadata(pdf_path)
            # Split text into chunks (now parallelized)
            if progress_callback:
                progress_callback("Splitting text into chunks...", 0.2)
            chunks = self.split_text(text)
            if not chunks:
                raise Exception(f"No valid chunks created from PDF: {pdf_path}")
            # Set initial batch size based on device
            max_batch_size = 128 if self.device == "cuda" else 32
            min_batch_size = 1
            total_chunks = len(chunks)
            i = 0
            while i < total_chunks:
                batch_size = max_batch_size
                success = False
                while batch_size >= min_batch_size and not success:
                    batch_chunks = chunks[i:i + batch_size]
                    if progress_callback:
                        progress = 0.2 + (0.7 * (i / total_chunks))
                        progress_callback(f"Processing chunk batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} (batch_size={batch_size})...", progress)
                    try:
                        batch_embeddings = self.model.encode(
                            batch_chunks,
                            batch_size=batch_size,
                            show_progress_bar=False,
                            device=self.device
                        )
                        batch_embeddings = self._normalize(np.array(batch_embeddings).astype('float32'))
                        self.index.add(batch_embeddings)
                        # Store document metadata
                        for j, chunk in enumerate(batch_chunks):
                            self.documents.append({
                                'text': chunk,
                                'source': os.path.basename(pdf_path),
                                'metadata': metadata,
                                'index': self.current_index + i + j
                            })
                        i += batch_size
                        success = True
                    except RuntimeError as e:
                        if self.device == "cuda" and ("CUDA out of memory" in str(e) or "CUDA error" in str(e)):
                            logger.warning(f"CUDA OOM at batch_size={batch_size}, reducing batch size...")
                            torch.cuda.empty_cache()
                            batch_size = batch_size // 2
                            if batch_size < min_batch_size:
                                logger.error(f"Minimum batch size reached, still OOM. Failing.")
                                raise Exception(f"Failed to process document due to CUDA OOM at minimum batch size: {str(e)}")
                        else:
                            raise
            self.current_index += total_chunks
            if progress_callback:
                progress_callback("Saving index...", 0.9)
        except Exception as e:
            logger.error(f"Error processing document {pdf_path}: {str(e)}")
            raise Exception(f"Failed to process document: {str(e)}")

    def save_index(self, index_path: str, documents_path: str) -> None:
        """Save the FAISS index and document metadata."""
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.index, index_path)
        
        with open(documents_path, 'w') as f:
            json.dump(self.documents, f)

    def load_index(self, index_path: str, documents_path: str) -> None:
        """Load the FAISS index and document metadata."""
        self.index = faiss.read_index(index_path)
        
        with open(documents_path, 'r') as f:
            self.documents = json.load(f)
        
        self.current_index = len(self.documents)

    def search(self, query: str, k: int = 5) -> list:
        """Search for similar documents using the FAISS index and cosine similarity."""
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), 
            k
        )
        # Debug output: print query embedding, distances, indices, and cosine similarity
        print("Query embedding (first 5 dims):", query_embedding[:5], "...")
        print("Cosine similarities:", distances)
        print("Indices:", indices)
        # Get similarity threshold from cache if available
        similarity_threshold = 0.8
        try:
            import streamlit as st
            if hasattr(st.session_state, 'cache') and hasattr(st.session_state.cache, 'similarity_threshold'):
                similarity_threshold = st.session_state.cache.similarity_threshold
        except Exception:
            pass
        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents) and score >= similarity_threshold:
                results.append({'doc': self.documents[idx], 'score': float(score)})
                print(f"Cosine similarity to doc {idx}: {score}")
        return results

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a single text string."""
        try:
            embedding = self.model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

def process_10k_documents():
    """Process all 10-K documents in the directory."""
    processor = DocumentProcessor()
    
    # Process all PDFs in the 10-K directory
    pdf_dir = Path("10-K")
    for pdf_file in pdf_dir.glob("*.pdf"):
        print(f"Processing {pdf_file.name}...")
        processor.process_document(str(pdf_file))
    
    # Save the index
    processor.save_index("data/vector_store/10k_index.faiss", "data/vector_store/10k_documents.json")
    print("Index built and saved successfully!")

if __name__ == "__main__":
    process_10k_documents() 