import sys

import psycopg2


def check_db_ready(host, db, user, password, port):
    try:
        conn = psycopg2.connect(host=host, dbname=db, user=user, password=password, port=port, connect_timeout=5)
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"Database not ready: {e}")
        return False


if __name__ == "__main__":
    # Get arguments from command line
    host = sys.argv[1]
    db = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    port = int(sys.argv[5])

    while not check_db_ready(host, db, user, password, port):
        print("Waiting for Postgres response...")
