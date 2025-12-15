import argparse
import config
from llm_engine import LLMEngine
from search_engine import SearchEngine
from crawler import LinkAnalyzer
from data_manager import DataManager
import time
import sys

def main():
    print("=== AI Research Agent ===")
    
    # 1. Initialize Components
    try:
        llm = LLMEngine()
        searcher = SearchEngine(pause=config.DELAY_BETWEEN_SEARCHES)
        analyzer = LinkAnalyzer(llm)
        data_manager = DataManager()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # 2. Get User Query
    user_query = input("\nEnter the topic you want to find datasets for (e.g. 'Bitcoin Transaction 2023'): ")
    if not user_query:
        print("Query cannot be empty.")
        return

    # 3. Analyze Query
    print("\nAnalyzing topic for potential dataset sources...")
    analysis_prompt = f"Analyze the following topic to find DATASETS. Identify key file formats (CSV/JSON), repository names, and technical terms:\nTopic: {user_query}\nKeep it concise."
    analysis = llm.generate_text(analysis_prompt)
    print(f"Analysis: {analysis}")

    # 4. Generate Search Queries
    print(f"\nGenerating {config.MAX_SEARCH_QUERIES} dataset search queries...")
    # We might need to batched generation if 200 is too hard for one pass, but let's try one pass first or split into 4 batches of 50.
    
    generated_queries = []
    batches = 4
    queries_per_batch = config.MAX_SEARCH_QUERIES // batches
    
    for i in range(batches):
        prompt = f"""
You are an expert Data Engineer. Based on the topic "{user_query}", generate a list of {queries_per_batch} Google search queries to find DOWNLOADABLE DATASETS.
Use advanced operators like: filetype:csv, filetype:json, filetype:parquet, "dataset", "corpus", "dump", site:kaggle.com, site:huggingface.co
Return ONLY valid JSON format:
{{
  "queries": [
    "query 1",
    ...
    "query {queries_per_batch}"
  ]
}}
"""
        print(f"Generating batch {i+1}/{batches}...")
        result = llm.generate_json(prompt, max_tokens=2048)
        if result and "queries" in result:
            generated_queries.extend(result["queries"])
        else:
            print("Failed to generate queries for this batch.")

    generated_queries = list(set(generated_queries)) # Unique
    print(f"Total unique queries generated: {len(generated_queries)}")
    
    if not generated_queries:
        print("No queries generated. Exiting.")
        return

    # 5. Execution Loop
    total_processed = 0
    
    for i, query in enumerate(generated_queries):
        print(f"\n[{i+1}/{len(generated_queries)}] Processing Query: {query}")
        
        # Search
        links = searcher.perform_search(query, num_results=config.MAX_RESULTS_PER_QUERY)
        print(f"Found {len(links)} links.")
        
        # Analyze & Filter
        useful_data = analyzer.process_links(query, links)
        print(f"Found {len(useful_data)} useful articles.")
        
        # Save
        for article in useful_data:
            data_manager.save_article(query, article)
            
        total_processed += len(links)
        print("-" * 50)
        
    data_manager.close()
    print(f"\n=== Job Complete. Processed {total_processed} links. Data saved to {data_manager.session_dir} ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(0)
