---
name: structured-ontology
description: SQLite-based knowledge base for Agent Teams with full-text search, graph queries, failure tracking, and private namespaces. Use when: (1) Storing structured knowledge (entities, relationships, properties), (2) Searching across documents and code, (3) Analyzing dependencies and impact, (4) Tracking failures and prevention, (5) Isolating agent knowledge with namespaces.
---

# Structured Ontology Skill

Knowledge base skill for OpenClaw Agent Teams. Provides structured storage, full-text search, graph traversal, and failure tracking.

## Quick Start

```python
from skill import StructuredOntologySkill

skill = StructuredOntologySkill({"db_path": "~/.openclaw/workspace/knowledge.db"})
await skill.initialize()

# Add knowledge
await skill.add_node("api:users", "api", "Users API")
await skill.add_edge("e1", "func:get_user", "api:users", "calls")
await skill.index_document("api:users", "User management API with CRUD endpoints")

# Query
results = await skill.search("user management")
chain = await skill.get_dependency_chain("api:users")
```

## Core Concepts

### Nodes (Entities)
- **id**: Unique identifier (e.g., `api:users`, `class:User`, `func:process_payment`)
- **type**: Category (api/class/function/decision/failure/fix/document...)
- **name**: Human-readable name
- **namespace**: Isolation scope (`public` or agent-specific)

### Edges (Relationships)
- **source_id**: Source node ID
- **target_id**: Target node ID
- **type**: Relationship type (depends_on/calls/implements/prevents/uses/extends...)
- **weight**: Edge weight for ranking (default: 1.0)

### Properties
- Key-value pairs attached to nodes or edges
- Supports simple types and JSON objects

### Namespaces
- **public**: Shared knowledge accessible to all agents
- **agent-specific**: Private knowledge (e.g., `coder`, `reviewer`, `tester`)

## Workflows

### 1. Store Code Knowledge

```python
# Document an API
await skill.add_node("api:payments", "api", "Payment Processing API",
    properties={"version": "2.0", "deprecated": False})

await skill.index_document("api:payments", """
    Payment API handles credit card processing via Stripe.
    Endpoints: POST /charge, GET /refunds, POST /webhooks
    Rate limit: 100 requests/minute
""")

# Link to dependencies
await skill.add_node("svc:stripe", "service", "Stripe")
await skill.add_edge("e1", "api:payments", "svc:stripe", "uses")
```

### 2. Track Dependencies

```python
# Build dependency graph
await skill.add_node("module:auth", "module", "Authentication Module")
await skill.add_node("lib:jwt", "library", "JWT Library")
await skill.add_edge("e1", "module:auth", "lib:jwt", "depends_on")

# Query: what does this depend on?
deps = await skill.get_dependency_chain("module:auth", max_depth=5)

# Query: what breaks if I change this?
impacted = await skill.get_impact_analysis("lib:jwt")
```

### 3. Search Knowledge

```python
# Index content
await skill.index_document("func:auth", 
    "authenticate user with OAuth2 and JWT tokens")

# Search
results = await skill.search("OAuth2 authentication", limit=10)
for r in results:
    print(f"{r['entity_id']}: {r['content'][:200]}")

# Search specific namespaces
results = await skill.search("config", namespaces=["public", "coder"])
```

### 4. Track Failures

```python
# Record a failure
failure_id = await skill.record_failure(
    "modulenotfound:dotenv",
    "build_failure",
    {"package": "python-dotenv", "env": "ci", "python": "3.11"},
    notes="Missing dev dependency"
)

# Check prevention before running similar task
prevention = await skill.get_failure_prevention("modulenotfound:dotenv")
if prevention:
    print(f"⚠️ This failed {prevention['occurrence_count']} times before")
    for rule in prevention.get('prevention_rules', []):
        print(f"💡 Prevention: {rule['action']}")

# Add prevention rule
await skill.add_prevention_rule(
    "modulenotfound:dotenv",
    '{"package": "python-dotenv"}',
    "Run `pip install python-dotenv` first"
)

# Resolve after fix
await skill.add_node("fix:dotenv", "fix", "Add dotenv to requirements.txt")
await skill.resolve_failure(failure_id, "fix:dotenv", success=True)
```

### 5. Namespace Isolation

