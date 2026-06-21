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
# MySQL connection settings - Aiven Cloud MySQL
# NOTE: Update host/port/user/password/database to match your
# Aiven service's "Connection information" page.
# ca.pem must be in the same folder as this file (downloaded
# from Aiven's "Secure connection" / certificate button).
# ------------------------------------------------------------
import os

DB_CONFIG = {
    "host": "mysql-285ca4dc-darshahid9-987c.i.aivencloud.com",       # e.g. mysql-285ca4dc-xxxx.aivencloud.com
    "port": 21399,                         # your Aiven port (NOT default 3306)
    "user": "avnadmin",
    "password": "AVNS_4gwLaOBmt7GWuJ98kom",
    "database": "food_wastage_db",
    "ssl_ca": os.path.join(os.path.dirname(__file__), "ca.pem"),
    "ssl_verify_cert": True,
    "ssl_verify_identity": False,
    "use_pure": True
    
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
