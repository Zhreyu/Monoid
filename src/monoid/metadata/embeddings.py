from typing import Any, List, Optional

class EmbeddingsManager:
    def __init__(self) -> None:
        self.model_name = "all-MiniLM-L6-v2" # Lightweight, good default
        self._model: Any = None

    @property
    def model(self) -> Any:
        if self._model is None:
            # Lazy load to avoid import cost if not used
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                print("sentence-transformers not installed. Embeddings disabled.")
                return None
        return self._model

    def generate(self, text: str) -> Optional[List[float]]:
        model = self.model
        if not model:
            return None

        # Determine device? CPU is likely fine for notesapp
        embeddings = model.encode(text)
        return list(embeddings.tolist())

embeddings_manager = EmbeddingsManager()
