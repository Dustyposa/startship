# 集成测试计划: 同步系统

## 目标

编写集成测试，验证同步系统的端到端功能，包括真实的 GitHub API 调用。

## 测试环境要求

### 必需配置
- `GITHUB_TOKEN` - 真实的 GitHub Personal Access Token
- 测试数据库（可以使用临时文件或内存数据库）

### 可选配置
- `GITHUB_USERNAME` - 用于测试的用户名
- 测试仓库（已加星标的仓库）

---

## 测试覆盖范围

### 1. SyncService 集成测试 (`tests/integration/test_sync_service_integration.py`)

#### 1.1 端到端同步流程
- [ ] 完整的全量同步流程
  - 获取 starred 仓库
  - 存储到数据库
  - 记录同步历史
- [ ] 完整的增量同步流程
  - 基于 last_synced_at 增量获取
  - 检测并更新变化
  - 软删除已取消星标的仓库

#### 1.2 变化检测验证
- [ ] 真实仓库数据变化检测
  - star 数变化
  - fork 数变化
  - 描述变化
- [ ] 新仓库正确添加
- [ ] 取消星标的仓库正确软删除

#### 1.3 错误处理
- [ ] 无效 GitHub Token 处理
- [ ] 网络错误处理
- [ ] API 限流处理

---

### 2. API 端点集成测试 (`tests/integration/test_sync_api_integration.py`)

#### 2.1 同步流程端点
- [ ] POST /api/sync/manual
  - 增量同步完整流程
  - 全量同步完整流程
  - 后台任务执行验证

#### 2.2 查询端点
- [ ] GET /api/sync/status
  - 实时同步状态
  - 仓库计数准确性
- [ ] GET /api/sync/history
  - 历史记录完整性
  - 分页功能
- [ ] GET /api/sync/repos/deleted
  - 软删除仓库查询
  - 恢复功能验证

#### 2.3 仓库操作端点
- [ ] POST /api/sync/repo/{name}/restore
  - 恢复软删除仓库
  - 恢复后仓库可查询

---

### 3. 调度器集成测试 (`tests/integration/test_scheduler_integration.py`)

#### 3.1 调度器启动和停止
- [ ] 调度器正常启动
- [ ] 调度器正常停止
- [ ] 任务正确注册

#### 3.2 定时任务验证
- [ ] 每日增量同步任务配置
- [ ] 每周全量同步任务配置
- [ ] 手动触发同步不影响调度任务

---

## 测试策略

### 数据准备
```python
# 集成测试 fixtures
@pytest.fixture(scope="module")
async def test_db():
    """创建测试数据库"""
    db = create_database("sqlite", db_path=":memory:")
    await db.initialize()
    yield db
    await db.close()

@pytest.fixture(scope="module")
def github_token():
    """获取真实 GitHub Token"""
    import os
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set")
    return token
```

### 测试隔离
- 每个测试使用独立的数据库或清理数据
- 测试顺序优化（独立测试可并行）

### 真实 API 调用
- 使用真实的 GitHub Token
- 可能需要 mock 某些不稳定的行为
- 设置合理的超时时间

---

## 实现阶段

### Phase 1: SyncService 集成测试 🔄
- [ ] 全量同步端到端测试
- [ ] 增量同步端到端测试
- [ ] 变化检测验证

### Phase 2: API 端点集成测试
- [ ] 手动同步端点
- [ ] 状态查询端点
- [ ] 历史记录端点
- [ ] 仓库恢复端点

### Phase 3: 调度器集成测试
- [ ] 调度器生命周期
- [ ] 定时任务验证

---

## 新建文件

- `tests/integration/test_sync_service_integration.py` - SyncService 集成测试
- `tests/integration/test_sync_api_integration.py` - API 集成测试
- `tests/integration/test_scheduler_integration.py` - 调度器集成测试
- `tests/integration/conftest.py` - 集成测试 fixtures

---

## 注意事项

### 性能考虑
- 真实 API 调用可能较慢
- 考虑使用测试数据缓存
- 设置合理的超时时间

### 失败处理
- 网络问题导致测试失败的处理
- API 限流时的重试策略
- 测试数据清理

### CI/CD 集成
- GitHub Token 的安全管理
- 测试环境的隔离
- 测试结果的报告
