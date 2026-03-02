#!/usr/bin/env python3
"""
Database Connection Diagnostics
Run this inside the Docker container to debug connection issues.
"""

import os
import socket
import ssl
import subprocess
from dotenv import load_dotenv

load_dotenv()

def header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

# Configuration
DB_SERVER = os.environ.get('DB_SERVER', '172.24.57.68')
DB_PORT = 1433
DB_NAME = os.environ.get('DB_NAME', 'Export_DB')
DB_USER = os.environ.get('DB_USER', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

header("1. Environment Variables")
print(f"DB_SERVER: {DB_SERVER}")
print(f"DB_NAME: {DB_NAME}")
print(f"DB_USER: {DB_USER}")
print(f"DB_PASSWORD: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(empty)'}")
print(f"DB_USE_WINDOWS_AUTH: {os.environ.get('DB_USE_WINDOWS_AUTH', 'not set')}")

header("2. OpenSSL Version & Config")
print(run_cmd("openssl version -a"))
print(f"\nOPENSSL_CONF env: {os.environ.get('OPENSSL_CONF', 'not set')}")

header("3. ODBC Driver Check")
print(run_cmd("odbcinst -q -d"))
print("\n/etc/odbcinst.ini:")
print(run_cmd("cat /etc/odbcinst.ini 2>/dev/null || echo 'File not found'"))

header("4. TCP Connection Test")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    result = sock.connect_ex((DB_SERVER, DB_PORT))
    if result == 0:
        print(f"OK: TCP connection to {DB_SERVER}:{DB_PORT} successful")
    else:
        print(f"FAIL: TCP connection failed with error code {result}")
    sock.close()
except Exception as e:
    print(f"FAIL: {e}")

header("5. TLS/SSL Handshake Test")
try:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((DB_SERVER, DB_PORT), timeout=5) as sock:
        # SQL Server doesn't do plain TLS handshake, but this shows SSL capabilities
        print(f"Socket connected to {DB_SERVER}:{DB_PORT}")
        print(f"Default SSL protocol: {ssl.PROTOCOL_TLS}")
        print(f"OpenSSL version: {ssl.OPENSSL_VERSION}")
except Exception as e:
    print(f"Connection test: {e}")

header("6. PyODBC Connection Test (Detailed)")
try:
    import pyodbc
    print(f"pyodbc version: {pyodbc.version}")
    print(f"ODBC drivers available: {pyodbc.drivers()}")

    # Build connection string
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"Encrypt=no;"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=10"
    )

    print(f"\nConnection string (password hidden):")
    print(conn_str.replace(DB_PASSWORD, '****'))

    print("\nAttempting connection...")
    conn = pyodbc.connect(conn_str)
    print("SUCCESS: Connected to database!")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print(f"SQL Server version: {row[0][:80]}...")
    conn.close()

except pyodbc.Error as e:
    print(f"PYODBC ERROR:")
    print(f"  State: {e.args[0] if e.args else 'N/A'}")
    print(f"  Message: {e.args[1] if len(e.args) > 1 else str(e)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

header("7. Testing with different TLS settings")
try:
    import pyodbc

    # Try with explicit TLS settings
    conn_str_tls = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"Encrypt=optional;"
        f"TrustServerCertificate=yes;"
    )

    print("Trying with Encrypt=optional...")
    try:
        conn = pyodbc.connect(conn_str_tls, timeout=10)
        print("SUCCESS with Encrypt=optional!")
        conn.close()
    except Exception as e:
        print(f"Failed: {e}")

    # Try without any encryption settings
    conn_str_plain = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
    )

    print("\nTrying without encryption settings...")
    try:
        conn = pyodbc.connect(conn_str_plain, timeout=10)
        print("SUCCESS without encryption settings!")
        conn.close()
    except Exception as e:
        print(f"Failed: {e}")

except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*60)
print("  Diagnostics complete -> 25022026")
print("="*60)
