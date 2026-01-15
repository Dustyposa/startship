# 任务计划: 数据同步系统

## 目标

实现智能数据同步系统，解决：
1. **增量同步** - 处理每天新增的 star
2. **变更检测** - 检测仓库更新（pushed_at 变化）
3. **软删除机制** - 取消 star 时保留笔记和标签
4. **自动更新** - 保持元数据最新
5. **后台任务** - 定时同步 + 手动触发

## 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 同步模式 | 混合模式 | 首次全量 + 日常增量 + 周期全量校验 |
| 删除处理 | 软删除 (is_deleted) | 保留用户笔记和标签数据 |
| 更新策略 | 自动更新 | 用户始终看到最新数据 |
| 触发方式 | 混合模式 | 手动同步 + 后台定期静默更新 |
| LLM 分析 | 用户控制 | "重新分析"按钮，控制成本 |
| 数据清理 | 不清理 | 历史数据永久保留 |

---

## 实现阶段

### Phase 1: 数据库架构 🗄️
- [x] 添加字段到 `repositories` 表
  - [x] `is_deleted BOOLEAN DEFAULT 0` - 软删除标记
  - [x] `last_synced_at TIMESTAMP` - 最后同步时间
  - [x] `last_analyzed_at TIMESTAMP` - 最后分析时间
- [x] 创建 `sync_history` 表
  - [x] id, sync_type, started_at, completed_at
  - [x] stats_added, stats_updated, stats_deleted, stats_failed
  - [x] error_message
- [x] 添加索引
  - [x] idx_repos_is_deleted
  - [x] idx_repos_last_synced
  - [x] idx_sync_history_type
- [x] 数据库迁移脚本 `005_add_sync_fields.sql`

### Phase 2: 核心同步服务 ⚙️
- [x] 创建 `src/services/sync.py`
  - [x] `SyncService` 类
    - [x] `full_sync(username)` - 全量同步
    - [x] `incremental_sync(username)` - 增量同步
    - [x] `needs_update(local, github)` - 变更检测
    - [x] `soft_delete_repo(name)` - 软删除
    - [x] `restore_repo(name)` - 恢复
- [x] 错误处理和重试机制
- [x] 同步统计记录到 sync_history

### Phase 3: API 接口 🔌
- [x] 创建 `src/api/routes/sync.py`
  - [x] GET `/api/sync/status` - 获取同步状态
  - [x] POST `/api/sync/manual` - 手动同步
  - [x] POST `/api/sync/repo/{name}/reanalyze` - 重新分析
  - [x] GET `/api/sync/history` - 同步历史
  - [x] GET `/api/repos/deleted` - 已删除仓库列表
  - [x] POST `/api/sync/repo/{name}/restore` - 恢复仓库
- [x] 在 `app.py` 中注册路由

### Phase 4: 后台定时任务 ⏰
- [x] 添加 APScheduler 依赖
- [x] 创建 `src/services/scheduler.py`
  - [x] `SyncScheduler` 类
  - [x] 每日增量同步（凌晨 2 点）
  - [x] 每周全量校验（周日凌晨 3 点）
- [x] 在应用启动时启动调度器

### Phase 5: 前端 UI 🎨
- [x] 同步状态组件
  - [x] 显示最后同步时间
  - [x] 显示待更新仓库数
  - [x] 手动同步按钮
  - [x] 全量同步按钮
- [x] 仓库详情页增强
  - [x] 重新分析按钮
  - [x] 显示最后分析时间
- [x] 同步历史页面
- [x] 已删除仓库页面

### Phase 6: 测试与优化 🧪
- [x] API 端点测试
- [x] 软删除和恢复测试
- [x] 变更检测逻辑测试
- [x] last_synced_at bug 修复
- [x] GitHub Token 同步测试
- [x] 同步状态端点修复（count 查询）
- [x] 单元测试 (59 个测试)
  - [x] test_sync_service.py (23 个)
  - [x] test_sync_routes.py (13 个)
  - [x] test_sync_scheduler.py (23 个)
