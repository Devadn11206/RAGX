import sqlite3
import json
import threading
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

class TelemetryService:
    def __init__(self, db_path="/tmp/telemetry.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS request_traces (
                        request_id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        query TEXT,
                        tenant_id TEXT,
                        user_id TEXT,
                        total_latency_ms REAL,
                        status TEXT,
                        error TEXT,
                        is_test_run BOOLEAN
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS llm_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT,
                        timestamp TEXT,
                        provider TEXT,
                        model TEXT,
                        route TEXT,
                        success BOOLEAN,
                        failure_reason TEXT,
                        latency_ms REAL,
                        tokens_input INTEGER,
                        tokens_output INTEGER,
                        estimated_cost REAL,
                        fallback_used BOOLEAN,
                        retry_count INTEGER,
                        circuit_breaker_state TEXT,
                        is_test_run BOOLEAN
                    )
                """)
                conn.commit()

    def start_trace(self, query: str, tenant_id: str, user_id: str, is_test_run: bool = False) -> str:
        request_id = str(uuid.uuid4())
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO request_traces (
                        request_id, timestamp, query, tenant_id, user_id, status, is_test_run
                    ) VALUES (?, ?, ?, ?, ?, 'STARTED', ?)
                """, (
                    request_id, datetime.now(timezone.utc).isoformat(), query, tenant_id, user_id, is_test_run
                ))
                conn.commit()
        return request_id

    def complete_trace(self, request_id: str, total_latency_ms: float, status: str, error: str = None):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE request_traces 
                    SET total_latency_ms = ?, status = ?, error = ?
                    WHERE request_id = ?
                """, (total_latency_ms, status, error, request_id))
                conn.commit()

    def log_llm_event(self, request_id: str, provider: str, model: str, route: str, success: bool,
                      failure_reason: str, latency_ms: float, tokens_input: int, tokens_output: int,
                      estimated_cost: float, fallback_used: bool, retry_count: int, circuit_breaker_state: str,
                      is_test_run: bool = False):
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO llm_events (
                        request_id, timestamp, provider, model, route, success, failure_reason,
                        latency_ms, tokens_input, tokens_output, estimated_cost, fallback_used,
                        retry_count, circuit_breaker_state, is_test_run
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_id, datetime.now(timezone.utc).isoformat(), provider, model, route, success,
                    failure_reason, latency_ms, tokens_input, tokens_output, estimated_cost, fallback_used,
                    retry_count, circuit_breaker_state, is_test_run
                ))
                conn.commit()
                
    def get_global_metrics(self) -> Dict[str, Any]:
        return self.get_detailed_metrics()

    def get_detailed_metrics(self) -> Dict[str, Any]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                total_queries = conn.execute("SELECT COUNT(*) FROM request_traces").fetchone()[0]
                
                success_row = conn.execute("SELECT COUNT(*) FROM request_traces WHERE status = 'SUCCESS'").fetchone()
                success_count = success_row[0] if success_row else 0
                failed_count = total_queries - success_count
                success_rate = (success_count / total_queries * 100) if total_queries > 0 else 0.0
                
                # Latency percentiles
                latencies = [row[0] for row in conn.execute("SELECT total_latency_ms FROM request_traces WHERE total_latency_ms IS NOT NULL ORDER BY total_latency_ms").fetchall()]
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    p50_idx = int(len(latencies) * 0.50)
                    p95_idx = min(int(len(latencies) * 0.95), len(latencies) - 1)
                    p50_latency = latencies[p50_idx]
                    p95_latency = latencies[p95_idx]
                else:
                    avg_latency = 0.0
                    p50_latency = 0.0
                    p95_latency = 0.0
                
                gemini_count = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'gemini'").fetchone()[0]
                groq_count = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'groq'").fetchone()[0]
                
                gemini_success = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'gemini' AND success = 1").fetchone()[0]
                gemini_fail = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'gemini' AND success = 0").fetchone()[0]
                groq_success = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'groq' AND success = 1").fetchone()[0]
                groq_fail = conn.execute("SELECT COUNT(*) FROM llm_events WHERE provider = 'groq' AND success = 0").fetchone()[0]
                
                small_count = conn.execute("SELECT COUNT(*) FROM llm_events WHERE model LIKE '%flash%' OR model LIKE '%8b%'").fetchone()[0]
                large_count = conn.execute("SELECT COUNT(*) FROM llm_events WHERE model LIKE '%pro%' OR model LIKE '%70b%' OR model LIKE '%120b%' OR model LIKE '%27b%'").fetchone()[0]
                total_llm = gemini_count + groq_count
                
                fallback_count = conn.execute("SELECT COUNT(*) FROM llm_events WHERE fallback_used = 1").fetchone()[0]
                fallback_rate = (fallback_count / total_llm * 100) if total_llm > 0 else 0.0
                
                total_cost_row = conn.execute("SELECT SUM(estimated_cost) FROM llm_events").fetchone()
                total_cost = total_cost_row[0] if total_cost_row and total_cost_row[0] else 0.0
                
                return {
                    "total_queries": total_queries,
                    "successful_queries": success_count,
                    "failed_queries": failed_count,
                    "success_rate": success_rate,
                    "avg_latency": avg_latency,
                    "p50_latency": p50_latency,
                    "p95_latency": p95_latency,
                    "gemini_count": gemini_count,
                    "gemini_success": gemini_success,
                    "gemini_fail": gemini_fail,
                    "groq_count": groq_count,
                    "groq_success": groq_success,
                    "groq_fail": groq_fail,
                    "small_count": small_count,
                    "large_count": large_count,
                    "fallback_count": fallback_count,
                    "fallback_rate": fallback_rate,
                    "total_cost": total_cost
                }

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT r.request_id, r.timestamp, r.query, r.tenant_id, r.user_id, r.total_latency_ms, r.status, r.error,
                           l.provider, l.model, l.fallback_used, l.estimated_cost
                    FROM request_traces r
                    LEFT JOIN llm_events l ON r.request_id = l.request_id
                    ORDER BY r.timestamp DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]

telemetry_service = TelemetryService()
