'use client';

import { useEffect, useState, useRef } from 'react';
import { Note, NoteType } from '@/types/note';
import { getAllNotes, getNotesByType, searchNotes } from '@/lib/notes';
import { NoteCard } from '@/components/NoteCard';

const NOTE_TYPES: NoteType[] = ['note', 'summary', 'synthesis', 'quiz', 'template'];

export default function Home() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<NoteType | 'all'>('all');
  const [showContent, setShowContent] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadNotes();
  }, [typeFilter]);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 100) {
        setShowContent(true);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  async function loadNotes() {
    try {
      setLoading(true);
      setError(null);
      const data = typeFilter === 'all'
        ? await getAllNotes()
        : await getNotesByType(typeFilter);
      setNotes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notes');
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!search.trim()) {
      loadNotes();
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await searchNotes(search);
      setNotes(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  const scrollToContent = () => {
    contentRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowContent(true);
  };

  return (
    <>
      {/* Hero Section */}
      <section className="hero-gradient" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* Minimal Nav */}
        <nav style={{ padding: '24px 32px' }}>
          <div style={{ maxWidth: '1152px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-0.025em', color: 'var(--color-text)' }}>
              monoid
            </span>
            <a href="/new" className="btn-primary btn-small">
              Create Note
            </a>
          </div>
        </nav>

        {/* Hero Content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '0 32px', marginTop: '-80px' }}>
          <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
            <h1 className="animate-fade-in-up" style={{ fontSize: 'clamp(40px, 8vw, 72px)', fontWeight: 700, letterSpacing: '-0.025em', color: 'var(--color-text)', lineHeight: 1.1 }}>
              Your thoughts,
              <br />
              <span style={{ color: 'var(--color-text-muted)' }}>structured beautifully.</span>
            </h1>

            <p className="animate-fade-in-up stagger-1" style={{ opacity: 0, marginTop: '32px', fontSize: '20px', color: 'var(--color-text-secondary)', maxWidth: '560px', marginLeft: 'auto', marginRight: 'auto' }}>
              AI-enhanced notes that evolve with you. Capture ideas, synthesize knowledge, and let intelligence do the rest.
            </p>

            <div className="animate-fade-in-up stagger-2" style={{ opacity: 0, marginTop: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
              <button onClick={scrollToContent} className="btn-primary">
                View Your Notes
              </button>
              <a href="/new" className="btn-secondary">
                Start Writing
              </a>
            </div>

            {/* Feature Pills */}
            <div className="animate-fade-in-up stagger-3" style={{ opacity: 0, marginTop: '64px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
              {['AI Enhancement', 'Smart Synthesis', 'Quick Templates', 'Auto Summary'].map((feature) => (
                <span key={feature} className="feature-pill">
                  {feature}
                </span>
              ))}
            </div>
          </div>

          {/* Scroll Indicator */}
          <div className="animate-bounce-slow" style={{ position: 'absolute', bottom: '48px', left: '50%', transform: 'translateX(-50%)' }}>
            <button
              onClick={scrollToContent}
              style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Scroll</span>
              <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </button>
          </div>
        </div>
      </section>

      {/* Notes Section */}
      <section
        ref={contentRef}
        style={{
          minHeight: '100vh',
          backgroundColor: 'var(--color-bg-dark)',
          padding: '64px 32px',
          opacity: showContent ? 1 : 0,
          transition: 'opacity 0.7s ease'
        }}
      >
        <div style={{ maxWidth: '1152px', margin: '0 auto' }}>
          {/* Section Header */}
          <div className={showContent ? 'animate-fade-in-up' : ''} style={{ marginBottom: '48px' }}>
            <h2 style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-text)' }}>
              Notes
            </h2>
            <p style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>
              {notes.length} {notes.length === 1 ? 'note' : 'notes'} in your collection
            </p>
          </div>

          {/* Search and Filters */}
          <div style={{ marginBottom: '32px' }}>
            <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', maxWidth: '500px', marginBottom: '16px' }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <svg
                  style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', width: '20px', height: '20px', color: 'var(--color-text-muted)' }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search notes..."
                  className="search-input"
                />
              </div>
              <button type="submit" className="btn-primary btn-small">
                Search
              </button>
            </form>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button
                onClick={() => { setTypeFilter('all'); setSearch(''); }}
                className={`filter-btn ${typeFilter === 'all' ? 'active' : ''}`}
              >
                All
              </button>
              {NOTE_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => { setTypeFilter(type); setSearch(''); }}
                  className={`filter-btn ${typeFilter === type ? 'active' : ''}`}
                  style={{ textTransform: 'capitalize' }}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div style={{ marginBottom: '32px', padding: '16px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '12px', color: '#dc2626' }}>
              {error}
            </div>
          )}

          {/* Loading State */}
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '96px 0' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <div className="spinner" />
                <span style={{ color: 'var(--color-text-muted)' }}>Loading notes...</span>
              </div>
            </div>
          ) : notes.length === 0 ? (
            /* Empty State */
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '96px 0' }}>
              <div style={{ width: '80px', height: '80px', marginBottom: '24px', borderRadius: '50%', backgroundColor: 'var(--color-surface)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg
                  style={{ width: '40px', height: '40px', color: 'var(--color-text-muted)' }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--color-text)' }}>No notes yet</h3>
              <p style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>Create your first note to get started</p>
              <a href="/new" className="btn-primary" style={{ marginTop: '24px' }}>
                Create Note
              </a>
            </div>
          ) : (
            /* Notes Grid */
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
              {notes.map((note, index) => (
                <div
                  key={note.id}
                  className={showContent ? 'animate-scale-in' : ''}
                  style={{
                    opacity: showContent ? 1 : 0,
                    animationDelay: `${Math.min(index * 0.05, 0.3)}s`
                  }}
                >
                  <NoteCard note={note} />
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
