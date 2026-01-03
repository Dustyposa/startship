-- Migration 002: Add network_cache table
-- This table stores cached network graph data to avoid recomputation

CREATE TABLE IF NOT EXISTS network_cache (
    id INTEGER PRIMARY KEY,
    nodes TEXT NOT NULL,
    edges TEXT NOT NULL,
    top_n INTEGER DEFAULT 100,
    k INTEGER DEFAULT 5,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on updated_at for efficient cache invalidation queries
CREATE INDEX IF NOT EXISTS idx_network_updated ON network_cache(updated_at);
