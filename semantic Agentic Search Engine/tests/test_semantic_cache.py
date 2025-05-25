import unittest
import os
import json
import shutil
from datetime import datetime
from src.semantic_cache import SemanticCache

class TestSemanticCache(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_cache_dir = "data/test_cache"
        cls.cache = SemanticCache(cache_dir=cls.test_cache_dir, similarity_threshold=0.85)

    def setUp(self):
        """Clear cache before each test."""
        self.cache.clear()

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_cache_dir):
            shutil.rmtree(self.test_cache_dir)

    def test_cache_initialization(self):
        """Test cache initialization."""
        self.assertTrue(os.path.exists(self.test_cache_dir))
        self.assertEqual(self.cache.similarity_threshold, 0.85)
        self.assertEqual(self.cache.get_stats()["total_queries"], 0)

    def test_cache_put_and_get(self):
        """Test putting and getting items from cache."""
        query = "What is Uber's revenue in 2021?"
        response = {
            "answer": "Uber's revenue in 2021 was $17.5 billion",
            "sources": ["Uber-2021-Annual-Report.pdf"]
        }
        
        # Put item in cache
        self.cache.put(query, response)
        
        # Get item from cache
        cached_response, is_hit = self.cache.get(query)
        
        self.assertTrue(is_hit)
        self.assertEqual(cached_response, response)
        self.assertEqual(self.cache.get_stats()["cache_hits"], 1)
        self.assertEqual(self.cache.get_stats()["cache_misses"], 0)

    def test_similar_queries(self):
        """Test cache hit with similar queries."""
        # Cache original query
        original_query = "What is Uber's revenue in 2021?"
        response = {
            "answer": "Uber's revenue in 2021 was $17.5 billion",
            "sources": ["Uber-2021-Annual-Report.pdf"]
        }
        self.cache.put(original_query, response)
        
        # Try similar query
        similar_query = "How much revenue did Uber make in 2021?"
        cached_response, is_hit = self.cache.get(similar_query)
        
        self.assertTrue(is_hit)
        self.assertEqual(cached_response, response)

    def test_dissimilar_queries(self):
        """Test cache miss with dissimilar queries."""
        # Cache original query
        original_query = "What is Uber's revenue in 2021?"
        response = {
            "answer": "Uber's revenue in 2021 was $17.5 billion",
            "sources": ["Uber-2021-Annual-Report.pdf"]
        }
        self.cache.put(original_query, response)
        
        # Try dissimilar query
        dissimilar_query = "What is Lyft's market share?"
        cached_response, is_hit = self.cache.get(dissimilar_query)
        
        self.assertFalse(is_hit)
        self.assertIsNone(cached_response)

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        # Add some queries
        queries = [
            ("What is Uber's revenue?", {"answer": "Revenue info"}),
            ("What is Lyft's revenue?", {"answer": "Revenue info"}),
            ("How many users does Uber have?", {"answer": "User info"})
        ]
        
        for query, response in queries:
            self.cache.put(query, response)
        
        stats = self.cache.get_stats()
        
        self.assertEqual(stats["total_queries"], 3)
        self.assertGreaterEqual(stats["cache_hits"], 0)
        self.assertGreaterEqual(stats["cache_misses"], 0)
        self.assertIsInstance(stats["hit_rate"], float)
        self.assertIsInstance(stats["last_updated"], str)

    def test_cache_persistence(self):
        """Test cache persistence across instances."""
        # Add item to cache
        query = "Test query"
        response = {"answer": "Test response"}
        self.cache.put(query, response)
        
        # Create new cache instance
        new_cache = SemanticCache(cache_dir=self.test_cache_dir)
        
        # Check if item persists
        cached_response, is_hit = new_cache.get(query)
        self.assertTrue(is_hit)
        self.assertEqual(cached_response, response)

    def test_cache_clear(self):
        """Test cache clearing functionality."""
        # Add some items
        self.cache.put("query1", {"answer": "response1"})
        self.cache.put("query2", {"answer": "response2"})
        
        # Clear cache
        self.cache.clear()
        
        # Verify cache is empty
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_queries"], 0)
        self.assertEqual(stats["cache_hits"], 0)
        self.assertEqual(stats["cache_misses"], 0)

if __name__ == '__main__':
    unittest.main() 