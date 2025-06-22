from huggingface_hub import hf_hub_download
from llama_cpp import Llama
import json
import re

# Download model
model_path = hf_hub_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    filename="mistral-7b-instruct-v0.2.Q4_K_M.gguf"
)

# Initialize model
model = Llama(
    model_path=model_path,
    n_ctx=4096,
    n_gpu_layers=33,  # Offload all layers to GPU
    n_threads=8
)

topic = "the Black Scholes Model"
prompt = f"""Generate exactly 20 search queries about: {topic} for finding relevant datasets.
Format as VALID JSON: {{"queries": ["query1", "query2", ...]}}
Include keywords like 'kaggle', 'papers with code', and 'hugging face'."""

# Generate response
output = model(
    prompt,
    max_tokens=400,
    temperature=0.3,  # Lower temp for more deterministic output
    stop=["}"],       # Stop at closing brace to complete JSON
)

# Extract and clean response
response_text = output['choices'][0]['text']

# 1. Find JSON substring using regex
json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
if json_match:
    json_str = json_match.group(0)
    try:
        # 2. Parse JSON
        queries = json.loads(json_str)
        print("Successfully parsed JSON:")
        for i, q in enumerate(queries['queries'], 1):
            print(f"{i}. {q}")
    except json.JSONDecodeError:
        print("JSON parsing failed. Raw response:")
        print(response_text)
else:
    print("No JSON found in response. Full output:")
    print(response_text)
