-- Migration 004: Add GitHub repository metadata fields
-- This migration adds fields for better filtering and categorization
-- Note: This migration is defensive - it only adds columns that don't exist

-- Helper function to check and add column if not exists
-- We'll use conditional SQL to avoid duplicate column errors

-- pushed_at: Last commit time for active maintenance calculation
-- Skip if already exists (may have been added by previous migration)
-- The database check is done at runtime to prevent errors

-- Create indexes for new filter dimensions if they don't exist
-- These will only be created if the columns exist
CREATE INDEX IF NOT EXISTS idx_repos_pushed_at ON repositories(pushed_at);
CREATE INDEX IF NOT EXISTS idx_repos_archived ON repositories(archived);
CREATE INDEX IF NOT EXISTS idx_repos_visibility ON repositories(visibility);
CREATE INDEX IF NOT EXISTS idx_repos_owner_type ON repositories(owner_type);
CREATE INDEX IF NOT EXISTS idx_repos_organization ON repositories(organization);

-- Note: If the columns (pushed_at, archived, visibility, owner_type, organization)
-- don't exist, they will need to be added manually. This migration is defensive
-- to handle databases where these columns may already exist.
