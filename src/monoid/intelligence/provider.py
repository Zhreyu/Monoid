from abc import ABC, abstractmethod
from typing import List
from monoid.core.domain import Note, NoteTag

class AIProvider(ABC):
    @abstractmethod
    def summarize(self, content: str) -> str:
        """Generate a summary of the content."""
        pass

    @abstractmethod
    def ask(self, context: str, question: str) -> str:
        """Answer a question based on the provided context."""
        pass

    @abstractmethod
    def synthesize(self, notes: List[Note], topic: str) -> str:
        """Synthesize multiple notes into a cohesive document."""
        pass

    @abstractmethod
    def generate_quiz(self, notes: List[Note]) -> str:
        """Generate a quiz/study material from notes."""
        pass

    @abstractmethod
    def suggest_tags(self, content: str) -> List[NoteTag]:
        """Suggest tags for the content."""
        pass

    @abstractmethod
    def generate_from_template(self, content: str, template_name: str) -> str:
        """Generate structured content using a template."""
        pass
