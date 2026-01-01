"""Contextual tips system that provides helpful hints after commands."""

import random
from typing import Any, Dict, List, Optional
from enum import Enum


class TipContext(Enum):
    """Different contexts where tips can appear."""
    AFTER_FIRST_NOTE = "after_first_note"
    AFTER_SEARCH_FEW_RESULTS = "after_search_few_results"
    AFTER_SEARCH_MANY_RESULTS = "after_search_many_results"
    AFTER_LIST_MANY_NOTES = "after_list_many_notes"
    AFTER_SHOW_NOTE = "after_show_note"
    AFTER_GRAPH_VIEW = "after_graph_view"
    AFTER_AI_COMMAND = "after_ai_command"
    GENERAL = "general"


# Define tips for each context
TIPS: Dict[TipContext, List[str]] = {
    TipContext.AFTER_FIRST_NOTE: [
        "Tip: Use [[note_id]] to link notes together",
        "Tip: Add tags with --tag to organize your notes",
        "Tip: Run 'monoid list' to see all your notes",
    ],
    TipContext.AFTER_SEARCH_FEW_RESULTS: [
        "Try semantic search with --semantic flag for concept-based matching",
        "Use broader search terms or try searching by tags",
        "Run 'monoid index' to rebuild the search index if results seem off",
    ],
    TipContext.AFTER_SEARCH_MANY_RESULTS: [
        "Tip: Narrow results by adding more keywords or using tags",
        "Tip: Use semantic search for more relevant conceptual matches",
    ],
    TipContext.AFTER_LIST_MANY_NOTES: [
        "Tip: Use 'monoid search' to find specific notes quickly",
        "Tip: Run 'monoid graph web' for interactive exploration of your notes",
        "Tip: Link related notes with [[note_id]] for better discoverability",
    ],
    TipContext.AFTER_SHOW_NOTE: [
        "Tip: Edit this note with 'monoid edit <note_id>'",
        "Tip: See connected notes with 'monoid graph show <note_id>'",
    ],
    TipContext.AFTER_GRAPH_VIEW: [
        "Tip: Run 'monoid graph web' for interactive exploration",
        "Tip: Link more notes with [[note_id]] to build richer connections",
    ],
    TipContext.AFTER_AI_COMMAND: [
        "Tip: AI outputs are saved as separate notes - originals never change",
        "Tip: Use 'monoid ask' to query your notes with natural language",
        "Tip: Try 'monoid synth' to find patterns across multiple notes",
    ],
    TipContext.GENERAL: [
        "Tip: Use 'monoid help' to see organized command groups",
        "Tip: Disable tips with --no-tips flag",
        "Tip: Your notes are plain Markdown - edit them with any text editor",
    ],
}


class TipManager:
    """Manages contextual tip display with frequency control."""

    def __init__(self, show_frequency: float = 0.2):
        """
        Initialize tip manager.

        Args:
            show_frequency: Probability of showing a tip (0.0 to 1.0)
        """
        self.show_frequency = show_frequency
        self._shown_tips: set[str] = set()

    def get_tip(self, context: TipContext, force: bool = False) -> Optional[str]:
        """
        Get a contextual tip if conditions are met.

        Args:
            context: The context in which to show a tip
            force: If True, always return a tip (ignoring frequency)

        Returns:
            Tip string or None
        """
        # Check if we should show a tip based on frequency
        if not force and random.random() > self.show_frequency:
            return None

        # Get available tips for this context
        tips = TIPS.get(context, TIPS[TipContext.GENERAL])

        # Filter out already shown tips
        available_tips = [tip for tip in tips if tip not in self._shown_tips]

        # If all tips shown, reset and use all tips
        if not available_tips:
            self._shown_tips.clear()
            available_tips = tips

        # Select a random tip
        if available_tips:
            tip = random.choice(available_tips)
            self._shown_tips.add(tip)
            return tip

        return None

    def should_show_tip(self, context: TipContext, **kwargs: Any) -> bool:
        """
        Determine if a tip should be shown based on context and conditions.

        Args:
            context: The context to check
            **kwargs: Additional context-specific parameters

        Returns:
            True if a tip should be shown
        """
        # Context-specific logic
        if context == TipContext.AFTER_SEARCH_FEW_RESULTS:
            result_count: int = kwargs.get('result_count', 0)
            return bool(result_count < 3)

        if context == TipContext.AFTER_SEARCH_MANY_RESULTS:
            result_count = kwargs.get('result_count', 0)
            return bool(result_count > 20)

        if context == TipContext.AFTER_LIST_MANY_NOTES:
            note_count: int = kwargs.get('note_count', 0)
            return bool(note_count > 10)

        if context == TipContext.AFTER_FIRST_NOTE:
            note_count = kwargs.get('note_count', 0)
            return bool(note_count <= 3)

        # Default: show based on frequency
        return random.random() <= self.show_frequency


# Global tip manager instance
tip_manager = TipManager(show_frequency=0.2)