- [x] 集成测试 (38 个测试)
  - [x] test_sync_service_integration.py (10 个)
  - [x] test_sync_api_integration.py (11 个)
  - [x] test_scheduler_integration.py (13 个)
- [x] 错误场景测试 (包含在单元/集成测试中)

---

## 测试结果 (2026-01-15 更新)

| 测试项 | 状态 | 结果 |
|--------|------|------|
| API 端点 | ✅ 通过 | 6个端点正常工作 |
| 软删除 | ✅ 通过 | is_deleted 字段正常 |
| 恢复功能 | ✅ 通过 | API 恢复正常 |
| 变更检测 | ✅ 通过 | last_synced_at bug 已修复 |
| 公共 API 同步 | ✅ 通过 | 成功同步 980 个仓库 |
| GitHub Token 同步 | ✅ 通过 | +2 ~72 -840，0 失败 |
| 同步状态端点 | ✅ 修复 | count 查询修正（98 → 141） |
| 后台调度器 | ✅ 通过 | Token 检测和启动正常 |
| 单元测试 | ✅ 通过 | 59 个测试全部通过 |
| 集成测试 | ✅ 通过 | 38 个测试全部通过 |
| **总计** | ✅ | **97 个测试全部通过** |

### 同步数据统计 (2026-01-15)
- 活跃仓库: 141 个
- 已删除仓库: 850 个
- 总仓库: 991 个
- 最后同步: 2026-01-15 19:45:51

### 已修复的问题

| 问题 | 描述 | 修复状态 |
|------|------|----------|
| last_synced_at 为空 | 首次同步后字段为 NULL，增量同步不更新 | ✅ 已修复 |
| 同步状态 count 错误 | 使用 search_repositories 导致 archived 仓库被过滤 | ✅ 已修复 |

---

## 错误追踪

| 错误 | 尝试 | 解决方案 |
|------|------|----------|
| | | |

---

## 新建文件
- `src/services/sync.py` - 同步服务 (400+ 行)
- `src/api/routes/sync.py` - 同步 API (200+ 行)
- `src/services/scheduler.py` - 定时任务 (150+ 行)
- `src/db/migrations/005_add_sync_fields.sql` - 数据库迁移
- `.env.example` - 环境变量示例文件（包含 GitHub Token 配置说明）
- `frontend/src/api/sync.ts` - 前端同步 API 客户端
- `frontend/src/components/SyncStatus.vue` - 同步状态组件
- `frontend/src/views/SyncHistoryView.vue` - 同步历史页面
- `frontend/src/views/DeletedReposView.vue` - 已删除仓库页面
- `tests/unit/test_sync_service.py` - SyncService 单元测试 (400+ 行)
- `tests/unit/test_sync_routes.py` - 同步 API 单元测试 (390+ 行)
- `tests/unit/test_sync_scheduler.py` - 调度器单元测试 (400+ 行)
- `tests/integration/conftest.py` - 集成测试 fixtures
- `tests/integration/test_sync_service_integration.py` - SyncService 集成测试 (510+ 行)
- `tests/integration/test_sync_api_integration.py` - 同步 API 集成测试 (330+ 行)
- `tests/integration/test_scheduler_integration.py` - 调度器集成测试 (290+ 行)
- `unit_test_plan.md` - 单元测试计划
- `integration_test_plan.md` - 集成测试计划

## 修改文件
- `src/db/sqlite.py` - 添加 execute_query() 和更新 search_repositories()
- `src/api/app.py` - 注册路由和启动调度器
- `src/config.py` - 移除 github_username 字段（仅 Token 模式）
- `src/github/client.py` - 移除 username 参数（仅 Token 模式）
- `src/services/sync.py` - 修复 last_synced_at NULL 处理逻辑
- `src/services/scheduler.py` - 移除 username 相关代码（仅 Token 模式）
- `src/api/routes/sync.py` - 修复同步状态 count 查询
- `pyproject.toml` - 添加 APScheduler 依赖
- `frontend/src/views/HomeView.vue` - 添加 SyncStatus 组件
- `frontend/src/views/RepoDetailView.vue` - 添加重新分析按钮
- `frontend/src/router/index.ts` - 添加新路由
