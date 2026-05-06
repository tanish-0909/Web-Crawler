import json
import re
from typing import Any, List, Optional

import requests

import config


class LLMEngine:
    def __init__(self):
        self.base = config.OLLAMA_BASE_URL.rstrip("/")
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_REQUEST_TIMEOUT
        print(f"Connecting to Ollama at {self.base} (model={self.model})...")
        self._ping_ollama_and_pick_model()

    def _ping_ollama_and_pick_model(self) -> None:
        try:
            r = requests.get(f"{self.base}/api/tags", timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.base}. Is `ollama serve` running? ({e})"
            ) from e

        names = [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
        if not names:
            raise RuntimeError(
                f"No models found in Ollama. Run: ollama pull {self.model}"
            )

        self.model = self._match_installed_model(names)

    def _match_installed_model(self, installed: List[str]) -> str:
        wanted = self.model.strip()
        if wanted in installed:
            return wanted
        tagged = [n for n in installed if n.startswith(wanted + ":")]
        if tagged:
            pick = sorted(tagged)[0]
            print(f"Resolved Ollama model '{wanted}' -> '{pick}'")
            return pick
        family_root = wanted.split(":")[0].lower()
        same_family = [n for n in installed if n.lower().split(":")[0] == family_root]
        if same_family:
            pick = sorted(same_family)[0]
            print(f"Resolved Ollama model family '{family_root}' -> '{pick}'")
            return pick
        raise RuntimeError(
            f"Model '{wanted}' not found. Installed: {installed}. Run: ollama pull {wanted}"
        )

    def _chat(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]] = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if stop:
            payload["options"]["stop"] = stop

        try:
            r = requests.post(
                f"{self.base}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}") from e

        data = r.json()
        msg = data.get("message") or {}
        content = msg.get("content")
        if not content:
            raise RuntimeError(f"Empty response from Ollama: {data}")
        return content.strip()

    def generate_json(self, prompt: str, max_tokens: int = 1000):
        text = self._chat(
            prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            stop=["```\n\n", "User:"],
        )
        return self._extract_json(text)

    def generate_text(self, prompt: str, max_tokens: int = 500):
        return self._chat(prompt, max_tokens=max_tokens, temperature=0.2)

    def extract_info(self, text: str, query: str, candidate_urls: Optional[List[str]] = None):
        """Same JSON shape as always; links only come in via indices into candidate_urls."""
        candidates = list(candidate_urls or [])[: config.MAX_CANDIDATE_URLS]
        if candidates:
            numbered = "\n".join(f"{i}: {u}" for i, u in enumerate(candidates))
            candidate_block = numbered
        else:
            candidate_block = "(No http(s) links could be extracted from this page HTML/text.)"

        prompt = f"""You are a Dataset Scraper Agent. Use ONLY facts supported by the Content below.
User topic: "{query}"

Content (truncated):
\"\"\"{(text or '')[:6000]}\"\"\"

Candidate URLs — these are the ONLY links you may treat as dataset/download targets.
You MUST choose targets by listing their integer indices (selected_indices). Do NOT invent URLs.
If none of the candidates are dataset/download/API targets for this topic, use an empty list.

{candidate_block}

Return ONLY valid JSON with these keys:
- "dataset_name": string (page or dataset title from content; use empty string if unclear)
- "description": string (brief; empty if unclear)
- "formats": array of strings like CSV, JSON, ZIP (infer only from content)
- "license": string or "Unknown"
- "relevance_score": integer 0-10 (10 = clear downloadable data for the topic)
- "selected_indices": array of integers — indices into the Candidate URLs list above ONLY

Do not include download_links or any URL strings in the JSON."""

        raw = self._chat(
            prompt,
            max_tokens=700,
            temperature=0.25,
            stop=["```\n\n", "User:"],
        )
        return self._extract_json(raw)

    def _extract_json(self, text: str):
        try:
            code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if code_block:
                return json.loads(code_block.group(1))

            bracket_match = re.search(r"\{[\s\S]*\}", text)
            if bracket_match:
                return json.loads(bracket_match.group(0))

            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Raw text: {text[:200]}...")
            return None
