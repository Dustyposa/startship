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
- **强制全量更新** - 同步 API 新增 `force_update` 参数，支持强制更新所有仓库
- **分页支持** - 搜索 API 支持返回总数和偏移量，方便前端实现分页
- **数字格式统一** - 星标数字使用 `formatStarCount` 格式化（如 11052 → 11k）

### Changed
- 数据库新增 `is_deleted`, `last_synced_at`, `last_analyzed_at` 字段
- 同步状态端点 `pending_updates` 现在实际计算待更新仓库数
- 前端代理端口配置从 8000 改为 8889，与后端端口保持一致
- 网络图 tooltip 支持长文本自动换行（添加 `word-break: break-all`）
- 搜索按钮和首页搜索框添加阴影效果，提升视觉体验

### Fixed
- 修复 `last_synced_at` 首次同步后为 NULL 的问题
- 修复同步状态端点仓库计数错误
- 修复仓库详情页面模板结构错误导致的 2 列布局问题
- 移除已废弃的 `tech_stack` 字段引用

## [0.2.0] - 2026-01-15

### Added
- 智能数据同步系统
- 完整测试覆盖