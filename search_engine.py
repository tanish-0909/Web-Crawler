import time

from googlesearch import search


class SearchEngine:
    def __init__(self, pause=2.0, run=None):
        self.pause = pause
        self.run = run

    def perform_search(self, query, num_results=100):
        """Hit Google (via googlesearch-python), return deduped URLs."""
        print(f"Searching for: {query}")
        links = []
        try:
            # wrapper tops out around 100 results per query — that's the library, not us
            for j in search(
                query,
                num=num_results if num_results < 100 else 100,
                stop=num_results,
                pause=self.pause,
            ):
                if j not in links:
                    links.append(j)
        except Exception as e:
            print(f"Error during search for '{query}': {e}")
            if self.run:
                self.run.search_failures += 1
            time.sleep(10)

        return links
