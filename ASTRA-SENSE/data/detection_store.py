import json
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'data' / 'detections.sqlite3'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                camera_id TEXT,
                camera_name TEXT,
                person_count INTEGER DEFAULT 0,
                object_count INTEGER DEFAULT 0,
                interaction_count INTEGER DEFAULT 0,
                summary TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp DESC)"
        )


def save_detection(camera_id, camera_name, persons, objects, interactions, summary=None, details=None):
    init_db()
    payload = {
        'camera_id': str(camera_id),
        'camera_name': str(camera_name),
        'person_count': len(persons or []),
        'object_count': len(objects or []),
        'interaction_count': len(interactions or []),
        'timestamp': datetime.utcnow().timestamp(),
        'summary': summary or f'{camera_name} | {len(persons or [])} people | {len(objects or [])} objects',
        'details': details or json.dumps({
            'camera_id': str(camera_id),
            'camera_name': str(camera_name),
            'person_count': len(persons or []),
            'object_count': len(objects or []),
            'interaction_count': len(interactions or []),
        }, indent=2),
    }
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO detections (timestamp, camera_id, camera_name, person_count, object_count, interaction_count, summary, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload['timestamp'],
                payload['camera_id'],
                payload['camera_name'],
                payload['person_count'],
                payload['object_count'],
                payload['interaction_count'],
                payload['summary'],
                payload['details'],
            ),
        )
        return cursor.lastrowid


def list_detections(limit=50):
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM detections
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_detection(detection_id):
    with _connect() as conn:
        conn.execute('DELETE FROM detections WHERE id = ?', (detection_id,))


def delete_all_detections():
    init_db()
    with _connect() as conn:
        conn.execute('DELETE FROM detections')


def update_detection_summary(detection_id, summary, details=None):
    with _connect() as conn:
        conn.execute(
            'UPDATE detections SET summary = ?, details = ? WHERE id = ?',
            (summary, details, detection_id),
        )


def get_detection(detection_id):
    with _connect() as conn:
        row = conn.execute('SELECT * FROM detections WHERE id = ?', (detection_id,)).fetchone()
        return dict(row) if row else None
