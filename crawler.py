import trafilatura
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import config

class ContentFetcher:
    def __init__(self):
        pass

    def fetch_url(self, url):
        """
        Downloads and parses the main content of the URL.
        Returns a dictionary with raw_html, text, and metadata.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
                if text:
                    return {
                        "url": url,
                        "text": text,
                        "raw_html": downloaded
                    }
        except Exception as e:
            # print(f"Error processing {url}: {e}")
            pass
        return None

class FilterAgent:
    def __init__(self, llm_engine):
        self.llm = llm_engine

    def is_relevant(self, query, article_text):
        """
        Uses LLM to determine if the article is relevant to the query.
        Uses a truncated version of the text to save tokens.
        """
        if not article_text:
            return False
            
        snippet = article_text[:1000] # First 1000 chars is usually enough for relevance check
        prompt = f"""
        Snippet: "{snippet}..."
        
        Task: Does this page likely contain a DOWNLOADABLE DATASET, RAW DATA TABLES, or API DOCUMENTATION for the query?
        Ignore general news or opinion articles unless they contain data tables.
        Answer only with JSON: {{"relevant": true/false, "reason": "found csv link / found data table / etc"}}
        """
        response = self.llm.generate_json(prompt, max_tokens=100)
        if response and isinstance(response, dict):
            return response.get("relevant", False)
        return False

class LinkAnalyzer:
    def __init__(self, llm_engine):
        self.fetcher = ContentFetcher()
        self.llm = llm_engine
        self.filter = FilterAgent(llm_engine)

    def process_links(self, query, links):
        """
        Process a list of links: fetch, filter, and return useful data.
        """
        useful_data = []
        # We can parallelize fetching, but LLM filtering is the bottleneck on GPU.
        # Fetching can be threaded.
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.fetcher.fetch_url, url): url for url in links}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    if data:
                        print(f"Analyzing content from: {url}")
                        if self.filter.is_relevant(query, data['text']):
                            print(f"Found relevant data: {url}")
                            # Extra extraction step
                            extracted_info = self.llm.extract_info(data['text'], query)
                            if extracted_info:
                                data.update(extracted_info)
                            useful_data.append(data)
                        else:
                            pass # print(f"Not relevant: {url}")
                except Exception as e:
                    print(f"Error analyzing {url}: {e}")
        
        return useful_data
