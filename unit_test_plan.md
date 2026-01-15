# 单元测试计划: 同步系统

## 目标

为同步系统编写全面的单元测试，确保代码质量和可维护性。

## 测试覆盖范围

### 1. SyncService 测试 (`tests/unit/test_sync_service.py`)

#### 1.1 _needs_update() 方法
- [ ] 推送时间变化时返回 True
- [ ] star 数变化时返回 True
- [ ] fork 数变化时返回 True
- [ ] 主语言变化时返回 True
- [ ] 描述变化时返回 True
- [ ] archived 状态变化时返回 True
- [ ] visibility 变化时返回 True
- [ ] owner_type 变化时返回 True
- [ ] 所有字段相同时返回 False
- [ ] 处理空值情况

#### 1.2 soft_delete_repo() 方法
- [ ] 成功软删除仓库
- [ ] is_deleted 字段设置为 1
- [ ] 不存在的仓库处理

#### 1.3 restore_repo() 方法
- [ ] 成功恢复软删除仓库
- [ ] is_deleted 字段设置为 0
- [ ] 恢复已存在的仓库

#### 1.4 full_sync() 方法
- [ ] 新增仓库
- [ ] 更新已有仓库
- [ ] 软删除取消星标的仓库
- [ ] 正确返回统计信息
- [ ] 记录同步历史
- [ ] GitHub API 错误处理
- [ ] 数据库错误处理

#### 1.5 incremental_sync() 方法
- [ ] 首次同步 (last_synced_at 为空)
- [ ] 增量新增仓库
- [ ] 增量更新仓库
- [ ] 增量软删除
- [ ] 正确返回统计信息

#### 1.6 辅助方法
- [ ] _init_stats() 初始化统计
- [ ] _process_new_repos() 处理新增
- [ ] _process_updates() 处理更新
- [ ] _process_deletions() 处理删除
- [ ] _record_sync_history() 记录历史
- [ ] _handle_sync_error() 错误处理

### 2. API 路由测试 (`tests/unit/test_sync_routes.py`)

#### 2.1 GET /api/sync/status
- [ ] 返回同步状态
- [ ] 正确计数活跃仓库
- [ ] 正确计数已删除仓库
- [ ] 无同步历史时的处理

#### 2.2 POST /api/sync/manual
- [ ] 增量同步触发
- [ ] 全量同步触发
- [ ] reanalyze 参数传递
- [ ] 后台任务执行

#### 2.3 GET /api/sync/history
- [ ] 返回同步历史
- [ ] limit 参数生效
- [ ] 空历史处理

#### 2.4 GET /api/sync/repos/deleted
- [ ] 返回已删除仓库
- [ ] limit 参数生效
- [ ] 无删除仓库处理

#### 2.5 POST /api/sync/repo/{name}/restore
- [ ] 成功恢复仓库
- [ ] 不存在的仓库处理

#### 2.6 POST /api/sync/repo/{name}/reanalyze
- [ ] 成功排队重新分析
- [ ] TODO: 实际功能待实现

### 3. SyncScheduler 测试 (`tests/unit/test_sync_scheduler.py`)

#### 3.1 初始化
- [ ] 正确初始化调度器
- [ ] 同步服务实例化

#### 3.2 调度任务
- [ ] 每日增量同步任务配置
- [ ] 每周全量同步任务配置
- [ ] 启动调度器
- [ ] 停止调度器

---

## 测试策略

### Mock 策略
- **GitHubClient**: Mock 返回预设的仓库数据
- **Database**: 使用内存数据库或 mock
- **Settings**: Mock 配置

### 测试数据
```python
# 测试仓库数据
sample_github_repos = [
    GitHubRepository(...),  # 新仓库
    GitHubRepository(...),  # 已有仓库（无变化）
    GitHubRepository(...),  # 已有仓库（有变化）
]

sample_local_repos = [
    {...},  # 本地仓库数据
]
```

### 边界情况
- 空仓库列表
- 无同步历史
- 网络错误
- 数据库错误

---

## 实现阶段

### Phase 1: SyncService 核心方法 ✅
- [x] _needs_update() 测试 (12 个测试)
- [x] soft_delete_repo() 测试 (2 个测试)
- [x] restore_repo() 测试 (3 个测试)

### Phase 2: SyncService 同步方法 ✅
- [x] full_sync() 测试 (4 个测试)
- [x] incremental_sync() 测试 (2 个测试)

### Phase 3: API 路由 ✅
- [x] status 端点 (3 个测试)
- [x] manual 端点 (3 个测试)
- [x] history 端点 (3 个测试)
- [x] deleted 端点 (2 个测试)
- [x] restore 端点 (2 个测试)

### Phase 4: Scheduler ✅
- [x] 初始化测试 (2 个测试)
- [x] 任务配置测试 (4 个测试)
- [x] 生命周期测试 (5 个测试)
- [x] 同步任务方法测试 (6 个测试)
- [x] 模块函数测试 (6 个测试)

---

## 新建文件

- `tests/unit/test_sync_service.py` - SyncService 测试 (23 个测试) ✅
- `tests/unit/test_sync_routes.py` - 同步 API 测试 (13 个测试) ✅
- `tests/unit/test_sync_scheduler.py` - 调度器测试 (23 个测试) ✅

## 依赖添加

- `pytest-mock` - Mock 支持（可能已安装）
- `pytest-asyncio` - 异步测试（已安装）

---

## 错误追踪

| 错误 | 尝试 | 解决方案 |
|------|------|----------|
| | | |

---

## 完成总结

**测试覆盖率：59 个单元测试全部通过 ✅**

### 按文件统计：
- `test_sync_service.py`: 23 个测试
  - TestNeedsUpdate: 12 个测试
  - TestSoftDeleteRepo: 2 个测试
  - TestRestoreRepo: 3 个测试
  - TestFullSync: 4 个测试
  - TestIncrementalSync: 2 个测试

- `test_sync_routes.py`: 13 个测试
  - TestSyncStatus: 3 个测试
  - TestManualSync: 3 个测试
  - TestSyncHistory: 3 个测试
  - TestDeletedRepos: 2 个测试
  - TestRestoreRepo: 2 个测试

- `test_sync_scheduler.py`: 23 个测试
  - TestSyncSchedulerInit: 2 个测试
  - TestJobConfiguration: 4 个测试
  - TestSchedulerLifecycle: 5 个测试
  - TestSyncJobMethods: 6 个测试
  - TestModuleFunctions: 6 个测试

### 测试内容覆盖：
1. **SyncService 核心方法**：
   - 8 个字段的变化检测
   - 软删除和恢复操作
   - 全量同步和增量同步

2. **API 路由**：
   - 同步状态查询
   - 手动触发同步
   - 同步历史记录
   - 已删除仓库管理
   - 仓库恢复功能

3. **调度器**：
   - 初始化和配置
   - Cron 任务配置
   - 启动/停止生命周期
   - 同步任务执行和错误处理
   - 全局单例管理

