"""Rough totals we accumulate while a scrape is running (for the reports at the end)."""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urlparse


@dataclass
class RunTotals:
    topic: str
    started_at: float = field(default_factory=time.time)
    queries_executed: int = 0
    search_hits_total: int = 0
    pages_fetched: int = 0
    pages_relevant: int = 0
    records_saved: int = 0
    duplicates_skipped: int = 0
    fetch_failures: int = 0
    search_failures: int = 0
    queries_no_results: List[str] = field(default_factory=list)
    saved_sources: List[str] = field(default_factory=list)

    _seen_sources: set = field(default_factory=set, repr=False)

    def track_source(self, url: str) -> None:
        if url not in self._seen_sources:
            self._seen_sources.add(url)
            self.saved_sources.append(url)

    def by_hostname(self) -> Counter:
        tallies = Counter()
        for u in self.saved_sources:
            try:
                host = urlparse(u).netloc.lower()
                if host:
                    tallies[host] += 1
            except Exception:
                tallies["(invalid)"] += 1
        return tallies
