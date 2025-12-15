import os
import pandas as pd
import json
import config
from datetime import datetime

class DataManager:
    def __init__(self, session_id=None):
        if not session_id:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(config.DATA_DIR, session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        self.csv_file = os.path.join(self.session_dir, "dataset.csv")
        self.data_buffer = []

    def save_article(self, query, article_data):
        """
        Saves a single article to disk (folder-wise) and appends to CSV buffer.
        """
        # 1. Save as text file
        safe_query = "".join([c if c.isalnum() else "_" for c in query])[:50]
        query_dir = os.path.join(self.session_dir, safe_query)
        os.makedirs(query_dir, exist_ok=True)
        
        filename = "".join([c if c.isalnum() else "_" for c in article_data['url']])[-50:] + ".txt"
        file_path = os.path.join(query_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {article_data['url']}\n")
            f.write(f"Query: {query}\n")
            f.write(f"Dataset Name: {article_data.get('dataset_name', 'N/A')}\n")
            f.write(f"Formats: {article_data.get('formats', '[]')}\n")
            f.write(f"Download Links: {article_data.get('download_links', '[]')}\n")
            f.write(f"License: {article_data.get('license', 'Unknown')}\n")
            f.write(f"Description: {article_data.get('description', 'N/A')}\n")
            f.write("-" * 80 + "\n")
            f.write(article_data['text'])
            
        # 2. Add to CSV buffer
        self.data_buffer.append({
            "query": query,
            "url": article_data['url'],
            "dataset_name": article_data.get('dataset_name', "N/A"),
            "formats": str(article_data.get('formats', [])),
            "download_links": str(article_data.get('download_links', [])),
            "license": article_data.get('license', "Unknown"),
            "relevance": article_data.get('relevance_score', 0),
            "local_path": file_path
        })
        
        # Auto-flush to CSV every 10 items
        if len(self.data_buffer) >= 10:
            self.flush_csv()

    def flush_csv(self):
        if not self.data_buffer:
            return
            
        df = pd.DataFrame(self.data_buffer)
        # Append if exists, else create
        if os.path.exists(self.csv_file):
            df.to_csv(self.csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.csv_file, index=False)
        
        self.data_buffer = []

    def close(self):
        self.flush_csv()
