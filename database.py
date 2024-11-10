import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class Database:
    def __init__(self):
        self.config = {
            'dbname': os.environ['PGDATABASE'],
            'user': os.environ['PGUSER'],
            'password': os.environ['PGPASSWORD'],
            'host': os.environ['PGHOST'],
            'port': os.environ['PGPORT']
        }

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()

    def get_building_codes(self, jurisdiction=None):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if columns exist
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'building_codes' 
                    AND column_name IN ('last_updated', 'created_at');
                """)
                existing_columns = [row['column_name'] for row in cur.fetchall()]

                # Construct base columns including sort columns in the SELECT
                base_columns = ['id', 'jurisdiction', 'category', 'section', 'content']
                date_columns = []
                if 'last_updated' in existing_columns:
                    date_columns.append('last_updated')
                if 'created_at' in existing_columns:
                    date_columns.append('created_at')

                # Build the query with all required columns
                query = f"""
                    SELECT DISTINCT {', '.join(base_columns)}, LOWER(category) as sort_category
                    {', ' + ', '.join(date_columns) if date_columns else ''}
                    FROM building_codes
                    WHERE (jurisdiction = %s OR %s IS NULL)
                    ORDER BY sort_category, section
                """
                
                cur.execute(query, (jurisdiction, jurisdiction))
                results = cur.fetchall()
                
                # Post-process to capitalize categories and remove sort column
                for row in results:
                    row['category'] = row['category'].title() if row['category'] else None
                    del row['sort_category']
                
                return results

    def get_jurisdictions(self):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT DISTINCT jurisdiction FROM building_codes ORDER BY jurisdiction")
                return [r['jurisdiction'] for r in cur.fetchall()]

    def get_categories(self):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT category, LOWER(category) as sort_category
                    FROM building_codes 
                    ORDER BY sort_category
                """)
                results = cur.fetchall()
                return [r['category'].title() if r['category'] else None for r in results]

    def update_category_case(self):
        """Update all categories to use consistent capitalization"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE building_codes
                    SET category = INITCAP(category)
                    WHERE category != INITCAP(category)
                """)
                conn.commit()
                return cur.rowcount
