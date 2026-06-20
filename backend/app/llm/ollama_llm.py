import requests

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class OllamaLLM:
    """
    Local LLM wrapper for Ollama.

    Supported example models:
    - qwen2.5-coder:7b
    - deepseek-coder:6.7b
    - llama3.1:8b

    This class only calls Ollama.
    It does not contain hardcoded Robot/Python/Playwright fallback code.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            generated_text = data.get("response", "").strip()

            if not generated_text:
                raise RuntimeError("Ollama returned an empty response.")

            return generated_text

        except requests.exceptions.ConnectionError as exc:
            logger.error("Unable to connect to Ollama at %s", self.base_url)
            raise RuntimeError(
                "Ollama is not running. Start it using: ollama serve"
            ) from exc

        except requests.exceptions.Timeout as exc:
            logger.error("Ollama request timed out.")
            raise RuntimeError(
                "Ollama request timed out. Try a smaller model or increase timeout."
            ) from exc

        except requests.exceptions.HTTPError as exc:
            logger.error("Ollama HTTP error: %s", exc)
            raise RuntimeError(
                f"Ollama HTTP error: {exc}"
            ) from exc

        except Exception as exc:
            logger.error("Ollama generation failed: %s", exc)
            raise RuntimeError(
                f"Ollama generation failed: {exc}"
            ) from exc