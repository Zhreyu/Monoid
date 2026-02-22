'use client';

import { Note } from '@/types/note';
import { formatRelativeTime, getFirstLine, getContentPreview, countTripleBrackets } from '@/lib/utils';

interface NoteCardProps {
  note: Note;
}

export function NoteCard({ note }: NoteCardProps) {
  const title = note.title || getFirstLine(note.content) || 'Untitled';
  const preview = getContentPreview(note.content);
  const bracketCount = countTripleBrackets(note.content);

  return (
    <a href={`/note/${note.id}`} className={`note-card type-${note.type}`}>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', marginBottom: '12px' }}>
          <span className={`type-badge type-${note.type}`}>
            {note.type}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {bracketCount > 0 && (
              <span style={{ padding: '2px 8px', fontSize: '12px', fontFamily: 'monospace', backgroundColor: 'rgba(255,255,255,0.6)', border: '1px dashed #d1d5db', borderRadius: '4px' }}>
                {'{{{'}{bracketCount}
              </span>
            )}
            {note.enhanced > 0 && (
              <span style={{ padding: '2px 8px', fontSize: '12px', color: '#6b7280', backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: '4px' }}>
                AI x{note.enhanced}
              </span>
            )}
          </div>
        </div>

        {/* Title */}
        <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-text)', lineHeight: 1.4, marginBottom: '8px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
          {title}
        </h3>

        {/* Preview */}
        {preview && (
          <p style={{ flex: 1, fontSize: '14px', color: 'var(--color-text-secondary)', lineHeight: 1.5, marginBottom: '16px', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {preview}
          </p>
        )}

        {/* Footer */}
        <div style={{ marginTop: 'auto', paddingTop: '12px', borderTop: '1px solid rgba(0,0,0,0.05)' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
            {formatRelativeTime(note.updated_at || note.created_at)}
          </span>
        </div>
      </div>
    </a>
  );
}
