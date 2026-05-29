#!/usr/bin/env python
"""
Create the NFL Fantasy Football database using Python/psycopg2.
Run: python create_db.py
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    host = os.getenv("DB_HOST", "localhost")
    database = os.getenv("DB_NAME", "nfl_fantasy")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    port = int(os.getenv("DB_PORT", "5432"))

    if not password:
        print("Error: DB_PASSWORD not set in .env file")
        print("Edit .env and add: DB_PASSWORD=your_password")
        return 1

    print(f"Connecting to PostgreSQL at {host}:{port}...")

    try:
        conn = psycopg2.connect(
            host=host,
            database="postgres",
            user=user,
            password=password,
            port=port
        )
        print("Connected to 'postgres' database.")

        cur = conn.cursor()

        # Drop database if exists (to start fresh)
        try:
            cur.execute(f"DROP DATABASE IF EXISTS {database}")
        except:
            pass

        # Create database
        try:
            cur.execute(f"CREATE DATABASE {database}")
            print(f"Created database: {database}")
        except psycopg2.ProgrammingError as e:
            if "already exists" in str(e):
                print(f"Database already exists: {database}")

        conn.close()

        # Connect to the new database
        print(f"Connecting to {database}...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        print(f"Connected to {database}")

        cur = conn.cursor()

        # Execute schema SQL
        with open("schema.sql", "r") as f:
            schema_sql = f.read()

        try:
            cur.execute(schema_sql)
            conn.commit()
            print("Tables and indexes created successfully!")
        except Exception as e:
            print(f"Schema execution error: {e}")
            conn.rollback()
            return 1

        # Show tables
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        print(f"\nTables created: {', '.join(tables)}")

        conn.close()

        print("\n" + "="*50)
        print("Database setup complete!")
        print("="*50)
        print("\nNext steps:")
        print("1. Run: python run.py --help")
        print("2. Run: python run.py --date 2025-09-04  (when season is active)")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
