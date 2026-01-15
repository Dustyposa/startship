-- Migration 003: Add user data tables for collections, tags, notes
-- This migration adds tables to store user-generated data like collections, tags, and notes

-- ============================================
-- Collections table (user folders)
-- ============================================
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    icon TEXT,
    color TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================
-- Tags table
-- ============================================
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT NOT NULL DEFAULT '#3B82F6',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================
-- Repository-Collection association table
-- ============================================
CREATE TABLE IF NOT EXISTS repo_collections (
    repo_id TEXT NOT NULL,
    collection_id TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (repo_id, collection_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
);

-- ============================================
-- Repository-Tag association table
-- ============================================
CREATE TABLE IF NOT EXISTS repo_tags (
    repo_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (repo_id, tag_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- ============================================
-- Notes and Ratings table
-- ============================================
CREATE TABLE IF NOT EXISTS notes (
    repo_id TEXT PRIMARY KEY,
    note TEXT,
    rating INTEGER DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (repo_id) REFERENCES repositories(name_with_owner) ON DELETE CASCADE
);

-- ============================================
-- User Settings table
-- ============================================
CREATE TABLE IF NOT EXISTS user_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_collections_position ON collections(position);
CREATE INDEX IF NOT EXISTS idx_collections_updated_at ON collections(updated_at);

CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_color ON tags(color);

CREATE INDEX IF NOT EXISTS idx_repo_collections_repo_id ON repo_collections(repo_id);
CREATE INDEX IF NOT EXISTS idx_repo_collections_collection_id ON repo_collections(collection_id);
CREATE INDEX IF NOT EXISTS idx_repo_collections_position ON repo_collections(position);

CREATE INDEX IF NOT EXISTS idx_repo_tags_repo_id ON repo_tags(repo_id);
CREATE INDEX IF NOT EXISTS idx_repo_tags_tag_id ON repo_tags(tag_id);

CREATE INDEX IF NOT EXISTS idx_notes_rating ON notes(rating);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at);

-- ============================================
-- Triggers to update timestamps
-- ============================================
CREATE TRIGGER IF NOT EXISTS update_collections_timestamp
AFTER UPDATE ON collections
FOR EACH ROW
BEGIN
    UPDATE collections SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_tags_timestamp
AFTER UPDATE ON tags
FOR EACH ROW
BEGIN
    UPDATE tags SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_notes_timestamp
AFTER UPDATE ON notes
FOR EACH ROW
BEGIN
    UPDATE notes SET updated_at = datetime('now') WHERE repo_id = NEW.repo_id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_settings_timestamp
AFTER UPDATE ON user_settings
FOR EACH ROW
BEGIN
    UPDATE user_settings SET updated_at = datetime('now') WHERE key = NEW.key;
END;
