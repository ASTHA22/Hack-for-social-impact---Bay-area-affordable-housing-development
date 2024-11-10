from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from database import Database

class CodeTracker:
    def __init__(self, db: Database):
        self.db = db

    def record_code_version(self, jurisdiction: str, version_number: str, effective_date: str) -> int:
        """Record a new code version for a jurisdiction"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO code_versions (jurisdiction, version_number, effective_date)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (jurisdiction, version_number) 
                    DO UPDATE SET effective_date = EXCLUDED.effective_date
                    RETURNING id
                """, (jurisdiction, version_number, effective_date))
                conn.commit()
                return cur.fetchone()[0]

    def record_code_update(self, code_version_id: int, section: str, category: str,
                         previous_content: Optional[str], new_content: str,
                         change_type: str) -> int:
        """Record a code update"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO code_updates 
                    (code_version_id, section, category, previous_content, new_content, change_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (code_version_id, section, category, previous_content, new_content, change_type))
                conn.commit()
                return cur.fetchone()[0]

    def get_code_updates(self, jurisdiction: Optional[str] = None,
                        category: Optional[str] = None,
                        from_date: Optional[str] = None,
                        limit: int = 100) -> List[Dict]:
        """Get code updates with optional filters"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT cu.*, cv.jurisdiction, cv.version_number, cv.effective_date
                    FROM code_updates cu
                    JOIN code_versions cv ON cu.code_version_id = cv.id
                    WHERE 1=1
                """
                params = []
                
                if jurisdiction:
                    query += " AND cv.jurisdiction = %s"
                    params.append(jurisdiction)
                
                if category:
                    query += " AND cu.category = %s"
                    params.append(category)
                
                if from_date:
                    query += " AND cu.update_date >= %s"
                    params.append(from_date)
                
                query += " ORDER BY cu.update_date DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                return cur.fetchall()

    def get_version_history(self, jurisdiction: Optional[str] = None) -> List[Dict]:
        """Get version history for jurisdictions"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT cv.*, COUNT(cu.id) as update_count
                    FROM code_versions cv
                    LEFT JOIN code_updates cu ON cv.id = cu.code_version_id
                    WHERE 1=1
                """
                params = []
                
                if jurisdiction:
                    query += " AND cv.jurisdiction = %s"
                    params.append(jurisdiction)
                
                query += " GROUP BY cv.id ORDER BY cv.effective_date DESC"
                
                cur.execute(query, params)
                return cur.fetchall()

    def subscribe_to_updates(self, email: str, jurisdiction: str, category: Optional[str] = None) -> int:
        """Subscribe to code updates for a jurisdiction"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO notification_subscriptions (user_email, jurisdiction, category)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_email, jurisdiction, category) DO NOTHING
                    RETURNING id
                """, (email, jurisdiction, category))
                conn.commit()
                return cur.fetchone()[0] if cur.rowcount > 0 else None

    def get_subscriptions(self, email: str) -> List[Dict]:
        """Get all subscriptions for a user"""
        with self.db.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM notification_subscriptions
                    WHERE user_email = %s
                    ORDER BY jurisdiction, category
                """, (email,))
                return cur.fetchall()
