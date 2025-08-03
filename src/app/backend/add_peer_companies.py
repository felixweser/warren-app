#!/usr/bin/env python3
"""
Add peer companies to the database for comparison functionality.
This script fetches financial data from SEC API for major tech companies.
"""

import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

headers = {
    'User-Agent': 'Felix Kuhlmann (kuhlmannfelix98@gmail.com)'
}

def insert_company(cursor, cik, ticker, name):
    cursor.execute("""
        INSERT INTO companies (cik, ticker, name)
        VALUES (%s, %s, %s)
        ON CONFLICT (cik) DO UPDATE SET ticker = EXCLUDED.ticker, name = EXCLUDED.name
        RETURNING id;
    """, (cik, ticker, name))
    return cursor.fetchone()[0]

def insert_statement(cursor, company_id, tag, taxonomy, unit, value, start, end, fy, fp, filed):
    cursor.execute("""
        INSERT INTO statements (company_id, tag, taxonomy, unit, value, start_date, end_date, fiscal_year, fiscal_period, filing_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, (company_id, tag, taxonomy, unit, value, start, end, fy, fp, filed))

def fetch_and_store(cik, ticker, name):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print(f"Fetching SEC data for {ticker} ({cik})...")
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Failed to fetch data for CIK {cik}. Status: {resp.status_code}")
        return False
    
    print(f"✅ Data fetched successfully for {ticker}!")
    data = resp.json()
    
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    try:
        company_id = insert_company(cur, cik, ticker, name)
        facts = data.get("facts", {}).get("us-gaap", {})

        count = 0
        for tag, tag_data in facts.items():
            for unit, fact_list in tag_data.get("units", {}).items():
                for fact in fact_list:
                    insert_statement(
                        cur, company_id, tag, "us-gaap", unit,
                        fact.get("val"), fact.get("start"), fact.get("end"),
                        fact.get("fy"), fact.get("fp"), fact.get("filed")
                    )
                    count += 1

        conn.commit()
        print(f"✅ Inserted {count} financial facts for {ticker}.")
        return True
    except Exception as e:
        print(f"❌ Error processing {ticker}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    # Major tech companies with their CIK numbers
    companies = [
        ("0000320193", "AAPL", "Apple Inc."),           # Apple
        ("0000789019", "MSFT", "Microsoft Corporation"), # Microsoft
        ("0001326801", "META", "Meta Platforms Inc."),   # Meta (Facebook)
        ("0001018724", "AMZN", "Amazon.com Inc."),       # Amazon
        ("0001045810", "NVDA", "NVIDIA Corporation"),    # NVIDIA
    ]
    
    print("🚀 Starting ETL process for peer companies...")
    print(f"📊 Will add {len(companies)} companies to database\n")
    
    successful = 0
    failed = 0
    
    for cik, ticker, name in companies:
        print(f"\n📈 Processing {ticker} - {name}")
        if fetch_and_store(cik, ticker, name):
            successful += 1
        else:
            failed += 1
        print("-" * 50)
    
    print(f"\n🎉 ETL Process Complete!")
    print(f"✅ Successfully added: {successful} companies")
    print(f"❌ Failed: {failed} companies")
    
    # Show final company list
    print("\n📊 Companies now in database:")
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    cur.execute('SELECT ticker, name FROM companies ORDER BY ticker')
    companies = cur.fetchall()
    for ticker, name in companies:
        print(f"  {ticker}: {name}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()