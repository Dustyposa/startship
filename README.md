# GitHub Star Helper

智能的 GitHub 星标仓库管理和分析助手。

**当前版本：v0.0.1**

## 开发状态

### 第一阶段：基础架构 ✅ 已完成
- [x] 项目结构与配置
- [x] 数据库层（SQLite + FTS5）
- [x] GitHub API 客户端（httpx，异步）
- [x] LLM 抽象层（OpenAI）
- [x] 初始化服务（获取并分析 stars）
- [x] 搜索服务（按分类/语言/stars 过滤）
- [x] 聊天服务（RAG 支持）
- [x] 基础 API 路由

### 第二阶段：意图识别与语义搜索 ✅ 已完成
- [x] 意图分类（基于 LLM 的查询路由）
- [x] 向量嵌入（Ollama nomic-embed-text）
- [x] 语义搜索（ChromaDB）
- [x] 混合搜索（FTS + 语义搜索，加权融合）
- [x] 统计聚合服务
- [x] 增强聊天（基于意图的流式响应）
- [x] 前端初始化页面（支持语义搜索选项）

**测试**：72 个通过 ✅（第二阶段完成时）

查看 [docs/plans/2024-12-30-stage2-intent-semantic-design.md](docs/plans/2024-12-30-stage2-intent-semantic-design.md) 了解第二阶段详情。

### 第三阶段：高级功能 ✅ 已完成
- [x] 多轮对话上下文
- [x] 高级 RAG（带查询扩展）
- [x] 仓库推荐
- [x] 趋势分析与洞察

**测试**：101 个通过 ✅

### 第四阶段：网络可视化 ✅ 已完成
- [x] 关系网络可视化（ECharts）
- [x] NetworkService（相似度计算与图构建）
- [x] 力导向图布局
- [x] 节点大小按分类数量，颜色按 star 数量
- [x] Top-K 相似连接（K=5）
- [x] 网络缓存（提升性能）

**测试**：117 个通过 ✅

---

## 产品计划

### 项目愿景

构建一个真正智能的 GitHub 星标仓库管理助手，能深刻理解用户意图，高效执行任务，并能随着需求的增长而平滑演进。

### 核心架构：混合执行模型

项目采用**"混合执行模型"**，在效率与灵活性之间取得平衡：

1. **高层工作流委托** - 优先调用服务端预定义的高级工作流，处理标准、重复性的任务
2. **原子工具编排** - 当高级工作流无法满足需求时，Agent 可回退到调用原子化工具，自行编排逻辑

### 实施路线图

#### 第一阶段：服务分离与工作流抽象 ✅
- 搭建基础 API 服务，提供原子工具和高级工作流
- 实现基础的混合执行决策能力
- 使用 Redis 进行 L2 缓存

#### 第二阶段：引入可靠性与效率（规划中）
- 引入工作流引擎（如 Temporal）重构高级工作流
- 建立完善的缓存失效机制
- 引入向量数据库作为 Agent 的 L1 缓存

#### 第三阶段：实现企业级能力（规划中）
- 部署完整的可观测性套件
- 提供声明式的工作流定义语言
- 引入 RBAC 或 OAuth 权限管理
- 谨慎引入多 Agent 协作模式

### 详细文档

完整的架构设计、AutoGen 实施方案、核心使用场景等内容，请查看：
**[product_plan.md](product_plan.md)**

---

## 功能特性

### 🎯 核心功能
- **智能对话**: 基于意图识别的智能对话系统
  - `chat`: 日常对话和简单问答
  - `stats`: 统计查询（如"按语言统计"、"有多少项目"）
  - `search`: 仓库搜索和推荐
- **混合搜索**: 结合全文搜索和语义搜索
  - 全文搜索 (FTS5): 基于关键词的快速匹配
  - 语义搜索: 基于向量相似度的智能匹配
  - 加权融合: 可配置的权重平衡（默认 0.3 FTS + 0.7 语义）
- **统计分析**: 仓库语言分布、分类统计等
- **初始化向导**: 从 GitHub 星标仓库一键初始化
  - 可选 LLM 深度分析
  - 可选向量嵌入生成（用于语义搜索）

### 💬 对话式交互
- 自然语言查询
- 智能意图识别（LLM 驱动）
- Server-Sent Events (SSE) 流式响应
- 上下文对话历史

### 🔧 技术架构
- **后端**: FastAPI + SQLite + ChromaDB
- **向量**: Ollama nomic-embed-text
- **前端**: Vue 3 + TypeScript + Tailwind CSS
- **AI**: OpenAI GPT for intent and chat

## 界面预览

### 首页
![首页](assets/home.png)

### 搜索页
![搜索页](assets/search.png)

### 聊天页
![聊天页](assets/chat.png)

### 网络可视化
![网络可视化](assets/network.png)

### 趋势分析
![趋势分析](assets/trend.png)

---

## 快速开始

