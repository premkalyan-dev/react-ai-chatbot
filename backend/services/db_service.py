import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="report",
        user="postgres",
        password="yourpassword",
        port=5432
    )
