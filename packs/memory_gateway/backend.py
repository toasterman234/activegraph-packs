"""Memory Gateway backend — in-memory SQLite implementation.

This is the default backend for Memory Gateway Pack v0.1.
It provides a simple key-value store for MemoryItems backed by SQLite.

v0.2 will add:
- Postgres + pgvector for vector similarity search
- Mem0 integration
- Supermemory integration

The backend interface is minimal:
  store_item(item_id, text, category, confidence, metadata)
  retrieve_by_query(query, top_k, min_score) → list[dict]
  enforce_limit(max_items)
  clear()

All implementations must satisfy this interface.
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Optional


# ------------------------------------------------------------------ helpers


def _word_set(text: str) -> set[str]:
    """Lowercase word set for keyword search."""
    STOPWORDS = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to",
        "for", "of", "with", "is", "are", "was", "were", "be",
        "it", "i", "we", "you", "they", "not",
    }
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def _jaccard(a: str, b: str) -> float:
    wa, wb = _word_set(a), _word_set(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


# ------------------------------------------------------------------ backend


class SqliteMemoryBackend:
    """SQLite-backed memory store.

    Uses ':memory:' by default (no persistence across runs).
    Pass a file path for persistence: SqliteMemoryBackend('memory.db').
    """

    _instances: dict[str, "SqliteMemoryBackend"] = {}

    def __init__(self, db_url: str = ":memory:"):
        self.db_url = db_url
        self._conn = sqlite3.connect(db_url, check_same_thread=False)
        self._setup()

    def _setup(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                item_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                category TEXT,
                confidence REAL DEFAULT 0.7,
                metadata TEXT DEFAULT '{}',
                created_at TEXT,
                last_retrieved_at TEXT,
                retrieval_count INTEGER DEFAULT 0
            )
        """)
        self._conn.commit()

    def store_item(
        self,
        item_id: str,
        text: str,
        category: Optional[str] = None,
        confidence: float = 0.7,
        metadata: Optional[dict] = None,
    ):
        """Store a new MemoryItem in the backend."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        self._conn.execute(
            """
            INSERT OR REPLACE INTO memory_items
                (item_id, text, category, confidence, metadata, created_at,
                 last_retrieved_at, retrieval_count)
            VALUES (?, ?, ?, ?, ?, ?, NULL, 0)
            """,
            (item_id, text, category, confidence, json.dumps(metadata or {}), now),
        )
        self._conn.commit()

    def retrieve_by_query(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.2,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve MemoryItems ranked by keyword overlap with query.

        Returns a list of dicts with: item_id, text, score, category, confidence.
        Sorted by score descending, limited to top_k.
        """
        cursor = self._conn.execute(
            "SELECT item_id, text, category, confidence FROM memory_items"
            + (" WHERE category = ?" if category else ""),
            (category,) if category else (),
        )
        rows = cursor.fetchall()

        scored = []
        for row in rows:
            item_id, text, cat, conf = row
            score = _jaccard(query, text)
            if score >= min_score:
                scored.append({
                    "item_id": item_id,
                    "text": text,
                    "category": cat,
                    "confidence": conf,
                    "score": round(score, 4),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def enforce_limit(self, max_items: int):
        """Evict least-recently-used items if over the limit."""
        cursor = self._conn.execute("SELECT COUNT(*) FROM memory_items")
        count = cursor.fetchone()[0]
        if count <= max_items:
            return
        excess = count - max_items
        self._conn.execute(
            """
            DELETE FROM memory_items WHERE item_id IN (
                SELECT item_id FROM memory_items
                ORDER BY COALESCE(last_retrieved_at, created_at) ASC
                LIMIT ?
            )
            """,
            (excess,),
        )
        self._conn.commit()

    def update_retrieval(self, item_id: str):
        """Update retrieval stats for an item."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            UPDATE memory_items
            SET retrieval_count = retrieval_count + 1,
                last_retrieved_at = ?
            WHERE item_id = ?
            """,
            (now, item_id),
        )
        self._conn.commit()

    def clear(self):
        """Remove all stored items."""
        self._conn.execute("DELETE FROM memory_items")
        self._conn.commit()

    def count(self) -> int:
        cursor = self._conn.execute("SELECT COUNT(*) FROM memory_items")
        return cursor.fetchone()[0]

    def close(self) -> None:
        """Close the underlying SQLite connection so the file handle is
        released (required before deleting the DB file on some platforms)."""
        try:
            self._conn.close()
        except Exception:
            pass


# ------------------------------------------------------------------ factory

_backends: dict[str, SqliteMemoryBackend] = {}


def get_backend(db_url: str = ":memory:") -> SqliteMemoryBackend:
    """Get or create a backend instance for the given db_url.

    In-memory backends are per-process singletons (shared within a run).
    File-based backends are also singletons keyed by path.
    """
    if db_url not in _backends:
        _backends[db_url] = SqliteMemoryBackend(db_url)
    return _backends[db_url]


def clear_all_backends():
    """Clear all backend instances and release their SQLite connections."""
    for backend in _backends.values():
        backend.clear()
        backend.close()
    _backends.clear()
