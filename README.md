# GitHub Star Helper

基于AutoGen和MCP的GitHub项目分析助手，提供对话式的项目分析和推荐服务。

## 功能特性

### 🎯 核心功能
- **年度总结**: 生成个人GitHub年度报告，分析技术栈和项目趋势
- **宝藏发现**: 找到你收藏但可能遗忘的优质项目
- **技术研究**: 深度分析特定技术栈和框架对比
- **学习路径**: 基于你的技术栈推荐个性化学习路线
- **趋势分析**: 分析技术趋势和团队技术选型
- **智能推荐**: AI驱动的项目和技术推荐

### 💬 对话式交互
- 自然语言查询
- 智能意图识别
- 上下文理解
- 富文本结果展示
- 实时对话体验

### 🔧 技术架构
- **前端**: 现代化Web界面，响应式设计
- **后端**: FastAPI + AutoGen Agent
- **集成**: MCP协议与GitHub工具通信
- **AI**: 智能工作流编排和意图分类

## 快速开始

### 环境要求
- Python 3.8+
- Node.js (可选，用于开发)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd startship
```

2. **安装Python依赖**
```bash
pip install -r requirements.txt
```

3. **启动服务**
```bash
python main.py
```

4. **访问应用**
打开浏览器访问: http://localhost:8000

### 使用方法

1. **连接GitHub账户**
   - 在顶部输入框中输入GitHub用户名
   - 点击"连接"按钮

2. **开始对话**
   - 使用快捷操作按钮快速开始
   - 或直接输入自然语言问题

3. **示例查询**
   ```
   生成我的2024年度总结
   推荐一些Python机器学习项目
   帮我分析React和Vue的技术趋势
   为我制定学习Rust的路径
   发现一些有趣的开源工具
   ```

## 项目结构

```
startship/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── api.py             # FastAPI后端服务
│   ├── autogen_agent.py   # AutoGen Agent实现
│   └── mcp_client.py      # MCP客户端
├── static/                # 前端静态文件
│   ├── index.html         # 主页面
│   ├── style.css          # 样式文件
│   └── app.js             # 前端逻辑
├── .trae/                 # 文档目录
│   └── documents/
│       ├── product_plan.md
│       ├── autogen_implementation_guide.md
│       └── autogen_mvp_implementation.md
├── main.py                # 主启动文件
├── requirements.txt       # Python依赖
└── README.md             # 项目说明
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

## API接口

### REST API
- `GET /` - 主页面
- `GET /health` - 健康检查
- `POST /api/chat` - 聊天接口
- `GET /api/quick-actions` - 获取快捷操作
- `GET /api/conversation-history` - 获取对话历史

### WebSocket
- `WS /ws` - 实时对话连接

## 开发指南

### 本地开发

1. **启动开发服务器**
```bash
python main.py
```

2. **代码格式化**
```bash
black src/
flake8 src/
```

3. **运行测试**
```bash
pytest
```

### 扩展功能

1. **添加新的意图类型**
   - 在 `autogen_agent.py` 中的 `IntentClassifier` 添加新模式
   - 在 `WorkflowOrchestrator` 中实现对应工作流

2. **自定义MCP工具**
   - 扩展 `mcp_client.py` 中的工具集合
   - 添加新的API调用方法

3. **前端界面定制**
   - 修改 `static/style.css` 调整样式
   - 扩展 `static/app.js` 添加新功能

## 配置说明

### 环境变量
- `ENVIRONMENT`: 运行环境 (development/production)
- `GITHUB_TOKEN`: GitHub API令牌 (可选)
- `MCP_SERVER_COMMAND`: MCP服务器启动命令

### 生产部署

1. **设置环境变量**
```bash
export ENVIRONMENT=production
```

2. **使用Gunicorn部署**
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 故障排除

### 常见问题

1. **MCP连接失败**
   - 检查MCP服务器是否正确安装
   - 确认服务器命令配置正确
   - 查看日志获取详细错误信息

2. **GitHub API限制**
   - 配置GitHub Token提高API限制
   - 实现请求缓存减少API调用

3. **前端加载问题**
   - 检查静态文件路径
   - 确认浏览器控制台无错误
   - 验证API接口可访问性

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