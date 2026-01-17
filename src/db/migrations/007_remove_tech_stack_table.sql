-- Migration: Remove tech_stack table and column
-- Date: 2025-01-17
-- Description: Remove repo_tech_stack table and tech_stack column, use primary_language instead

-- Drop the tech_stack table
DROP TABLE IF EXISTS repo_tech_stack;

-- Drop related indexes
DROP INDEX IF EXISTS idx_tech_stack_tech;
DROP INDEX IF EXISTS idx_tech_stack_repo;

-- Remove tech_stack column from repositories table
-- Note: For new databases without this column, the migration system will skip this
ALTER TABLE repositories DROP COLUMN tech_stack;
