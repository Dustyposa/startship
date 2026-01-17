# FTS5 全文搜索详解

> 从第一性原理理解 SQLite FTS5 的本质

---

## 核心原理

### 倒排索引

全文搜索的本质是**倒排索引**。

```
正排索引（普通表）:
文档1 → [python, is, great]
文档2 → [java, is, fun]

倒排索引（FTS5）:
python → [文档1, 文档3, 文档5]
java   → [文档2]
is     → [文档1, 文档2]
```

**为什么倒排？**

搜索 "python" 时：
- 正排：遍历所有文档 → 慢
- 倒排：直接查询 "python" → 快

---

## 表结构

### 双表模式（实际应用）

```
主表（repositories）:
├── 存储原始数据（30+ 字段）
├── 用 B-tree 索引
└── 提供完整数据

虚拟表（repositories_fts）:
├── 存储倒排索引（词 → rowid）
├── 只索引 4 个字段
└── 用于全文搜索
```

### 关联

```
通过 rowid 关联:
repositories.rowid = repositories_fts.rowid

查询流程:
1. FTS5 查询 → 获得匹配的 rowid 列表
2. JOIN 主表 → 获得完整数据
```

---

## 索引存储

### 存储内容

FTS5 虚拟表存储的是**压缩的倒排索引**：

```
词 → [(文档ID, 词频, 位置列表), ...]

示例:
"python" → [
  (rowid=1, freq=3, positions=[10, 50, 100]),
  (rowid=2, freq=1, positions=[25]),
  (rowid=3, freq=5, positions=[5, 15, 25, 35, 45])
]
```

### 数据结构

| 数据 | 说明 | 格式 |
|------|------|------|
| **词** | 分词后的词 | UTF-8 字符串 |
| **rowid** | 文档 ID | varint 压缩 |
| **词频** | 出现次数 | varint 压缩 |
| **位置** | 词在文档中的位置 | delta 编码 |

### 压缩技术

**varint**: 变长整数编码
```
1      → 0x01 (1字节)
127    → 0x7F (1字节)
128    → 0x80 0x01 (2字节)
```

**delta 编码**: 存储差值
```
位置: [10, 50, 100, 200]
不压缩: 16 字节
压缩后: [10, 40, 50, 100] → 8 字节
```

---

## 分词

### 分词器类型

```sql
CREATE VIRTUAL TABLE fts USING fts5(
    content,
    tokenize='simple|porter|unicode61|ascii|trigram'
);
```

| 分词器 | 说明 | 示例 |
|--------|------|------|
| **simple** | 默认，空格+标点分割，小写化 | `Hello World` → `[hello, world]` |
| **porter** | simple + 词干提取 | `running` → `run` |
| **unicode61** | Unicode 支持 | 支持 UTF-8 |
| **ascii** | 只处理 ASCII | 忽略中文 |
| **trigram** | 三元组，模糊搜索 | `search` → `[sea, ear, arc, rch]` |

### 分词过程

```
输入: "Python Programming Language"

simple 分词:
1. 按空格分割: ["Python", "Programming", "Language"]
2. 转小写: ["python", "programming", "language"]
3. 移除标点: ["python", "programming", "language"]
```

---

## 搜索模式

### SQLite 搜索模式本质

只有 **2 种**：

1. **结构化搜索**（精确/范围匹配）
   - 使用 B-tree 索引
   - `WHERE id = 1`, `WHERE stars > 1000`
   - LIKE 前缀能用索引，包含匹配全表扫描

2. **全文搜索**（倒排索引）
   - 使用 FTS5 倒排索引
   - `WHERE fts MATCH 'query'`
   - BM25 相关性排序

### FTS5 查询语法

