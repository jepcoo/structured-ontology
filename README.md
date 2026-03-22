<!-- markdownlint-disable MD033 -->
<p align="center">
 <h1 align="center">📚 Structured Ontology Skill</h1>
 <p align="center">
 SQLite-based knowledge base for AI Agent Teams<br />
 Full‑text search · Graph queries · Failure tracking · Private namespaces
 </p>
 <p align="center">
 <a href="https://github.com/openclaw/skills/structured-ontology"><img src="https://img.shields.io/badge/OpenClaw-Skill-4c9f38?logo=github" alt="OpenClaw Skill"></a>
 <a href="https://www.sqlite.org/index.html"><img src="https://img.shields.io/badge/SQLite-3-blue?logo=sqlite" alt="SQLite"></a>
 <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python"></a>
 <a href="https://github.com/openclaw/skills/structured-ontology/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"></a>
 <a href="#"><img src="https://img.shields.io/badge/tests-31%20passed-brightgreen" alt="Tests"></a>
 <a href="#"><img src="https://img.shields.io/badge/performance-100nodes%2F0.01s-brightgreen" alt="Performance"></a>
 </p>
</p>

---

**Structured Ontology** is a skill for [OpenClaw](https://github.com/openclaw/openclaw) Agent Teams. 
It provides a unified, persistent knowledge base with:

- **Structured storage** – Entities (nodes), relationships (edges), and key‑value properties.
- **Full‑text search** – Fast keyword search with SQLite FTS5.
- **Graph queries** – Recursive CTE for dependency chains and impact analysis.
- **Failure tracking** – Record errors, prevent recurrence, and store fixes.
- **Private namespaces** – Isolate agent knowledge with fine‑grained permissions.

Perfect for code knowledge bases, team collaboration, dependency management, and self‑improving agents.

---

## 📦 Installation

### Using ClawHub (recommended)

```bash
clawhub install structured-ontology
```

### Manual install

Copy the skill folder to your OpenClaw skills directory:

```bash
git clone https://github.com/openclaw/skills/structured-ontology.git
cp -r structured-ontology ~/.openclaw/skills/
```

### Dependencies

No external dependencies – uses Python standard library only:
- `sqlite3` – Database engine (with FTS5 support)
- `asyncio` – Async I/O
- `pathlib`, `json`, `hashlib`, `typing` – Utilities

If you plan to run tests:

```bash
pip install pytest pytest-asyncio
```

---

## ⚙️ Configuration

Add to your OpenClaw configuration file (`~/.openclaw/openclaw.json`):

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

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `db_path` | string | `~/.openclaw/workspace/knowledge.db` | SQLite database file path |
| `default_namespace` | string | `"public"` | Fallback namespace when none is provided |
| `lazy` | boolean | `true` | Load skill on-demand (recommended) |

---

## 🚀 Quick Start

```python
from skill import StructuredOntologySkill

skill = StructuredOntologySkill({"db_path": "~/.openclaw/workspace/knowledge.db"})
await skill.initialize()

# Add a node (entity)
await skill.add_node("api:users", "api", "Users API",
    properties={"version": "1.0.0"})

# Index a document for search
await skill.index_document("api:users",
    "User management API with CRUD operations and OAuth2 authentication")

# Add a relationship
await skill.add_edge("e1", "func:get_user", "api:users", "calls")

# Search
results = await skill.search("user management")
for r in results:
    print(r["entity_id"], r["content"][:100])

# Dependency chain
chain = await skill.get_dependency_chain("api:users", max_depth=3)

# Impact analysis
impacted = await skill.get_impact_analysis("api:users")
print("Impacted:", [n["name"] for n in impacted])

# Record and prevent a failure
await skill.record_failure(
    "modulenotfound:dotenv", "build_failure",
    {"package": "python-dotenv", "env": "ci"},
    notes="Missing dev dependency"
)

prevention = await skill.get_failure_prevention("modulenotfound:dotenv")
if prevention and not prevention["resolved"]:
    print("⚠️ This failure has occurred", prevention["occurrence_count"], "times")

await skill.close()
```

---

## 📖 Core Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Node** | An entity – API, function, class, decision, failure, fix, etc. | `api:users`, `func:login` |
| **Edge** | A relationship between nodes. | `depends_on`, `calls`, `implements`, `prevents` |
| **Property** | Key‑value metadata attached to nodes or edges. | `{"version": "1.0.0"}` |
| **Namespace** | Isolation scope. `public` is shared; others are private. | `public`, `coder`, `reviewer` |
| **Failure Fingerprint** | A hashable string representing an error. | `test:connection_timeout` |
| **Prevention Rule** | Proactive rule to warn/act before repeating a failure. | `{"package": "dotenv"} → "pip install"` |

---

## 🔍 API Reference

### Node Operations

| Method | Description |
|--------|-------------|
| `add_node(id, type, name, properties, namespace)` | Add an entity node. |
| `get_node(id, namespace)` | Retrieve node details (with properties). |
| `delete_node(id)` | Delete a node (cascades edges). |
| `list_nodes(type, namespace)` | List nodes with optional filters. |

### Edge Operations

| Method | Description |
|--------|-------------|
| `add_edge(id, source, target, type, weight, properties, namespace)` | Add a relationship. |
| `get_outgoing_edges(node_id, edge_type, namespace)` | Get edges from a node. |
| `get_incoming_edges(node_id, edge_type, namespace)` | Get edges to a node. |

### Search & Graph

| Method | Description |
|--------|-------------|
| `index_document(entity_id, content, namespace)` | Index text for full‑text search. |
| `search(query, limit, namespaces)` | Perform FTS5 search. |
| `get_dependency_chain(node_id, max_depth, edge_types)` | Recursive traversal of dependencies. |
| `get_impact_analysis(node_id, max_depth)` | Reverse dependencies (what breaks if I change this?). |

### Failure Tracking

| Method | Description |
|--------|-------------|
| `record_failure(fingerprint, error_type, context, notes)` | Log a failure occurrence. |
| `get_failure_prevention(fingerprint)` | Get failure details, occurrence count, and prevention rules. |
| `add_prevention_rule(fingerprint, condition, action)` | Add a proactive rule to warn/act before repeating. |
| `resolve_failure(failure_id, fix_node_id, success)` | Mark a failure as resolved. |

### Administration

| Method | Description |
|--------|-------------|
| `set_namespace_permissions(agent_id, read, write)` | Configure which namespaces an agent can access. |
| `get_stats()` | Database statistics (counts per table). |
| `vacuum()` / `reindex()` | Maintenance operations. |

For detailed documentation, see [DOCS.md](DOCS.md).

---

## 🧪 Testing

Run the test suite to verify everything works:

```bash
cd structured-ontology

# Unit tests
pytest tests/test_skill.py -v

# Integration tests
python test_integration.py
```

**Expected output:**

```
============================================================
Structured Ontology Skill - Integration Test
============================================================

[Test 1] Node CRUD Operations
  [PASS] Node CRUD successful

[Test 2] Edge Operations
  [PASS] Edge operations successful

[Test 3] Full-text Search
  [PASS] Search successful, found 1 results

...

============================================================
Summary: 10 passed, 0 failed
============================================================

All tests passed!
```

---

## 📊 Performance

| Operation | Scale | Latency | Status |
|-----------|-------|---------|--------|
| **Bulk insert** | 100 nodes | <0.01s | ✅ Excellent |
| **Full-text search** | 1000 documents | <0.1s | ✅ Excellent |
| **Dependency chain** | Depth 5 | <0.01s | ✅ Excellent |
| **Memory usage** | Active operations | <30MB | ✅ Efficient |
| **Concurrency** | Multi-agent | WAL mode | ✅ Supported |

---

## 🤝 Use Cases

### 1. Code Knowledge Base

```python
# Document your codebase
await skill.add_node("api:payments", "api", "Payment API")
await skill.add_node("func:process_payment", "function", "process_payment()")
await skill.add_edge("e1", "func:process_payment", "api:payments", "implements")
await skill.index_document("api:payments", "Payment API with Stripe integration")

# Query dependencies
chain = await skill.get_dependency_chain("api:payments")
```

### 2. Team Collaboration

```python
# Each agent has private namespace
await skill.set_namespace_permissions("agent:coder",
    read_namespaces=["public", "coder"],
    write_namespaces=["coder"])

await skill.set_namespace_permissions("agent:reviewer",
    read_namespaces=["public", "coder", "reviewer"],
    write_namespaces=["reviewer"])
```

### 3. Failure Prevention

```python
# Record and learn from failures
await skill.record_failure("test:timeout", "test_failure",
    {"test": "test_api", "timeout": "30s"})

# Check before running similar tasks
prevention = await skill.get_failure_prevention("test:timeout")
if prevention:
    print(f"⚠️ Failed {prevention['occurrence_count']} times before")
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository.
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`).
3. **Make** your changes, add tests.
4. **Run** the test suite and ensure it passes.
5. **Commit** your changes (`git commit -m 'Add some amazing feature'`).
6. **Push** to the branch (`git push origin feature/amazing-feature`).
7. **Open** a Pull Request.

Please also update documentation when adding or changing features.

---

## 📄 License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- [SQLite](https://www.sqlite.org/) – Embedded database engine.
- [OpenClaw](https://github.com/openclaw/openclaw) – Agent framework.
- [pytest](https://docs.pytest.org/) – Testing framework.

---

## 📞 Support

For questions, bug reports, or feature requests, please [open an issue on GitHub](https://github.com/openclaw/skills/structured-ontology/issues).

---

<p align="center">Made with ❤️ for the OpenClaw community</p>
