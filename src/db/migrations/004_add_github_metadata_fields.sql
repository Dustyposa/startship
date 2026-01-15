-- Migration 004: Add GitHub repository metadata fields
-- This migration adds fields for better filtering and categorization

-- Add new columns to repositories table
-- Using ALTER TABLE with IF NOT EXISTS pattern requires checking first
-- For SQLite, we use a try-catch approach by wrapping in a transaction

-- Note: These columns are used by the sync system and GitHub API integration
-- If any of these fail (e.g., column already exists), the migration continues

-- pushed_at: Last commit time for active maintenance calculation
ALTER TABLE repositories ADD COLUMN pushed_at TIMESTAMP;

-- archived: Whether the repository is archived
ALTER TABLE repositories ADD COLUMN archived BOOLEAN DEFAULT 0;

-- visibility: Repository visibility (public, private)
ALTER TABLE repositories ADD COLUMN visibility TEXT DEFAULT 'public';

-- owner_type: Type of owner (User, Organization, Bot)
ALTER TABLE repositories ADD COLUMN owner_type TEXT;

-- organization: Organization name if owned by org
ALTER TABLE repositories ADD COLUMN organization TEXT;

-- Create indexes for new filter dimensions
CREATE INDEX IF NOT EXISTS idx_repos_pushed_at ON repositories(pushed_at);
CREATE INDEX IF NOT EXISTS idx_repos_archived ON repositories(archived);
CREATE INDEX IF NOT EXISTS idx_repos_visibility ON repositories(visibility);
CREATE INDEX IF NOT EXISTS idx_repos_owner_type ON repositories(owner_type);
CREATE INDEX IF NOT EXISTS idx_repos_organization ON repositories(organization);
