from llama_cpp import Llama
from huggingface_hub import hf_hub_download
import json
import re
import config

class LLMEngine:
    def __init__(self):
        print(f"Downloading model {config.MODEL_FILENAME} from {config.REPO_ID}...")
        try:
            self.model_path = hf_hub_download(
                repo_id=config.REPO_ID,
                filename=config.MODEL_FILENAME
            )
        except Exception as e:
            print(f"Error downloading model: {e}")
            raise
        
        print("Initializing Llama model allow for GPU offloading...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=config.N_CTX,
            n_gpu_layers=config.N_GPU_LAYERS,
            n_threads=config.N_THREADS,
            verbose=False
        )

    def generate_json(self, prompt, max_tokens=1000):
        """
        Generates text and attempts to parse it as JSON.
        """
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            stop=["```", "User:", "\n\n"],
            echo=False
        )
        text = output['choices'][0]['text']
        return self._extract_json(text)

    def generate_text(self, prompt, max_tokens=500):
        output = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.2, # Lower temperature for analysis
            echo=False
        )
        return output['choices'][0]['text'].strip()

    def extract_info(self, text, query):
        """
        Extracts structured dataset metadata from the text.
        """
        prompt = f"""
You are a Dataset Scraper Agent. 
Context: User is looking for datasets about "{query}".
Content: "{text[:3000]}..."

Task: Extract dataset details in JSON format.
1. "dataset_name": Title of the dataset or page.
2. "description": Brief description of what data is contained (rows, columns, subject).
3. "formats": List of available formats (e.g., CSV, JSON, API, ZIP, HTML_TABLE).
4. "download_links": List of direct download URLs or Access APIs.
5. "license": Any license information mentioned (e.g., MIT, CC-BY, Unknown).
6. "relevance_score": 0-10 (10 = Direct CSV/JSON link found, 0 = Irrelevant blog).

Return ONLY the JSON.
"""
        return self.generate_json(prompt, max_tokens=600)


    def _extract_json(self, text):
        """
        Tries to extract JSON from the text using regex and parsing.
        """
        try:
            # Try to find a code block first
            code_block = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if code_block:
                return json.loads(code_block.group(1))
            
            # Try to find variables like content = {...}
            bracket_match = re.search(r'\{.*\}', text, re.DOTALL)
            if bracket_match:
                return json.loads(bracket_match.group(0))
            
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Raw text: {text[:200]}...")
            return None
