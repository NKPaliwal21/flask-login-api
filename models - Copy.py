import psycopg2
from config import Config

# Connect to the PostgreSQL database
conn = psycopg2.connect(Config.DB_URL)
cursor = conn.cursor()

# Fetch a user by username
def get_user_by_username(username):
#    cursor.execute("SELECT * FROM ivrtest.users WHERE username = %s", (username,))
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

    return cursor.fetchone()

# Insert a new user
def create_user(username, password):
    cursor.execute(
#        "INSERT INTO ivrtest.users (username, password) VALUES (%s, %s)",(username, password))
        "INSERT INTO ivrtest.users (username, password) VALUES (%s, %s)",(username, password))        
    conn.commit()
