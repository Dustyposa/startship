-- Migration 005: Add sync fields and sync_history table
-- Adds support for data synchronization system

-- Add new fields to repositories table
ALTER TABLE repositories ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
ALTER TABLE repositories ADD COLUMN last_synced_at TIMESTAMP;
ALTER TABLE repositories ADD COLUMN last_analyzed_at TIMESTAMP;

-- Create sync_history table
CREATE TABLE IF NOT EXISTS sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,  -- 'full', 'incremental', 'manual'
    started_at TIMESTAMP NOT NULL DEFAULT (datetime('now')),
    completed_at TIMESTAMP,
    stats_added INTEGER DEFAULT 0,
    stats_updated INTEGER DEFAULT 0,
    stats_deleted INTEGER DEFAULT 0,
    stats_failed INTEGER DEFAULT 0,
    error_message TEXT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_repos_is_deleted ON repositories(is_deleted);
CREATE INDEX IF NOT EXISTS idx_repos_last_synced ON repositories(last_synced_at);
CREATE INDEX IF NOT EXISTS idx_sync_history_type ON sync_history(sync_type, started_at DESC);

-- Update existing repos: set last_synced_at to indexed_at for existing data
UPDATE repositories SET last_synced_at = indexed_at WHERE last_synced_at IS NULL;
