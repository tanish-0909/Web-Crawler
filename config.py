import os

# Configuration for the Agent
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# LLM Configuration
# Using Mistral-7B-Instruct-v0.2 as it provides a good balance of performance/size.
# Alternative for lower VRAM: "microsoft/Phi-3-mini-4k-instruct-gguf"
REPO_ID = "TheBloke/Mistral-7B-Instruct-v0.2-GGUF"
MODEL_FILENAME = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"

# Model Parameters
N_CTX = 4096  # Context window
N_GPU_LAYERS = -1  # -1 means all layers to GPU
N_THREADS = 8

# Search Configuration
MAX_SEARCH_QUERIES = 200 # User requested 200+
MAX_RESULTS_PER_QUERY = 100 # User requested 100+
DELAY_BETWEEN_SEARCHES = 2.0 # To avoid rate limits

# Scraping Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
