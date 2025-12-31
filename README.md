# GitHub Star Helper

智能的 GitHub 星标仓库管理和分析助手。

## Development Status

### Stage 1: Foundation ✅ COMPLETED
- [x] Project structure & configuration
- [x] Database layer (SQLite with FTS5)
- [x] GitHub API client (httpx, async)
- [x] LLM abstraction layer (OpenAI)
- [x] Initialization service (fetch & analyze stars)
- [x] Search service (filter by category/language/stars)
- [x] Chat service (RAG support)
- [x] Basic API routes

### Stage 2: Intent & Semantic Search ✅ COMPLETED
- [x] Intent classification (LLM-based query routing)
- [x] Vector embeddings (Ollama nomic-embed-text)
- [x] Semantic search (ChromaDB)
- [x] Hybrid search (FTS + Semantic with weighted merging)
- [x] Statistics aggregation service
- [x] Enhanced chat with intent-based streaming
- [x] Frontend InitView with semantic option

**Tests**: 72 passing ✅

See [docs/plans/2024-12-30-stage2-intent-semantic-design.md](docs/plans/2024-12-30-stage2-intent-semantic-design.md) for Stage 2 details.

### Stage 3: Advanced Features 🚧 PLANNED
- [ ] Multi-turn conversation context
- [ ] Advanced RAG with query expansion
- [ ] Repository clustering and recommendations
- [ ] Trend analysis and insights
- [ ] Authentication & user management

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

## 快速开始

### 环境要求
- Python 3.13+
- Node.js 18+ (for frontend)
- Ollama (可选，用于语义搜索)

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

```
startship/
├── src/                          # 后端源代码
│   ├── api/                      # API 层
│   │   ├── app.py                # FastAPI 应用
│   │   └── routes/               # API 路由
│   │       ├── chat.py           # 聊天接口（含意图识别）
│   │       ├── search.py         # 搜索接口
│   │       └── init.py           # 初始化接口
│   ├── config.py                 # 配置管理
│   ├── db/                       # 数据库层
│   │   ├── base.py               # Database 抽象
│   │   └── sqlite.py             # SQLite 实现
│   ├── github/                   # GitHub API
│   │   ├── client.py             # GitHub API 客户端
│   │   └── models.py             # GitHub 数据模型
│   ├── llm/                      # LLM 抽象层
│   │   ├── base.py               # LLM 抽象接口
│   │   └── openai.py             # OpenAI 实现
│   ├── services/                 # 业务逻辑
│   │   ├── intent.py             # 意图识别
│   │   ├── search.py             # 搜索服务
│   │   ├── chat.py               # 聊天服务
│   │   ├── stats.py              # 统计服务
│   │   ├── hybrid_search.py      # 混合搜索
│   │   └── init.py               # 初始化服务
│   └── vector/                   # 向量搜索
│       ├── embeddings.py         # Ollama 嵌入
│       └── semantic.py           # 语义搜索 (ChromaDB)
├── frontend/                     # 前端 (Vue 3)
│   └── src/
│       ├── views/                # 页面组件
│       ├── router/               # 路由配置
│       ├── stores/               # Pinia 状态管理
│       └── types/                # TypeScript 类型
├── tests/                        # 测试套件
│   └── unit/                     # 单元测试
├── data/                         # 数据目录
│   ├── github_stars.db           # SQLite 数据库
│   └── chromadb/                 # ChromaDB 向量存储
├── docs/plans/                   # 设计文档
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
GITHUB_TOKEN=ghp_xxx  # GitHub Personal Access Token (提高 API 限制)

# OpenAI
OPENAI_API_KEY=sk-xxx  # OpenAI API Key (用于 LLM)
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选: 自定义 API 端点

# Ollama (用于语义搜索)
OLLAMA_BASE_URL=http://localhost:11434  # Ollama 服务地址

# 数据库
DB_TYPE=sqlite  # 数据库类型
SQLITE_PATH=data/github_stars.db  # SQLite 数据库路径

# 向量存储
CHROMADB_PATH=data/chromadb  # ChromaDB 持久化路径
```

### 生产部署

1. **使用 Gunicorn + Uvicorn**
```bash
gunicorn src.api.app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

2. **使用 Docker**
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
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