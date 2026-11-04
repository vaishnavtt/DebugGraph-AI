"""
Event correlation and grouping engine for DebugGraph AI.
Groups related log events by shared correlation IDs, recurring exception patterns,
and temporal proximity without asserting unverified causal claims.
"""
from collections import defaultdict
from datetime import timedelta
from typing import List, Optional
import uuid

from app.schemas.logs import LogEntry, LogEventGroup


class EventGrouper:
    """Correlates parsed log entries into logical clusters."""

    CORRELATION_KEYS = [
        "correlation_id",
        "request_id",
        "trace_id",
        "transaction_id",
        "order_id",
        "session_id",
        "req_id",
    ]

    @classmethod
    def group_events(
        cls, entries: List[LogEntry], temporal_window_seconds: int = 60
    ) -> List[LogEventGroup]:
        """Group related log entries using multiple non-causal heuristic dimensions."""
        groups: List[LogEventGroup] = []
        grouped_entry_ids = set()

        # Strategy 1: Shared Correlation / Request ID matching
        id_clusters: defaultdict = defaultdict(list)
        for entry in entries:
            for key in cls.CORRELATION_KEYS:
                val = entry.attributes.get(key)
                if val:
                    cluster_key = f"{key}:{str(val).strip()}"
                    id_clusters[cluster_key].append(entry)
                    break

        for cluster_id, cluster_entries in id_clusters.items():
            if len(cluster_entries) >= 2:
                key_name, key_val = cluster_id.split(":", 1)
                e_ids = [e.entry_id for e in cluster_entries]
                services = {e.service for e in cluster_entries if e.service}
                svc_name = services.pop() if len(services) == 1 else None

                timestamps = [e.timestamp for e in cluster_entries if e.timestamp]
                start_ts = min(timestamps) if timestamps else None
                end_ts = max(timestamps) if timestamps else None

                groups.append(
                    LogEventGroup(
                        group_id=f"grp_corr_{uuid.uuid4().hex[:8]}",
                        group_type="shared_correlation_id",
                        service=svc_name,
                        description=f"Correlated events sharing {key_name}: {key_val}",
                        entry_ids=e_ids,
                        entry_count=len(e_ids),
                        start_timestamp=start_ts,
                        end_timestamp=end_ts,
                    )
                )
                grouped_entry_ids.update(e_ids)

        # Strategy 2: Common Exception Signature
        exception_clusters: defaultdict = defaultdict(list)
        for entry in entries:
            if entry.exception_type:
                cluster_key = (entry.service or "unknown", entry.exception_type)
                exception_clusters[cluster_key].append(entry)

        for (svc, exc_type), cluster_entries in exception_clusters.items():
            if len(cluster_entries) >= 2:
                e_ids = [e.entry_id for e in cluster_entries]
                timestamps = [e.timestamp for e in cluster_entries if e.timestamp]
                start_ts = min(timestamps) if timestamps else None
                end_ts = max(timestamps) if timestamps else None

                groups.append(
                    LogEventGroup(
                        group_id=f"grp_exc_{uuid.uuid4().hex[:8]}",
                        group_type="common_exception",
                        service=svc if svc != "unknown" else None,
                        description=f"Recurrent {exc_type} observed {len(e_ids)} times in {svc}",
                        entry_ids=e_ids,
                        entry_count=len(e_ids),
                        start_timestamp=start_ts,
                        end_timestamp=end_ts,
                    )
                )

        # Strategy 3: Temporal Proximity for High-Severity Events (ERROR, CRITICAL)
        # Explicitly annotated as temporal correlation only
        high_severity_entries = [
            e for e in entries
            if e.severity in ("ERROR", "CRITICAL") and e.timestamp is not None
        ]
        # Sort chronologically
        high_severity_entries.sort(key=lambda x: x.timestamp)  # type: ignore[arg-type]

        i = 0
        while i < len(high_severity_entries):
            current = high_severity_entries[i]
            window_entries = [current]
            window_limit = current.timestamp + timedelta(seconds=temporal_window_seconds)  # type: ignore[operator]

            j = i + 1
            while j < len(high_severity_entries):
                candidate = high_severity_entries[j]
                if candidate.timestamp <= window_limit:  # type: ignore[operator]
                    window_entries.append(candidate)
                    j += 1
                else:
                    break

            if len(window_entries) >= 2:
                # Check if this exact set is already represented in previous groups
                w_ids = [e.entry_id for e in window_entries]
                services = {e.service for e in window_entries if e.service}
                svc_label = ", ".join(sorted(services)) if services else "unspecified service"

                groups.append(
                    LogEventGroup(
                        group_id=f"grp_temp_{uuid.uuid4().hex[:8]}",
                        group_type="temporal_proximity",
                        service=services.pop() if len(services) == 1 else None,
                        description=(
                            f"Burst of {len(w_ids)} high-severity events within "
                            f"{temporal_window_seconds}s in [{svc_label}] (temporal proximity only; non-causal)"
                        ),
                        entry_ids=w_ids,
                        entry_count=len(w_ids),
                        start_timestamp=window_entries[0].timestamp,
                        end_timestamp=window_entries[-1].timestamp,
                    )
                )
                i = j
            else:
                i += 1

        return groups

