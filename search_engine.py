import time

from googlesearch import search

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None


class SearchEngine:
    def __init__(self, pause=2.0, run=None):
        self.pause = pause
        self.run = run

    def perform_search(self, query, num_results=100):
        """Try Google first; if we get nothing (common when HTML changes / rate limits), use DDGS."""
        print(f"Searching for: {query}")
        links: list[str] = []
        want = min(num_results, 100)

        try:
            for j in search(
                query,
                num_results=want,
                sleep_interval=self.pause,
            ):
                if j not in links:
                    links.append(j)
        except Exception as e:
            print(f"Google search error ('{query}'): {e}")
            if self.run:
                self.run.search_failures += 1
            time.sleep(5)

        if not links and DDGS is not None:
            print("  -> trying DuckDuckGo instead")
            try:
                for item in DDGS().text(query, max_results=want):
                    href = item.get("href")
                    if href and href not in links:
                        links.append(href)
                    if len(links) >= want:
                        break
                time.sleep(min(self.pause, 3.0))
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")
                if self.run:
                    self.run.search_failures += 1

        return links
