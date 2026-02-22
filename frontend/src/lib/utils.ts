/**
 * Generate a timestamp-based note ID matching the CLI format
 * Format: YYYYMMDDhhmmss (e.g., 20250103142530)
 */
export function generateNoteId(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${year}${month}${day}${hours}${minutes}${seconds}`;
}

/**
 * Compute SHA256 checksum of content (first 32 chars)
 * Matches the CLI implementation
 */
export async function computeChecksum(content: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(content);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex.slice(0, 32);
}

/**
 * Count triple bracket blocks in content
 */
export function countTripleBrackets(content: string): number {
  const matches = content.match(/\{\{\{.*?\}\}\}/gs);
  return matches ? matches.length : 0;
}

/**
 * Extract triple bracket commands from content
 */
export function extractTripleBrackets(content: string): string[] {
  const matches = content.match(/\{\{\{(.*?)\}\}\}/gs);
  return matches ? matches.map(m => m.slice(3, -3).trim()) : [];
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format relative time
 */
export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

/**
 * Get first line as title fallback
 */
export function getFirstLine(content: string): string {
  const firstLine = content.split('\n')[0].trim();
  // Remove markdown heading syntax
  return firstLine.replace(/^#+\s*/, '');
}

/**
 * Get content preview (first few lines, stripped of markdown)
 */
export function getContentPreview(content: string, maxLength: number = 150): string {
  const stripped = content
    .replace(/^#+\s*/gm, '') // Remove headings
    .replace(/\*\*|__/g, '') // Remove bold
    .replace(/\*|_/g, '') // Remove italic
    .replace(/`{1,3}[^`]*`{1,3}/g, '') // Remove code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to text
    .replace(/\n+/g, ' ') // Replace newlines with spaces
    .trim();
  return truncate(stripped, maxLength);
}
