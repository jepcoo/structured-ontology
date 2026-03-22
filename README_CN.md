<!-- markdownlint-disable MD033 -->
<p align="center">
 <h1 align="center">📚 Structured Ontology Skill</h1>
 <p align="center">
 为 AI Agent 团队打造的 SQLite 知识库<br />
 全文搜索 · 图查询 · 失败追踪 · 私有命名空间
 </p>
 <p align="center">
 <a href="https://github.com/jepcoo/structured-ontology"><img src="https://img.shields.io/badge/OpenClaw-Skill-4c9f38?logo=github" alt="OpenClaw Skill"></a>
 <a href="https://www.sqlite.org/index.html"><img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite" alt="SQLite"></a>
 <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python"></a>
 <a href="https://github.com/jepcoo/structured-ontology/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
 <a href="#"><img src="https://img.shields.io/badge/tests-31%20通过 -brightgreen" alt="Tests"></a>
 <a href="#"><img src="https://img.shields.io/badge/performance-100 节点%2F0.01s-brightgreen" alt="Performance"></a>
 </p>
</p>

---

**Structured Ontology** 是专为 [OpenClaw](https://github.com/openclaw/openclaw) Agent 团队设计的技能，提供统一、持久化的知识库：

- **结构化存储** – 实体（节点）、关系（边）、键值对属性
- **全文搜索** – 基于 SQLite FTS5 的快速关键词搜索
- **图查询** – 递归 CTE 实现依赖链和影响分析
- **失败追踪** – 记录错误、预防复发、存储修复方案
- **私有命名空间** – 细粒度权限控制，隔离 Agent 知识

适用于代码知识库、团队协作、依赖管理和自进化 Agent。

---

## 📦 安装

### 使用 ClawHub（推荐）

```bash
clawhub install structured-ontology
```

### 手动安装

将技能文件夹复制到 OpenClaw skills 目录：

```bash
git clone https://github.com/jepcoo/structured-ontology.git
cp -r structured-ontology ~/.openclaw/skills/
```

### 依赖

无需外部依赖 – 仅使用 Python 标准库：
- `sqlite3` – 数据库引擎（支持 FTS5）
- `asyncio` – 异步 I/O
- `pathlib`, `json`, `hashlib`, `typing` – 工具库

如需运行测试：

```bash
pip install pytest pytest-asyncio
```

---

## ⚙️ 配置

添加到 OpenClaw 配置文件（`~/.openclaw/openclaw.json`）：

```json
{
  "skills": {
    "structured-ontology": {
      "enabled": true,
      "lazy": true,
      "config": {
        "db_path": "~/.openclaw/workspace/knowledge.db",
        "default_namespace": "public"
      }
    }
  }
}
```

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | string | `~/.openclaw/workspace/knowledge.db` | SQLite 数据库文件路径 |
| `default_namespace` | string | `"public"` | 未提供命名空间时的默认值 |
| `lazy` | boolean | `true` | 按需加载技能（推荐） |

---

## 🚀 快速开始

```python
from skill import StructuredOntologySkill

skill = StructuredOntologySkill({"db_path": "~/.openclaw/workspace/knowledge.db"})
await skill.initialize()

# 添加节点（实体）
await skill.add_node("api:users", "api", "Users API",
    properties={"version": "1.0.0"})

# 索引文档以便搜索
await skill.index_document("api:users",
    "用户管理 API，支持 CRUD 操作和 OAuth2 认证")

# 添加关系
await skill.add_edge("e1", "func:get_user", "api:users", "calls")

# 搜索
results = await skill.search("用户管理")
for r in results:
    print(r["entity_id"], r["content"][:100])

# 依赖链查询
chain = await skill.get_dependency_chain("api:users", max_depth=3)

# 影响分析
impacted = await skill.get_impact_analysis("api:users")
print("受影响的模块:", [n["name"] for n in impacted])

# 记录和预防失败
await skill.record_failure(
    "modulenotfound:dotenv", "build_failure",
    {"package": "python-dotenv", "env": "ci"},
    notes="缺少开发依赖"
)

prevention = await skill.get_failure_prevention("modulenotfound:dotenv")
if prevention and not prevention["resolved"]:
    print("⚠️ 此失败已发生", prevention["occurrence_count"], "次")

await skill.close()
```

---

## 📖 核心概念

| 概念 | 说明 | 示例 |
|------|------|------|
| **节点 (Node)** | 实体 – API、函数、类、决策、失败、修复等 | `api:users`, `func:login` |
| **边 (Edge)** | 节点间的关系 | `depends_on`, `calls`, `implements`, `prevents` |
| **属性 (Property)** | 附加到节点或边的键值对元数据 | `{"version": "1.0.0"}` |
| **命名空间 (Namespace)** | 隔离范围。`public` 是共享的，其他是私有的 | `public`, `coder`, `reviewer` |
| **失败指纹 (Failure Fingerprint)** | 表示错误的可哈希字符串 | `test:connection_timeout` |
| **预防规则 (Prevention Rule)** | 在重复失败前警告/操作的主动规则 | `{"package": "dotenv"} → "pip install"` |

---

## 🔍 API 参考

### 节点操作

| 方法 | 说明 |
|------|------|
| `add_node(id, type, name, properties, namespace)` | 添加实体节点 |
| `get_node(id, namespace)` | 获取节点详情（含属性） |
| `delete_node(id)` | 删除节点（级联删除边） |
| `list_nodes(type, namespace)` | 列出节点（支持过滤） |

### 边操作

| 方法 | 说明 |
|------|------|
| `add_edge(id, source, target, type, weight, properties, namespace)` | 添加关系 |
| `get_outgoing_edges(node_id, edge_type, namespace)` | 获取从节点出发的边 |
| `get_incoming_edges(node_id, edge_type, namespace)` | 获取指向节点的边 |

### 搜索与图查询

| 方法 | 说明 |
|------|------|
| `index_document(entity_id, content, namespace)` | 索引文本以进行全文搜索 |
| `search(query, limit, namespaces)` | 执行 FTS5 搜索 |
| `get_dependency_chain(node_id, max_depth, edge_types)` | 递归遍历依赖关系 |
| `get_impact_analysis(node_id, max_depth)` | 反向依赖（修改这个会影响什么？） |

### 失败追踪

| 方法 | 说明 |
|------|------|
| `record_failure(fingerprint, error_type, context, notes)` | 记录失败发生 |
| `get_failure_prevention(fingerprint)` | 获取失败详情、发生次数和预防规则 |
| `add_prevention_rule(fingerprint, condition, action)` | 添加主动规则以在重复前警告/操作 |
| `resolve_failure(failure_id, fix_node_id, success)` | 标记失败为已解决 |

### 管理操作

| 方法 | 说明 |
|------|------|
| `set_namespace_permissions(agent_id, read, write)` | 配置 Agent 可访问的命名空间 |
| `get_stats()` | 数据库统计（每表的计数） |
| `vacuum()` / `reindex()` | 维护操作 |

详细文档请参阅 [DOCS.md](DOCS.md)。

---

## 🧪 测试

运行测试套件验证功能：

```bash
cd structured-ontology

# 单元测试
pytest tests/test_skill.py -v

# 集成测试
python test_integration.py
```

**预期输出：**

```
============================================================
Structured Ontology Skill - 集成测试
============================================================

[测试 1] 节点 CRUD 操作
  [通过] 节点 CRUD 成功

[测试 2] 边操作
  [通过] 边操作成功

[测试 3] 全文搜索
  [通过] 搜索成功，找到 1 个结果

...

============================================================
汇总：10 通过，0 失败
============================================================

所有测试通过！
```

---

## 📊 性能

| 操作 | 规模 | 延迟 | 状态 |
|------|------|------|------|
| **批量插入** | 100 节点 | <0.01 秒 | ✅ 优秀 |
| **全文搜索** | 1000 文档 | <0.1 秒 | ✅ 优秀 |
| **依赖链查询** | 深度 5 | <0.01 秒 | ✅ 优秀 |
| **内存占用** | 活跃操作 | <30MB | ✅ 高效 |
| **并发** | 多 Agent | WAL 模式 | ✅ 支持 |

---

## 🤝 使用场景

### 1. 代码知识库

```python
# 记录代码结构
await skill.add_node("api:payments", "api", "Payment API")
await skill.add_node("func:process_payment", "function", "process_payment()")
await skill.add_edge("e1", "func:process_payment", "api:payments", "implements")
await skill.index_document("api:payments", "集成 Stripe 的支付 API")

# 查询依赖
chain = await skill.get_dependency_chain("api:payments")
```

### 2. 团队协作

```python
# 每个 Agent 有私有命名空间
await skill.set_namespace_permissions("agent:coder",
    read_namespaces=["public", "coder"],
    write_namespaces=["coder"])

await skill.set_namespace_permissions("agent:reviewer",
    read_namespaces=["public", "coder", "reviewer"],
    write_namespaces=["reviewer"])
```

### 3. 失败预防

```python
# 记录并从失败中学习
await skill.record_failure("test:timeout", "test_failure",
    {"test": "test_api", "timeout": "30s"})

# 运行类似任务前检查
prevention = await skill.get_failure_prevention("test:timeout")
if prevention:
    print(f"⚠️ 之前失败过 {prevention['occurrence_count']} 次")
```

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. **Fork** 本仓库
2. **创建** 功能分支（`git checkout -b feature/amazing-feature`）
3. **修改** 代码并添加测试
4. **运行** 测试套件确保通过
5. **提交** 更改（`git commit -m 'Add some amazing feature'`）
6. **推送** 到分支（`git push origin feature/amazing-feature`）
7. **发起** Pull Request

添加或修改功能时请同时更新文档。

---

## 📄 许可证

本项目采用 MIT 许可证 – 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [SQLite](https://www.sqlite.org/) – 嵌入式数据库引擎
- [OpenClaw](https://github.com/openclaw/openclaw) – Agent 框架
- [pytest](https://docs.pytest.org/) – 测试框架

---

## 📞 支持

如有问题、Bug 报告或功能建议，请 [在 GitHub 上提 Issue](https://github.com/jepcoo/structured-ontology/issues)。

---

<p align="center">为 OpenClaw 社区用心制作 ❤️</p>
