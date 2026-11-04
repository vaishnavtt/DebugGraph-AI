"""
Neo4j driver connection manager and lifecycle management.
Provides connection pooling, health verification, and graceful offline handling.
"""
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional
import neo4j
from neo4j import Driver, GraphDatabase, Session
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Neo4jDriverManager:
    """
    Manages the lifecycle of the Neo4j Bolt driver.
    Ensures safe initialization, connectivity verification, and idempotent schema constraints.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        self.uri = uri or settings.NEO4J_URI
        self.username = username or settings.NEO4J_USERNAME
        self.password = password or settings.NEO4J_PASSWORD or ""
        self.database = database or getattr(settings, "NEO4J_DATABASE", "neo4j")
        self._driver: Optional[Driver] = None
        self._initialized: bool = False

    def get_driver(self) -> Optional[Driver]:
        """
        Lazily creates and returns the Neo4j driver instance.
        Returns None if credentials are missing or driver initialization fails.
        """
        if self._driver is not None:
            return self._driver

        if not self.uri:
            logger.warning("NEO4J_URI is not configured; Neo4j driver disabled.")
            return None

        try:
            auth = (self.username, self.password) if self.username and self.password else None
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=auth,
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=10.0,
            )
            logger.info("Initialized Neo4j driver for URI: %s (database: %s)", self.uri, self.database)
            return self._driver
        except Exception as exc:
            logger.warning("Failed to initialize Neo4j driver: %s", exc)
            self._driver = None
            return None

    def verify_connectivity(self) -> bool:
        """
        Verifies active Bolt connectivity to the Neo4j database instance.
        Returns True if connected and verified; False otherwise.
        """
        driver = self.get_driver()
        if not driver:
            return False

        try:
            driver.verify_connectivity()
            return True
        except (ServiceUnavailable, Neo4jError, Exception) as exc:
            logger.warning("Neo4j connectivity check failed: %s", exc)
            return False

    @contextmanager
    def get_session(self, database: Optional[str] = None) -> Generator[Session, None, None]:
        """
        Context manager for acquiring and safely closing a Neo4j session.
        Raises ServiceUnavailable if the database is unreachable.
        """
        driver = self.get_driver()
        if not driver:
            raise ServiceUnavailable("Neo4j driver is not available or configured.")

        db_name = database or self.database
        session = driver.session(database=db_name)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        write: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Executes a Cypher query and returns the records as a list of dicts.
        Handles session lifecycle and error logging.
        """
        driver = self.get_driver()
        if not driver:
            logger.debug("Cannot execute query: Neo4j driver unavailable.")
            return []

        parameters = parameters or {}
        try:
            with self.get_session() as session:
                if write:
                    result = session.run(query, parameters)
                else:
                    result = session.run(query, parameters)
                return [record.data() for record in result]
        except (ServiceUnavailable, Neo4jError, Exception) as exc:
            logger.error("Failed to execute Cypher query [%s]: %s", query, exc)
            raise

    def init_schema(self) -> bool:
        """
        Initializes schema constraints and uniqueness indexes idempotently.
        Ensures entity deduplication for Services, Databases, APIs, Repositories,
        Incidents, Errors, Deployments, and Commits.
        """
        if not self.verify_connectivity():
            logger.warning("Cannot initialize Neo4j schema: database unreachable.")
            return False

        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Service) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Database) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:API) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Repository) REQUIRE r.url IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Error) REQUIRE e.signature IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (dp:Deployment) REQUIRE dp.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Commit) REQUIRE c.sha IS UNIQUE",
        ]

        try:
            with self.get_session() as session:
                for constraint in constraints:
                    session.run(constraint)
            logger.info("Neo4j schema constraints successfully verified/created.")
            self._initialized = True
            return True
        except Exception as exc:
            logger.error("Failed to initialize Neo4j constraints: %s", exc)
            return False

    def close(self) -> None:
        """Closes the underlying Neo4j driver cleanly."""
        if self._driver:
            try:
                self._driver.close()
                logger.info("Closed Neo4j driver connection.")
            except Exception as exc:
                logger.warning("Error while closing Neo4j driver: %s", exc)
            finally:
                self._driver = None


# Global driver singleton
_neo4j_driver_manager: Optional[Neo4jDriverManager] = None


def get_neo4j_driver() -> Neo4jDriverManager:
    """Retrieve or initialize the global Neo4j driver manager singleton."""
    global _neo4j_driver_manager
    if _neo4j_driver_manager is None:
        _neo4j_driver_manager = Neo4jDriverManager()
    return _neo4j_driver_manager

