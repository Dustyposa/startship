-- Migration: Rebuild FTS5 table with unicode61 tokenizer
-- Date: 2025-01-18
-- Description: Add unicode61 tokenizer for better multi-language support (case-insensitive, diacritics removed)

-- Drop existing triggers
DROP TRIGGER IF EXISTS repositories_ai;
DROP TRIGGER IF EXISTS repositories_ad;
DROP TRIGGER IF EXISTS repositories_au;

-- Drop old FTS5 table
DROP TABLE IF EXISTS repositories_fts;

-- Recreate FTS5 table with unicode61 tokenizer
CREATE VIRTUAL TABLE repositories_fts USING fts5(
    name_with_owner,
    name,
    description,
    summary,
    content='repositories',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 1'
);

-- Rebuild FTS5 content from existing repositories
INSERT INTO repositories_fts(rowid, name_with_owner, name, description, summary)
SELECT rowid, name_with_owner, name, description, summary
FROM repositories;

-- Recreate triggers to keep FTS5 table in sync
CREATE TRIGGER IF NOT EXISTS repositories_ai AFTER INSERT ON repositories BEGIN
    INSERT INTO repositories_fts(rowid, name_with_owner, name, description, summary)
    VALUES (new.rowid, new.name_with_owner, new.name, new.description, new.summary);
END;

CREATE TRIGGER IF NOT EXISTS repositories_ad AFTER DELETE ON repositories BEGIN
    INSERT INTO repositories_fts(repositories_fts, rowid, name_with_owner, name, description, summary)
    VALUES ('delete', old.rowid, old.name_with_owner, old.name, old.description, old.summary);
END;

CREATE TRIGGER IF NOT EXISTS repositories_au AFTER UPDATE ON repositories BEGIN
    INSERT INTO repositories_fts(repositories_fts, rowid, name_with_owner, name, description, summary)
    VALUES ('delete', old.rowid, old.name_with_owner, old.name, old.description, old.summary);
    INSERT INTO repositories_fts(rowid, name_with_owner, name, description, summary)
    VALUES (new.rowid, new.name_with_owner, new.name, new.description, new.summary);
END;
