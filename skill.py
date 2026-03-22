"""
Structured Ontology Skill for OpenClaw.
SQLite-based knowledge base with full-text search, graph queries, failure tracking, and namespaces.
"""

import asyncio
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

from db import Database


class StructuredOntologySkill:
    """
    Structured Ontology Skill - Knowledge base for Agent Teams.
    
    Provides:
    - Structured storage (entities, relationships, properties)
    - Full-text search (SQLite FTS5)
    - Graph queries (recursive CTE for dependency chains)
    - Failure tracking and prevention
    - Private namespaces per agent
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.db_path = self.config.get("db_path", "~/.openclaw/workspace/knowledge.db")
        self.db_path = str(Path(self.db_path).expanduser())
        self.default_namespace = self.config.get("default_namespace", "public")
        self.db = Database(self.db_path)
        self._initialized = False
        self._namespace_permissions: Dict[str, Dict] = {}  # agent_id -> {read: [], write: []}

    async def initialize(self):
        """Initialize the skill and database."""
        if not self._initialized:
            await self.db.init_db()
            self._initialized = True

    async def _check_namespace_permission(self, agent_id: Optional[str],
                                           namespace: str,
                                           permission: str = "read") -> bool:
        """Check if agent has permission for namespace."""
        # No agent_id = direct access, allow all namespaces (for testing/direct usage)
        if not agent_id:
            return True
        
        # Public namespace is always accessible
        if namespace == "public":
            return True
        
        perms = self._namespace_permissions.get(agent_id, {})
        allowed = perms.get(f"{permission}_namespaces", [])
        
        return namespace in allowed

    # ========== Node Operations ==========

    async def add_node(self, node_id: str, type: str, name: str,
                       properties: Optional[Dict] = None,
                       namespace: str = "public",
                       agent_id: Optional[str] = None) -> bool:
        """
        Add an entity node to the ontology.
        
        Args:
            node_id: Unique identifier for the node
            type: Node type (api/class/function/decision/failure/fix...)
            name: Human-readable name
            properties: Optional properties dict
            namespace: Namespace for isolation (default: "public")
            agent_id: Calling agent ID for permission check
        
        Returns:
            bool: Success flag
        """
        await self.initialize()
        
        if not await self._check_namespace_permission(agent_id, namespace, "write"):
            raise PermissionError(f"Agent {agent_id} cannot write to namespace {namespace}")
        
        success = await self.db.add_node(node_id, type, name, namespace)
        
        if success and properties:
            for key, value in properties.items():
                await self.db.set_property(node_id, "node", key, value, namespace)
        
        return success

    async def get_node(self, node_id: str,
                       namespace: Optional[str] = None,
                       agent_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get node information by ID.
        
        Args:
            node_id: Node identifier
            namespace: Optional namespace filter
            agent_id: Calling agent ID for permission check
        
        Returns:
            Node dict or None
        """
        await self.initialize()
        
        node = await self.db.get_node(node_id, namespace)
        
        if node:
            if not await self._check_namespace_permission(agent_id, node["namespace"], "read"):
                return None
            
            # Load properties
            props = await self.db.get_all_properties(node_id, "node")
            node["properties"] = props
        
        return node

    async def delete_node(self, node_id: str,
                          agent_id: Optional[str] = None) -> bool:
        """Delete a node by ID."""
        await self.initialize()
        
        node = await self.db.get_node(node_id)
        if node:
            if not await self._check_namespace_permission(agent_id, node["namespace"], "write"):
                raise PermissionError(f"Agent {agent_id} cannot delete from namespace {node['namespace']}")
            await self.db.unindex_document(node_id)
        
        return await self.db.delete_node(node_id)

    async def list_nodes(self, type: Optional[str] = None,
                         namespace: Optional[str] = None,
                         agent_id: Optional[str] = None) -> List[Dict]:
        """List nodes with optional filters."""
        await self.initialize()
        
        if namespace and not await self._check_namespace_permission(agent_id, namespace, "read"):
            return []
        
        return await self.db.list_nodes(type, namespace)

    # ========== Edge Operations ==========

    async def add_edge(self, edge_id: str, source_id: str, target_id: str,
                       edge_type: str, weight: float = 1.0,
                       properties: Optional[Dict] = None,
                       namespace: str = "public",
                       agent_id: Optional[str] = None) -> bool:
        """
        Add a relationship edge between nodes.
        
        Args:
            edge_id: Unique identifier for the edge
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Relationship type (depends_on/calls/implements/prevents...)
            weight: Edge weight (default: 1.0)
            properties: Optional properties dict
            namespace: Namespace (default: "public")
            agent_id: Calling agent ID
        
        Returns:
            bool: Success flag
        """
        await self.initialize()
        
        if not await self._check_namespace_permission(agent_id, namespace, "write"):
            raise PermissionError(f"Agent {agent_id} cannot write to namespace {namespace}")
        
        success = await self.db.add_edge(edge_id, source_id, target_id,
                                          edge_type, weight, namespace)
        
        if success and properties:
            for key, value in properties.items():
                await self.db.set_property(edge_id, "edge", key, value, namespace)
        
        return success

    async def get_edge(self, edge_id: str) -> Optional[Dict]:
        """Get edge by ID."""
        await self.initialize()
        return await self.db.get_edge(edge_id)

    async def get_outgoing_edges(self, node_id: str,
                                  edge_type: Optional[str] = None,
                                  namespace: Optional[str] = None) -> List[Dict]:
        """Get all outgoing edges from a node."""
        await self.initialize()
        return await self.db.get_outgoing_edges(node_id, edge_type, namespace)

    async def get_incoming_edges(self, node_id: str,
                                  edge_type: Optional[str] = None,
                                  namespace: Optional[str] = None) -> List[Dict]:
        """Get all incoming edges to a node."""
        await self.initialize()
        return await self.db.get_incoming_edges(node_id, edge_type, namespace)

    async def delete_edge(self, edge_id: str,
                          agent_id: Optional[str] = None) -> bool:
        """Delete an edge by ID."""
        await self.initialize()
        return await self.db.delete_edge(edge_id)

    # ========== Property Operations ==========

    async def set_property(self, entity_id: str, key: str, value: Any,
                           entity_type: str = "node",
                           namespace: str = "public",
                           agent_id: Optional[str] = None) -> bool:
        """Set a property on an entity."""
        await self.initialize()
        
        if not await self._check_namespace_permission(agent_id, namespace, "write"):
            raise PermissionError(f"Agent {agent_id} cannot write to namespace {namespace}")
        
        return await self.db.set_property(entity_id, entity_type, key, value, namespace)

    async def get_property(self, entity_id: str, key: str,
                           entity_type: str = "node") -> Optional[Any]:
        """Get a property value."""
        await self.initialize()
        return await self.db.get_property(entity_id, entity_type, key)

    async def get_all_properties(self, entity_id: str,
                                  entity_type: str = "node") -> Dict[str, Any]:
        """Get all properties for an entity."""
        await self.initialize()
        return await self.db.get_all_properties(entity_id, entity_type)

    # ========== Full-Text Search ==========

    async def index_document(self, entity_id: str, content: str,
                             namespace: str = "public",
                             agent_id: Optional[str] = None) -> bool:
        """Index a document for full-text search."""
        await self.initialize()
        
        if not await self._check_namespace_permission(agent_id, namespace, "write"):
            raise PermissionError(f"Agent {agent_id} cannot write to namespace {namespace}")
        
        return await self.db.index_document(entity_id, content, namespace)

    async def search(self, query: str, limit: int = 10,
                     namespaces: Optional[List[str]] = None,
                     agent_id: Optional[str] = None) -> List[Dict]:
        """
        Perform full-text search.
        
        Args:
            query: Search query string
            limit: Max results (default: 10)
            namespaces: List of namespaces to search (default: all accessible)
            agent_id: Calling agent ID
        
        Returns:
            List of matching results with entity info
        """
        await self.initialize()
        
        # Filter namespaces by agent permissions
        if namespaces and agent_id:
            allowed = []
            for ns in namespaces:
                if await self._check_namespace_permission(agent_id, ns, "read"):
                    allowed.append(ns)
            namespaces = allowed if allowed else None
        
        return await self.db.search(query, limit, namespaces)

    async def unindex_document(self, entity_id: str,
                                agent_id: Optional[str] = None) -> bool:
        """Remove a document from search index."""
        await self.initialize()
        return await self.db.unindex_document(entity_id)

    # ========== Graph Queries ==========

    async def get_dependency_chain(self, node_id: str, max_depth: int = 5,
                                    edge_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Get dependency chain using recursive CTE.
        
        Args:
            node_id: Starting node ID
            max_depth: Maximum traversal depth (default: 5)
            edge_types: Filter by edge types (e.g., ["depends_on", "calls"])
        
        Returns:
            List of edges in the dependency chain
        """
        await self.initialize()
        return await self.db.get_dependency_chain(node_id, max_depth, edge_types)

    async def get_impact_analysis(self, node_id: str, max_depth: int = 3) -> List[Dict]:
        """
        Get nodes that would be impacted by changes to this node.
        (Reverse dependency chain)
        
        Args:
            node_id: Node to analyze
            max_depth: Maximum traversal depth
        
        Returns:
            List of impacted nodes
        """
        await self.initialize()
        
        # Get all nodes that depend on this node
        chain = await self.db.get_dependency_chain(node_id, max_depth)
        
        # Collect unique source nodes (these are impacted)
        impacted_ids = set(e["source_id"] for e in chain)
        impacted = []
        
        for nid in impacted_ids:
            node = await self.db.get_node(nid)
            if node:
                impacted.append(node)
        
        return impacted

    # ========== Failure Tracking ==========

    async def record_failure(self, fingerprint: str, error_type: str,
                             context: Dict, notes: str = "") -> str:
        """
        Record a failure occurrence.
        
        Args:
            fingerprint: Error fingerprint (e.g., "modulenotfound:xyz")
            error_type: Type of failure (test_failure/build_failure/review_rejection)
            context: Context dict (environment, version, dependencies)
            notes: Optional notes
        
        Returns:
            Failure record ID
        """
        await self.initialize()
        
        failure_id = f"failure:{hashlib.sha256(fingerprint.encode()).hexdigest()[:12]}"
        return await self.db.record_failure(failure_id, fingerprint, error_type,
                                             context, notes)

    async def get_failure_prevention(self, fingerprint: str) -> Optional[Dict]:
        """
        Get failure prevention information.
        
        Args:
            fingerprint: Error fingerprint to look up
        
        Returns:
            Failure record with prevention suggestions, or None
        """
        await self.initialize()
        
        failure = await self.db.get_failure(fingerprint)
        
        if failure:
            # Get prevention rules for this fingerprint
            rules = await self.db.get_prevention_rules(fingerprint)
            failure["prevention_rules"] = rules
            
            # Get associated fixes
            conn = self.db._get_connection()
            cursor = conn.execute(
                """SELECT ff.*, n.name as fix_name, n.type as fix_type
                   FROM failure_fixes ff
                   LEFT JOIN nodes n ON ff.fix_node_id = n.id
                   WHERE ff.failure_id = ?""",
                (failure["id"],)
            )
            failure["fixes"] = [dict(row) for row in cursor.fetchall()]
        
        return failure

    async def add_prevention_rule(self, failure_fingerprint: str,
                                   trigger_condition: str,
                                   action: str) -> bool:
        """
        Add a prevention rule.
        
        Args:
            failure_fingerprint: Fingerprint this rule applies to
            trigger_condition: JSON condition expression
            action: Warning message or auto-action
        
        Returns:
            bool: Success flag
        """
        await self.initialize()
        
        rule_id = f"rule:{hashlib.sha256(failure_fingerprint.encode()).hexdigest()[:12]}"
        return await self.db.add_prevention_rule(rule_id, failure_fingerprint,
                                                  trigger_condition, action)

    async def get_unresolved_failures(self, error_type: Optional[str] = None) -> List[Dict]:
        """Get all unresolved failures."""
        await self.initialize()
        return await self.db.get_unresolved_failures(error_type)

    async def resolve_failure(self, failure_id: str, fix_node_id: str,
                               success: bool = True) -> bool:
        """Mark a failure as resolved."""
        await self.initialize()
        return await self.db.resolve_failure(failure_id, fix_node_id, success)

    # ========== Namespace Permissions ==========

    async def set_namespace_permissions(self, agent_id: str,
                                         read_namespaces: List[str],
                                         write_namespaces: List[str]):
        """
        Configure namespace permissions for an agent.
        
        Args:
            agent_id: Agent identifier
            read_namespaces: List of namespaces agent can read
            write_namespaces: List of namespaces agent can write
        """
        self._namespace_permissions[agent_id] = {
            "read_namespaces": read_namespaces,
            "write_namespaces": write_namespaces
        }

    # ========== Custom Queries ==========

    async def query_custom(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """
        Execute custom read-only SQL query.
        
        Args:
            sql: SQL query (SELECT only)
            params: Query parameters
        
        Returns:
            Query results
        """
        await self.initialize()
        
        # Security: Only allow SELECT queries
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        if any(kw in sql_upper for kw in ["DELETE", "DROP", "INSERT", "UPDATE", "ALTER"]):
            raise ValueError("Destructive operations not allowed in custom queries")
        
        conn = self.db._get_connection()
        cursor = conn.execute(sql, params or [])
        return [dict(row) for row in cursor.fetchall()]

    # ========== Maintenance ==========

    async def vacuum(self):
        """Vacuum the database to reclaim space."""
        await self.initialize()
        await self.db.vacuum()

    async def reindex(self):
        """Rebuild all indexes."""
        await self.initialize()
        await self.db.reindex()

    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        await self.initialize()
        return await self.db.get_stats()

    async def close(self):
        """Close the database connection."""
        self.db.close()


# ========== OpenClaw Skill Integration ==========

async def handle_call(method_name: str, args: Dict, config: Optional[Dict] = None) -> Any:
    """
    OpenClaw skill handler.
    
    Args:
        method_name: Method to call
        args: Method arguments
        config: Skill configuration
    
    Returns:
        Method result
    """
    skill = StructuredOntologySkill(config)
    try:
        method = getattr(skill, method_name, None)
        if not method:
            raise AttributeError(f"Method not found: {method_name}")
        
        result = await method(**args)
        return result
    finally:
        await skill.close()


# Convenience function for sync contexts
def call_skill(method_name: str, args: Dict, config: Optional[Dict] = None) -> Any:
    """Call skill method synchronously."""
    return asyncio.run(handle_call(method_name, args, config))