### 环境要求
- Python 3.13+
- Node.js 18+（前端）
- Ollama（可选，用于语义搜索）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd startship
```

2. **安装Python依赖**
```bash
# 使用 uv (推荐)
uv pip install -e .

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置必要的配置
```

4. **（可选）安装 Ollama 用于语义搜索**
```bash
# 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取嵌入模型
ollama pull nomic-embed-text
ollama serve
```

5. **启动后端服务**
```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

6. **启动前端（开发模式）**
```bash
cd frontend
npm install
npm run dev
```

7. **访问应用**
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

### 使用方法

1. **初始化系统**
   - 访问 http://localhost:5173/init
   - 输入 GitHub 用户名
   - 选择是否启用语义搜索（需要 Ollama）
   - 点击"开始初始化"

2. **开始对话**
   - 访问 http://localhost:5173/chat
   - 输入自然语言问题

3. **示例查询**
   ```
   按语言统计我的仓库
   有多少 Python 项目
   搜索一些机器学习相关的仓库
   有哪些 React 相关的项目
   ```

## 项目结构

### Docker 部署（推荐）

最快速的部署方式是使用 Docker。详细部署指南请查看 **[DEPLOYMENT.md](DEPLOYMENT.md)**。

**快速启动：**
```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

**访问地址：**
- 前端：http://localhost:3001
- 后端 API：http://localhost:8889

### 项目结构

```
startship/
├── src/                          # 后端源代码
│   ├── api/                      # API 层
│   │   ├── app.py                # FastAPI 应用
│   │   └── routes/               # API 路由
│   │       ├── chat.py           # 聊天接口（含意图识别）
│   │       ├── search.py         # 搜索接口
│   │       ├── init.py           # 初始化接口
│   │       ├── trends.py         # 趋势分析接口
│   │       └── network.py        # 网络可视化接口
│   ├── config.py                 # 配置管理
│   ├── data/                     # 数据模型
│   ├── db/                       # 数据库层
│   │   ├── base.py               # 数据库抽象
│   │   └── sqlite.py             # SQLite 实现
│   ├── github/                   # GitHub API
│   │   ├── client.py             # GitHub API 客户端
│   │   ├── models.py             # GitHub 数据模型
│   │   └── graphql.py            # GraphQL 查询
│   ├── llm/                      # LLM 抽象层
│   │   ├── base.py               # LLM 抽象接口
│   │   └── openai.py             # OpenAI 实现
│   ├── services/                 # 业务逻辑
│   │   ├── intent.py             # 意图识别
│   │   ├── search.py             # 搜索服务
│   │   ├── chat.py               # 聊天服务
│   │   ├── stats.py              # 统计服务
│   │   ├── hybrid_search.py      # 混合搜索
│   │   ├── init.py               # 初始化服务
│   │   ├── network.py            # 网络分析服务
│   │   ├── trend_analysis.py     # 趋势分析服务
│   │   ├── recommendation.py     # 推荐服务
│   │   ├── context.py            # 对话上下文
│   │   └── query_expander.py     # 查询扩展
│   └── vector/                   # 向量搜索
│       ├── embeddings.py         # Ollama 嵌入
│       └── semantic.py           # 语义搜索 (ChromaDB)
├── frontend/                     # 前端 (Vue 3)
│   └── src/
│       ├── views/                # 页面组件
│       │   ├── HomeView.vue      # 首页
│       │   ├── InitView.vue      # 初始化页
│       │   ├── SearchView.vue    # 搜索页
│       │   ├── ChatView.vue      # 聊天页
│       │   ├── NetworkView.vue   # 网络可视化页
│       │   ├── TrendView.vue     # 趋势分析页
│       │   ├── RepoDetailView.vue # 仓库详情页
│       │   ├── CollectionsView.vue # 收藏页
│       │   └── TechProfileView.vue # 技术画像页
│       ├── components/           # 可复用组件
│       ├── composables/          # 组合式函数
│       ├── router/               # 路由配置
│       ├── stores/               # Pinia 状态管理
│       └── types/                # TypeScript 类型
├── tests/                        # 测试套件
│   └── unit/                     # 单元测试
├── data/                         # 数据目录
│   └── github_stars.db           # SQLite 数据库
├── docker-compose.yml            # Docker 编排配置
├── Dockerfile.backend            # 后端 Docker 镜像
├── Dockerfile.frontend           # 前端 Docker 镜像
├── DEPLOYMENT.md                 # 部署指南
├── product_plan.md               # 产品计划（详细架构设计）
├── pyproject.toml                # Python 项目配置
└── README.md                     # 项目说明
```

## 核心使用场景

### 1. 快速全面的年度总结
**场景**: 年终回顾，了解自己一年来的技术成长轨迹

**示例对话**:
```
用户: "生成我的2024年度GitHub总结"
AI: 分析你的star历史，生成包含技术栈分布、项目亮点、成长趋势的可视化报告
```

### 2. 特定技术栈的深度研究
**场景**: 学习新技术前的调研，了解生态和最佳实践

**示例对话**:
```
用户: "我想深入了解Rust生态，推荐一些优质项目"
AI: 提供Rust核心库、工具链、应用案例的分类推荐和学习路径
```

### 3. 发现被遗忘的宝藏项目
**场景**: 重新发现早期收藏但遗忘的优质项目

**示例对话**:
```
用户: "帮我找找那些被遗忘的宝藏项目"
AI: 基于项目质量、更新活跃度等维度，挖掘你收藏中的隐藏宝藏
```

### 4. 团队技术趋势分析
**场景**: 技术选型决策，了解行业趋势和最佳实践

**示例对话**:
```
用户: "分析一下前端框架的技术趋势"
AI: 对比React、Vue、Angular等框架的发展趋势、社区活跃度、适用场景
```

### 5. 自动化学习路径生成
**场景**: 制定个性化学习计划，基于现有技能推荐进阶方向

**示例对话**:
```
用户: "我会Python和Django，想学习云原生技术"
AI: 基于你的技能基础，推荐Docker→Kubernetes→微服务的渐进式学习路径
```

### 6. 技术选型支持
**场景**: 项目技术选型时的决策支持

**示例对话**:
```
用户: "对比一下FastAPI和Flask的优缺点"
AI: 从性能、生态、学习曲线等维度对比，并根据项目需求给出建议
```

## API 接口

### REST API

#### 初始化
- `GET /api/init/status` - 获取初始化状态
- `POST /api/init/start` - 开始初始化（从 GitHub stars）

#### 聊天
- `POST /api/chat` - 发送聊天消息（非流式）
- `POST /api/chat/stream` - 流式聊天（带意图识别）
  - SSE 事件类型: `intent`, `content`, `search_results`, `done`
- `GET /api/chat/{session_id}` - 获取对话历史
- `DELETE /api/chat/{session_id}` - 删除对话

#### 搜索
- `GET /api/search` - 搜索仓库（支持过滤）
- `GET /api/categories` - 获取分类列表
- `GET /api/repo/{name_with_owner}` - 获取单个仓库详情

#### 系统
- `GET /` - 根路径
- `GET /health` - 健康检查
- `GET /stats` - 获取服务统计

### 交互式文档
访问 http://localhost:8000/docs 查看 Swagger UI 文档

## 开发指南

### 本地开发

1. **启动后端开发服务器**
```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

