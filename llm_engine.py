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
        Extracts structured information from the text based on the query.
        """
        prompt = f"""
You are a data extractor. 
Context: User is looking for "{query}".
Content: "{text[:3000]}..."

Task: Extract the following information in JSON format:
1. "summary": A brief summary of the content.
2. "dataset_links": List of any direct download links or API endpoints found.
3. "key_points": List of key facts relevant to the query.
4. "relevance_score": A score from 0-10.

Return ONLY the JSON.
"""
        return self.generate_json(prompt, max_tokens=500)


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
