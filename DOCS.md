# structured-ontology 完整文档

## 📖 概述

**structured-ontology** 是一个基于 SQLite 的结构化知识库技能，为 OpenClaw Agent Teams 提供统一的知识存储、检索和推理能力。

### 核心特性

| 特性 | 说明 |
|------|------|
| **结构化存储** | 实体（节点）、关系（边）、属性（键值对）三层模型 |
| **全文搜索** | 基于 SQLite FTS5，支持高效关键词检索 |
| **图查询** | 递归 CTE 实现依赖链、影响分析等多跳查询 |
| **失败追踪** | 记录失败指纹、修复方案，主动预警预防 |
| **命名空间** | 公共 + 私有命名空间，支持 Agent 知识隔离 |
| **版本控制** | 时间戳追踪，支持基础版本管理 |

### 适用场景

- 🤖 **Agent 团队协作** - 共享知识、避免重复工作
- 📚 **代码知识库** - 存储 API、函数、类的关系
- ⚠️ **失败预防** - 记录错误及解决方案，避免重复踩坑
- 🔍 **知识检索** - 全文搜索 + 图遍历查询
- 📊 **依赖分析** - 追踪模块依赖、影响范围

---

## 🚀 快速开始

### 1. 安装技能

```bash
# 使用 clawhub 安装
clawhub install structured-ontology

# 或手动复制到 skills 目录
cp -r skills/structured-ontology ~/.openclaw/skills/
```

### 2. 配置技能

在 OpenClaw 配置中添加：

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

### 3. 基本使用

```python
from skill import StructuredOntologySkill

# 初始化
skill = StructuredOntologySkill({
    "db_path": "~/.openclaw/workspace/knowledge.db"
})
await skill.initialize()

# 添加节点
await skill.add_node("api:users", "api", "Users API",
    properties={"version": "1.0.0"},
    namespace="public")

# 添加关系
await skill.add_edge("e1", "func:get_user", "api:users", "calls")

# 搜索
results = await skill.search("user management")

# 查询依赖
chain = await skill.get_dependency_chain("api:users")
```

---

## 📐 架构设计

### 数据库架构

```
┌─────────────────────────────────────────────────────────────┐
│                        SQLite Database                       │
├─────────────┬──────────────┬──────────────┬─────────────────┤
│   nodes     │    edges     │  properties  │      fts        │
│  (实体表)   │   (关系表)    │  (属性表)    │   (全文索引)    │
├─────────────┼──────────────┼──────────────┼─────────────────┤
│ id          │ id           │ entity_id    │ content         │
│ type        │ source_id    │ entity_type  │ entity_id       │
│ name        │ target_id    │ key          │ namespace       │
│ namespace   │ type         │ value        │                 │
│ created_at  │ weight       │ namespace    │                 │
│ updated_at  │ namespace    │              │                 │
│             │ created_at   │              │                 │
├─────────────┴──────────────┴──────────────┴─────────────────┤
│  failures  │  failure_fixes  │  prevention_rules            │
│ (失败表)   │   (修复表)      │    (预防规则表)               │
└─────────────────────────────────────────────────────────────┘
```

### 数据模型

#### 1. 节点（Nodes）- 实体

```
节点 = {
    id: string,          // 唯一标识，如 "api:users", "func:login"
    type: string,        // 类型，如 "api", "function", "class", "failure"
    name: string,        // 人类可读名称
    namespace: string,   // 命名空间，如 "public", "coder", "reviewer"
    created_at: datetime,
    updated_at: datetime
}
```

**常见类型：**
- `api` - API 接口
- `function` - 函数/方法
- `class` - 类
- `module` - 模块
- `file` - 文件
- `decision` - 决策记录
- `failure` - 失败记录
- `fix` - 修复方案
- `document` - 文档

#### 2. 边（Edges）- 关系

```
边 = {
    id: string,          // 唯一标识
    source_id: string,   // 源节点 ID
    target_id: string,   // 目标节点 ID
    type: string,        // 关系类型
    weight: float,       // 权重（默认 1.0）
    namespace: string,   // 命名空间
    created_at: datetime
}
```