```sql
-- 简单查询
WHERE fts MATCH 'python'

-- 布尔查询
WHERE fts MATCH 'python AND web'
WHERE fts MATCH 'python OR web'
WHERE fts MATCH 'python NOT web'

-- 前缀查询
WHERE fts MATCH 'pyt*'  -- 必须加 *

-- 短语查询
WHERE fts MATCH '"web framework"'

-- 列限定
WHERE fts MATCH 'title:python'
```

---

## 排名算法

### BM25 公式

```
rank = IDF × (TF × (k1 + 1)) / (TF + k1 × (1 - b + b × 文档长度/平均长度))
```

**参数**:
- `TF` (词频) = 词在文档中出现次数（索引时存储）
- `IDF` (逆文档频率) = log(总文档数 / 包含该词的文档数)（查询时计算）
- `k1` = 调节参数（1.2）
- `b` = 长度惩罚参数（0.75）

### 计算时机

| 数据 | 索引时 | 查询时 |
|------|--------|--------|
| TF（词频） | ✅ 存储 | ❌ |
| 位置列表 | ✅ 存储 | ❌ |
| 文档长度 | ✅ 存储 | ❌ |
| IDF | ❌ | ✅ 计算 |
| BM25 rank | ❌ | ✅ 计算 |

**为什么 rank 不预存？**
- IDF 依赖查询词组合
- 无数种查询组合，无法全部预存
- 动态计算更灵活

---

## 与 PostgreSQL tsearch 对比

| 特性 | SQLite FTS5 | PostgreSQL tsearch |
|------|-------------|-------------------|
| **本质** | 倒排索引 | 倒排索引 |
| **索引存储** | 虚拟表 | GIN/GiST 索引 |
| **分词器** | 5 种内置 | 20+ 语言配置 |
| **排名算法** | BM25（固定） | 多种（可调） |
| **高级功能** | 基础 | 完善（高亮、距离查询） |
| **并发** | 弱 | 强 |
| **适用** | 嵌入式、小型 | 企业级、大型 |

**本质相同，实现细节不同。**

---

## 前缀匹配

### 支持，但需要手动加 `*`

```sql
-- 带通配符（支持）
WHERE fts MATCH 'pyt*'  → 匹配 python, pytorch

-- 不带通配符（不支持）
WHERE fts MATCH 'pyt'   → 找不到
```

**原理**: 倒排索引只存储完整的词，前缀查询需要遍历所有以 `pyt` 开头的词。

---

## 本项目应用

### 表结构

```sql
-- 主表（存储所有数据）
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY,
    name_with_owner TEXT,
    name TEXT,
    description TEXT,
    summary TEXT,
    -- ... 30+ 个字段
);

-- FTS5 虚拟表（只索引需要搜索的字段）
CREATE VIRTUAL TABLE repositories_fts USING fts5(
    name_with_owner,
    name,
    description,
    summary,
    content='repositories',
    content_rowid='rowid'
);
```

### 查询

```sql
-- 全文搜索
SELECT r.* FROM repositories r
INNER JOIN repositories_fts fts ON r.rowid = fts.rowid
WHERE repositories_fts MATCH 'python web'
ORDER BY rank;
```

### 触发器自动同步

```sql
-- 插入/更新主表时，自动更新 FTS5 索引
CREATE TRIGGER repositories_ai AFTER INSERT ON repositories BEGIN
    INSERT INTO repositories_fts(rowid, name, description, summary)
    VALUES (new.rowid, new.name, new.description, new.summary);
END;
```

---

## 总结

### 本质

```
FTS5 = 倒排索引 + BM25 排名
```

### 关键点

1. **双表结构**: 主表存数据，虚拟表存索引
2. **压缩存储**: varint + delta 编码
3. **动态排名**: 查询时计算 rank，不预存
4. **前缀匹配**: 需要手动加 `*`
5. **与 PostgreSQL**: 本质相同，实现细节不同

### 适用场景

- ✅ 需要搜索文本内容
- ✅ 需要相关性排序
- ✅ 嵌入式、小型应用
- ⚠️ 大型应用考虑 PostgreSQL
