import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.db_params = {
            "dbname": os.getenv("DB_NAME", "job_search_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_params)
            print("database connected (b^_^)b ")
        except Exception as e:
            print(f"(+_+) database connection error: {e}")
            raise

    def insert_email(self, subject, sender, received_date, label):
        try:
            # check if the email already exists !!
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM job_emails 
                    WHERE subject = %s 
                    AND recieved_date = %s
                    AND sender = %s
                """, (subject, received_date, sender))
                
                existing = cur.fetchone()
                if existing:
                    print(f"ミ(ノ_ _)ノ skipping any duplicates: {subject}")
                    return None

                # no dupes, insert the new email
                cur.execute("""
                    INSERT INTO job_emails (subject, sender, recieved_date, label)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """, (subject, sender, received_date, label))
                self.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            print(f"(+_+) error inserting email: {e}")
            self.conn.rollback()
            return None

    def get_all_emails(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, subject, sender, recieved_date, label 
                    FROM job_emails 
                    ORDER BY recieved_date DESC;
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"(+_+) error fetching emails: {e}")
            return []

    def update_email_label(self, email_id, new_label):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE job_emails 
                    SET label = %s 
                    WHERE id = %s;
                """, (new_label, email_id))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"(+_+) error updating email label: {e}")
            self.conn.rollback()
            return False
        
    def get_statistics(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM job_emails")
                total_count = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT label, COUNT(*) as count 
                    FROM job_emails 
                    GROUP BY label 
                    ORDER BY count DESC
                """)
                label_counts = cur.fetchall()
                
                # last 7 days*
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM job_emails 
                    WHERE recieved_date >= NOW() - INTERVAL '7 days'
                """)
                recent_count = cur.fetchone()[0]
                
                return {
                    'total': total_count,
                    'by_label': label_counts,
                    'recent': recent_count
                }
        except Exception as e:
            print(f"(+_+) error getting statistics: {e}")
            return None    

    def close(self):
        if self.conn:
            self.conn.close()