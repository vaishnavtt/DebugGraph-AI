"""
Knowledge Graph Manager for DebugGraph AI.
Provides idempotent entity ingestion, multi-hop dependency traversal,
blast radius calculation, and service topology exploration using Neo4j and Cypher.
"""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional, Set
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.core.logging import get_logger
from app.graph.driver import Neo4jDriverManager, get_neo4j_driver

logger = get_logger(__name__)

# Allowed node labels and relationship types to prevent Cypher injection
VALID_NODE_LABELS = {
    "Service",
    "Database",
    "API",
    "Repository",
    "Incident",
    "Error",
    "Deployment",
    "Commit",
}

VALID_RELATIONSHIPS = {
    "DEPENDS_ON",
    "CALLS",
    "CONNECTS_TO",
    "PRODUCES_ERROR",
    "AFFECTED_BY",
    "DEPLOYED_WITH",
    "MODIFIED_BY",
    "BELONGS_TO",
}


class KnowledgeGraphManager:
    """
    Manages knowledge graph operations for microservices, dependencies,
    databases, APIs, repositories, commits, and incidents in Neo4j.
    """

    def __init__(self, driver_manager: Optional[Neo4jDriverManager] = None) -> None:
        self.driver_manager = driver_manager or get_neo4j_driver()

    def is_available(self) -> bool:
        """Returns True if the Neo4j database is reachable; False otherwise."""
        return self.driver_manager.verify_connectivity()

    # =========================================================================
    # 1. ENTITY INGESTION (IDEMPOTENT MERGE)
    # =========================================================================

    def register_service(
        self,
        name: str,
        environment: str = "production",
        tier: Optional[str] = None,
        team: Optional[str] = None,
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Idempotently registers or updates a Service node.
        """
        query = """
        MERGE (s:Service {name: $name})
        ON CREATE SET
            s.environment = $environment,
            s.tier = $tier,
            s.team = $team,
            s.status = $status,
            s.metadata = $metadata_json,
            s.created_at = $timestamp,
            s.updated_at = $timestamp
        ON MATCH SET
            s.environment = $environment,
            s.tier = coalesce($tier, s.tier),
            s.team = coalesce($team, s.team),
            s.status = $status,
            s.metadata = $metadata_json,
            s.updated_at = $timestamp
        RETURN s.name AS name, s.environment AS environment, s.tier AS tier,
               s.team AS team, s.status AS status
        """
        metadata_json = json.dumps(metadata or {})
        timestamp = datetime.now(timezone.utc).isoformat()
        records = self.driver_manager.execute_query(
            query,
            {
                "name": name,
                "environment": environment,
                "tier": tier,
                "team": team,
                "status": status,
                "metadata_json": metadata_json,
                "timestamp": timestamp,
            },
            write=True,
        )
        if records:
            return records[0]
        return {"name": name, "status": status}

    def register_database(
        self,
        name: str,
        db_type: str = "postgresql",
        host: Optional[str] = None,
        port: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers a Database node."""
        query = """
        MERGE (d:Database {name: $name})
        ON CREATE SET
            d.type = $type,
            d.host = $host,
            d.port = $port,
            d.metadata = $metadata_json,
            d.created_at = $timestamp
        ON MATCH SET
            d.type = $type,
            d.host = coalesce($host, d.host),
            d.port = coalesce($port, d.port),
            d.metadata = $metadata_json,
            d.updated_at = $timestamp
        RETURN d.name AS name, d.type AS type
        """
        records = self.driver_manager.execute_query(
            query,
            {
                "name": name,
                "type": db_type,
                "host": host,
                "port": port,
                "metadata_json": json.dumps(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            write=True,
        )
        return records[0] if records else {"name": name}

    def register_api(
        self,
        name: str,
        endpoint: Optional[str] = None,
        method: str = "GET",
        protocol: str = "HTTP",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers an API node."""
        query = """
        MERGE (a:API {name: $name})
        ON CREATE SET
            a.endpoint = $endpoint,
            a.method = $method,
            a.protocol = $protocol,
            a.metadata = $metadata_json,
            a.created_at = $timestamp
        ON MATCH SET
            a.endpoint = coalesce($endpoint, a.endpoint),
            a.method = $method,
            a.protocol = $protocol,
            a.metadata = $metadata_json,
            a.updated_at = $timestamp
        RETURN a.name AS name, a.endpoint AS endpoint, a.method AS method
        """
        records = self.driver_manager.execute_query(
            query,
            {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "protocol": protocol,
                "metadata_json": json.dumps(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            write=True,
        )
        return records[0] if records else {"name": name}

    def register_repository(
        self,
        url: str,
        name: Optional[str] = None,
        default_branch: str = "main",
        owner: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers a Git Repository node."""
        query = """
        MERGE (r:Repository {url: $url})
        ON CREATE SET
            r.name = $name,
            r.default_branch = $default_branch,
            r.owner = $owner,
            r.metadata = $metadata_json,
            r.created_at = $timestamp
        ON MATCH SET
            r.name = coalesce($name, r.name),
            r.default_branch = $default_branch,
            r.owner = coalesce($owner, r.owner),
            r.metadata = $metadata_json,
            r.updated_at = $timestamp
        RETURN r.url AS url, r.name AS name, r.default_branch AS default_branch
        """
        records = self.driver_manager.execute_query(
            query,
            {
                "url": url,
                "name": name or url.split("/")[-1].replace(".git", ""),
                "default_branch": default_branch,
                "owner": owner,
                "metadata_json": json.dumps(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            write=True,
        )
        return records[0] if records else {"url": url}

    def connect_service_to_repo(self, service_name: str, repo_url: str) -> bool:
        """Connects a Service to its Repository via BELONGS_TO."""
        query = """
        MATCH (s:Service {name: $service_name})
        MATCH (r:Repository {url: $repo_url})
        MERGE (s)-[rel:BELONGS_TO]->(r)
        ON CREATE SET rel.created_at = $timestamp
        RETURN count(rel) AS count
        """
        records = self.driver_manager.execute_query(
            query,
            {
                "service_name": service_name,
                "repo_url": repo_url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            write=True,
        )
        return bool(records and records[0].get("count", 0) > 0)

    def register_incident(
        self,
        incident_id: str,
        title: str,
        severity: str = "HIGH",
        status: str = "INVESTIGATING",
        service_name: Optional[str] = None,
        error_signatures: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers an Incident node and links affected service and errors."""
        query = """
        MERGE (i:Incident {id: $incident_id})
        ON CREATE SET
            i.title = $title,
            i.severity = $severity,
            i.status = $status,
            i.metadata = $metadata_json,
            i.created_at = $timestamp
        ON MATCH SET
            i.title = $title,
            i.severity = $severity,
            i.status = $status,
            i.metadata = $metadata_json,
            i.updated_at = $timestamp
        RETURN i.id AS id, i.title AS title, i.severity AS severity
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        records = self.driver_manager.execute_query(
            query,
            {
                "incident_id": incident_id,
                "title": title,
                "severity": severity,
                "status": status,
                "metadata_json": json.dumps(metadata or {}),
                "timestamp": timestamp,
            },
            write=True,
        )

        # Link to affected service
        if service_name:
            link_svc_query = """
            MATCH (i:Incident {id: $incident_id})
            MATCH (s:Service {name: $service_name})
            MERGE (s)-[r:AFFECTED_BY]->(i)
            ON CREATE SET r.created_at = $timestamp
            """
            self.driver_manager.execute_query(
                link_svc_query,
                {"incident_id": incident_id, "service_name": service_name, "timestamp": timestamp},
                write=True,
            )

        # Link to errors
        if error_signatures:
            for sig in error_signatures:
                self.register_error(signature=sig)
                link_err_query = """
                MATCH (i:Incident {id: $incident_id})
                MATCH (e:Error {signature: $signature})
                MERGE (i)-[r:PRODUCES_ERROR]->(e)
                """
                self.driver_manager.execute_query(
                    link_err_query,
                    {"incident_id": incident_id, "signature": sig},
                    write=True,
                )

        return records[0] if records else {"id": incident_id}

    def register_error(
        self,
        signature: str,
        error_type: Optional[str] = None,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers an Error node and connects to service if provided."""
        query = """
        MERGE (e:Error {signature: $signature})
        ON CREATE SET
            e.error_type = $error_type,
            e.message = $message,
            e.metadata = $metadata_json,
            e.created_at = $timestamp
        ON MATCH SET
            e.error_type = coalesce($error_type, e.error_type),
            e.message = coalesce($message, e.message),
            e.metadata = $metadata_json,
            e.updated_at = $timestamp
        RETURN e.signature AS signature
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        records = self.driver_manager.execute_query(
            query,
            {
                "signature": signature,
                "error_type": error_type,
                "message": message,
                "metadata_json": json.dumps(metadata or {}),
                "timestamp": timestamp,
            },
            write=True,
        )

        if service_name:
            link_query = """
            MATCH (s:Service {name: $service_name})
            MATCH (e:Error {signature: $signature})
            MERGE (s)-[r:PRODUCES_ERROR]->(e)
            ON CREATE SET r.created_at = $timestamp
            """
            self.driver_manager.execute_query(
                link_query,
                {"service_name": service_name, "signature": signature, "timestamp": timestamp},
                write=True,
            )

        return records[0] if records else {"signature": signature}

    def register_commit(
        self,
        sha: str,
        message: str,
        author: Optional[str] = None,
        timestamp: Optional[str] = None,
        url: Optional[str] = None,
        repo_url: Optional[str] = None,
        service_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Idempotently registers a Git Commit node and associates it with Repository and Service."""
        query = """
        MERGE (c:Commit {sha: $sha})
        ON CREATE SET
            c.message = $message,
            c.author = $author,
            c.timestamp = $commit_time,
            c.url = $url,
            c.metadata = $metadata_json,
            c.created_at = $sys_time
        ON MATCH SET
            c.message = $message,
            c.author = coalesce($author, c.author),
            c.timestamp = coalesce($commit_time, c.timestamp),
            c.url = coalesce($url, c.url),
            c.metadata = $metadata_json
        RETURN c.sha AS sha, c.message AS message
        """
        sys_time = datetime.now(timezone.utc).isoformat()
        records = self.driver_manager.execute_query(
            query,
            {
                "sha": sha,
                "message": message,
                "author": author,
                "commit_time": timestamp or sys_time,
                "url": url,
                "metadata_json": json.dumps(metadata or {}),
                "sys_time": sys_time,
            },
            write=True,
        )

        if repo_url:
            self.register_repository(url=repo_url)
            repo_link_query = """
            MATCH (r:Repository {url: $repo_url})
            MATCH (c:Commit {sha: $sha})
            MERGE (r)-[rel:MODIFIED_BY]->(c)
            """
            self.driver_manager.execute_query(
                repo_link_query,
                {"repo_url": repo_url, "sha": sha},
                write=True,
            )

        if service_name:
            svc_link_query = """
            MATCH (s:Service {name: $service_name})
            MATCH (c:Commit {sha: $sha})
            MERGE (s)-[rel:MODIFIED_BY]->(c)
            """
            self.driver_manager.execute_query(
                svc_link_query,
                {"service_name": service_name, "sha": sha},
                write=True,
            )

        return records[0] if records else {"sha": sha}

    def register_dependency(
        self,
        source: str,
        target: str,
        relation_type: str = "DEPENDS_ON",
        source_type: str = "Service",
        target_type: str = "Service",
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Idempotently registers a directed relationship between two entities.
        Validates relationship and node labels against whitelist to prevent Cypher injection.
        """
        if relation_type not in VALID_RELATIONSHIPS:
            raise ValueError(f"Invalid relationship type: {relation_type}. Allowed: {VALID_RELATIONSHIPS}")
        if source_type not in VALID_NODE_LABELS or target_type not in VALID_NODE_LABELS:
            raise ValueError(f"Invalid node labels: {source_type}, {target_type}. Allowed: {VALID_NODE_LABELS}")

        # Dynamic query with strictly validated identifiers
        query = f"""
        MERGE (src:{source_type} {{name: $source}})
        MERGE (tgt:{target_type} {{name: $target}})
        MERGE (src)-[r:{relation_type}]->(tgt)
        SET r += $properties
        RETURN src.name AS source, tgt.name AS target, type(r) AS relation_type
        """
        props = properties or {}
        props["updated_at"] = datetime.now(timezone.utc).isoformat()

        records = self.driver_manager.execute_query(
            query,
            {"source": source, "target": target, "properties": props},
            write=True,
        )
        return records[0] if records else {
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "source_type": source_type,
            "target_type": target_type,
            "properties": props,
        }

    # =========================================================================
    # 2. GRAPH QUERIES & TOPOLOGY EXPLORATION
    # =========================================================================

    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information about a service, including its direct callers,
        callees, connected databases, APIs, and repositories.
        """
        query = """
        MATCH (s:Service {name: $service_name})
        OPTIONAL MATCH (s)-[:DEPENDS_ON]->(downstream:Service)
        OPTIONAL MATCH (upstream:Service)-[:DEPENDS_ON]->(s)
        OPTIONAL MATCH (s)-[:CONNECTS_TO]->(db:Database)
        OPTIONAL MATCH (s)-[:CALLS]->(api:API)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(repo:Repository)
        RETURN s.name AS name,
               s.environment AS environment,
               s.tier AS tier,
               s.team AS team,
               s.status AS status,
               s.metadata AS metadata,
               collect(DISTINCT upstream.name) AS upstream_dependencies,
               collect(DISTINCT downstream.name) AS downstream_dependencies,
               collect(DISTINCT db.name) AS connected_databases,
               collect(DISTINCT api.name) AS connected_apis,
               collect(DISTINCT repo.url) AS repositories
        """
        try:
            records = self.driver_manager.execute_query(query, {"service_name": service_name})
            if not records:
                return None

            row = records[0]
            # Parse metadata json if stored as string
            meta = row.get("metadata")
            if isinstance(meta, str):
                try:
                    row["metadata"] = json.loads(meta)
                except Exception:
                    row["metadata"] = {}
            elif not isinstance(meta, dict):
                row["metadata"] = {}

            # Filter None from collected lists
            for key in ["upstream_dependencies", "downstream_dependencies", "connected_databases", "connected_apis", "repositories"]:
                row[key] = [item for item in row.get(key, []) if item is not None]

            return row
        except Exception as exc:
            logger.error("Failed to get service [%s]: %s", service_name, exc)
            return None

    def get_service_dependencies(
        self,
        service_name: str,
        direction: str = "both",
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Executes bounded multi-hop dependency traversal for a microservice.
        direction: 'upstream' (who calls this), 'downstream' (who this calls), or 'both'.
        max_depth: clamped between 1 and 5 to prevent unbounded traversal.
        """
        depth = max(1, min(max_depth, 5))
        result: Dict[str, Any] = {
            "service_name": service_name,
            "direction": direction,
            "max_depth": depth,
            "upstream": [],
            "downstream": [],
            "databases": [],
            "apis": [],
            "traversal_paths": [],
        }

        try:
            # 1. Downstream dependencies: (s)-[:DEPENDS_ON*1..depth]->(downstream)
            if direction in ("downstream", "both"):
                downstream_query = f"""
                MATCH path = (s:Service {{name: $service_name}})-[:DEPENDS_ON*1..{depth}]->(target:Service)
                RETURN target.name AS name, [n IN nodes(path) | n.name] AS path_names
                """
                downstream_records = self.driver_manager.execute_query(
                    downstream_query, {"service_name": service_name}
                )
                downstream_set = set()
                for rec in downstream_records:
                    downstream_set.add(rec["name"])
                    result["traversal_paths"].append(rec["path_names"])
                result["downstream"] = sorted(list(downstream_set))

                # Connected databases along downstream path
                db_query = f"""
                MATCH (s:Service {{name: $service_name}})-[:DEPENDS_ON*0..{depth}]->(svc:Service)-[:CONNECTS_TO]->(db:Database)
                RETURN DISTINCT db.name AS db_name
                """
                db_records = self.driver_manager.execute_query(db_query, {"service_name": service_name})
                result["databases"] = sorted([r["db_name"] for r in db_records if r.get("db_name")])

                # Connected APIs along downstream path
                api_query = f"""
                MATCH (s:Service {{name: $service_name}})-[:DEPENDS_ON*0..{depth}]->(svc:Service)-[:CALLS]->(api:API)
                RETURN DISTINCT api.name AS api_name
                """
                api_records = self.driver_manager.execute_query(api_query, {"service_name": service_name})
                result["apis"] = sorted([r["api_name"] for r in api_records if r.get("api_name")])

            # 2. Upstream dependencies: (source)-[:DEPENDS_ON*1..depth]->(s)
            if direction in ("upstream", "both"):
                upstream_query = f"""
                MATCH path = (source:Service)-[:DEPENDS_ON*1..{depth}]->(s:Service {{name: $service_name}})
                RETURN source.name AS name, [n IN nodes(path) | n.name] AS path_names
                """
                upstream_records = self.driver_manager.execute_query(
                    upstream_query, {"service_name": service_name}
                )
                upstream_set = set()
                for rec in upstream_records:
                    upstream_set.add(rec["name"])
                    result["traversal_paths"].append(rec["path_names"])
                result["upstream"] = sorted(list(upstream_set))

            return result
        except Exception as exc:
            logger.error("Failed to get dependencies for [%s]: %s", service_name, exc)
            return result

    def calculate_blast_radius(
        self,
        service_name: str,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Calculates the cascade failure impact and blast radius if a given microservice fails.
        Identifies:
        - All upstream services that transitively depend on this service.
        - All downstream services, databases, and APIs.
        - Computes a normalized blast radius score (0.0 to 1.0) and severity rating.
        """
        depth = max(1, min(max_depth, 5))
        deps = self.get_service_dependencies(service_name, direction="both", max_depth=depth)

        upstream_services = set(deps.get("upstream", []))
        downstream_services = set(deps.get("downstream", []))
        all_services = sorted(list(upstream_services.union(downstream_services)))
        connected_dbs = deps.get("databases", [])
        connected_apis = deps.get("apis", [])

        # Direct dependents (1-hop upstream callers)
        direct_callers_query = """
        MATCH (u:Service)-[:DEPENDS_ON]->(s:Service {name: $service_name})
        RETURN collect(DISTINCT u.name) AS direct_callers
        """
        direct_records = self.driver_manager.execute_query(
            direct_callers_query, {"service_name": service_name}
        )
        direct_callers = direct_records[0].get("direct_callers", []) if direct_records else []
        direct_count = len(direct_callers)
        total_affected = len(all_services)

        # Blast radius score formula:
        # direct callers heavily weighted (0.35 each up to 0.7)
        # transitive callers weighted (0.10 each)
        # downstream dependency complexity (0.05 each)
        # connected databases (0.10 each)
        raw_score = (
            (direct_count * 0.25)
            + ((total_affected - direct_count) * 0.08)
            + (len(connected_dbs) * 0.15)
            + (len(connected_apis) * 0.05)
        )
        blast_radius_score = round(min(1.0, max(0.0, raw_score)), 2)

        # Classify severity
        if blast_radius_score >= 0.7 or direct_count >= 5:
            severity = "CRITICAL"
        elif blast_radius_score >= 0.4 or direct_count >= 2:
            severity = "HIGH"
        elif blast_radius_score >= 0.2 or total_affected >= 1:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "service_name": service_name,
            "blast_radius_score": blast_radius_score,
            "severity_level": severity,
            "direct_dependents_count": direct_count,
            "total_impacted_services_count": total_affected,
            "impacted_services": all_services,
            "impacted_databases": connected_dbs,
            "impacted_apis": connected_apis,
            "dependency_chains": deps.get("traversal_paths", []),
        }

    def get_related_errors(self, service_name: str) -> List[Dict[str, Any]]:
        """
        Finds errors produced by this service or its direct dependencies.
        """
        query = """
        MATCH (s:Service {name: $service_name})
        OPTIONAL MATCH (s)-[:PRODUCES_ERROR]->(e:Error)
        OPTIONAL MATCH (s)-[:DEPENDS_ON]->(dep:Service)-[:PRODUCES_ERROR]->(dep_err:Error)
        RETURN coalesce(e.signature, dep_err.signature) AS signature,
               coalesce(e.error_type, dep_err.error_type) AS error_type,
               coalesce(e.message, dep_err.message) AS message,
               CASE WHEN e IS NOT NULL THEN s.name ELSE dep.name END AS producer_service
        """
        try:
            records = self.driver_manager.execute_query(query, {"service_name": service_name})
            return [r for r in records if r.get("signature")]
        except Exception as exc:
            logger.error("Failed to get related errors for [%s]: %s", service_name, exc)
            return []

    def get_repo_for_service(self, service_name: str) -> Optional[str]:
        """Finds the GitHub repository URL associated with a microservice."""
        query = """
        MATCH (s:Service {name: $service_name})-[:BELONGS_TO]->(r:Repository)
        RETURN r.url AS repo_url
        LIMIT 1
        """
        try:
            records = self.driver_manager.execute_query(query, {"service_name": service_name})
            return records[0].get("repo_url") if records else None
        except Exception:
            return None

    def health_check(self) -> Dict[str, Any]:
        """Performs a Neo4j health check and node count summary."""
        connected = self.driver_manager.verify_connectivity()
        if not connected:
            return {
                "status": "unavailable",
                "connected": False,
                "uri": self.driver_manager.uri,
                "database": self.driver_manager.database,
                "node_counts": None,
                "error": "Failed to establish Bolt connection with Neo4j server.",
            }

        counts_query = """
        CALL {
            MATCH (s:Service) RETURN 'services' AS label, count(s) AS count
            UNION
            MATCH (d:Database) RETURN 'databases' AS label, count(d) AS count
            UNION
            MATCH (a:API) RETURN 'apis' AS label, count(a) AS count
            UNION
            MATCH (r:Repository) RETURN 'repositories' AS label, count(r) AS count
            UNION
            MATCH (i:Incident) RETURN 'incidents' AS label, count(i) AS count
            UNION
            MATCH (e:Error) RETURN 'errors' AS label, count(e) AS count
            UNION
            MATCH (c:Commit) RETURN 'commits' AS label, count(c) AS count
        }
        RETURN label, count
        """
        node_counts: Dict[str, int] = {}
        try:
            records = self.driver_manager.execute_query(counts_query)
            for r in records:
                node_counts[r["label"]] = r["count"]
            status = "healthy"
            err = None
        except Exception as exc:
            status = "degraded"
            err = str(exc)

        return {
            "status": status,
            "connected": True,
            "uri": self.driver_manager.uri,
            "database": self.driver_manager.database,
            "node_counts": node_counts,
            "error": err,
        }

