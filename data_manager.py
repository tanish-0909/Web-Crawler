import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

import config
from session_stats import RunTotals
from url_grounding import normalize_page_url


class DataManager:
    def __init__(
        self,
        session_id=None,
        run: Optional[RunTotals] = None,
    ):
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(config.DATA_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.csv_file = os.path.join(self.session_dir, "dataset.csv")
        self.pending_rows = []
        self.already_saved = set()
        self.run = run

    def save_article(self, query: str, article_data: dict) -> bool:
        """Write the txt snapshot + queue a CSV row. False means we skipped a duplicate page."""
        page_url = article_data.get("url") or ""
        key = normalize_page_url(page_url)
        if key in self.already_saved:
            if self.run:
                self.run.duplicates_skipped += 1
            return False
        self.already_saved.add(key)

        safe_query = "".join([c if c.isalnum() else "_" for c in query])[:50]
        query_dir = os.path.join(self.session_dir, safe_query)
        os.makedirs(query_dir, exist_ok=True)

        filename = "".join([c if c.isalnum() else "_" for c in page_url])[-50:] + ".txt"
        file_path = os.path.join(query_dir, filename)

        verified = article_data.get("verified_download_links") or article_data.get(
            "download_links", []
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {page_url}\n")
            f.write(f"Query: {query}\n")
            f.write(f"Dataset Name: {article_data.get('dataset_name', 'N/A')}\n")
            f.write(f"Formats: {article_data.get('formats', [])}\n")
            f.write(f"Verified download links (grounded): {verified}\n")
            f.write(f"Candidates offered to model: {article_data.get('candidates_count', 0)}\n")
            f.write(f"License: {article_data.get('license', 'Unknown')}\n")
            f.write(f"Description: {article_data.get('description', 'N/A')}\n")
            f.write("-" * 80 + "\n")
            f.write(article_data.get("text") or "")

        saved_at = datetime.now().isoformat(timespec="seconds")

        self.pending_rows.append(
            {
                "query": query,
                "url": page_url,
                "source_url": page_url,
                "dataset_name": article_data.get("dataset_name", "N/A"),
                "formats": str(article_data.get("formats", [])),
                "verified_download_links": str(
                    article_data.get("verified_download_links", [])
                ),
                "download_links": str(article_data.get("download_links", [])),
                "candidates_count": article_data.get("candidates_count", 0),
                "license": article_data.get("license", "Unknown"),
                "relevance": article_data.get("relevance_score", 0),
                "saved_at": saved_at,
                "local_path": file_path,
            }
        )

        if self.run:
            self.run.records_saved += 1
            self.run.track_source(page_url)

        if len(self.pending_rows) >= 10:
            self.flush_csv()

        return True

    def flush_csv(self):
        if not self.pending_rows:
            return

        chunk = pd.DataFrame(self.pending_rows)
        if os.path.exists(self.csv_file):
            chunk.to_csv(self.csv_file, mode="a", header=False, index=False)
        else:
            chunk.to_csv(self.csv_file, index=False)

        self.pending_rows = []

    def close(self) -> None:
        self.flush_csv()
        if self.run:
            self._write_reports()

    def _write_reports(self) -> None:
        assert self.run is not None
        ended = time.time()
        summary_path = os.path.join(self.session_dir, "research_summary.json")
        report_path = os.path.join(self.session_dir, "research_report.md")

        cfg_snapshot: Dict[str, Any] = {
            "OLLAMA_BASE_URL": config.OLLAMA_BASE_URL,
            "OLLAMA_MODEL": config.OLLAMA_MODEL,
            "MAX_SEARCH_QUERIES": config.MAX_SEARCH_QUERIES,
            "MAX_RESULTS_PER_QUERY": config.MAX_RESULTS_PER_QUERY,
            "MAX_CANDIDATE_URLS": config.MAX_CANDIDATE_URLS,
        }

        by_domain = dict(self.run.by_hostname())
        summary = {
            "topic": self.run.topic,
            "session_dir": self.session_dir,
            "started_at_unix": self.run.started_at,
            "ended_at_unix": ended,
            "duration_seconds": round(ended - self.run.started_at, 2),
            "counts": {
                "queries_executed": self.run.queries_executed,
                "search_hits_total": self.run.search_hits_total,
                "pages_fetched": self.run.pages_fetched,
                "pages_relevant": self.run.pages_relevant,
                "records_saved": self.run.records_saved,
                "duplicates_skipped": self.run.duplicates_skipped,
                "fetch_failures": self.run.fetch_failures,
                "search_failures": self.run.search_failures,
            },
            "by_domain": by_domain,
            "sources": self.run.saved_sources,
            "queries_no_results": self.run.queries_no_results,
            "config": cfg_snapshot,
            "methodology_note": (
                "Download targets are grounded: only URLs harvested from each page may "
                "appear as verified_download_links; the LLM selects candidate indices only."
            ),
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        lines = [
            "# Research session report",
            "",
            f"- **Topic:** {self.run.topic}",
            f"- **Session directory:** `{self.session_dir}`",
            f"- **Ollama model:** `{config.OLLAMA_MODEL}`",
            f"- **Duration (s):** {summary['duration_seconds']}",
            "",
            "## Counts",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ]
        for k, v in summary["counts"].items():
            lines.append(f"| {k.replace('_', ' ')} | {v} |")

        lines.extend(
            [
                "",
                "## Sources by domain",
                "",
            ]
        )
        if by_domain:
            for dom, n in sorted(by_domain.items(), key=lambda x: (-x[1], x[0])):
                lines.append(f"- `{dom}`: {n}")
        else:
            lines.append("- _(none)_")

        lines.extend(["", "## Saved page URLs", ""])
        sources = self.run.saved_sources
        cap = 400
        for i, u in enumerate(sources[:cap], 1):
            lines.append(f"{i}. {u}")
        if len(sources) > cap:
            lines.append(f"\n_…and {len(sources) - cap} more (see research_summary.json)._")

        if self.run.queries_no_results:
            lines.extend(["", "## Sample queries with zero search results", ""])
            for q in self.run.queries_no_results[:40]:
                lines.append(f"- `{q}`")

        lines.extend(
            [
                "",
                "## Methodology",
                "",
                summary["methodology_note"],
                "",
            ]
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"\nWrote {summary_path}")
        print(f"Wrote {report_path}")
