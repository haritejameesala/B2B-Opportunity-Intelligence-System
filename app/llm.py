import json
import re
import requests


class LocalLlama:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.1:8b"

    def analyze(self, system_prompt, user_prompt):
        prompt = f"""
SYSTEM:
{system_prompt}

USER:
{user_prompt}
"""

        print(f"[LLAMA] model={self.model} endpoint={self.base_url}/api/generate")
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.05,
                    "num_predict": 1800,
                },
            },
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()

        raw_response = data.get("response", "")
        if not isinstance(raw_response, str) or not raw_response.strip():
            raise ValueError("Ollama returned no response text.")
        print(f"[LLAMA] raw response:\n{raw_response}")
        return raw_response

    def _extract_json(self, text):
        text = text.strip()

        # Remove markdown code fences
        text = re.sub(
            r"^```json\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"^```\s*",
            "",
            text
        )

        text = re.sub(
            r"\s*```$",
            "",
            text
        )

        # Try direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting JSON object
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]

            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise ValueError(
            "Could not extract valid JSON from Llama response:\n\n"
            + text
        )

    def analyze_json(self, system_prompt, user_prompt):
        system_prompt += """

IMPORTANT:
Return ONLY valid JSON.
Do not use markdown.
Do not explain the answer.
Do not add text before or after the JSON.
"""

        raw_response = self.analyze(system_prompt, user_prompt)
        parsed = self._extract_json(raw_response)
        print(
            "[PARSE] parsed JSON response:\n"
            + json.dumps(parsed, indent=2, ensure_ascii=False)
        )
        return parsed


# Keep compatibility with the existing code.
GroqLLM = LocalLlama