import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticCache:
    def __init__(self, cache_dir: str = "data/cache", similarity_threshold: float = 0.85):
        """
        Initialize the semantic cache.
        
        Args:
            cache_dir: Directory to store cache files
            similarity_threshold: Threshold for considering queries similar (0-1)
        """
        self.cache_dir = os.path.abspath(cache_dir)
        self.similarity_threshold = similarity_threshold
        self.document_processor = DocumentProcessor()
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.cache_file = os.path.join(self.cache_dir, "semantic_cache.json")
        self.cache: Dict = self._load_cache()
        
        logger.info(f"Initialized semantic cache with threshold {similarity_threshold}")

    def _load_cache(self) -> Dict:
        """Load cache from disk or initialize empty cache."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Error loading cache file, initializing empty cache")
                return self._initialize_empty_cache()
        return self._initialize_empty_cache()

    def _initialize_empty_cache(self) -> Dict:
        """Initialize an empty cache structure."""
        return {
            "queries": {},  # query_id -> {query, embedding, response, timestamp}
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_queries": 0,
                "cache_hits": 0,
                "cache_misses": 0
            }
        }

    def _save_cache(self):
        """Save cache to disk."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            logger.info("Cache saved successfully")
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
            raise

    def _get_query_embedding(self, query: str) -> np.ndarray:
        """Get embedding for a query using the document processor."""
        return self.document_processor.get_embedding(query)

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))

    def get(self, query: str) -> Tuple[Optional[Dict], bool]:
        """
        Get cached response for a query if a similar query exists.
        
        Args:
            query: The query to look up
            
        Returns:
            Tuple of (cached_response, is_hit)
            - cached_response: The cached response if found, None otherwise
            - is_hit: True if cache hit, False if cache miss
        """
        if not self.cache["queries"]:
            self.cache["metadata"]["cache_misses"] += 1
            self._save_cache()
            return None, False

        query_embedding = self._get_query_embedding(query)
        best_similarity = 0
        best_match = None

        for cached_query in self.cache["queries"].values():
            cached_embedding = np.array(cached_query["embedding"])
            similarity = self._compute_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = cached_query

        if best_similarity >= self.similarity_threshold:
            self.cache["metadata"]["cache_hits"] += 1
            self._save_cache()
            logger.info(f"Cache hit with similarity {best_similarity:.2f}")
            return best_match["response"], True
        
        self.cache["metadata"]["cache_misses"] += 1
        self._save_cache()
        logger.info(f"Cache miss with best similarity {best_similarity:.2f}")
        return None, False

    def put(self, query: str, response: Dict):
        """
        Add a query-response pair to the cache.
        
        Args:
            query: The query to cache
            response: The response to cache
        """
        query_id = f"q_{len(self.cache['queries'])}"
        query_embedding = self._get_query_embedding(query)
        
        self.cache["queries"][query_id] = {
            "query": query,
            "embedding": query_embedding.tolist(),
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        self.cache["metadata"]["total_queries"] += 1
        self.cache["metadata"]["last_updated"] = datetime.now().isoformat()
        
        self._save_cache()
        logger.info(f"Cached new query-response pair with ID {query_id}")

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.cache["metadata"]["cache_hits"] + self.cache["metadata"]["cache_misses"]
        hit_rate = float(self.cache["metadata"]["cache_hits"] / total_requests) if total_requests > 0 else 0.0
        
        return {
            "total_queries": self.cache["metadata"]["total_queries"],
            "cache_hits": self.cache["metadata"]["cache_hits"],
            "cache_misses": self.cache["metadata"]["cache_misses"],
            "hit_rate": hit_rate,
            "last_updated": self.cache["metadata"]["last_updated"]
        }

    def clear(self):
        """Clear the cache."""
        self.cache = self._initialize_empty_cache()
        self._save_cache()
        logger.info("Cache cleared") 