**常见关系类型：**
- `depends_on` - 依赖
- `calls` - 调用
- `implements` - 实现
- `uses` - 使用
- `extends` - 继承
- `contains` - 包含
- `prevents` - 预防
- `fixes` - 修复

#### 3. 属性（Properties）- EAV 模型

```
属性 = {
    entity_id: string,   // 节点或边的 ID
    entity_type: string, // "node" 或 "edge"
    key: string,         // 属性键
    value: string,       // 属性值（支持 JSON）
    namespace: string
}
```

**示例：**
```json
{
    "entity_id": "api:users",
    "entity_type": "node",
    "key": "version",
    "value": "1.0.0"
}
```

---

## 📚 API 参考

### 初始化

```python
from skill import StructuredOntologySkill

skill = StructuredOntologySkill(config={
    "db_path": "~/.openclaw/workspace/knowledge.db",
    "default_namespace": "public"
})
await skill.initialize()
```

---

### 节点操作

#### `add_node(node_id, type, name, properties, namespace, agent_id)`

添加实体节点。

**参数：**
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `node_id` | string | ✅ | - | 唯一标识 |
| `type` | string | ✅ | - | 节点类型 |
| `name` | string | ✅ | - | 显示名称 |
| `properties` | dict | ❌ | `None` | 属性字典 |
| `namespace` | string | ❌ | `"public"` | 命名空间 |
| `agent_id` | string | ❌ | `None` | 调用者 ID |

**返回：** `bool` - 成功标志

**示例：**
```python
await skill.add_node(
    "api:payments",
    "api",
    "Payment API",
    properties={"version": "2.0", "deprecated": False},
    namespace="public"
)
```

---

#### `get_node(node_id, namespace, agent_id)`

获取节点信息。

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `node_id` | string | 节点 ID |
| `namespace` | string | 命名空间过滤 |
| `agent_id` | string | 调用者 ID（权限检查） |

**返回：** `dict` 或 `None`

**示例：**
```python
node = await skill.get_node("api:payments")
if node:
    print(f"Name: {node['name']}")
    print(f"Properties: {node['properties']}")
```

---

#### `delete_node(node_id, agent_id)`

删除节点。

**返回：** `bool`

---

#### `list_nodes(type, namespace, agent_id)`

列出节点。

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `type` | string | 类型过滤 |
| `namespace` | string | 命名空间过滤 |
| `agent_id` | string | 调用者 ID |

**返回：** `List[dict]`

**示例：**
```python
apis = await skill.list_nodes(type="api")
for api in apis:
    print(api['name'])
```

---

### 边操作

#### `add_edge(edge_id, source_id, target_id, edge_type, weight, properties, namespace, agent_id)`

添加关系边。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `edge_id` | string | - | 边 ID |
| `source_id` | string | - | 源节点 |
| `target_id` | string | - | 目标节点 |
| `edge_type` | string | - | 关系类型 |
| `weight` | float | `1.0` | 权重 |
| `properties` | dict | `None` | 属性 |
| `namespace` | string | `"public"` | 命名空间 |

**示例：**
```python
await skill.add_edge(
    "e1",
    "func:process_payment",
    "api:payments",
    "calls",
    weight=1.0
)
```

---

#### `get_outgoing_edges(node_id, edge_type, namespace)`

获取出边（该节点指向其他节点）。

**返回：** `List[dict]`

---

#### `get_incoming_edges(node_id, edge_type, namespace)`

获取入边（其他节点指向该节点）。

---

### 属性操作

#### `set_property(entity_id, key, value, entity_type, namespace, agent_id)`

设置属性。

**示例：**
```python
await skill.set_property("api:payments", "rate_limit", "100/min")
await skill.set_property("api:payments", "endpoints", ["/charge", "/refund"])
```

---

#### `get_property(entity_id, key, entity_type)`

获取单个属性。

---

#### `get_all_properties(entity_id, entity_type)`

获取所有属性。

**返回：** `dict`

---

### 全文搜索

#### `index_document(entity_id, content, namespace, agent_id)`

索引文档用于搜索。

