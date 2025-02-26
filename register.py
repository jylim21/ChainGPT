import os
import json
import psycopg2
import datetime
import bcrypt
import uuid
from dotenv import load_dotenv

load_dotenv()

dbhost = os.environ.get("DB_HOST")
dbuser = os.environ.get("DB_USER")
dbpassword = os.environ.get("DB_PASSWORD")
dbname = os.environ.get("DB_NAME")

# conn_str = f"{dbuser}:{dbpassword}@{dbhost}:5432/{dbname}" 
# cl_data._data_layer = SQLAlchemyDataLayer(f"postgresql+asyncpg://{conn_str}", storage_provider=cl_data.base.BaseStorageClient)

def register_user(username: str, password: str) -> bool:
    """Registers a new user by adding them to the 'logins' table."""
    try:
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Connect to the PostgreSQL database
        conn_str = f"host={dbhost} dbname={dbname} user={dbuser} password={dbpassword}"
        conn = psycopg2.connect(conn_str)

        id = str (uuid.uuid4()) 
        identifier = username
        metadata = { "role" : "admin" }
        created_date = datetime.datetime.now().isoformat()



        with conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT id FROM users WHERE identifier = %s""", (identifier,))
                check_exist=cur.fetchall()
            
            if len (check_exist) > 0:
                print ( "User already exist." )
                return  False
            with conn.cursor() as cur:

                cur.execute(
                    """INSERT INTO logins (id, "createdAt", "passwordHash") VALUES (%s, %s, %s)""" ,
                    (id, created_date, hashed_password),
                )

            with conn.cursor() as cur:
                # User information table
                cur.execute(
                    """INSERT INTO users (id, identifier, metadata, "createdAt") VALUES (%s, %s, %s, %s)""" ,
                    ( id , identifier, json.dumps(metadata), created_date)
                )
            conn.commit()

            print("User registered successfully.")
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    new_username = input("Enter a new username: ")
    new_password = input("Enter a new password: ")
    register_user(new_username, new_password)
