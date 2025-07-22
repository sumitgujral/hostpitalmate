import mysql.connector
import pymysql.cursors

class DatabaseManager:
    
    def __init__(self, host, user, password, database,port,cursorclass,charset,connect_timeout,read_timeout,write_timeout):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.port = port
        self.cursorclass = cursorclass
        self.charset = charset
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout

    def connect(self):
        self.connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            passwd=self.password,
            database=self.database,
            port=self.port,
            cursorclass=self.cursorclass, 
            charset=self.charset, 
            connect_timeout=self.connect_timeout, 
            read_timeout = self.read_timeout,  
            write_timeout=self.write_timeout
            )
            
        print("Database connected successfully!")
        return True

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database disconnected.")

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        if not self.connection or not self.connection.is_connected():
            raise ConnectionError("Database connection is not active.")

        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params)

        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
            self.connection.commit()
            result = cursor.rowcount
        elif fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None

        cursor.close()
        return result