2. **启动前端开发服务器**
```bash
cd frontend
npm run dev
```

3. **运行测试**
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_intent.py -v

# 查看覆盖率
pytest --cov=src tests/
```

4. **代码格式化**
```bash
# Python
black src/
ruff check src/ --fix

# TypeScript
cd frontend
npm run lint
npm run format
```

### 扩展功能

1. **添加新的意图类型**
   - 在 `src/services/intent.py` 中添加新的 `IntentResult` 类型
   - 在 `src/api/routes/chat.py` 的 `chat_stream` 中添加处理逻辑

2. **调整混合搜索权重**
   - 修改 `src/services/hybrid_search.py` 中的 `fts_weight` 和 `semantic_weight`

3. **自定义嵌入模型**
   - 修改 `src/vector/embeddings.py` 使用不同的 Ollama 模型或其他嵌入服务

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下变量：

```bash
# GitHub
GITHUB_TOKEN=ghp_xxx  # GitHub 个人访问令牌（提高 API 限制）

# OpenAI
OPENAI_API_KEY=sk-xxx  # OpenAI API 密钥（用于 LLM）
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选：自定义 API 端点

# Ollama（用于语义搜索）
OLLAMA_BASE_URL=http://localhost:11434  # Ollama 服务地址

# 数据库
DB_TYPE=sqlite  # 数据库类型
SQLITE_PATH=data/github_stars.db  # SQLite 数据库路径

# 向量存储
CHROMADB_PATH=data/chromadb  # ChromaDB 持久化路径
```

### 生产部署

详细的 Docker 部署指南、环境变量配置、故障排查等内容，请查看 **[DEPLOYMENT.md](DEPLOYMENT.md)**。

**快速命令：**
```bash
# Docker 部署（推荐）
docker compose up -d --build

# 查看 Docker 日志
docker compose logs -f backend
docker compose logs -f frontend

# 停止服务
docker compose down
```

## 故障排除

### 常见问题

1. **Ollama 连接失败**
   - 确保 Ollama 服务正在运行: `ollama serve`
   - 验证嵌入模型已安装: `ollama list`
   - 检查 `OLLAMA_BASE_URL` 配置是否正确

2. **ChromaDB 初始化错误**
   - 确保有写入权限到 `data/chromadb` 目录
   - 如果出现持久化错误，尝试删除 `data/chromadb` 重新初始化

3. **GitHub API 限制**
   - 配置 `GITHUB_TOKEN` 提高请求限制
   - 使用 `max_repos` 参数限制初始化数量

4. **语义搜索不工作**
   - 确保初始化时启用了 `enable_semantic`
   - 检查 Ollama 服务可访问性
   - 查看后端日志获取详细错误信息

5. **前端无法连接后端**
   - 检查后端是否运行在 http://localhost:8000
   - 验证 CORS 配置
   - 查看浏览器控制台错误信息

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请创建Issue或联系项目维护者。