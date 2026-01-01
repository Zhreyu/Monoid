from abc import ABC, abstractmethod
from typing import List, Optional
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

    @abstractmethod
    def enhance(self, content: str, extra_prompt: Optional[str] = None, context: Optional[str] = None) -> str:
        """
        Enhance note content: tighten prose, add corrections, expand {{{...}}} commands.

        Args:
            content: The note content to enhance
            extra_prompt: Optional additional instructions from user
            context: Optional context from related notes

        Returns:
            Enhanced note content
        """
        pass
