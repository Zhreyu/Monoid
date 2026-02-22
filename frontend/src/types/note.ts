export type NoteType = 'note' | 'summary' | 'synthesis' | 'quiz' | 'template';

export interface Note {
  id: string;
  type: NoteType;
  title: string | null;
  content: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  version: number;
  checksum: string;
  links: string[];
  provenance: string | null;
  enhanced: number;
}

export interface NoteCreate {
  title?: string;
  content: string;
  type?: NoteType;
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  type?: NoteType;
}
