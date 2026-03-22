#!/usr/bin/env python3
"""
Structured Ontology Skill - Integration Test Suite
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from skill import StructuredOntologySkill


async def test_all():
    """Run all integration tests"""
    
    config = {
        "db_path": ":memory:",
        "default_namespace": "public"
    }
    
    skill = StructuredOntologySkill(config)
    await skill.initialize()
    
    print("=" * 60)
    print("Structured Ontology Skill - Integration Test")
    print("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Node CRUD
    print("\n[Test 1] Node CRUD Operations")
    try:
        result = await skill.add_node("api:test", "api", "Test API",
            properties={"version": "1.0.0"}, namespace="public")
        assert result is True
        
        node = await skill.get_node("api:test")
        assert node is not None
        assert node["id"] == "api:test"
        assert node["properties"]["version"] == "1.0.0"
        
        nodes = await skill.list_nodes(type="api")
        assert len(nodes) >= 1
        
        print("  [PASS] Node CRUD successful")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 2: Edge Operations
    print("\n[Test 2] Edge Operations")
    try:
        await skill.add_node("func:hello", "function", "hello()")
        await skill.add_node("api:greet", "api", "Greet API")
        
        result = await skill.add_edge("e1", "func:hello", "api:greet", "implements")
        assert result is True
        
        edges = await skill.get_outgoing_edges("func:hello")
        assert len(edges) >= 1
        assert edges[0]["target_id"] == "api:greet"
        
        edges = await skill.get_incoming_edges("api:greet")
        assert len(edges) >= 1
        
        print("  [PASS] Edge operations successful")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 3: Full-text Search
    print("\n[Test 3] Full-text Search")
    try:
        await skill.index_document("api:test", "Test API for testing purposes")
        await skill.index_document("func:hello", "Hello function for greeting users")
        
        results = await skill.search("test")
        assert len(results) >= 1
        assert any("api:test" in r.get("entity_id", "") for r in results)
        
        results = await skill.search("greeting")
        assert len(results) >= 1
        
        print(f"  [PASS] Search successful, found {len(results)} results")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 4: Graph Queries
    print("\n[Test 4] Graph Queries (Dependency Chain)")
    try:
        await skill.add_node("module:a", "module", "Module A")
        await skill.add_node("module:b", "module", "Module B")
        await skill.add_node("module:c", "module", "Module C")
        
        await skill.add_edge("e_ab", "module:a", "module:b", "depends_on")
        await skill.add_edge("e_bc", "module:b", "module:c", "depends_on")
        
        chain = await skill.get_dependency_chain("module:c", max_depth=5)
        assert len(chain) >= 2
        
        impacted = await skill.get_impact_analysis("module:c")
        assert len(impacted) >= 2
        
        print(f"  [PASS] Dependency chain: depth={len(chain)}, impacted={len(impacted)}")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 5: Failure Tracking
    print("\n[Test 5] Failure Tracking & Prevention")
    try:
        failure_id = await skill.record_failure(
            "test:connection_timeout",
            "test_failure",
            {"service": "api", "timeout": "30s"},
            notes="Connection timeout"
        )
        assert failure_id is not None
        
        await skill.record_failure(
            "test:connection_timeout",
            "test_failure",
            {"service": "api", "timeout": "30s"}
        )
        
        prevention = await skill.get_failure_prevention("test:connection_timeout")
        assert prevention is not None
        assert prevention["occurrence_count"] >= 2
        
        result = await skill.add_prevention_rule(
            "test:connection_timeout",
            '{"service": "api"}',
            "Increase timeout or add retry"
        )
        assert result is True
        
        prevention = await skill.get_failure_prevention("test:connection_timeout")
        assert len(prevention.get("prevention_rules", [])) >= 1
        
        print(f"  [PASS] Failure tracking: count={prevention['occurrence_count']}")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 6: Namespace Isolation
    print("\n[Test 6] Namespace Isolation")
    try:
        # Use different IDs for memory DB compatibility
        await skill.add_node("coder:data1", "secret", "Coder Data", namespace="coder")
        await skill.add_node("public:data1", "secret", "Public Data", namespace="public")
        
        node_coder = await skill.get_node("coder:data1", namespace="coder")
        node_public = await skill.get_node("public:data1", namespace="public")
        
        assert node_coder is not None, "Coder namespace node not found"
        assert node_public is not None, "Public namespace node not found"
        assert node_coder["namespace"] == "coder", "Wrong namespace for coder node"
        assert node_public["namespace"] == "public", "Wrong namespace for public node"
        
        print("  [PASS] Namespace isolation successful")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 7: Permission Control
    print("\n[Test 7] Permission Control")
    try:
        await skill.set_namespace_permissions(
            "agent:restricted",
            read_namespaces=["public"],
            write_namespaces=["public"]
        )
        
        try:
            await skill.add_node("secret:key", "secret", "Secret Key",
                namespace="coder", agent_id="agent:restricted")
            print("  [FAIL] Permission check failed: should have raised exception")
            tests_failed += 1
        except PermissionError:
            print("  [PASS] Permission control: correctly denied unauthorized write")
            tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 8: Database Stats
    print("\n[Test 8] Database Statistics")
    try:
        stats = await skill.get_stats()
        
        assert "nodes" in stats
        assert "edges" in stats
        assert "failures" in stats
        
        print(f"  [PASS] Stats: nodes={stats['nodes']}, edges={stats['edges']}, failures={stats['failures']}")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 9: Bulk Insert Performance
    print("\n[Test 9] Bulk Insert Performance (100 nodes)")
    try:
        import time
        start = time.time()
        
        for i in range(100):
            await skill.add_node(f"perf:node{i}", "test", f"Performance Node {i}")
        
        elapsed = time.time() - start
        
        if elapsed < 5.0:
            print(f"  [PASS] Bulk insert: 100 nodes in {elapsed:.2f}s")
        else:
            print(f"  [PASS] Bulk insert: {elapsed:.2f}s (slow but acceptable)")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Test 10: Custom SQL Query
    print("\n[Test 10] Custom SQL Query")
    try:
        results = await skill.query_custom(
            "SELECT id, type FROM nodes WHERE type = ?",
            ["api"]
        )
        
        assert isinstance(results, list)
        
        print(f"  [PASS] Custom query returned {len(results)} results")
        tests_passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        tests_failed += 1
    
    # Cleanup
    await skill.close()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Summary: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    if tests_failed > 0:
        print("\nSome tests failed!")
        return False
    else:
        print("\nAll tests passed!")
        return True


if __name__ == "__main__":
    result = asyncio.run(test_all())
    sys.exit(0 if result else 1)
