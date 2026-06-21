# ============================================================
# Project   : Local Food Wastage Management System
# File      : db_utils.py
# Purpose   : Reusable MySQL connection and query helper
#             functions used across the Streamlit app
# Author    : Shahid Bashir Dar
# ============================================================

import os
import tempfile
import mysql.connector
import pandas as pd
import streamlit as st

# ------------------------------------------------------------
# MySQL connection settings - Aiven Cloud MySQL
# Credentials are read from Streamlit secrets (.streamlit/secrets.toml
# locally, or the "Secrets" panel on Streamlit Community Cloud).
# NEVER hardcode credentials directly in this file.
# ------------------------------------------------------------

def _get_ca_cert_path():
    """
    Write the CA certificate (stored as a secret string) to a temp
    file and return its path, since mysql-connector needs a file path,
    not raw text.
    """
    ca_cert_content = st.secrets["mysql"]["ssl_ca_content"]
    tmp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
    tmp_file.write(ca_cert_content)
    tmp_file.close()
    return tmp_file.name


def get_connection():
    """Create and return a new MySQL connection using Streamlit secrets."""
    db_secrets = st.secrets["mysql"]

    config = {
        "host": db_secrets["host"],
        "port": int(db_secrets["port"]),
        "user": db_secrets["user"],
        "password": db_secrets["password"],
        "database": db_secrets["database"],
        "ssl_ca": _get_ca_cert_path(),
        "ssl_verify_cert": True,
        "ssl_verify_identity": False,
        "use_pure": True,
    }
    return mysql.connector.connect(**config)


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
