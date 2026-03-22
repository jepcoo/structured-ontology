"""
Test suite for structured-ontology skill.
Uses in-memory SQLite database for isolation.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill import StructuredOntologySkill


@pytest.fixture
async def skill():
    """Create skill instance with in-memory database."""
    config = {"db_path": ":memory:", "default_namespace": "public"}
    s = StructuredOntologySkill(config)
    await s.initialize()
    yield s
    await s.close()


@pytest.fixture
async def skill_with_data(skill):
    """Create skill instance with sample data."""
    # Add nodes
    await skill.add_node("api:users", "api", "Users API", namespace="public")
    await skill.add_node("func:get_user", "function", "get_user", namespace="public")
    await skill.add_node("func:create_user", "function", "create_user", namespace="public")
    await skill.add_node("class:User", "class", "User", namespace="public")
    
    # Add edges
    await skill.add_edge("e1", "func:get_user", "api:users", "calls", namespace="public")
    await skill.add_edge("e2", "func:create_user", "api:users", "calls", namespace="public")
    await skill.add_edge("e3", "func:get_user", "class:User", "returns", namespace="public")
    
    # Add properties
    await skill.set_property("api:users", "version", "1.0.0")
    await skill.set_property("api:users", "deprecated", False)
    
    # Index for search
    await skill.index_document("api:users", "Users API provides user management endpoints")
    await skill.index_document("func:get_user", "Retrieve a user by ID from the database")
    
    yield skill


# ========== Node Tests ==========

@pytest.mark.asyncio
async def test_add_and_get_node(skill):
    """Test adding and retrieving a node."""
    success = await skill.add_node(
        "api:users", "api", "Users API",
        properties={"version": "1.0.0"},
        namespace="public"
    )
    assert success is True
    
    node = await skill.get_node("api:users")
    assert node is not None
    assert node["id"] == "api:users"
    assert node["type"] == "api"
    assert node["namespace"] == "public"
    assert node["properties"]["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_delete_node(skill):
    """Test deleting a node."""
    await skill.add_node("temp:node", "temp", "Temporary Node")
    
    success = await skill.delete_node("temp:node")
    assert success is True
    
    node = await skill.get_node("temp:node")
    assert node is None


@pytest.mark.asyncio
async def test_list_nodes(skill):
    """Test listing nodes with filters."""
    await skill.add_node("api:users", "api", "Users API")
    await skill.add_node("api:orders", "api", "Orders API")
    await skill.add_node("func:auth", "function", "authenticate")
    
    all_nodes = await skill.list_nodes()
    assert len(all_nodes) == 3
    
    api_nodes = await skill.list_nodes(type="api")
    assert len(api_nodes) == 2
    
    func_nodes = await skill.list_nodes(type="function")
    assert len(func_nodes) == 1


# ========== Edge Tests ==========

@pytest.mark.asyncio
async def test_add_and_get_edge(skill):
    """Test adding and retrieving an edge."""
    await skill.add_node("a", "class", "ClassA")
    await skill.add_node("b", "class", "ClassB")
    
    success = await skill.add_edge("e1", "a", "b", "extends")
    assert success is True
    
    edge = await skill.get_edge("e1")
    assert edge is not None
    assert edge["source_id"] == "a"
    assert edge["target_id"] == "b"
    assert edge["type"] == "extends"


@pytest.mark.asyncio
async def test_get_outgoing_edges(skill_with_data):
    """Test getting outgoing edges from a node."""
    edges = await skill_with_data.get_outgoing_edges("func:get_user")
    assert len(edges) == 2
    
    # Filter by type
    returns_edges = await skill_with_data.get_outgoing_edges("func:get_user", edge_type="returns")
    assert len(returns_edges) == 1
    assert returns_edges[0]["target_id"] == "class:User"


@pytest.mark.asyncio
async def test_get_incoming_edges(skill_with_data):
    """Test getting incoming edges to a node."""
    edges = await skill_with_data.get_incoming_edges("api:users")
    assert len(edges) == 2  # Both functions call this API


# ========== Property Tests ==========

@pytest.mark.asyncio
async def test_set_and_get_property(skill):
    """Test setting and getting properties."""
    await skill.add_node("node1", "class", "TestClass")
    
    success = await skill.set_property("node1", "version", "2.0.0")
    assert success is True
    
    value = await skill.get_property("node1", "version")
    assert value == "2.0.0"
    
    # Test complex property
    await skill.set_property("node1", "metadata", {"author": "test", "tags": ["a", "b"]})
    metadata = await skill.get_property("node1", "metadata")
    assert metadata["author"] == "test"
    assert len(metadata["tags"]) == 2


@pytest.mark.asyncio
async def test_get_all_properties(skill):
    """Test getting all properties for an entity."""
    await skill.add_node("node1", "class", "TestClass")
    await skill.set_property("node1", "prop1", "value1")
    await skill.set_property("node1", "prop2", "value2")
    await skill.set_property("node1", "prop3", {"nested": "value"})
    
    props = await skill.get_all_properties("node1")
    assert len(props) == 3
    assert props["prop1"] == "value1"
    assert props["prop3"]["nested"] == "value"


# ========== Full-Text Search Tests ==========

@pytest.mark.asyncio
async def test_search(skill_with_data):
    """Test full-text search."""
    results = await skill_with_data.search("user")
    assert len(results) >= 1
    
    # Check that results contain expected entity
    entity_ids = [r["entity_id"] for r in results]
    assert "api:users" in entity_ids or "func:get_user" in entity_ids


@pytest.mark.asyncio
async def test_search_with_namespaces(skill):
    """Test search with namespace filtering."""
    await skill.add_node("public:doc", "document", "Public Doc")
    await skill.add_node("private:doc", "document", "Private Doc")
    
    await skill.index_document("public:doc", "This is public content", namespace="public")
    await skill.index_document("private:doc", "This is private content", namespace="private")
    
    # Search only public namespace
    results = await skill.search("content", namespaces=["public"])
    assert len(results) == 1
    assert results[0]["entity_id"] == "public:doc"


# ========== Graph Query Tests ==========

@pytest.mark.asyncio
async def test_dependency_chain(skill_with_data):
    """Test dependency chain query."""
    chain = await skill_with_data.get_dependency_chain("api:users")
    
    assert len(chain) >= 2  # At least the two functions that call it
    
    # Check chain structure
    for edge in chain:
        assert "source_id" in edge
        assert "target_id" in edge
        assert "type" in edge
        assert "depth" in edge


@pytest.mark.asyncio
async def test_impact_analysis(skill_with_data):
    """Test impact analysis (reverse dependencies)."""
    impacted = await skill_with_data.get_impact_analysis("class:User")
    
    # func:get_user returns User, so it should be impacted
    impacted_ids = [n["id"] for n in impacted]
    assert "func:get_user" in impacted_ids


# ========== Failure Tracking Tests ==========

@pytest.mark.asyncio
async def test_record_failure(skill):
    """Test recording a failure."""
    fingerprint = "modulenotfound:xyz"
    context = {"package": "xyz", "env": "dev", "version": "1.0.0"}
    
    failure_id = await skill.record_failure(
        fingerprint, "build_failure", context,
        notes="Missing dependency"
    )
    
    assert failure_id is not None
    assert failure_id.startswith("failure:")


@pytest.mark.asyncio
async def test_failure_prevention(skill):
    """Test failure prevention lookup."""
    fingerprint = "test:failure:abc"
    
    # Record failure
    await skill.record_failure(
        fingerprint, "test_failure",
        {"test": "test_something", "env": "ci"}
    )
    
    # Add prevention rule
    await skill.add_prevention_rule(
        fingerprint,
        '{"test_name": "test_something"}',
        "Run `npm install` before tests"
    )
    
    # Get prevention info
    prevention = await skill.get_failure_prevention(fingerprint)
    
    assert prevention is not None
    assert prevention["occurrence_count"] == 1
    assert len(prevention["prevention_rules"]) == 1


@pytest.mark.asyncio
async def test_resolve_failure(skill):
    """Test resolving a failure."""
    fingerprint = "build:error:123"
    
    # Record failure
    failure_id = await skill.record_failure(
        fingerprint, "build_failure", {"error": "syntax error"}
    )
    
    # Add fix node
    await skill.add_node("fix:123", "fix", "Fix syntax error")
    
    # Resolve failure
    success = await skill.resolve_failure(failure_id, "fix:123", success=True)
    assert success is True
    
    # Verify resolution
    prevention = await skill.get_failure_prevention(fingerprint)
    assert prevention["resolved"] == 1
    assert prevention["resolution_id"] == "fix:123"


@pytest.mark.asyncio
async def test_get_unresolved_failures(skill):
    """Test getting unresolved failures."""
    await skill.record_failure("fail:1", "test_failure", {})
    await skill.record_failure("fail:2", "build_failure", {})
    
    # Record and resolve one
    failure_id = await skill.record_failure("fail:3", "test_failure", {})
    await skill.add_node("fix:3", "fix", "Fix for fail:3")
    await skill.resolve_failure(failure_id, "fix:3")
    
    unresolved = await skill.get_unresolved_failures()
    assert len(unresolved) == 2  # fail:1 and fail:2


# ========== Namespace Isolation Tests ==========

@pytest.mark.asyncio
async def test_namespace_isolation(skill):
    """Test namespace isolation."""
    # Set up agent with limited namespace access
    await skill.set_namespace_permissions(
        "agent:test",
        read_namespaces=["public"],
        write_namespaces=["public"]
    )
    
    # Add node to private namespace (direct access, no agent_id)
    await skill.add_node("priv:1", "secret", "my secret", namespace="coder")
    
    # Query with agent that doesn't have access to coder namespace
    pub_node = await skill.get_node("priv:1", agent_id="agent:test")
    assert pub_node is None
    
    # Query with correct namespace directly - should find it (no agent check)
    priv_node = await skill.get_node("priv:1", namespace="coder")
    assert priv_node is not None
    assert priv_node["namespace"] == "coder"


@pytest.mark.asyncio
async def test_namespace_permissions(skill):
    """Test namespace permission checking."""
    # Set up permissions for coder agent
    await skill.set_namespace_permissions(
        "agent:coder",
        read_namespaces=["public", "coder"],
        write_namespaces=["coder"]
    )
    
    # Set up permissions for other agent (limited)
    await skill.set_namespace_permissions(
        "agent:other",
        read_namespaces=["public"],
        write_namespaces=["public"]
    )
    
    # Add nodes (direct access, no agent_id)
    await skill.add_node("public:node", "public", "Public", namespace="public")
    await skill.add_node("coder:node", "private", "Coder Private", namespace="coder")
    await skill.add_node("other:node", "private", "Other Private", namespace="other")
    
    # Coder agent can read public and coder namespaces
    public_node = await skill.get_node("public:node", agent_id="agent:coder")
    assert public_node is not None
    
    coder_node = await skill.get_node("coder:node", agent_id="agent:coder")
    assert coder_node is not None
    
    # Coder agent cannot read other namespace
    other_node = await skill.get_node("other:node", agent_id="agent:coder")
    assert other_node is None
    
    # Other agent can only read public
    other_pub = await skill.get_node("public:node", agent_id="agent:other")
    assert other_pub is not None
    
    other_coder = await skill.get_node("coder:node", agent_id="agent:other")
    assert other_coder is None


# ========== Custom Query Tests ==========

@pytest.mark.asyncio
async def test_custom_query(skill_with_data):
    """Test custom SQL queries."""
    # Valid SELECT query
    results = await skill_with_data.query_custom(
        "SELECT id, type FROM nodes WHERE type = ?",
        ["api"]
    )
    assert len(results) == 1
    assert results[0]["id"] == "api:users"
    
    # Should reject non-SELECT queries
    with pytest.raises(ValueError):
        await skill_with_data.query_custom("DELETE FROM nodes")
    
    with pytest.raises(ValueError):
        await skill_with_data.query_custom("UPDATE nodes SET name='x'")


# ========== Statistics Tests ==========

@pytest.mark.asyncio
async def test_get_stats(skill_with_data):
    """Test database statistics."""
    stats = await skill_with_data.get_stats()
    
    assert "nodes" in stats
    assert "edges" in stats
    assert "properties" in stats
    
    assert stats["nodes"] >= 4  # We added at least 4 nodes
    assert stats["edges"] >= 3  # We added at least 3 edges


# ========== Integration Tests ==========

@pytest.mark.asyncio
async def test_full_workflow(skill):
    """Test a complete workflow: create, query, search, track failure."""
    # 1. Create knowledge structure
    await skill.add_node("api:payment", "api", "Payment API")
    await skill.add_node("svc:stripe", "service", "Stripe Service")
    await skill.add_node("func:process_payment", "function", "process_payment")
    
    await skill.add_edge("e1", "func:process_payment", "api:payment", "calls")
    await skill.add_edge("e2", "api:payment", "svc:stripe", "uses")
    
    await skill.set_property("api:payment", "version", "2.0.0")
    await skill.set_property("api:payment", "rate_limit", "100/min")
    
    # 2. Index for search
    await skill.index_document("api:payment", 
        "Payment API handles credit card processing via Stripe integration")
    
    # 3. Search
    results = await skill.search("stripe")
    assert len(results) >= 1
    
    # 4. Query dependencies
    chain = await skill.get_dependency_chain("svc:stripe")
    assert len(chain) == 2  # func -> api -> stripe
    
    # 5. Record a failure
    failure_id = await skill.record_failure(
        "stripe:timeout", "integration_failure",
        {"service": "stripe", "error": "timeout", "retry": 3}
    )
    assert failure_id is not None
    
    # 6. Get stats
    stats = await skill.get_stats()
    assert stats["nodes"] == 3
    assert stats["edges"] == 2
    assert stats["failures"] == 1
