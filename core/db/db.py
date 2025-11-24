import psycopg2
from psycopg2 import sql

# ------------------
# Database Connection
# __________________


class Database:
    conn = None

    @classmethod
    def connect(self, dbname, user, password, host="localhost", port=5432):
        self.conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        self.conn.autocommit = True

    @classmethod
    def execute(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

            try:
                return cur.fetchall()

            except psycopg2.ProgrammingError:
                return None
