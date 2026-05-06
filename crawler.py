import concurrent.futures

import trafilatura

import config
from url_grounding import harvest_urls


def _attach_verified_links(raw_llm: dict | None, candidates: list[str]) -> dict:
    """Turn selected_indices (+ stray URLs we trust) into verified_download_links."""
    row = dict(raw_llm) if raw_llm else {}
    verified: list[str] = []
    picks = row.get("selected_indices")
    if isinstance(picks, list):
        for i in picks:
            if isinstance(i, int) and 0 <= i < len(candidates):
                verified.append(candidates[i])

    ok = set(candidates)
    for key in ("download_links", "urls"):
        leftover = row.pop(key, None)
        if isinstance(leftover, list):
            for item in leftover:
                if isinstance(item, str) and item in ok and item not in verified:
                    verified.append(item)

    row["verified_download_links"] = verified
    row["download_links"] = verified
    row["candidates_count"] = len(candidates)
    row.pop("selected_indices", None)
    return row


class ContentFetcher:
    def fetch_url(self, url):
        """Grab HTML via trafilatura; body text can be empty but we still keep HTML for link parsing."""
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            text = trafilatura.extract(
                downloaded, include_comments=False, include_tables=True
            )
            return {
                "url": url,
                "text": text or "",
                "raw_html": downloaded,
            }
        except Exception:
            return None


class FilterAgent:
    def __init__(self, llm_engine):
        self.llm = llm_engine

    def is_relevant(self, query, article_text):
        """Quick yes/no pass before we burn tokens on full extraction."""
        if not article_text:
            return False

        snippet = article_text[:1200]
        prompt = f"""Snippet from a web page:
\"\"\"{snippet}\"\"\"

Task: Does this page likely contain a DOWNLOADABLE DATASET, RAW DATA TABLES, or API / bulk data access related to: "{query}"?
Ignore pure opinion/blog unless it embeds data tables or download links.

Answer ONLY valid JSON (no other text):
{{"relevant": true or false, "reason": "short phrase"}}"""

        response = self.llm.generate_json(prompt, max_tokens=120)
        if response and isinstance(response, dict):
            return bool(response.get("relevant", False))
        return False


class LinkAnalyzer:
    def __init__(self, llm_engine):
        self.fetcher = ContentFetcher()
        self.llm = llm_engine
        self.filter = FilterAgent(llm_engine)

    def process_links(self, query, links, run=None):
        """Fetch in parallel, relevance filter, then structured pull with grounded URLs."""
        kept = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            pending = {pool.submit(self.fetcher.fetch_url, url): url for url in links}

            for future in concurrent.futures.as_completed(pending):
                url = pending[future]
                try:
                    payload = future.result()
                    if not payload:
                        if run:
                            run.fetch_failures += 1
                        continue

                    if run:
                        run.pages_fetched += 1

                    print(f"Analyzing content from: {url}")
                    if self.filter.is_relevant(query, payload["text"]):
                        if run:
                            run.pages_relevant += 1
                        print(f"Found relevant data: {url}")

                        candidates = harvest_urls(
                            payload["url"],
                            payload.get("raw_html"),
                            payload.get("text"),
                            config.MAX_CANDIDATE_URLS,
                        )

                        extracted = self.llm.extract_info(
                            payload["text"], query, candidates
                        )
                        payload.update(_attach_verified_links(extracted, candidates))
                        kept.append(payload)
                except Exception as e:
                    print(f"Error analyzing {url}: {e}")

        return kept
