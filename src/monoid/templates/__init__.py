"""Template system for structured AI generation."""

from monoid.templates.registry import TemplateRegistry, Template
from monoid.templates.builtin import get_builtin_templates

# Global registry instance
registry = TemplateRegistry()

# Register built-in templates on import
for template in get_builtin_templates():
    registry.register(template)

__all__ = ["registry", "TemplateRegistry", "Template"]
