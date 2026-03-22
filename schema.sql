-- structured-ontology SQLite Schema
-- Knowledge base with entities, relationships, full-text search, failure tracking, and namespaces

-- Entity Table (Nodes)
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- api/class/function/decision/failure/fix...
    name TEXT NOT NULL,
    namespace TEXT DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Relationship Table (Edges)
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- depends_on/calls/implements/prevents...
    weight REAL DEFAULT 1.0,
    namespace TEXT DEFAULT 'public',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
);

-- Properties Table (EAV Pattern)
CREATE TABLE IF NOT EXISTS properties (
    entity_id TEXT NOT NULL,  -- Node ID or Edge ID
    entity_type TEXT NOT NULL,  -- 'node' or 'edge'
    key TEXT NOT NULL,
    value TEXT,  -- Simple types in TEXT, complex as JSON
    namespace TEXT DEFAULT 'public',
    PRIMARY KEY (entity_id, entity_type, key)
);

-- Full-Text Search Virtual Table (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(
    content,
    entity_id,
    namespace,
    tokenize = 'porter unicode61'
);

-- Failure Records Table
CREATE TABLE IF NOT EXISTS failures (
    id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,  -- Error fingerprint (e.g., error type + key symbols)
    error_type TEXT,  -- test_failure / build_failure / review_rejection
    context TEXT,  -- JSON context (environment, version, dependencies)
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    occurrence_count INT DEFAULT 1,
    resolved BOOLEAN DEFAULT 0,
    resolution_id TEXT,  -- Reference to fix node (optional)
    notes TEXT
);

-- Failure-Fix Relationship Table
CREATE TABLE IF NOT EXISTS failure_fixes (
    failure_id TEXT,
    fix_node_id TEXT,  -- Points to fix node in nodes table
    applied_at TIMESTAMP,
    success BOOLEAN,  -- Whether this fix ultimately resolved the failure
    PRIMARY KEY (failure_id, fix_node_id),
    FOREIGN KEY (failure_id) REFERENCES failures(id) ON DELETE CASCADE,
    FOREIGN KEY (fix_node_id) REFERENCES nodes(id)
);

-- Prevention Rules Table (for proactive warnings)
CREATE TABLE IF NOT EXISTS prevention_rules (
    id TEXT PRIMARY KEY,
    failure_fingerprint TEXT,
    trigger_condition TEXT,  -- JSON condition expression
    action TEXT,  -- Warning message or auto-executed action
    enabled BOOLEAN DEFAULT 1
);

-- Indexes for Optimization
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_namespace ON nodes(namespace);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
CREATE INDEX IF NOT EXISTS idx_edges_namespace ON edges(namespace);
CREATE INDEX IF NOT EXISTS idx_failures_fingerprint ON failures(fingerprint);
CREATE INDEX IF NOT EXISTS idx_failures_resolved ON failures(resolved);
CREATE INDEX IF NOT EXISTS idx_properties_entity ON properties(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_properties_key ON properties(key);

-- Trigger: Auto-update updated_at on nodes
CREATE TRIGGER IF NOT EXISTS update_nodes_timestamp AFTER UPDATE ON nodes
BEGIN
    UPDATE nodes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Auto-update updated_at on edges (optional, for edge properties)
CREATE TRIGGER IF NOT EXISTS update_edges_timestamp AFTER UPDATE ON edges
BEGIN
    UPDATE edges SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
