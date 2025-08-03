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

def get_gaap_element_info(cursor, tag):
    """Get GAAP element information for a given tag"""
    cursor.execute("""
        SELECT standard_label, documentation, financial_statement
        FROM gaap_elements
        WHERE element_name = %s;
    """, (tag,))
    
    result = cursor.fetchone()
    if result:
        return result[0], result[1], result[2]  # standard_label, documentation, financial_statement
    else:
        return None, None, None

def insert_statement_enhanced(cursor, company_id, tag, taxonomy, unit, value, start, end, fy, fp, filed, standard_label, documentation, financial_statement):
    cursor.execute("""
        INSERT INTO statements (company_id, tag, taxonomy, unit, value, start_date, end_date, fiscal_year, fiscal_period, filing_date, standard_label, documentation, financial_statement)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (company_id, tag, start_date, end_date) DO UPDATE SET
            value = EXCLUDED.value,
            standard_label = EXCLUDED.standard_label,
            documentation = EXCLUDED.documentation,
            financial_statement = EXCLUDED.financial_statement;
    """, (company_id, tag, taxonomy, unit, value, start, end, fy, fp, filed, standard_label, documentation, financial_statement))

def fetch_and_store_enhanced(cik, ticker, name):
    """Enhanced version that includes GAAP element information"""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    print(f"📥 Fetching SEC data for {ticker} ({cik})...")
    
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"❌ Failed to fetch data for CIK {cik}. Status: {resp.status_code}")
        return
    
    print(f"✅ Data fetched successfully for {ticker}!")
    data = resp.json()
    
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    # First, ensure the statements table has the new columns
    print("🔧 Ensuring database schema is up to date...")
    cur.execute("""
        ALTER TABLE statements 
        ADD COLUMN IF NOT EXISTS standard_label TEXT,
        ADD COLUMN IF NOT EXISTS documentation TEXT,
        ADD COLUMN IF NOT EXISTS financial_statement TEXT;
    """)
    
    company_id = insert_company(cur, cik, ticker, name)
    facts = data.get("facts", {}).get("us-gaap", {})

    count = 0
    enriched_count = 0
    unknown_tags = set()
    
    print(f"📊 Processing {len(facts)} different financial tags...")
    
    for tag, tag_data in facts.items():
        # Get GAAP element information for this tag
        standard_label, documentation, financial_statement = get_gaap_element_info(cur, tag)
        
        if standard_label:
            enriched_count += 1
        else:
            unknown_tags.add(tag)
        
        for unit, fact_list in tag_data.get("units", {}).items():
            for fact in fact_list:
                insert_statement_enhanced(
                    cur, company_id, tag, "us-gaap", unit,
                    fact.get("val"), fact.get("start"), fact.get("end"),
                    fact.get("fy"), fact.get("fp"), fact.get("filed"),
                    standard_label, documentation, financial_statement
                )
                count += 1
        
        if count % 5000 == 0:
            print(f"   Processed {count} financial facts...")

    conn.commit()
    
    # Show statistics
    print(f"✅ Successfully inserted {count} financial facts!")
    print(f"🏷️  {enriched_count} tags had GAAP element information")
    print(f"❓ {len(unknown_tags)} tags not found in GAAP elements")
    
    # Show financial statement breakdown
    cur.execute("""
        SELECT financial_statement, COUNT(DISTINCT tag) as unique_tags, COUNT(*) as total_facts
        FROM statements 
        WHERE company_id = %s AND financial_statement IS NOT NULL
        GROUP BY financial_statement
        ORDER BY total_facts DESC;
    """, (company_id,))
    
    print(f"📋 Financial statement breakdown for {ticker}:")
    for stmt, unique_tags, total_facts in cur.fetchall():
        print(f"   {stmt}: {unique_tags} unique tags, {total_facts} total facts")
    
    # Show some sample enriched data
    cur.execute("""
        SELECT tag, standard_label, financial_statement, COUNT(*) as fact_count
        FROM statements 
        WHERE company_id = %s AND standard_label IS NOT NULL
        GROUP BY tag, standard_label, financial_statement
        ORDER BY fact_count DESC
        LIMIT 10;
    """, (company_id,))
    
    print(f"\n🎯 Top 10 enriched financial elements:")
    for tag, label, stmt, fact_count in cur.fetchall():
        print(f"   {tag}: {label} ({stmt}) - {fact_count} facts")
    
    if unknown_tags:
        print(f"\n❓ Sample unknown tags (first 10):")
        for tag in list(unknown_tags)[:10]:
            print(f"   {tag}")
    
    conn.close()

if __name__ == "__main__":
    fetch_and_store_enhanced("0001652044", "GOOGL", "Alphabet Inc.")