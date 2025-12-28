-- ============================================
-- GitHub Star RAG Service - SQLite Schema
-- ============================================

-- ============================================
-- Repositories table
-- ============================================
CREATE TABLE IF NOT EXISTS repositories (
    -- Primary key
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Basic information
    name_with_owner TEXT UNIQUE NOT NULL,  -- Format: "owner/repo"
    name TEXT NOT NULL,
    owner TEXT NOT NULL,

    -- Metadata from GitHub
    description TEXT,
    primary_language TEXT,
    languages TEXT,                      -- JSON array: ["Python": 80, "JS": 20]
    topics TEXT,                         -- JSON array: ["web", "api"]
    stargazer_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    url TEXT,
    homepage_url TEXT,

    -- LLM analysis results
    summary TEXT,                        -- One-line summary
    categories TEXT,                     -- JSON array: ["工具", "前端"]
    features TEXT,                       -- JSON array of features
    tech_stack TEXT,                     -- JSON array of technologies
    use_cases TEXT,                      -- JSON array of use cases
    readme_summary TEXT,                 -- Summary of README

    -- README storage
    readme_path TEXT,                    -- Path to README file
    readme_content TEXT,                 -- Cached README content (optional)

    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    indexed_at TEXT DEFAULT (datetime('now')),

    -- Full-text search
    search_text TEXT                     -- Combined text for FTS
);

-- ============================================
-- Repository categories (many-to-many)
-- ============================================
CREATE TABLE IF NOT EXISTS repo_categories (
    repo_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (repo_id, category),
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- ============================================
-- Repository tech stack (many-to-many)
-- ============================================
CREATE TABLE IF NOT EXISTS repo_tech_stack (
    repo_id INTEGER NOT NULL,
    tech TEXT NOT NULL,
    PRIMARY KEY (repo_id, tech),
    FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
);

-- ============================================
-- Conversations (chat sessions)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================
-- Messages (within conversations)
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,                  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_repos_name_with_owner ON repositories(name_with_owner);
CREATE INDEX IF NOT EXISTS idx_repos_language ON repositories(primary_language);
CREATE INDEX IF NOT EXISTS idx_repos_stars ON repositories(stargazer_count);
CREATE INDEX IF NOT EXISTS idx_repos_indexed_at ON repositories(indexed_at);

CREATE INDEX IF NOT EXISTS idx_categories_category ON repo_categories(category);
CREATE INDEX IF NOT EXISTS idx_categories_repo ON repo_categories(repo_id);

CREATE INDEX IF NOT EXISTS idx_tech_stack_tech ON repo_tech_stack(tech);
CREATE INDEX IF NOT EXISTS idx_tech_stack_repo ON repo_tech_stack(repo_id);

CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================
-- Trigger to update updated_at timestamp
-- ============================================
CREATE TRIGGER IF NOT EXISTS update_repositories_timestamp
AFTER UPDATE ON repositories
FOR EACH ROW
BEGIN
    UPDATE repositories SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_conversations_timestamp
AFTER UPDATE ON conversations
FOR EACH ROW
BEGIN
    UPDATE conversations SET updated_at = datetime('now') WHERE id = NEW.id;
END;
