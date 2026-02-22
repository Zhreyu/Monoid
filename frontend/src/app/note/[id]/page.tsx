import NotePageClient from './NotePageClient';

export function generateStaticParams() {
  // Return a placeholder to satisfy static export requirement
  // The actual note loading happens client-side
  return [{ id: '_' }];
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function NotePage({ params }: PageProps) {
  const { id } = await params;
  return <NotePageClient id={id} />;
}