**示例：**
```python
await skill.index_document("api:payments", """
    Payment API handles credit card processing via Stripe.
    Endpoints: POST /charge, GET /refunds, POST /webhooks
    Rate limit: 100 requests/minute
    Authentication: Bearer token required
""")
```

---

#### `search(query, limit, namespaces, agent_id)`

全文搜索。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `query` | string | - | 搜索词 |
| `limit` | int | `10` | 结果数量 |
| `namespaces` | List[string] | `None` | 命名空间列表 |
| `agent_id` | string | `None` | 调用者 ID |

**返回：** `List[dict]` - 包含 `entity_id`, `content`, `namespace`, `type`, `name`

**示例：**
```python
results = await skill.search("stripe payment", limit=5)
for r in results:
    print(f"{r['entity_id']}: {r['content'][:100]}")
```

---

### 图查询

#### `get_dependency_chain(node_id, max_depth, edge_types)`

获取依赖链（递归查询）。

**参数：**
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `node_id` | string | - | 起始节点 |
| `max_depth` | int | `5` | 最大深度 |
| `edge_types` | List[string] | `None` | 边类型过滤 |

**返回：** `List[dict]` - 边列表，包含 `depth` 字段

**示例：**
```python
# 查找 api:payments 的所有依赖
chain = await skill.get_dependency_chain("api:payments", max_depth=3)
for edge in chain:
    print(f"Depth {edge['depth']}: {edge['source_id']} --[{edge['type']}]--> {edge['target_id']}")
```

---

#### `get_impact_analysis(node_id, max_depth)`

影响分析（反向依赖）。

**返回：** `List[dict]` - 受影响的节点列表

**示例：**
```python
# 如果修改 api:payments，会影响哪些模块？
impacted = await skill.get_impact_analysis("api:payments")
print("受影响的模块：")
for node in impacted:
    print(f"  - {node['name']} ({node['id']})")
```

---

### 失败追踪

#### `record_failure(fingerprint, error_type, context, notes)`

记录失败。

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `fingerprint` | string | 错误指纹（如 "modulenotfound:dotenv"） |
| `error_type` | string | 错误类型（"build_failure", "test_failure", "review_rejection"） |
| `context` | dict | 上下文（环境、版本、依赖等） |
| `notes` | string | 备注 |

**返回：** `string` - 失败记录 ID

**示例：**
```python
failure_id = await skill.record_failure(
    "modulenotfound:python-dotenv",
    "build_failure",
    {"package": "python-dotenv", "env": "ci", "python": "3.11"},
    notes="Missing dev dependency in requirements.txt"
)
```

---

#### `get_failure_prevention(fingerprint)`

获取失败预防信息。

**返回：** `dict` 或 `None`，包含：
- `id`, `fingerprint`, `error_type`
- `occurrence_count` - 发生次数
- `first_seen`, `last_seen` - 时间
- `resolved` - 是否已解决
- `prevention_rules` - 预防规则列表
- `fixes` - 修复方案列表

**示例：**
```python
prevention = await skill.get_failure_prevention("modulenotfound:dotenv")
if prevention:
    print(f"⚠️ 这个错误发生过 {prevention['occurrence_count']} 次")
    if prevention['resolved']:
        print(f"✅ 已通过 {prevention['resolution_id']} 解决")
    for rule in prevention.get('prevention_rules', []):
        print(f"💡 预防：{rule['action']}")
```

---

#### `add_prevention_rule(failure_fingerprint, trigger_condition, action)`

添加预防规则。

**示例：**
```python
await skill.add_prevention_rule(
    "modulenotfound:python-dotenv",
    '{"package": "python-dotenv"}',
    "Run `pip install python-dotenv` before building"
)
```

---

#### `resolve_failure(failure_id, fix_node_id, success)`

标记失败为已解决。

---

#### `get_unresolved_failures(error_type)`

获取未解决的失败列表。

---

### 命名空间权限

#### `set_namespace_permissions(agent_id, read_namespaces, write_namespaces)`

配置 Agent 的命名空间权限。

**示例：**
```python
await skill.set_namespace_permissions(
    "agent:coder",
    read_namespaces=["public", "coder"],
    write_namespaces=["coder"]
)
```

