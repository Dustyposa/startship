-- Migration 009: Add semantic edge type support
-- This migration adds 'semantic' to the allowed edge types in graph_edges table

-- Recreate the table with semantic edge type support
CREATE TABLE IF NOT EXISTS graph_edges_new (
    source_repo TEXT NOT NULL,
    target_repo TEXT NOT NULL,
    edge_type TEXT NOT NULL CHECK(edge_type IN ('author', 'dependency', 'ecosystem', 'collection', 'semantic')),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0 AND weight <= 1),
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source_repo, target_repo, edge_type),
    FOREIGN KEY (source_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE,
    FOREIGN KEY (target_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE
);

-- Migrate existing data
INSERT INTO graph_edges_new (source_repo, target_repo, edge_type, weight, metadata, created_at, updated_at)
SELECT source_repo, target_repo, edge_type, weight, metadata, created_at, updated_at
FROM graph_edges;

-- Drop old table and rename new one
DROP TABLE graph_edges;
ALTER TABLE graph_edges_new RENAME TO graph_edges;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type, weight DESC);

-- Recreate trigger
CREATE TRIGGER IF NOT EXISTS update_edges_timestamp
AFTER UPDATE ON graph_edges
FOR EACH ROW
BEGIN
    UPDATE graph_edges SET updated_at = datetime('now')
    WHERE source_repo = NEW.source_repo
      AND target_repo = NEW.target_repo
      AND edge_type = NEW.edge_type;
END;
