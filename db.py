"""
Database operations wrapper for structured-ontology skill.
Provides connection pooling, transaction management, and basic CRUD operations.
"""

import sqlite3
import json
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


class Database:
    """SQLite database wrapper with connection pooling support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = None
        self._initialized = False

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection (thread-local)."""
        if self._local is None:
            self._local = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode for manual transaction control
            )
            self._local.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrency
            self._local.execute("PRAGMA journal_mode=WAL")
            self._local.execute("PRAGMA synchronous=NORMAL")
            self._local.execute("PRAGMA foreign_keys=ON")
        return self._local

    async def init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        schema_path = Path(__file__).parent / "schema.sql"
        
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            conn.commit()
            self._initialized = True
        else:
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

    # ========== Node Operations ==========

    async def add_node(self, node_id: str, node_type: str, name: str,
                       namespace: str = "public") -> bool:
        """Add a node to the database."""
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO nodes (id, type, name, namespace)
                   VALUES (?, ?, ?, ?)""",
                (node_id, node_type, name, namespace)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def get_node(self, node_id: str, namespace: Optional[str] = None) -> Optional[Dict]:
        """Get a node by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT id, type, name, namespace, created_at, updated_at
               FROM nodes WHERE id = ?""",
            (node_id,)
        )
        row = cursor.fetchone()
        
        if row and (namespace is None or row["namespace"] == namespace):
            return dict(row)
        return None

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node by ID."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def list_nodes(self, node_type: Optional[str] = None,
                         namespace: Optional[str] = None) -> List[Dict]:
        """List nodes with optional filters."""
        conn = self._get_connection()
        query = "SELECT id, type, name, namespace, created_at, updated_at FROM nodes WHERE 1=1"
        params = []
        
        if node_type:
            query += " AND type = ?"
            params.append(node_type)
        if namespace:
            query += " AND namespace = ?"
            params.append(namespace)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ========== Edge Operations ==========

    async def add_edge(self, edge_id: str, source_id: str, target_id: str,
                       edge_type: str, weight: float = 1.0,
                       namespace: str = "public") -> bool:
        """Add an edge to the database."""
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO edges (id, source_id, target_id, type, weight, namespace)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (edge_id, source_id, target_id, edge_type, weight, namespace)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def get_edge(self, edge_id: str) -> Optional[Dict]:
        """Get an edge by ID."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT id, source_id, target_id, type, weight, namespace, created_at
               FROM edges WHERE id = ?""",
            (edge_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    async def get_outgoing_edges(self, node_id: str, edge_type: Optional[str] = None,
                                  namespace: Optional[str] = None) -> List[Dict]:
        """Get all outgoing edges from a node."""
        conn = self._get_connection()
        query = """SELECT id, source_id, target_id, type, weight, namespace
                   FROM edges WHERE source_id = ?"""
        params = [node_id]
        
        if edge_type:
            query += " AND type = ?"
            params.append(edge_type)
        if namespace:
            query += " AND namespace = ?"
            params.append(namespace)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    async def get_incoming_edges(self, node_id: str, edge_type: Optional[str] = None,
                                  namespace: Optional[str] = None) -> List[Dict]:
        """Get all incoming edges to a node."""
        conn = self._get_connection()
        query = """SELECT id, source_id, target_id, type, weight, namespace
                   FROM edges WHERE target_id = ?"""
        params = [node_id]
        
        if edge_type:
            query += " AND type = ?"
            params.append(edge_type)
        if namespace:
            query += " AND namespace = ?"
            params.append(namespace)
        
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge by ID."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    # ========== Property Operations ==========

    async def set_property(self, entity_id: str, entity_type: str,
                           key: str, value: Any, namespace: str = "public") -> bool:
        """Set a property on an entity (node or edge)."""
        conn = self._get_connection()
        try:
            # Convert complex types to JSON
            value_str = json.dumps(value) if not isinstance(value, str) else value
            
            conn.execute(
                """INSERT OR REPLACE INTO properties (entity_id, entity_type, key, value, namespace)
                   VALUES (?, ?, ?, ?, ?)""",
                (entity_id, entity_type, key, value_str, namespace)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def get_property(self, entity_id: str, entity_type: str,
                           key: str) -> Optional[Any]:
        """Get a property value from an entity."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT value FROM properties
               WHERE entity_id = ? AND entity_type = ? AND key = ?""",
            (entity_id, entity_type, key)
        )
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                return row["value"]
        return None

    async def get_all_properties(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """Get all properties for an entity."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT key, value FROM properties
               WHERE entity_id = ? AND entity_type = ?""",
            (entity_id, entity_type)
        )
        props = {}
        for row in cursor.fetchall():
            try:
                props[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                props[row["key"]] = row["value"]
        return props

    async def delete_property(self, entity_id: str, entity_type: str, key: str) -> bool:
        """Delete a property from an entity."""
        conn = self._get_connection()
        try:
            conn.execute(
                """DELETE FROM properties
                   WHERE entity_id = ? AND entity_type = ? AND key = ?""",
                (entity_id, entity_type, key)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    # ========== Full-Text Search Operations ==========

    async def index_document(self, entity_id: str, content: str,
                             namespace: str = "public") -> bool:
        """Index a document for full-text search."""
        conn = self._get_connection()
        try:
            # Delete existing index for this entity
            conn.execute(
                "DELETE FROM fts WHERE entity_id = ?",
                (entity_id,)
            )
            # Insert new index
            conn.execute(
                "INSERT INTO fts (content, entity_id, namespace) VALUES (?, ?, ?)",
                (content, entity_id, namespace)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def search(self, query: str, limit: int = 10,
                     namespaces: Optional[List[str]] = None) -> List[Dict]:
        """Perform full-text search."""
        conn = self._get_connection()
        
        if namespaces:
            placeholders = ",".join("?" * len(namespaces))
            sql = f"""
                SELECT f.entity_id, f.content, f.namespace, n.type, n.name
                FROM fts f
                LEFT JOIN nodes n ON f.entity_id = n.id
                WHERE f.content MATCH ?
                AND f.namespace IN ({placeholders})
                ORDER BY rank
                LIMIT ?
            """
            params = [query] + list(namespaces) + [limit]
        else:
            sql = """
                SELECT f.entity_id, f.content, f.namespace, n.type, n.name
                FROM fts f
                LEFT JOIN nodes n ON f.entity_id = n.id
                WHERE f.content MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            params = [query, limit]
        
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    async def unindex_document(self, entity_id: str) -> bool:
        """Remove a document from the search index."""
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM fts WHERE entity_id = ?", (entity_id,))
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    # ========== Dependency Chain Query (Recursive CTE) ==========

    async def get_dependency_chain(self, node_id: str, max_depth: int = 5,
                                    edge_types: Optional[List[str]] = None) -> List[Dict]:
        """Get dependency chain using recursive CTE."""
        conn = self._get_connection()
        
        if edge_types:
            placeholders = ",".join("?" * len(edge_types))
            type_filter = f"AND e.type IN ({placeholders})"
            params = [node_id] + edge_types + [max_depth]
        else:
            type_filter = ""
            params = [node_id, max_depth]
        
        sql = f"""
            WITH RECURSIVE dep_chain AS (
                SELECT e.id, e.source_id, e.target_id, e.type, e.weight, 1 as depth
                FROM edges e
                WHERE e.target_id = ?
                {type_filter}
                
                UNION ALL
                
                SELECT e.id, e.source_id, e.target_id, e.type, e.weight, dc.depth + 1
                FROM edges e
                INNER JOIN dep_chain dc ON e.target_id = dc.source_id
                WHERE dc.depth < ?
                {type_filter.replace('?', '?')}
            )
            SELECT * FROM dep_chain ORDER BY depth
        """
        
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # ========== Failure Tracking Operations ==========

    async def record_failure(self, failure_id: str, fingerprint: str,
                             error_type: str, context: Dict,
                             notes: str = "") -> str:
        """Record a failure occurrence."""
        conn = self._get_connection()
        now = sqlite3.datetime.datetime.now().isoformat()
        
        with self.transaction():
            # Check if failure already exists
            cursor = conn.execute(
                "SELECT id, occurrence_count FROM failures WHERE fingerprint = ?",
                (fingerprint,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing failure
                conn.execute(
                    """UPDATE failures
                       SET last_seen = ?, occurrence_count = occurrence_count + 1,
                           context = ?, notes = ?
                       WHERE fingerprint = ?""",
                    (now, json.dumps(context), notes, fingerprint)
                )
                return existing["id"]
            else:
                # Insert new failure
                conn.execute(
                    """INSERT INTO failures
                       (id, fingerprint, error_type, context, first_seen, last_seen, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (failure_id, fingerprint, error_type, json.dumps(context),
                     now, now, notes)
                )
                return failure_id

    async def get_failure(self, fingerprint: str) -> Optional[Dict]:
        """Get failure record by fingerprint."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT * FROM failures WHERE fingerprint = ?""",
            (fingerprint,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get("context"):
                result["context"] = json.loads(result["context"])
            return result
        return None

    async def resolve_failure(self, failure_id: str, fix_node_id: str,
                               success: bool = True) -> bool:
        """Mark a failure as resolved with a fix."""
        conn = self._get_connection()
        now = sqlite3.datetime.datetime.now().isoformat()
        
        with self.transaction():
            conn.execute(
                """INSERT OR REPLACE INTO failure_fixes
                   (failure_id, fix_node_id, applied_at, success)
                   VALUES (?, ?, ?, ?)""",
                (failure_id, fix_node_id, now, success)
            )
            
            if success:
                conn.execute(
                    """UPDATE failures
                       SET resolved = 1, resolution_id = ?
                       WHERE id = ?""",
                    (fix_node_id, failure_id)
                )
        
        return True

    async def get_unresolved_failures(self, error_type: Optional[str] = None) -> List[Dict]:
        """Get all unresolved failures."""
        conn = self._get_connection()
        query = "SELECT * FROM failures WHERE resolved = 0"
        params = []
        
        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)
        
        cursor = conn.execute(query, params)
        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get("context"):
                result["context"] = json.loads(result["context"])
            results.append(result)
        return results

    # ========== Prevention Rules Operations ==========

    async def add_prevention_rule(self, rule_id: str, failure_fingerprint: str,
                                   trigger_condition: str, action: str) -> bool:
        """Add a prevention rule."""
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO prevention_rules
                   (id, failure_fingerprint, trigger_condition, action, enabled)
                   VALUES (?, ?, ?, ?, 1)""",
                (rule_id, failure_fingerprint, trigger_condition, action)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    async def get_prevention_rules(self, fingerprint: Optional[str] = None) -> List[Dict]:
        """Get prevention rules, optionally filtered by fingerprint."""
        conn = self._get_connection()
        
        if fingerprint:
            cursor = conn.execute(
                """SELECT * FROM prevention_rules
                   WHERE failure_fingerprint = ? AND enabled = 1""",
                (fingerprint,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM prevention_rules WHERE enabled = 1"
            )
        
        return [dict(row) for row in cursor.fetchall()]

    async def disable_prevention_rule(self, rule_id: str) -> bool:
        """Disable a prevention rule."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE prevention_rules SET enabled = 0 WHERE id = ?",
                (rule_id,)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    # ========== Maintenance Operations ==========

    async def vacuum(self):
        """Vacuum the database to reclaim space."""
        conn = self._get_connection()
        conn.execute("VACUUM")
        conn.commit()

    async def reindex(self):
        """Rebuild all indexes."""
        conn = self._get_connection()
        conn.execute("REINDEX")
        conn.commit()

    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        stats = {}
        
        for table in ["nodes", "edges", "properties", "failures", "fts"]:
            cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()["count"]
        
        return stats

    def close(self):
        """Close the database connection."""
        if self._local:
            self._local.close()
            self._local = None
