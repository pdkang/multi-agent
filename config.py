import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = BASE_DIR / "10-K"
CACHE_DIR = DATA_DIR / "faiss_index"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ARES_API_KEY = os.getenv("ARES_API_KEY")

# Document Processing
CHUNK_SIZE = 400
CHUNK_OVERLAP = 100

# Embedding Settings
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_DIMENSION = 768

# Cache Settings
CACHE_FILE = DATA_DIR / "semantic_cache.json"
SIMILARITY_THRESHOLD = 0.3

# FAISS Settings
FAISS_INDEX_FILE = CACHE_DIR / "index.faiss"
FAISS_METADATA_FILE = CACHE_DIR / "index.json"

# Test Settings
TEST_CONFIG = {
    "test_data_dir": BASE_DIR / "test_data",
    "cache_dir": BASE_DIR / "test_cache",
    "temp_dir": BASE_DIR / "test_temp"
}

# Create test directories
for dir_path in TEST_CONFIG.values():
    dir_path.mkdir(exist_ok=True) 