---

### 维护操作

#### `get_stats()`

获取数据库统计。

**返回：** `dict` - 包含各表记录数

```python
stats = await skill.get_stats()
print(f"Nodes: {stats['nodes']}")
print(f"Edges: {stats['edges']}")
print(f"Failures: {stats['failures']}")
```

---

#### `vacuum()`

压缩数据库，回收空间。

---

#### `reindex()`

重建索引。

---

#### `query_custom(sql, params)`

执行自定义只读 SQL 查询。

**限制：** 仅允许 `SELECT` 语句

**示例：**
```python
results = await skill.query_custom(
    "SELECT id, name FROM nodes WHERE type = ? AND namespace = ?",
    ["api", "public"]
)
```

---

## 💡 使用场景

### 场景 1：代码知识库

```python
# 记录 API 结构
await skill.add_node("api:users", "api", "Users API")
await skill.add_node("func:get_user", "function", "get_user()")
await skill.add_node("class:User", "class", "User")

# 建立关系
await skill.add_edge("e1", "func:get_user", "api:users", "implements")
await skill.add_edge("e2", "func:get_user", "class:User", "returns")

# 添加文档
await skill.index_document("api:users", """
    Users API provides CRUD operations for user management.
    Endpoints: GET /users, POST /users, PUT /users/:id, DELETE /users/:id
    Authentication: JWT required
    Rate limit: 100 requests/minute
""")

# 查询
chain = await skill.get_dependency_chain("api:users")
```

---

### 场景 2：失败预防

```python
# 记录构建失败
await skill.record_failure(
    "test:auth_fails",
    "test_failure",
    {"test": "test_login", "error": "401 Unauthorized"},
    notes="JWT token expired"
)

# 添加预防规则
await skill.add_prevention_rule(
    "test:auth_fails",
    '{"test_name": "test_login"}',
    "Refresh JWT token before running auth tests"
)

# 下次运行前检查
prevention = await skill.get_failure_prevention("test:auth_fails")
if prevention and not prevention['resolved']:
    print(f"⚠️ 警告：test_login 曾经失败 {prevention['occurrence_count']} 次")
```

---

### 场景 3：Agent 团队协作

```python
# Coder Agent 记录实现
await skill.set_namespace_permissions("agent:coder", 
    read_namespaces=["public", "coder"],
    write_namespaces=["coder"])

await skill.add_node("feature:auth", "feature", "Authentication Feature",
    namespace="coder")

# Reviewer Agent 记录评审
await skill.set_namespace_permissions("agent:reviewer",
    read_namespaces=["public", "coder", "reviewer"],
    write_namespaces=["reviewer"])

await skill.add_node("review:auth", "review", "Code Review for Auth",
    namespace="reviewer")
await skill.add_edge("e1", "review:auth", "feature:auth", "reviews")

# 公共知识共享
await skill.add_node("doc:auth-guide", "document", "Auth Guide",
    namespace="public")
```

---

### 场景 4：依赖分析

```python
# 构建依赖图
await skill.add_node("module:auth", "module", "Auth Module")
await skill.add_node("lib:jwt", "library", "JWT Library")
await skill.add_node("lib:bcrypt", "library", "Bcrypt Library")

await skill.add_edge("e1", "module:auth", "lib:jwt", "depends_on")
await skill.add_edge("e2", "module:auth", "lib:bcrypt", "depends_on")

# 影响分析：如果修改 jwt 库，会影响什么？
impacted = await skill.get_impact_analysis("lib:jwt")
print("修改 JWT 库将影响：")
for node in impacted:
    print(f"  - {node['name']}")
```

---

## 🔒 安全与权限

### 命名空间隔离

```
┌─────────────────────────────────────────────────────────┐
│                    Namespace Hierarchy                   │
├─────────────────────────────────────────────────────────┤
│  public          - 所有 Agent 可读                       │
│  ├── coder       - Coder Agent 私有                      │
│  ├── reviewer    - Reviewer Agent 私有                   │
│  ├── tester      - Tester Agent 私有                     │
│  └── ...         - 其他 Agent 私有                       │
└─────────────────────────────────────────────────────────┘
```

