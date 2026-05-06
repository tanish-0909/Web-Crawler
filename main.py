import sys

import config
from crawler import LinkAnalyzer
from data_manager import DataManager
from llm_engine import LLMEngine
from search_engine import SearchEngine
from session_stats import RunTotals


def main():
    print("=== AI Research Agent ===")

    user_query = input(
        "\nEnter the topic you want to find datasets for "
        "(e.g. 'Bitcoin transactions 2023'): "
    ).strip()
    if not user_query:
        print("Query cannot be empty.")
        return

    run = RunTotals(topic=user_query)

    try:
        llm = LLMEngine()
        searcher = SearchEngine(pause=config.DELAY_BETWEEN_SEARCHES, run=run)
        analyzer = LinkAnalyzer(llm)
        store = DataManager(run=run)
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    try:
        print("\nAnalyzing topic for potential dataset sources...")
        analysis_prompt = (
            f"Analyze the following topic to find DATASETS. Identify key file formats "
            f"(CSV/JSON), repository names, and technical terms:\nTopic: {user_query}\n"
            f"Keep it concise."
        )
        analysis = llm.generate_text(analysis_prompt)
        print(f"Analysis: {analysis}")

        print(f"\nGenerating {config.MAX_SEARCH_QUERIES} dataset search queries...")
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
            print(f"Generating batch {i + 1}/{batches}...")
            result = llm.generate_json(prompt, max_tokens=2048)
            if result and "queries" in result:
                generated_queries.extend(result["queries"])
            else:
                print("Failed to generate queries for this batch.")

        generated_queries = list(dict.fromkeys(generated_queries))
        print(f"Total unique queries generated: {len(generated_queries)}")

        if not generated_queries:
            print("No queries generated. Exiting.")
            return

        total_processed = 0

        for i, query in enumerate(generated_queries):
            run.queries_executed += 1
            print(f"\n[{i + 1}/{len(generated_queries)}] Processing Query: {query}")

            links = searcher.perform_search(
                query, num_results=config.MAX_RESULTS_PER_QUERY
            )
            print(f"Found {len(links)} links.")
            run.search_hits_total += len(links)

            if (
                not links
                and len(run.queries_no_results)
                < config.MAX_QUERIES_NO_RESULTS_TRACKED
            ):
                run.queries_no_results.append(query)

            useful_data = analyzer.process_links(query, links, run=run)
            print(f"Found {len(useful_data)} useful articles.")

            for article in useful_data:
                store.save_article(query, article)

            total_processed += len(links)
            print("-" * 50)

        print(
            f"\n=== Job complete. Processed {total_processed} search hits. "
            f"Data and reports: {store.session_dir} ==="
        )
    finally:
        store.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(0)
