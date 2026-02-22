import { getSupabase } from './supabase';
import { Note, NoteCreate, NoteType } from '@/types/note';
import { generateNoteId, computeChecksum } from './utils';

/**
 * Fetch all notes (excluding soft-deleted)
 */
export async function getAllNotes(): Promise<Note[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('notes')
    .select('*')
    .is('deleted_at', null)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data || [];
}

/**
 * Fetch notes by type
 */
export async function getNotesByType(type: NoteType): Promise<Note[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('notes')
    .select('*')
    .eq('type', type)
    .is('deleted_at', null)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data || [];
}

/**
 * Fetch a single note by ID
 */
export async function getNote(id: string): Promise<Note | null> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('notes')
    .select('*')
    .eq('id', id)
    .is('deleted_at', null)
    .single();

  if (error) {
    if (error.code === 'PGRST116') return null; // Not found
    throw error;
  }
  return data;
}

/**
 * Create a new note
 */
export async function createNote(input: NoteCreate): Promise<Note> {
  const supabase = getSupabase();
  const id = generateNoteId();
  const now = new Date().toISOString();
  const checksum = await computeChecksum(input.content);

  const note: Note = {
    id,
    type: input.type || 'note',
    title: input.title || null,
    content: input.content,
    created_at: now,
    updated_at: now,
    deleted_at: null,
    version: 1,
    checksum,
    links: [],
    provenance: null,
    enhanced: 0,
  };

  const { data, error } = await supabase
    .from('notes')
    .insert(note)
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Update an existing note
 */
export async function updateNote(
  id: string,
  updates: { title?: string; content?: string; type?: NoteType }
): Promise<Note> {
  const supabase = getSupabase();
  const now = new Date().toISOString();
  const updateData: Record<string, unknown> = {
    ...updates,
    updated_at: now,
  };

  // Recompute checksum if content changed
  if (updates.content) {
    updateData.checksum = await computeChecksum(updates.content);
  }

  const { data, error } = await supabase
    .from('notes')
    .update(updateData)
    .eq('id', id)
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Update note after enhancement
 */
export async function updateNoteAfterEnhance(
  id: string,
  content: string
): Promise<Note> {
  const supabase = getSupabase();
  const now = new Date().toISOString();
  const checksum = await computeChecksum(content);

  // First get current enhanced count
  const { data: current } = await supabase
    .from('notes')
    .select('enhanced')
    .eq('id', id)
    .single();

  const enhanced = (current?.enhanced || 0) + 1;

  const { data, error } = await supabase
    .from('notes')
    .update({
      content,
      updated_at: now,
      checksum,
      enhanced,
    })
    .eq('id', id)
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Soft delete a note
 */
export async function deleteNote(id: string): Promise<void> {
  const supabase = getSupabase();
  const now = new Date().toISOString();

  const { error } = await supabase
    .from('notes')
    .update({ deleted_at: now })
    .eq('id', id);

  if (error) throw error;
}

/**
 * Search notes by content or title
 */
export async function searchNotes(query: string): Promise<Note[]> {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from('notes')
    .select('*')
    .is('deleted_at', null)
    .or(`title.ilike.%${query}%,content.ilike.%${query}%`)
    .order('updated_at', { ascending: false });

  if (error) throw error;
  return data || [];
}
