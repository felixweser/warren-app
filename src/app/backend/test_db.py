#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

try:
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    # Test basic connection
    cur.execute("SELECT COUNT(*) FROM companies")
    company_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM statements")
    statement_count = cur.fetchone()[0]
    
    cur.execute("SELECT ticker, name FROM companies LIMIT 1")
    sample_company = cur.fetchone()
    
    cur.close()
    conn.close()
    
    print("✅ Database connection successful!")
    print(f"📊 Companies: {company_count}")
    print(f"📈 Statements: {statement_count}")
    if sample_company:
        print(f"📋 Sample company: {sample_company[0]} - {sample_company[1]}")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")