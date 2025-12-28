from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import frontmatter

class NoteType(str, Enum):
    NOTE = "note"
    SUMMARY = "summary"
    SYNTHESIS = "synthesis"
    QUIZ = "quiz"
    TEMPLATE = "template"

class NoteTag(BaseModel):
    name: str
    source: str = "user" # 'user' or 'ai'
    confidence: float = 1.0

    def __hash__(self) -> int:
        return hash((self.name, self.source))

class NoteMetadata(BaseModel):
    id: str
    type: NoteType = NoteType.NOTE
    title: Optional[str] = None
    tags: List[NoteTag] = Field(default_factory=list)
    created: datetime = Field(default_factory=datetime.now)
    updated: Optional[datetime] = None
    links: List[str] = Field(default_factory=list) # Outgoing links (extracted or explicit)
    provenance: Optional[str] = None # ID of source note if derivative

    @field_validator("type", mode="before")
    def validate_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            return NoteType(v)
        return v
    
    @field_validator("tags", mode="before")
    def validate_tags(cls, v: Any) -> Any:
        # Handle migration from list of strings or legacy format
        if not v:
            return []
        parsed = []
        for item in v:
            if isinstance(item, str):
                parsed.append(NoteTag(name=item, source="user", confidence=1.0))
            elif isinstance(item, dict):
                parsed.append(NoteTag(**item))
            elif isinstance(item, NoteTag):
                parsed.append(item)
        return parsed

class Note(BaseModel):
    metadata: NoteMetadata
    content: str
    path: Optional[str] = None

    @property
    def filename(self) -> str:
        return f"{self.metadata.id}.md"

    def to_markdown(self) -> str:
        # Convert Pydantic model to dict for frontmatter
        data = self.metadata.model_dump(exclude_none=True, mode='json')
        # Simplify enums
        data['type'] = self.metadata.type.value
        
        post = frontmatter.Post(self.content, **data)
        return str(frontmatter.dumps(post))

    @classmethod
    def from_markdown(cls, content: str, path: Optional[str] = None) -> "Note":
        post = frontmatter.loads(content)
        # Ensure ID is present
        if 'id' not in post.metadata:
            pass
            
        # Handle legacy 'ai_tags' if present by merging them into tags
        if 'ai_tags' in post.metadata:
            ai_tags = post.metadata.pop('ai_tags', [])
            current_tags = post.metadata.get('tags', [])
            # If current_tags is none, make it list
            if current_tags is None:
                current_tags = []
            
            # Combine
            post.metadata['tags'] = current_tags + ai_tags

        metadata = NoteMetadata(**post.metadata)
        return cls(metadata=metadata, content=post.content, path=path)
