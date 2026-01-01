from openai import OpenAI
import json
from typing import List
from monoid.config import config
from monoid.intelligence.provider import AIProvider
from monoid.core.domain import Note, NoteTag

class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        if not config.openai_key:
            raise ValueError("OpenAI API key not found. Set MONOID_OPENAI_KEY or OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=config.openai_key)
        self.model = "gpt-4o-mini" # Cost effective

    def summarize(self, content: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes notes. Output concise markdown."},
                {"role": "user", "content": f"Summarize the following note:\n\n{content}"}
            ]
        )
        return str(response.choices[0].message.content or "")

    def ask(self, context: str, question: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer the user's question based strictly on the provided context. If the answer is not in the context, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
        )
        return str(response.choices[0].message.content or "")

    def synthesize(self, notes: List[Note], topic: str) -> str:
        context = "\n---\n".join([f"Note {n.metadata.id}:\n{n.content}" for n in notes])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Synthesize the provided notes into a cohesive, well-structured document on the given topic. Use headers and bullet points. Output markdown."},
                {"role": "user", "content": f"Topic: {topic}\n\nNotes:\n{context}"}
            ]
        )
        return str(response.choices[0].message.content or "")

    def generate_quiz(self, notes: List[Note]) -> str:
        context = "\n---\n".join([f"Note {n.metadata.id}:\n{n.content}" for n in notes])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a tutor. Generate a quiz with questions and answers based on the notes. Output markdown with Q: and A: sections."},
                {"role": "user", "content": f"Notes:\n{context}"}
            ]
        )
        return str(response.choices[0].message.content or "")

    def suggest_tags(self, content: str) -> List[NoteTag]:
        # Use simple JSON mode for structured output
        prompt = f"""
        Analyze the following text and suggest 3-5 semantic tags. 
        Return a JSON object with a key 'tags' containing a list of objects, each with 'name' (str) and 'confidence' (float 0-1).
        
        Text:
        {content[:2000]}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a semantic tagger. Output valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            data = json.loads(response.choices[0].message.content or "{}")
            tags = []
            for item in data.get("tags", []):
                tags.append(NoteTag(
                    name=item['name'].lower().replace(' ', '-'),
                    source="ai",
                    confidence=item.get('confidence', 0.8)
                ))
            return tags
        except Exception as e:
            print(f"Error parsing AI tags: {e}")
            return []

    def generate_from_template(self, content: str, template_name: str) -> str:
        """Generate structured content using a template."""
        from monoid.templates import registry

        template = registry.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        prompt = template.format_prompt(content)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": template.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return str(response.choices[0].message.content or "")
