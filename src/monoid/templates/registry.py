"""Template registry for managing AI generation templates."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class Template(BaseModel):
    """A template for structured AI generation."""

    name: str
    description: str
    structure: Dict[str, str]  # Field name -> description
    system_prompt: str

    def format_prompt(self, content: str) -> str:
        """Format the template prompt with the given content."""
        structure_desc = "\n".join([
            f"- **{field}**: {desc}"
            for field, desc in self.structure.items()
        ])

        return f"""{self.system_prompt}

**Expected Structure:**
{structure_desc}

**Source Content:**
{content}

Please generate a well-structured note following the template structure above. Focus on extracting patterns, abstractions, and key insights rather than simply dumping information."""


class TemplateRegistry:
    """Registry for managing templates."""

    def __init__(self) -> None:
        self._templates: Dict[str, Template] = {}

    def register(self, template: Template) -> None:
        """Register a template."""
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        return self._templates.get(name)

    def list(self) -> List[Template]:
        """List all registered templates."""
        return list(self._templates.values())

    def exists(self, name: str) -> bool:
        """Check if a template exists."""
        return name in self._templates
