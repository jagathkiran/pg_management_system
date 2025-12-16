import sqlite3
import pandas as pd
import os

# Database path
DB_PATH = "./database/pg_management.db"

def list_tables(conn):
    """Lists all tables in the SQLite database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [t[0] for t in tables]

def view_table(conn, table_name):
    """Views and prints the content of a specific table using pandas."""
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        print(f"\n--- Table: {table_name} ---")
        if df.empty:
            print("(Empty)")
        else:
            # Set display options for better readability of wide tables
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000) # Adjust based on terminal width
            pd.set_option('display.colheader_justify', 'left')
            print(df.to_string(index=False)) # index=False to hide pandas default index
        print("-" * 30)
    except pd.io.sql.DatabaseError as e:
        print(f"Error reading table '{table_name}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred while viewing table '{table_name}': {e}")

def main():
    """Main function to connect to DB and display all table contents."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at '{DB_PATH}'. Please ensure the backend has been run to create it.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        tables = list_tables(conn)
        
        if not tables:
            print(f"No tables found in the database '{DB_PATH}'.")
            return
            
        print(f"Found {len(tables)} tables in '{DB_PATH}': {', '.join(tables)}")
        print("\nDisplaying contents of all tables:")
        
        for table in tables:
            view_table(conn, table)

    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
