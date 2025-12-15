from googlesearch import search
import time
import random

class SearchEngine:
    def __init__(self, pause=2.0):
        self.pause = pause

    def perform_search(self, query, num_results=100):
        """
        Executes a Google Search and returns a unique list of URLs.
        """
        print(f"Searching for: {query}")
        links = []
        try:
            # googlesearch-python's generic search function
            # num: number of results per page (approx)
            # stop: query limit
            # pause: time to wait between HTTP requests
            for j in search(query, num=num_results if num_results < 100 else 100, stop=num_results, pause=self.pause):
                if j not in links:
                    links.append(j)
        except Exception as e:
            print(f"Error during search for '{query}': {e}")
            # Backoff strategy could be added here
            time.sleep(10) 
        
        return links
