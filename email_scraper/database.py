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
            "port": os.getenv("DB_PORT", "5432"),
        }
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.db_params)
            print("database connected (b^_^)b ")
        except Exception as e:
            print(f"(+_+) database connection error: {e}")
            raise

    def insert_email(self, subject, sender, received_date, label, message_id=None):
        try:
            with self.conn.cursor() as cur:
                # first, try to dedupe by message_id if it exists already
                if message_id:
                    cur.execute(
                        """
                        SELECT id FROM job_emails
                        WHERE message_id = %s
                    """,
                        (message_id,),
                    )
                    existing_by_msg = cur.fetchone()
                    if existing_by_msg:
                        print(f"ミ(ノ_ _)ノ skipping duplicate by message_id: {subject}")
                        return None

                # by subject + date + sender as fallback
                cur.execute(
                    """
                    SELECT id FROM job_emails 
                    WHERE subject = %s 
                    AND recieved_date = %s
                    AND sender = %s
                """,
                    (subject, received_date, sender),
                )

                existing = cur.fetchone()
                if existing:
                    print(f"ミ(ノ_ _)ノ skipping any duplicates: {subject}")
                    return None

                # insert the new email
                if message_id:
                    cur.execute(
                        """
                        INSERT INTO job_emails (subject, sender, recieved_date, label, message_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id;
                    """,
                        (subject, sender, received_date, label, message_id),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO job_emails (subject, sender, recieved_date, label)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id;
                    """,
                        (subject, sender, received_date, label),
                    )
                self.conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            print(f"(+_+) error inserting email: {e}")
            self.conn.rollback()
            return None

    def get_emails(self, label=None, search=None):

        try:
            with self.conn.cursor() as cur:
                base_query = """
                    SELECT id, subject, sender, recieved_date, label 
                    FROM job_emails
                """
                conditions = []
                params = []

                if label and label.lower() != "all":
                    conditions.append("label = %s")
                    params.append(label)

                if search:
                    conditions.append("(subject ILIKE %s OR sender ILIKE %s)")
                    like = f"%{search}%"
                    params.extend([like, like])

                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                base_query += " ORDER BY recieved_date DESC;"

                cur.execute(base_query, params)
                return cur.fetchall()
        except Exception as e:
            print(f"(+_+) error fetching filtered emails: {e}")
            return []

    def get_all_emails(self):

        return self.get_emails()

    def update_email_label(self, email_id, new_label):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE job_emails 
                    SET label = %s 
                    WHERE id = %s;
                """,
                    (new_label, email_id),
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"(+_+) error updating email label: {e}")
            self.conn.rollback()
            return False

    def delete_email(self, email_id):
        # delete an email from the database by its ID
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM job_emails 
                    WHERE id = %s
                """,
                    (email_id,),
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"(+_+) error deleting email: {e}")
            self.conn.rollback()
            return False

    def get_statistics(self):
        try:
            with self.conn.cursor() as cur:
                # total count
                cur.execute("SELECT COUNT(*) FROM job_emails")
                total_count = cur.fetchone()[0]

                # counts by label
                cur.execute(
                    """
                    SELECT label, COUNT(*) as count 
                    FROM job_emails 
                    GROUP BY label 
                    ORDER BY count DESC
                """
                )
                label_counts = cur.fetchall()

                # last 7 days
                cur.execute(
                    """
                    SELECT COUNT(*) 
                    FROM job_emails 
                    WHERE recieved_date >= NOW() - INTERVAL '7 days'
                """
                )
                recent_count = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT
                        SUM(CASE WHEN label = 'application' THEN 1 ELSE 0 END) AS applications,
                        SUM(CASE WHEN label = 'interview' THEN 1 ELSE 0 END)   AS interviews,
                        SUM(CASE WHEN label = 'offer' THEN 1 ELSE 0 END)       AS offers,
                        SUM(CASE WHEN label = 'rejection' THEN 1 ELSE 0 END)   AS rejections
                    FROM job_emails;
                """
                )
                pipeline_row = cur.fetchone()
                pipeline = {
                    "applications": pipeline_row[0] or 0,
                    "interviews": pipeline_row[1] or 0,
                    "offers": pipeline_row[2] or 0,
                    "rejections": pipeline_row[3] or 0,
                }

                return {
                    "total": total_count,
                    "by_label": label_counts,
                    "recent": recent_count,
                    "pipeline": pipeline,
                }
        except Exception as e:
            print(f"(+_+) error getting statistics: {e}")
            return None

    def close(self):
        if self.conn:
            self.conn.close()
