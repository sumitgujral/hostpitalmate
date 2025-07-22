import pymysql
import pymysql.cursors

class DatabaseManager:
    def __init__(self, host, user, password, database, port, charset="utf8mb4",
                 connect_timeout=10, read_timeout=10, write_timeout=10):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset=self.charset,
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                write_timeout=self.write_timeout,
            )
            print("Database connected successfully!")
            return True
        except pymysql.Error as e:
            print(f"FATAL: Error connecting to database: {e}")
            self.connection = None
            return False

    def disconnect(self):
        if self.connection and self.connection.open:
            self.connection.close()
            print("Database disconnected.")
        else:
            print("No active database connection to disconnect.")

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        if not self.connection or not self.connection.open:
            raise ConnectionError("Database connection is not active.")

        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        
        try:
            cursor.execute(query, params)

            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP')):
                self.connection.commit()
                result = cursor.rowcount
            elif fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = None

            return result
        except pymysql.Error as e:
            self.connection.rollback()
            print(f"Error executing query: {e}")
            raise
        finally:
            cursor.close()
