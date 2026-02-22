# Monoid Supabase Sync Setup

## Quick Start

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned

### 2. Run the Schema

1. Open your Supabase project dashboard
2. Go to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy the contents of `schema.sql` and paste it
5. Click **Run** (or press Cmd/Ctrl + Enter)

### 3. Get Your Credentials

1. Go to **Project Settings** > **API**
2. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public** key (under "Project API keys")

### 4. Configure Monoid

Set these environment variables:

```bash
# Required
export MONOID_SUPABASE_URL="https://your-project.supabase.co"
export MONOID_SUPABASE_KEY="your-anon-public-key"

# Optional: Enable auto-sync (syncs every 10 new notes)
export MONOID_SYNC_ENABLED="true"
export MONOID_AUTO_SYNC_THRESHOLD="10"  # default is 10
```

Add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) for persistence.

### 5. Migrate Existing Notes

```bash
# One-time migration of all local notes to Supabase
monoid db migrate
```

### 6. Start Syncing

```bash
# Check sync status
monoid db status

# Manual sync (bidirectional)
monoid db sync

# Force full sync (re-uploads everything)
monoid db sync --force

# Pull only (download new notes from web)
monoid db pull

# Push only (upload local changes)
monoid db push
```

## How It Works

### Sync Algorithm

1. **Push**: Local changes are uploaded to Supabase
2. **Pull**: Remote changes are downloaded to local
3. **Conflicts**: Resolved by "latest wins" (most recent `updated_at`)
4. **Embeddings**: Synced to pgvector for web semantic search

### Auto-Sync

When `MONOID_SYNC_ENABLED=true`:
- Every note create/edit is tracked
- After 10 new notes, sync runs silently in the background
- Threshold configurable via `MONOID_AUTO_SYNC_THRESHOLD`

### Data Stored

| Table | Contents |
|-------|----------|
| `notes` | Note content, metadata, timestamps |
| `tags` | User and AI-generated tags with confidence |
| `embeddings` | 384-dim vectors for semantic search |

## Troubleshooting

### "Supabase not configured"

Make sure both env vars are set:
```bash
echo $MONOID_SUPABASE_URL
echo $MONOID_SUPABASE_KEY
```

### "Failed to connect"

1. Check your Project URL is correct (includes `https://`)
2. Verify you're using the **anon/public** key (not the secret key)
3. Check Supabase project is active (not paused)

### Sync seems slow

The first sync uploads all embeddings which can take time. Subsequent syncs are incremental and much faster.
