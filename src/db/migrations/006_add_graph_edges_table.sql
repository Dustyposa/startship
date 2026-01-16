-- Migration 006: Add graph edges and status tables
-- This migration adds tables to store repository relationships and graph computation status

-- ============================================
-- Graph Edges table (repository relationships)
-- ============================================
CREATE TABLE IF NOT EXISTS graph_edges (
    source_repo TEXT NOT NULL,
    target_repo TEXT NOT NULL,
    edge_type TEXT NOT NULL CHECK(edge_type IN ('author', 'dependency', 'ecosystem', 'collection')),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0 AND weight <= 1),
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (source_repo, target_repo, edge_type),
    FOREIGN KEY (source_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE,
    FOREIGN KEY (target_repo) REFERENCES repositories(name_with_owner) ON DELETE CASCADE
);

-- ============================================
-- Graph Status table (computation tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS graph_status (
    repo_id INTEGER PRIMARY KEY,
    edges_computed_at TEXT,
    dependencies_parsed_at TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_repo, weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type, weight DESC);

-- ============================================
-- Triggers to update timestamps
-- ============================================
CREATE TRIGGER IF NOT EXISTS update_edges_timestamp
AFTER UPDATE ON graph_edges
FOR EACH ROW
BEGIN
    UPDATE graph_edges SET updated_at = datetime('now')
    WHERE source_repo = NEW.source_repo
      AND target_repo = NEW.target_repo
      AND edge_type = NEW.edge_type;
END;