### 权限检查

```python
# 写入时检查
await skill.add_node("secret:api_key", "secret", "API Key",
    namespace="coder",  # 只有 coder 能写
    agent_id="agent:coder")

# 读取时检查
node = await skill.get_node("secret:api_key",
    agent_id="agent:reviewer")  # 返回 None（无权限）
```

---

## 📊 性能优化

### 1. 批量操作

```python
# ✅ 推荐：批量添加
for i in range(100):
    await skill.add_node(f"node:{i}", "type", f"Node {i}")

# ❌ 避免：频繁初始化
for i in range(100):
    skill = StructuredOntologySkill()
    await skill.initialize()
    await skill.add_node(...)
    await skill.close()
```

### 2. 索引优化

```python
# 定期重建索引
await skill.reindex()

# 压缩数据库
await skill.vacuum()
```

### 3. 查询限制

```python
# ✅ 限制深度
chain = await skill.get_dependency_chain("node", max_depth=3)

# ✅ 过滤类型
chain = await skill.get_dependency_chain("node", 
    edge_types=["depends_on", "calls"])
```

---

## 🧪 测试

运行测试套件：

```bash
cd skills/structured-ontology
pip install pytest pytest-asyncio
pytest tests/test_skill.py -v
```

**测试覆盖：**
- ✅ 节点增删查
- ✅ 边操作
- ✅ 属性管理
- ✅ 全文搜索
- ✅ 依赖链查询
- ✅ 失败追踪
- ✅ 命名空间隔离
- ✅ 权限控制

---

## 📁 文件结构

```
skills/structured-ontology/
├── SKILL.md              # OpenClaw 技能说明
├── DOCS.md               # 本文档
├── README.md             # 快速开始
├── skill.py              # 主实现
├── db.py                 # 数据库封装
├── schema.sql            # SQLite 架构
├── skill.yaml            # 技能元数据
├── _meta.json            # 元数据
├── pytest.ini            # 测试配置
├── .gitignore            # Git 忽略
└── tests/
    └── test_skill.py     # 测试套件
```

---

## 🔧 故障排除

### 问题 1：权限错误

```
PermissionError: Agent agent:X cannot write to namespace Y
```

**解决：** 确保设置了正确的命名空间权限：
```python
await skill.set_namespace_permissions("agent:X",
    read_namespaces=["public", "Y"],
    write_namespaces=["Y"])
```

---

### 问题 2：搜索无结果

**检查：**
1. 文档是否已索引：`await skill.index_document(...)`
2. 命名空间是否正确
3. 搜索词是否匹配

---

### 问题 3：数据库锁定

**解决：**
```python
# 确保关闭连接
await skill.close()

# 或重新初始化
skill = StructuredOntologySkill(config)
await skill.initialize()
```

---

## 📝 最佳实践

### 1. 命名规范

```python
# ✅ 推荐
"api:users"           # 类型：名称
"func:get_user"       # 函数
"class:User"          # 类
"failure:auth_error"  # 失败记录

# ❌ 避免
"users"               # 缺少类型前缀
"getUser"             # 命名不一致
```

### 2. 文档化

```python
# ✅ 为重要节点添加文档
await skill.index_document("api:users", """
    Users API - User management endpoints
    - GET /users - List all users
    - POST /users - Create user
    - Authentication: JWT required
""")
```

### 3. 失败指纹

```python
# ✅ 使用有意义的指纹
"modulenotfound:python-dotenv"
"test:login_timeout"

# ❌ 避免过于泛化
"error"
"failure"
```

### 4. 定期清理

```python
# 每周清理一次
await skill.vacuum()
await skill.reindex()
```

---

## 📚 相关资源

- [SQLite 文档](https://www.sqlite.org/docs.html)
- [FTS5 全文搜索](https://www.sqlite.org/fts5.html)
- [递归 CTE](https://www.sqlite.org/lang_with.html)
- [OpenClaw Skills](https://docs.openclaw.ai/skills)

---

**版本：** 1.0.0  
**作者：** workspace-coordinator  
**许可证：** MIT
