# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **智能数据同步系统** - GitHub 星标仓库自动同步
  - 增量/全量同步、软删除保护、变更检测、后台定时任务
  - 6 个新 API 端点 (`/api/sync/*`)
  - 3 个新前端页面 (同步状态、历史记录、已删除仓库)
- **AI 重新分析** - 单个仓库 AI 重新分析功能
- **完整测试覆盖** - 100 个测试 (62 单元 + 38 集成)

### Changed
- 数据库新增 `is_deleted`, `last_synced_at`, `last_analyzed_at` 字段
- 同步状态端点 `pending_updates` 现在实际计算待更新仓库数

### Fixed
- 修复 `last_synced_at` 首次同步后为 NULL 的问题
- 修复同步状态端点仓库计数错误

## [0.2.0] - 2026-01-15

### Added
- 智能数据同步系统
- 完整测试覆盖