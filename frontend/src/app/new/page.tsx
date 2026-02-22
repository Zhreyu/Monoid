'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { NoteType } from '@/types/note';
import { createNote } from '@/lib/notes';

const NOTE_TYPES: NoteType[] = ['note', 'summary', 'synthesis', 'quiz', 'template'];

export default function NewNotePage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [type, setType] = useState<NoteType>('note');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) {
      setError('Content is required');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const note = await createNote({
        title: title.trim() || undefined,
        content: content.trim(),
        type,
      });
      router.push(`/note/${note.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create note');
      setSaving(false);
    }
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--color-bg)' }}>
      {/* Nav */}
      <nav style={{ padding: '24px 32px', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ maxWidth: '768px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <a
            href="/"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)' }}
          >
            <svg style={{ width: '20px', height: '20px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            <span>Back</span>
          </a>
          <span style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text)' }}>monoid</span>
          <div style={{ width: '64px' }} />
        </div>
      </nav>

      {/* Content */}
      <main style={{ maxWidth: '768px', margin: '0 auto', padding: '48px 32px' }}>
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-text)' }}>Create Note</h1>
          <p style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>
            Start with a blank canvas or use filler prompts for AI expansion
          </p>
        </div>

        {error && (
          <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#dc2626' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Title and Type Row */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Title (optional)"
              style={{
                flex: 1,
                padding: '12px 16px',
                fontSize: '16px',
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: '12px',
                color: 'var(--color-text)',
              }}
            />
            <select
              value={type}
              onChange={(e) => setType(e.target.value as NoteType)}
              className={`type-badge type-${type}`}
              style={{
                padding: '12px 16px',
                fontSize: '14px',
                borderRadius: '12px',
                border: '2px solid',
                cursor: 'pointer',
                fontWeight: 500,
              }}
            >
              {NOTE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Content */}
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your note... use {{{ }}} for AI filler prompts"
            style={{
              width: '100%',
              height: '320px',
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
            autoFocus
          />

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
            <button
              type="button"
              onClick={() => router.push('/')}
              className="btn-secondary btn-small"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !content.trim()}
              className="btn-primary"
              style={{ opacity: saving || !content.trim() ? 0.5 : 1 }}
            >
              {saving ? 'Creating...' : 'Create Note'}
            </button>
          </div>
        </form>

        {/* Help Card */}
        <div style={{ marginTop: '48px', padding: '24px', backgroundColor: 'var(--color-accent-light)', border: '1px solid #bfdbfe', borderRadius: '16px' }}>
          <h3 style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: '8px' }}>Pro tip: Use filler prompts</h3>
          <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
            Wrap any placeholder text with triple brackets, then use the enhance button to expand them with AI.
          </p>
          <code style={{ display: 'block', padding: '12px', backgroundColor: 'rgba(255,255,255,0.5)', borderRadius: '8px', fontSize: '14px', fontFamily: 'monospace', color: 'var(--color-text)' }}>
            {'{{{'} explain binary search intuition {'}}}'}
          </code>
        </div>
      </main>
    </div>
  );
}
