import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")
print(f"DB_CONN: {DB_CONN}")

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
        return
    
    print(f"✅ Data fetched successfully for {ticker}!")
    data = resp.json()
    
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
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
    conn.close()
    print(f"✅ Inserted {count} financial facts into database.")

if __name__ == "__main__":
    fetch_and_store("0001652044", "GOOGL", "Alphabet Inc.")
