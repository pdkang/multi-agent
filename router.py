import os
from typing import Dict, Any
from datetime import datetime
import logging
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
from config import ARES_API_KEY
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryRouter:
    def __init__(self):
        """Initialize the query router with OpenAI client and logging setup."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.log_file = "data/logs/routing_decisions.json"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def classify_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify the query intent using GPT-3.5.
        
        Args:
            query: The user's query string
            
        Returns:
            Dict containing:
            - intent: "local" or "web"
            - confidence: float between 0 and 1
            - reason: explanation for the decision
        """
        try:
            # Create prompt for intent classification
            prompt = f"""Classify if this query should be answered using local 10-K documents or web search.
            Query: {query}
            
            Respond in JSON format:
            {{
                "intent": "local" or "web",
                "confidence": float between 0 and 1,
                "reason": "explanation for the decision"
            }}
            
            Rules:
            - Use "local" if the query is about specific 10-K document content
            - Use "web" if the query is about recent events or external information
            - Be conservative in confidence scores
            """

            # Get classification from GPT-3.5
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": "You are a query classification assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}
            )

            # Parse the response
            classification = json.loads(response.choices[0].message.content)
            return classification

        except Exception as e:
            logger.error(f"Error classifying query intent: {str(e)}")
            # Default to local search on error
            return {
                "intent": "local",
                "confidence": 0.5,
                "reason": f"Error in classification: {str(e)}"
            }

    def route_query(self, query: str) -> list:
        """
        Route the query to appropriate handler based on intent.
        Args:
            query: The user's query string
        Returns:
            List of results in the expected UI format
        """
        try:
            # Classify the query
            classification = self.classify_intent(query)
            # Log the decision
            decision = {
                "query": query,
                "intent": classification["intent"],
                "confidence": classification["confidence"],
                "reason": classification["reason"],
                "timestamp": datetime.now().isoformat()
            }
            self._log_decision(decision)
            # If intent is web, do web search
            if classification["intent"] == "web":
                web_results = self._tavily_web_search(query)
                # Convert to expected format for UI
                formatted = []
                for r in web_results.get('results', []):
                    text_val = r.get('snippet') or r.get('text') or r.get('content') or r.get('description', '')
                    formatted.append({
                        'doc': {
                            'text': text_val,
                            'source': r.get('title', r.get('url', 'web')),
                            'metadata': {'url': r.get('url', '')}
                        },
                        'score': 1.0  # or some default
                    })
                return formatted
            else:
                # For local intent, return an empty list (handled by local search in app)
                return []
        except Exception as e:
            logger.error(f"Error routing query: {str(e)}")
            return []

    def _tavily_web_search(self, query: str) -> Dict[str, Any]:
        """
        Perform a real web search using the Tavily API.
        Args:
            query: The search query
        Returns:
            Dict containing web search results
        """
        url = "https://api.tavily.com/search"
        if not TAVILY_API_KEY:
            logger.error("Missing TAVILY_API_KEY in environment.")
            return {"results": [], "source": "tavily_api", "error": "Missing API key"}
        headers = {
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {"query": query}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print("Tavily raw response:", response.json())
                return response.json()
            else:
                logger.error(f"Tavily API request failed: {response.status_code} {response.text}")
                return {"results": [], "source": "tavily_api", "error": f"Status {response.status_code}"}
        except Exception as e:
            logger.error(f"Tavily API request exception: {e}")
            return {"results": [], "source": "tavily_api", "error": str(e)}

    def _log_decision(self, decision: Dict[str, Any]) -> None:
        """
        Log routing decisions to a JSON file.
        
        Args:
            decision: The routing decision to log
        """
        try:
            # Create log entry
            log_entry = {
                "timestamp": decision["timestamp"],
                "query": decision["query"],
                "intent": decision["intent"],
                "confidence": decision["confidence"],
                "reason": decision["reason"]
            }
            
            # Append to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
            logger.info(f"Logged routing decision: {decision['intent']} (confidence: {decision['confidence']})")
            
        except Exception as e:
            logger.error(f"Error logging routing decision: {str(e)}")

def main():
    """Example usage of the QueryRouter."""
    router = QueryRouter()
    
    # Test queries
    test_queries = [
        "What is Uber's revenue in 2021?",
        "What are the latest earnings for Tesla?",
        "What are the key risks mentioned in Lyft's 10-K?",
        "What is the current stock price of Apple?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            cached_result, is_hit = st.session_state.cache.get(query)
            print("Cached result for query:", cached_result, "is_hit:", is_hit)
            if is_hit and cached_result:
                st.info("Retrieved from cache")
                results = cached_result
            else:
                decision = router.route_query(query)
                results = decision
            print(f"Intent: {results['intent']}")
            print(f"Confidence: {results['confidence']}")
            print(f"Reason: {results['reason']}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 