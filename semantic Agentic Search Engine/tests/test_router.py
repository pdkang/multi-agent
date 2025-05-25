import unittest
import json
import os
from datetime import datetime
from src.router import QueryRouter

class TestQueryRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.router = QueryRouter()
        # Create a test log file in a temporary location
        cls.test_log_file = "data/logs/test_routing_decisions.json"
        cls.router.log_file = cls.test_log_file
        os.makedirs(os.path.dirname(cls.test_log_file), exist_ok=True)

    def setUp(self):
        """Clear the test log file before each test."""
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_classify_intent_structure(self):
        """Test intent classification structure and types."""
        query = "What is Uber's revenue in 2021?"
        result = self.router.classify_intent(query)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn("intent", result)
        self.assertIn("confidence", result)
        self.assertIn("reason", result)
        
        # Check types
        self.assertIn(result["intent"], ["local", "web"])
        self.assertIsInstance(result["confidence"], float)
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 1)
        self.assertIsInstance(result["reason"], str)

    def test_route_query_structure(self):
        """Test query routing structure and types."""
        query = "What are the key risks in Lyft's 10-K?"
        result = self.router.route_query(query)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn("query", result)
        self.assertIn("intent", result)
        self.assertIn("confidence", result)
        self.assertIn("reason", result)
        self.assertIn("timestamp", result)
        
        # Check types
        self.assertEqual(result["query"], query)
        self.assertIn(result["intent"], ["local", "web"])
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["reason"], str)
        self.assertIsInstance(result["timestamp"], str)

    def test_log_decision(self):
        """Test decision logging functionality."""
        decision = {
            "query": "Test query",
            "intent": "local",
            "confidence": 0.8,
            "reason": "Test reason",
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the decision
        self.router._log_decision(decision)
        
        # Check if log file exists
        self.assertTrue(os.path.exists(self.test_log_file))
        
        # Read and verify log entry
        with open(self.test_log_file, 'r') as f:
            log_entry = json.loads(f.readline())
            
        self.assertEqual(log_entry["query"], decision["query"])
        self.assertEqual(log_entry["intent"], decision["intent"])
        self.assertEqual(log_entry["confidence"], decision["confidence"])
        self.assertEqual(log_entry["reason"], decision["reason"])

    def test_simulate_web_search(self):
        """Test web search simulation."""
        query = "Test web search query"
        result = self.router._simulate_web_search(query)
        
        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn("results", result)
        self.assertIn("source", result)
        
        # Check results
        self.assertIsInstance(result["results"], list)
        self.assertGreater(len(result["results"]), 0)
        self.assertEqual(result["source"], "simulated_web_search")
        
        # Check result structure
        for item in result["results"]:
            self.assertIn("title", item)
            self.assertIn("snippet", item)
            self.assertIn("url", item)

    def test_error_handling(self):
        """Test error handling in classification."""
        # Test with empty query
        result = self.router.classify_intent("")
        self.assertIn(result["intent"], ["local", "web"])
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["reason"], str)

if __name__ == '__main__':
    unittest.main() 