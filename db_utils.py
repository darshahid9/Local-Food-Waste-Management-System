# ============================================================
# Project   : Local Food Wastage Management System
# File      : db_utils.py
# Purpose   : Reusable MySQL connection and query helper
#             functions used across the Streamlit app
# Author    : Shahid Bashir Dar
# ============================================================

import mysql.connector
import pandas as pd

# ------------------------------------------------------------
# MySQL connection settings
# NOTE: Update these values to match your local MySQL setup
# ------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "food_wastage_db"
}


def get_connection():
    """Create and return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def run_query(query, params=None):
    """
    Run a SELECT query and return results as a pandas DataFrame.
    Use this for all read-only / analysis queries.
    """
    conn = get_connection()
    try:
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df


def execute_action(query, params=None):
    """
    Run an INSERT / UPDATE / DELETE statement.
    Commits the transaction and returns number of affected rows.
    Use this for all CRUD write operations.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        affected = cursor.rowcount
    finally:
        cursor.close()
        conn.close()
    return affected
