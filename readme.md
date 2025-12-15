# Deep Research AI Agent 

An autonomous research agent designed to perform extensive, overnight web scraping and dataset creation for any given topic. Powered by local LLMs (Mistral-7B) to filter noise and extract high-quality data.

## Features
- **Autonomous Query Generation**: breaks down a topic into 200+ targeted search queries.
- **Deep Web Crawling**: Fetches and parses 100+ results per query.
- **AI-Powered Filtering**: Uses a local LLM to read articles and decide if they are relevant to your research.
- **Intelligent Extraction**: Summarizes content, extracts key data points, and categorizes findings.
- **Structured Output**: Saves data in organized folders and a consolidated `dataset.csv`.
- **Privacy-First**: Runs locally on your hardware (optimized for 6GB VRAM GPUs like RTX 3050/4050).

## Installation

### Prerequisites
- Python 3.8+
- NVIDIA GPU with ~6GB VRAM (recommended for speed)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (optional but recommended for `llama-cpp-python`)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/deep-research-agent.git
   cd deep-research-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   **GPU Acceleration Note:**
   If the LLM runs on CPU (slow), verify `llama-cpp-python` is installed with CUDA support:
   ```powershell
   # Windows PowerShell
   $env:CMAKE_ARGS="-DLLAMA_CUBLAS=on"
   pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
   ```

## Usage

1. Run the main script:
   ```bash
   python main.py
   ```
2. Enter your research topic when prompted (e.g., *"Generative AI impact on software engineering jobs"*).
3. The agent will:
   - Download the model (first run only).
   - Generate search queries.
   - Start the search-crawl-filter loop.

*Tip: This process is designed to be comprehensive. It may take several hours to process thousands of links. Perfect for running overnight.*

## Configuration

Edit `config.py` to tune the agent:

- `MAX_SEARCH_QUERIES`: Number of queries to generate (default: 200).
- `MAX_RESULTS_PER_QUERY`: Depth of search per query (default: 100).
- `N_GPU_LAYERS`: Set to `-1` to offload all to GPU.
- `DELAY_BETWEEN_SEARCHES`: Increase this if you hit Google rate limits.

## Output Structure

Data is saved in the `data/` directory, grouped by session:

```
data/
└── 20231215_143022/
    ├── dataset.csv          # Master index with summaries and relevance scores
    ├── query_safe_name/     # Folder for specific sub-topic
    │   ├── article_1.txt    # Raw text content and metadata
    │   └── article_2.txt
    └── ...
```

## Architecture

1. **Analysis**: LLM breaks down the user topic.
2. **Search**: Google Search API finds relevant URLs.
3. **Fetch**: `Trafilatura` + Multithreading downloads content rapidly.
4. **Filter & Extract**: Mistral-7B (GGUF) reads the content, discards irrelevant pages, and extracts insights.
5. **Storage**: Data is committed to disk in real-time.
