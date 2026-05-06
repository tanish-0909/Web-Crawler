import os

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)


def _env_str(key: str, default: str) -> str:
    v = os.environ.get(key)
    return v.strip() if v else default


def _env_int(key: str, default: int) -> int:
    v = os.environ.get(key)
    if v is None or not v.strip():
        return default
    try:
        return int(v.strip())
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    v = os.environ.get(key)
    if v is None or not v.strip():
        return default
    try:
        return float(v.strip())
    except ValueError:
        return default


# Ollama HTTP API — defaults picked for a small GPU + room left for context
OLLAMA_BASE_URL = _env_str("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = _env_str("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_REQUEST_TIMEOUT = _env_float("OLLAMA_REQUEST_TIMEOUT", 600.0)

MAX_CANDIDATE_URLS = _env_int("MAX_CANDIDATE_URLS", 120)

MAX_SEARCH_QUERIES = _env_int("MAX_SEARCH_QUERIES", 200)
MAX_RESULTS_PER_QUERY = _env_int("MAX_RESULTS_PER_QUERY", 100)
DELAY_BETWEEN_SEARCHES = _env_float("DELAY_BETWEEN_SEARCHES", 2.0)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

MAX_QUERIES_NO_RESULTS_TRACKED = _env_int("MAX_QUERIES_NO_RESULTS_TRACKED", 80)
