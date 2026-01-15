# 任务计划: 重新设计 GitHub Star Helper 分类系统

## 目标
取消使用 topics 作为分类，改用基于 GitHub API 官方字段的实用分类维度。

## 新分类策略

### 主分类
- **language** (TypeScript, Python, Go, Rust, JavaScript...)

### 衍生标签 (计算字段)
1. **按星数**: 🔥 热门项目 (>10k⭐)
2. **按活跃度**: 🟢 活跃维护 (7天内有提交)
3. **按时间**: 🆕 新项目 (2025年创建)
4. **按类型**: 🏢 组织项目 / 👤 个人项目

## 任务阶段

### Phase 1: 分析现有代码
- [x] 查看 src/services/init.py 中的 topics 分类逻辑
- [x] 查看 src/services/search.py 中的筛选逻辑
- [x] 查看数据库 schema
- [ ] 查看前端 SearchView.vue 筛选选项

### Phase 2: 修改后端
- [x] 添加缺失字段到 GitHub 模型 (archived, visibility, owner.type, organization) - 模型已有
- [x] 创建数据库迁移添加缺失字段 (pushed_at, archived, visibility, owner_type, organization)
- [x] 修改 search API 路由暴露新维度筛选参数
- [x] 修改 sqlite.py add_repository 方法保存新字段

### Phase 3: 修改前端
- [x] 更新 SearchView.vue 筛选选项
- [x] 更新类型定义 (Repository, SearchFilters)
- [x] 更新 repos store 传递新筛选参数

### Phase 4: 测试验证
- [x] 后端服务器启动测试
- [x] 数据库迁移验证
- [x] API 健康检查
- [x] 搜索 API 筛选测试
- [x] 前端构建测试
- [x] 数据库字段验证

## 错误记录
| 错误 | 尝试 | 解决方案 |
|------|------|----------|
| 缺少数据库字段 | 代码中保存了 push_at 等字段但 schema 没有 | 创建迁移 004 添加缺失字段 |

## 决策记录
| 决策 | 理由 |
|------|------|
| 取消 topics 分类 | topics 太细粒度，不适合作为主分类 |
| 使用 language 作为主分类 | GitHub API 官方字段，准确且实用 |
| 添加衍生标签 | 提供更多维度的筛选能力 |
| 创建迁移而非修改 schema | 保持向后兼容性 |
