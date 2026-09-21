"""
AI provider abstraction (section 5's requirement: don't lock the app to one
vendor). Every adapter implements complete_json(): given a system prompt and
a user prompt, return raw text from the model, requested in JSON mode where
the provider supports it.

Callers are responsible for parsing/validating/repairing that text — see
app/services/json_repair.py and section 23 (AI output validation). Models
routinely add preamble or malformed JSON even in "JSON mode", so this
interface deliberately returns a raw string rather than pretending the
provider guarantees valid JSON.
"""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    name: str

    @abstractmethod
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    def embed(self, text: str) -> list[float]:
        """Return an embedding vector for text. Optional capability —
        providers without an embeddings API inherit this error instead of
        being forced to implement it; the matching agent treats embedding
        absence as 'similarity unavailable' and falls back to heuristics."""
        raise NotImplementedError(f"{self.name} does not implement embeddings")