# Deep Dataset Scraper

An autonomous agent that searches the web for **downloadable datasets** on a topic you choose. It uses a **local LLM via Ollama** to draft search queries, judge whether a page is data‑related, and summarize metadata. **Download targets are grounded**: only URLs actually present on the fetched page can appear as verified links (the model picks indices into that list).

## Prerequisites

1. **Python 3.10+**
2. **[Ollama](https://ollama.com/)** installed and running (`ollama serve` is usually automatic after install).
3. At least one chat model pulled. The default in [`config.py`](config.py) is **`llama3.2:3b`** — a strong choice for structured JSON on **~6 GB VRAM / 16 GB RAM** with comfortable headroom.

```powershell
ollama pull llama3.2:3b
```

Override with environment variables if needed:

```powershell
$env:OLLAMA_MODEL = "mistral"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
```

## Setup (Windows PowerShell)

```powershell
cd D:\Webcrawler
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

```powershell
python main.py
```

Enter a topic (e.g. *Historical weather CSV Europe*). The agent will:

1. Analyze the topic.
2. Generate many targeted Google queries (batched JSON).
3. Fetch pages, filter with the LLM, extract grounded metadata.
4. Save rows under `data/{session_id}/` and write **`research_report.md`** + **`research_summary.json`**.

## Output

| Artifact | Description |
|----------|-------------|
| `dataset.csv` | Catalog with verified links, candidates count, timestamps |
| `research_report.md` | Human-readable counts, domains, sources |
| `research_summary.json` | Same stats + full source list + config snapshot |
| Per-query folders | `.txt` archives of scraped text |

## Configuration

See [`config.py`](config.py): search volume, delays, `MAX_CANDIDATE_URLS`, Ollama URL/model, etc.

## Limits

Google HTML results and site blocking are outside this repo’s control. Grounding prevents **invented download URLs**; it does not guarantee every topic yields thousands of unique files without APIs or authenticated sources.
