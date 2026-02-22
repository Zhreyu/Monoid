'use client';

import { useEffect, useState } from 'react';

export default function NotFound() {
  const [shouldShow, setShouldShow] = useState(false);

  useEffect(() => {
    // GitHub Pages SPA redirect for dynamic routes
    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
    const path = window.location.pathname.replace(basePath, '');

    // If this is a note page, redirect to home with path param
    if (path.startsWith('/note/') && path !== '/note/_') {
      const redirectUrl = basePath + '/?p=' + encodeURIComponent(path);
      window.location.replace(redirectUrl);
      return;
    }

    // Otherwise show the 404 page
    setShouldShow(true);
  }, []);

  if (!shouldShow) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--color-bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'var(--color-bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '48px', fontWeight: 700, color: 'var(--color-text)', marginBottom: '16px' }}>
          404
        </h1>
        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '24px' }}>
          Page not found
        </p>
        <a
          href="/"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            backgroundColor: 'var(--color-accent)',
            color: 'white',
            borderRadius: '9999px',
            textDecoration: 'none',
            fontWeight: 500
          }}
        >
          Go home
        </a>
      </div>
    </div>
  );
}
