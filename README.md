# Deep Dataset Scraper 📀⛏️

An intelligent, autonomous agent designed to build massive Machine Learning datasets by scraping the web. It uses a local LLM to generate targeted queries, filter for valid data sources, and extract direct download links and metadata.

## 🎯 Purpose
Unlike generic web scrapers, this tool is optimized for **Data Engineering** tasks. It actively ignores blog posts and opinion pieces, hunting specifically for:
- CSV/JSON/Parquet files
- Kaggle & HuggingFace datasets
- SQL Dumps
- API Documentation
- Raw HTML tables

## 🚀 Key Features
- **Dataset-Focused Querying**: Auto-generates queries using advanced operators (`filetype:csv`, `site:kaggle.com`, `intitle:index of`).
- **Smart Filtering**: The local LLM (Mistral-7B) reads page content to verify if it actually contains a dataset or valid access method.
- **Metadata Extraction**: Extracts:
  - Dataset Name & Description
  - File Formats
  - Direct Download Links
  - Licensing Info (e.g., CC-BY, MIT)
- **Structured Storage**:
  - Saves a master `dataset.csv` with all metadata.
  - Archives raw page content for further parsing.

## 🛠️ Installation

1. **Clone & Install**:
   ```bash
   git clone https://github.com/yourusername/Deep-Dataset-Scraper.git
   cd Deep-Dataset-Scraper
   pip install -r requirements.txt
   ```

2. **GPU Setup** (Critical for speed):
   Ensure `llama-cpp-python` is using your NVIDIA GPU.
   ```powershell
   $env:CMAKE_ARGS="-DLLAMA_CUBLAS=on"
   pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
   ```

## 💻 Usage

1. Run the scraper:
   ```bash
   python main.py
   ```
2. Enter your target dataset topic (e.g., *"Historical Weather Data Europe"* or *"Chest X-Ray Images DICOM"*).

3. The agent will:
   - Analyze technical terms around the topic.
   - Generate ~200 specific search queries.
   - Crawl thousands of results.
   - Filter and catalog every valid dataset found.

## 📂 Output Structure

Data is stored in `data/{session_id}/`:

| File | Description |
|------|-------------|
| `dataset.csv` | Master catalog containing **Download Links**, **License**, **Formats**, etc. |
| `query_folder/*.txt` | Raw text of the verified pages, serving as a text corpus if needed. |

## ⚙️ Configuration (`config.py`)
- `MAX_SEARCH_QUERIES`: Default 200. Increase for deeper scraping.
- `MAX_RESULTS_PER_QUERY`: Default 100.
- `N_GPU_LAYERS`: Set to `-1` for max performance on RTX 4050.

## 🧠 Model Info
Uses `Mistral-7B-Instruct-v0.2-GGUF` (Quantized) for a balance of reasoning capability and memory efficiency (fits in 6GB VRAM).

## 📜 License
MIT