```python
# Configure agent permissions
await skill.set_namespace_permissions(
    "agent:coder",
    read_namespaces=["public", "coder"],
    write_namespaces=["coder"]
)

# Store private config
await skill.add_node("config:api_key", "secret", "Stripe API Key",
    namespace="coder")  # Only coder agent can access

# Public knowledge
await skill.add_node("doc:readme", "document", "README",
    namespace="public")  # Everyone can read
```

## Methods

### Node Operations
| Method | Description |
|--------|-------------|
| `add_node(id, type, name, properties, namespace)` | Add entity |
| `get_node(id, namespace)` | Get entity info |
| `delete_node(id)` | Delete entity |
| `list_nodes(type, namespace)` | List with filters |

### Edge Operations
| Method | Description |
|--------|-------------|
| `add_edge(id, source, target, type, weight, namespace)` | Add relationship |
| `get_edge(id)` | Get edge info |
| `get_outgoing_edges(node_id, type, namespace)` | Get outgoing |
| `get_incoming_edges(node_id, type, namespace)` | Get incoming |

### Property Operations
| Method | Description |
|--------|-------------|
| `set_property(entity_id, key, value, entity_type)` | Set property |
| `get_property(entity_id, key, entity_type)` | Get property |
| `get_all_properties(entity_id, entity_type)` | Get all |

### Search Operations
| Method | Description |
|--------|-------------|
| `index_document(entity_id, content, namespace)` | Index for search |
| `search(query, limit, namespaces)` | Full-text search |
| `unindex_document(entity_id)` | Remove from index |

### Graph Operations
| Method | Description |
|--------|-------------|
| `get_dependency_chain(node_id, max_depth, edge_types)` | Dependency traversal |
| `get_impact_analysis(node_id, max_depth)` | Reverse dependencies |

### Failure Operations
| Method | Description |
|--------|-------------|
| `record_failure(fingerprint, error_type, context, notes)` | Record failure |
| `get_failure_prevention(fingerprint)` | Get failure + prevention |
| `resolve_failure(failure_id, fix_node_id, success)` | Mark resolved |
| `get_unresolved_failures(error_type)` | List unresolved |
| `add_prevention_rule(fingerprint, condition, action)` | Add rule |

### Maintenance
| Method | Description |
|--------|-------------|
| `get_stats()` | Database statistics |
| `vacuum()` | Reclaim space |
| `reindex()` | Rebuild indexes |
| `query_custom(sql, params)` | Custom SELECT query |

## Integration with Agent Teams

### For Coder Agent
```python
# Track code structure
await skill.add_node("file:auth.py", "file", "auth.py")
await skill.add_node("func:login", "function", "login()")
await skill.add_edge("e1", "file:auth.py", "func:login", "contains")

# Record build failures
await skill.record_failure("build:error:123", "build_failure",
    {"file": "auth.py", "line": 42, "error": "SyntaxError"})
```

### For Reviewer Agent
```python
# Track review decisions
await skill.add_node("pr:456", "pull_request", "PR #456")
await skill.add_node("decision:approve", "decision", "Approved")
await skill.add_edge("e1", "pr:456", "decision:approve", "result")

# Search similar past reviews
results = await skill.search("security vulnerability authentication")
```

### For Tester Agent
```python
# Track test failures
await skill.record_failure("test:login_fails", "test_failure",
    {"test": "test_login", "expected": "200", "got": "500"})

# Link to fix
await skill.add_node("fix:login_timeout", "fix", "Increase login timeout")
await skill.resolve_failure("failure:...", "fix:login_timeout")
```

## Files

| File | Purpose |
|------|---------|
| `skill.py` | Main skill implementation |
| `db.py` | Database operations wrapper |
| `schema.sql` | SQLite schema |
| `skill.yaml` | Skill metadata |
| `tests/test_skill.py` | Test suite |

## Performance Tips

1. **Batch writes**: Group related operations in transactions
2. **Limit depth**: Use `max_depth` in graph queries
3. **Namespace filtering**: Filter early in searches
4. **Periodic vacuum**: Run `vacuum()` during low-traffic periods
5. **WAL mode**: Enabled by default for concurrency

## Security

- All queries use parameterized statements (no SQL injection)
- Namespace permissions control access
- Custom queries restricted to SELECT only
- Sensitive data should use private namespaces
