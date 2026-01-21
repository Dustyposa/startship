# Changelog

All notable changes to this project will be documented in this file.

## [1.2.1] - 2026-01-21

### Changed
- 代码重构：简化代码逻辑，删除冗余方法和中间变量
- 代码优化：减少 561 行代码，提升可维护性
- 优化导入语句组织，简化函数签名

### Added
- 综合测试覆盖：混合推荐系统的单元测试、集成测试、端到端测试
- 搜索加载动画：骨架屏和"搜索中..."状态显示
- Axios 超时配置：10秒超时防止请求挂起
- 搜索结果数据补全：自动从数据库获取完整数据
- 前端空值处理：formatStarCount/formatRelativeTime 返回 'N/A'

### Fixed
- 搜索结果缺少星标数、Fork数、日期信息
- 前端无法解析后端返回的数据格式（languages/topics 为字符串）
- Vue 模板编译错误（缺失闭合标签）
- 搜索时无加载反馈导致用户体验不佳

## [1.2.0] - 2026-01-20

### Added
- 混合推荐系统：融合图谱关系 (65%) 和语义相似度 (35%)
- 语义边发现服务：自动计算仓库间语义相似度
- 推荐API端点：`/api/recommendations/{repo}`
- 语义边重建API：`/api/graph/semantic-edges/rebuild`
- 增量语义边更新：同步时只更新变化仓库
- 推荐来源标注：显示推荐来源（同一作者、技术栈、语义相似等）
- 推荐侧边栏：仓库详情页添加相似项目推荐

### Changed
- 搜索页推荐区域：使用混合推荐替代纯图谱推荐
- 同步服务：集成语义边增量更新
- 全量同步：自动重建所有语义边

## [1.1.0] - 2026-01-19

### Added
- 语义搜索完全集成：搜索、同步、初始化一体化
- 搜索服务集成混合搜索（FTS5 + 语义向量）
- 同步时自动更新向量索引（语义字段变化时）
- 初始化时自动向量化，启用语义搜索
- 语义搜索支持单个仓库的增删改查

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