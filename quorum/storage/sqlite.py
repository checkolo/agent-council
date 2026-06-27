from __future__ import annotations

import json
import os
import sqlite3
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def default_db_path() -> Path:
    env = os.environ.get("QUORUM_DB_PATH", "")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".quorum" / "quorum.db"


class Storage:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    template TEXT NOT NULL,
                    input_text TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'fast',
                    status TEXT NOT NULL DEFAULT 'pending',
                    decision_report TEXT,
                    cost_usd REAL DEFAULT 0,
                    duration_ms INTEGER DEFAULT 0,
                    max_cost REAL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS run_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    member TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                );
                CREATE INDEX IF NOT EXISTS idx_run_events_run_id ON run_events(run_id);
                CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at DESC);
            """)
            try:
                conn.execute("ALTER TABLE runs ADD COLUMN error TEXT")
            except sqlite3.OperationalError:
                pass

    def get_setting(self, key: str) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else None

    def set_setting(self, key: str, value: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )

    def create_run(
        self,
        template: str,
        input_text: str,
        mode: str = "fast",
        max_cost: float | None = None,
    ) -> str:
        run_id = str(uuid.uuid4())[:8]
        now = datetime.now(UTC).isoformat()
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO runs (id, template, input_text, mode, status, max_cost, created_at)
                   VALUES (?, ?, ?, ?, 'pending', ?, ?)""",
                (run_id, template, input_text, mode, max_cost, now),
            )
        return run_id

    def update_run(
        self,
        run_id: str,
        *,
        status: str | None = None,
        decision_report: dict | None = None,
        cost_usd: float | None = None,
        duration_ms: int | None = None,
        error: str | None = None,
    ) -> None:
        fields: list[str] = []
        values: list[Any] = []
        if status is not None:
            fields.append("status = ?")
            values.append(status)
            if status == "complete":
                fields.append("completed_at = ?")
                values.append(datetime.now(UTC).isoformat())
        if decision_report is not None:
            fields.append("decision_report = ?")
            values.append(json.dumps(decision_report))
        if cost_usd is not None:
            fields.append("cost_usd = ?")
            values.append(cost_usd)
        if duration_ms is not None:
            fields.append("duration_ms = ?")
            values.append(duration_ms)
        if error is not None:
            fields.append("error = ?")
            values.append(error)
        if not fields:
            return
        values.append(run_id)
        with self.connect() as conn:
            conn.execute(
                f"UPDATE runs SET {', '.join(fields)} WHERE id = ?",
                values,
            )

    def add_event(
        self,
        run_id: str,
        event_type: str,
        payload: dict,
        member: str | None = None,
    ) -> int:
        now = datetime.now(UTC).isoformat()
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO run_events (run_id, event_type, member, payload, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (run_id, event_type, member, json.dumps(payload), now),
            )
            return cur.lastrowid or 0

    def get_run(self, run_id: str) -> dict | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get("decision_report"):
                result["decision_report"] = json.loads(result["decision_report"])
            return result

    def list_runs(
        self,
        limit: int = 20,
        offset: int = 0,
        template: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        query = "SELECT * FROM runs WHERE 1=1"
        params: list[Any] = []
        if template:
            query += " AND template = ?"
            params.append(template)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with self.connect() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                r = dict(row)
                if r.get("decision_report"):
                    r["decision_report"] = json.loads(r["decision_report"])
                results.append(r)
            return results

    def get_events(self, run_id: str, after_id: int = 0) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """SELECT * FROM run_events
                   WHERE run_id = ? AND id > ?
                   ORDER BY id ASC""",
                (run_id, after_id),
            ).fetchall()
            return [
                {
                    **dict(row),
                    "payload": json.loads(row["payload"]),
                }
                for row in rows
            ]

    def self_test(self) -> bool:
        test_id = f"test-{uuid.uuid4().hex[:6]}"
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                (test_id, "ok"),
            )
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (test_id,)
            ).fetchone()
            conn.execute("DELETE FROM settings WHERE key = ?", (test_id,))
        return row is not None and row["value"] == "ok"
