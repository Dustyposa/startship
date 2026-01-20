# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **语义搜索** - 基于向量嵌入的智能搜索系统
  - bge-m3 嵌入模型（1024 维向量）
  - ChromaDB 向量存储
  - 混合搜索引擎：FTS5 (权重 0.3) + 语义搜索 (权重 0.7)
  - 概念理解、同义词识别、跨语言搜索
  - 搜索准确率从 4% 提升到 96%（+92%）
  - 48 个测试全部通过（29 单元 + 19 集成）
  - 4 个新环境变量（Ollama 和 ChromaDB 配置）
- **向量管理 API** - 语义搜索支持接口
  - `GET /api/vector/status` - 向量索引状态查询
  - `POST /api/vector/reindex` - 批量重新索引
- **智能数据同步系统** - GitHub 星标仓库自动同步
  - 增量/全量同步、软删除保护、变更检测、后台定时任务
  - 6 个新 API 端点 (`/api/sync/*`)
  - 2 个新前端页面 (同步状态、历史记录)
- **AI 重新分析** - 单个仓库 AI 重新分析功能
- **完整测试覆盖** - 100 个测试 (62 单元 + 38 集成)
- **强制全量更新** - 同步 API 新增 `force_update` 参数，支持强制更新所有仓库
- **分页支持** - 搜索 API 支持返回总数和偏移量，方便前端实现分页
- **数字格式统一** - 星标数字使用 `formatStarCount` 格式化（如 11052 → 11k）

### Changed
- 语义搜索嵌入模型从 nomic-embed-text (768维) 升级到 bge-m3 (1024维)，准确率从 85% 提升到 96%
- 数据库新增 `is_deleted`, `last_synced_at`, `last_analyzed_at` 字段
- 同步状态端点 `pending_updates` 现在实际计算待更新仓库数
- 前端代理端口配置从 8000 改为 8889，与后端端口保持一致
- 网络图 tooltip 支持长文本自动换行（添加 `word-break: break-all`）
- 搜索按钮和首页搜索框添加阴影效果，提升视觉体验

### Removed
- **已删除仓库恢复功能** - 移除 deleted/restore 相关端点和测试
  - 删除 `GET /api/sync/repos/deleted` 端点
  - 删除 `POST /api/sync/repo/{name}/restore` 端点
  - 删除 `SyncStatusResponse.deleted_repos` 字段
  - 简化同步逻辑，专注于核心同步功能
  - 删除 9 个相关测试，新增测试 fixture 减少代码重复

### Fixed
- 修复 `last_synced_at` 首次同步后为 NULL 的问题
- 修复同步状态端点仓库计数错误
- 修复仓库详情页面模板结构错误导致的 2 列布局问题
- 移除已废弃的 `tech_stack` 字段引用

### Refactored
- 优化语义搜索相关代码结构（5 个文件）
  - `src/services/vectorization.py` - 提取常量配置，简化错误处理
  - `src/api/routes/vector.py` - 提取辅助函数，提升可测试性
  - `src/api/app.py` - 提取 `_init_semantic_search()` 函数
  - `src/services/search.py` - 现代化类型注解
  - `src/api/routes/search.py` - 增强参数解析功能

## [0.2.0] - 2026-01-15

### Added
- 智能数据同步系统
- 完整测试覆盖