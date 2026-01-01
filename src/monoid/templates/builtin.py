"""Built-in templates for common note patterns."""

from typing import List
from monoid.templates.registry import Template


def get_builtin_templates() -> List[Template]:
    """Get all built-in templates."""
    return [
        Template(
            name="dsa-pattern",
            description="Data Structures & Algorithms pattern documentation",
            structure={
                "Pattern Name": "Clear, descriptive name for the pattern",
                "When to Use": "Scenarios and problem characteristics where this pattern applies",
                "Approach": "High-level strategy and key insights (not step-by-step code)",
                "Time Complexity": "Big-O analysis",
                "Space Complexity": "Big-O analysis",
                "Key Insights": "Core algorithmic insights and intuitions",
                "Example Problems": "Classic problems that use this pattern",
                "Related Patterns": "Similar or complementary patterns",
            },
            system_prompt="""You are an expert computer scientist specializing in algorithmic thinking and pattern recognition.

Your task is to analyze the provided content and extract a DSA pattern note. Focus on:
- The PATTERN itself, not individual problem solutions
- WHY the pattern works (intuition and insight)
- WHEN to recognize it (problem characteristics)
- Abstract strategy, not implementation details

Avoid:
- Line-by-line code explanations
- Problem-specific details that don't generalize
- Verbose descriptions without insight"""
        ),

        Template(
            name="architecture",
            description="Software architecture pattern documentation",
            structure={
                "Pattern Name": "Name of the architectural pattern",
                "Context": "When and where this pattern is relevant",
                "Problem": "What problem does this pattern solve?",
                "Solution": "How does the pattern solve it? (structure and behavior)",
                "Trade-offs": "Benefits and drawbacks",
                "Key Components": "Main architectural elements",
                "Examples": "Real-world systems or scenarios using this pattern",
                "Variations": "Common variants or related patterns",
            },
            system_prompt="""You are a software architect with deep expertise in system design patterns.

Your task is to analyze the provided content and extract an architectural pattern note. Focus on:
- The PATTERN'S essence and rationale
- Trade-offs and decision factors
- When and why to use this pattern
- Structural relationships, not code

Avoid:
- Implementation details or specific technologies
- Excessive detail about one example
- Surface-level descriptions without insight"""
        ),

        Template(
            name="concept",
            description="Learning and knowledge concept documentation",
            structure={
                "Concept": "Clear name for the concept",
                "Definition": "Precise, concise definition",
                "Key Points": "3-5 most important things to understand",
                "Examples": "Concrete examples that illustrate the concept",
                "Analogies": "Helpful mental models or analogies (if applicable)",
                "Common Misconceptions": "What people often get wrong",
                "Connections": "How this relates to other concepts",
                "Questions for Deeper Understanding": "Thought-provoking questions",
            },
            system_prompt="""You are an expert educator skilled at distilling complex concepts into clear, memorable explanations.

Your task is to analyze the provided content and extract a concept note. Focus on:
- CLARITY over completeness
- Mental models and intuition
- What makes this concept click
- Connections to other ideas

Avoid:
- Lengthy definitions copied verbatim
- Lists of facts without synthesis
- Jargon without explanation"""
        ),

        Template(
            name="decision",
            description="Decision framework and rationale documentation",
            structure={
                "Decision Context": "What decision needs to be made and why",
                "Options Considered": "Alternatives that were evaluated",
                "Decision Criteria": "What factors matter and how to weigh them",
                "Recommendation": "What decision to make",
                "Rationale": "Why this decision makes sense given the criteria",
                "Risks and Mitigations": "What could go wrong and how to handle it",
                "Reversibility": "How easy is it to change this decision later?",
            },
            system_prompt="""You are a strategic thinker skilled at decision analysis and documentation.

Your task is to analyze the provided content and extract a decision framework note. Focus on:
- The STRUCTURE of the decision (criteria, trade-offs)
- Clear rationale that others can understand
- Risk awareness
- Making the decision repeatable

Avoid:
- Personal opinions without justification
- Missing context or criteria
- One-sided arguments"""
        ),

        Template(
            name="retrospective",
            description="Reflection and retrospective documentation",
            structure={
                "What Happened": "Brief summary of the event/project/period",
                "What Went Well": "Successes and positive outcomes",
                "What Didn't Go Well": "Challenges and failures",
                "Key Learnings": "Insights and takeaways",
                "Root Causes": "Deeper analysis of why things happened",
                "Action Items": "Specific, concrete things to do differently",
                "Questions": "Open questions or areas for further exploration",
            },
            system_prompt="""You are a reflective practitioner skilled at extracting lessons from experience.

Your task is to analyze the provided content and extract a retrospective note. Focus on:
- PATTERNS and root causes, not just symptoms
- Actionable insights
- Honest assessment (both good and bad)
- Learning mindset

Avoid:
- Blame or defensiveness
- Surface-level observations
- Vague action items"""
        ),
    ]
