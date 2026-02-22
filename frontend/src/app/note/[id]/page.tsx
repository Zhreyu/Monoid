'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { Note, NoteType } from '@/types/note';
import { getNote, updateNote, updateNoteAfterEnhance, deleteNote } from '@/lib/notes';
import { formatDate, countTripleBrackets } from '@/lib/utils';

const NOTE_TYPES: NoteType[] = ['note', 'summary', 'synthesis', 'quiz', 'template'];

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function NotePage({ params }: PageProps) {
  const { id } = use(params);
  const router = useRouter();
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [enhancing, setEnhancing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [editType, setEditType] = useState<NoteType>('note');
  const [customPrompt, setCustomPrompt] = useState('');
  const [showPromptInput, setShowPromptInput] = useState(false);

  useEffect(() => {
    loadNote();
  }, [id]);

  async function loadNote() {
    try {
      setLoading(true);
      setError(null);
      const data = await getNote(id);
      if (!data) {
        setError('Note not found');
        return;
      }
      setNote(data);
      setEditContent(data.content);
      setEditTitle(data.title || '');
      setEditType(data.type);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load note');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!note) return;
    try {
      setSaving(true);
      setError(null);
      const updated = await updateNote(note.id, {
        content: editContent,
        title: editTitle || undefined,
        type: editType,
      });
      setNote(updated);
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save note');
    } finally {
      setSaving(false);
    }
  }

  async function handleEnhance() {
    if (!note) return;
    try {
      setEnhancing(true);
      setError(null);

      const response = await fetch('/api/enhance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: editContent || note.content,
          prompt: customPrompt || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Enhancement failed');
      }

      const { enhanced } = await response.json();
      const updated = await updateNoteAfterEnhance(note.id, enhanced);
      setNote(updated);
      setEditContent(enhanced);
      setShowPromptInput(false);
      setCustomPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Enhancement failed');
    } finally {
      setEnhancing(false);
    }
  }

  async function handleDelete() {
    if (!note) return;
    if (!confirm('Delete this note?')) return;
    try {
      await deleteNote(note.id);
      router.push('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete note');
    }
  }

  function highlightBrackets(content: string): string {
    return content.replace(
      /(\{\{\{.*?\}\}\})/gs,
      '<span class="triple-bracket">$1</span>'
    );
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div className="spinner" />
          <span style={{ color: 'var(--color-text-muted)' }}>Loading note...</span>
        </div>
      </div>
    );
  }

  if (error && !note) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '64px', height: '64px', margin: '0 auto 16px', borderRadius: '50%', backgroundColor: '#fef2f2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg style={{ width: '32px', height: '32px', color: '#ef4444' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p style={{ color: '#dc2626', marginBottom: '16px', fontWeight: 500 }}>{error}</p>
          <a href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
            <svg style={{ width: '20px', height: '20px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to notes
          </a>
        </div>
      </div>
    );
  }

  if (!note) return null;

  const bracketCount = countTripleBrackets(isEditing ? editContent : note.content);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg)' }}>
      {/* Nav */}
      <nav style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ maxWidth: '768px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <a href="/" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}>
            <svg style={{ width: '20px', height: '20px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back</span>
          </a>
          <span style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text)' }}>monoid</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {!isEditing ? (
              <>
                <button onClick={() => setIsEditing(true)} className="btn-secondary btn-small">
                  Edit
                </button>
                <button
                  onClick={handleDelete}
                  style={{ padding: '8px 16px', fontSize: '14px', fontWeight: 500, color: '#dc2626', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '9999px', cursor: 'pointer' }}
                >
                  Delete
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditContent(note.content);
                    setEditTitle(note.title || '');
                    setEditType(note.type);
                  }}
                  className="btn-secondary btn-small"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="btn-primary btn-small"
                  style={{ opacity: saving ? 0.5 : 1 }}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Content */}
      <main style={{ maxWidth: '768px', margin: '0 auto', padding: '48px 32px' }}>
        {error && (
          <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#dc2626' }}>
            {error}
          </div>
        )}

        {/* Meta Info */}
        <div style={{ marginBottom: '32px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px' }}>
          {isEditing ? (
            <select
              value={editType}
              onChange={(e) => setEditType(e.target.value as NoteType)}
              className={`type-badge type-${editType}`}
              style={{ padding: '6px 12px', borderRadius: '9999px', border: '2px solid', cursor: 'pointer', fontWeight: 500 }}
            >
              {NOTE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          ) : (
            <span className={`type-badge type-${note.type}`}>{note.type}</span>
          )}
          <span style={{ color: 'var(--color-text-muted)' }}>·</span>
          <span style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>{formatDate(note.created_at)}</span>
          {note.enhanced > 0 && (
            <>
              <span style={{ color: 'var(--color-text-muted)' }}>·</span>
              <span style={{ padding: '4px 10px', fontSize: '12px', fontWeight: 500, backgroundColor: 'var(--color-accent-light)', color: 'var(--color-accent)', borderRadius: '9999px' }}>
                AI enhanced x{note.enhanced}
              </span>
            </>
          )}
        </div>

        {/* Title */}
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            placeholder="Title (optional)"
            style={{
              width: '100%',
              marginBottom: '24px',
              padding: '12px 16px',
              fontSize: '24px',
              fontWeight: 600,
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              color: 'var(--color-text)',
            }}
          />
        ) : note.title && (
          <h1 style={{ marginBottom: '24px', fontSize: '32px', fontWeight: 700, color: 'var(--color-text)' }}>{note.title}</h1>
        )}

        {/* Content */}
        {isEditing ? (
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            placeholder="Write your note..."
            style={{
              width: '100%',
              height: '384px',
              padding: '20px',
              fontSize: '14px',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
              lineHeight: 1.6,
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              color: 'var(--color-text)',
              resize: 'vertical',
            }}
          />
        ) : (
          <div
            style={{
              padding: '24px',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: '12px',
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
              fontSize: '14px',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
            }}
            dangerouslySetInnerHTML={{ __html: highlightBrackets(note.content) }}
          />
        )}

        {/* Enhancement Section */}
        <div style={{ marginTop: '32px', padding: '24px', backgroundColor: 'var(--color-bg-dark)', borderRadius: '12px', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h3 style={{ fontWeight: 600, color: 'var(--color-text)' }}>AI Enhancement</h3>
              {bracketCount > 0 ? (
                <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>
                  {bracketCount} filler prompt{bracketCount > 1 ? 's' : ''} ready to expand
                </p>
              ) : (
                <p style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>
                  Improve prose, fix grammar, or add context
                </p>
              )}
            </div>

            {showPromptInput ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Additional instructions..."
                  style={{
                    width: '200px',
                    padding: '10px 16px',
                    fontSize: '14px',
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: '9999px',
                    color: 'var(--color-text)',
                  }}
                />
                <button onClick={() => setShowPromptInput(false)} className="btn-secondary btn-small">
                  Cancel
                </button>
                <button
                  onClick={handleEnhance}
                  disabled={enhancing}
                  style={{
                    padding: '10px 24px',
                    fontSize: '14px',
                    fontWeight: 500,
                    backgroundColor: 'var(--color-accent)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    cursor: 'pointer',
                    opacity: enhancing ? 0.5 : 1,
                  }}
                >
                  {enhancing ? 'Enhancing...' : 'Enhance'}
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button onClick={() => setShowPromptInput(true)} className="btn-secondary btn-small">
                  + Custom prompt
                </button>
                <button
                  onClick={handleEnhance}
                  disabled={enhancing}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px 24px',
                    fontSize: '14px',
                    fontWeight: 500,
                    backgroundColor: 'var(--color-accent)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '9999px',
                    cursor: 'pointer',
                    opacity: enhancing ? 0.5 : 1,
                  }}
                >
                  {enhancing ? (
                    <>
                      <div style={{ width: '16px', height: '16px', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                      Enhancing...
                    </>
                  ) : (
                    <>
                      <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      Enhance
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Note ID */}
        <div style={{ marginTop: '32px', textAlign: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>{note.id}</span>
        </div>
      </main>
    </div>
  );
}
