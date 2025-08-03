import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

def verify_enriched_data():
    """Verify the enriched GOOGL data import"""
    
    print("🔗 Connecting to database...")
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    # Basic counts
    cur.execute("SELECT COUNT(*) FROM companies;")
    company_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM statements;")
    statement_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM statements WHERE standard_label IS NOT NULL;")
    enriched_count = cur.fetchone()[0]
    
    print(f"📊 Database Overview:")
    print(f"   🏢 Companies: {company_count}")
    print(f"   📋 Total statements: {statement_count}")
    print(f"   🏷️  Enriched statements: {enriched_count} ({enriched_count/statement_count*100:.1f}%)")
    
    # Financial statement breakdown
    cur.execute("""
        SELECT 
            financial_statement,
            COUNT(*) as fact_count,
            COUNT(DISTINCT tag) as unique_tags,
            MIN(fiscal_year) as earliest_year,
            MAX(fiscal_year) as latest_year
        FROM statements 
        WHERE financial_statement IS NOT NULL
        GROUP BY financial_statement
        ORDER BY fact_count DESC;
    """)
    
    print(f"\n📈 Financial Statement Breakdown:")
    for stmt, fact_count, unique_tags, earliest, latest in cur.fetchall():
        print(f"   {stmt}:")
        print(f"      📊 {fact_count} facts ({unique_tags} unique tags)")
        print(f"      📅 Years: {earliest} - {latest}")
    
    # Sample enriched data
    cur.execute("""
        SELECT 
            tag,
            standard_label,
            financial_statement,
            fiscal_year,
            value,
            unit
        FROM statements 
        WHERE standard_label IS NOT NULL 
            AND fiscal_year = 2023 
            AND financial_statement = 'Statement of Income'
        ORDER BY ABS(value) DESC
        LIMIT 10;
    """)
    
    print(f"\n🎯 Top 10 Income Statement Items (2023):")
    for tag, label, stmt, year, value, unit in cur.fetchall():
        formatted_value = f"{value:,.0f}" if value else "N/A"
        print(f"   {label}:")
        print(f"      💰 {formatted_value} {unit}")
        print(f"      🏷️  {tag}")
    
    # Check for common financial metrics
    key_metrics = [
        'Revenues',
        'NetIncomeLoss', 
        'Assets',
        'Liabilities',
        'StockholdersEquity',
        'OperatingIncomeLoss'
    ]
    
    print(f"\n🔍 Key Financial Metrics Availability:")
    for metric in key_metrics:
        cur.execute("""
            SELECT COUNT(*), MIN(fiscal_year), MAX(fiscal_year)
            FROM statements 
            WHERE tag = %s;
        """, (metric,))
        
        result = cur.fetchone()
        if result and result[0] > 0:
            count, min_year, max_year = result
            print(f"   ✅ {metric}: {count} facts ({min_year}-{max_year})")
        else:
            print(f"   ❌ {metric}: Not found")
    
    # Check year coverage
    cur.execute("""
        SELECT fiscal_year, COUNT(*) as fact_count
        FROM statements 
        WHERE fiscal_year IS NOT NULL
        GROUP BY fiscal_year
        ORDER BY fiscal_year DESC
        LIMIT 10;
    """)
    
    print(f"\n📅 Year Coverage (latest 10 years):")
    for year, count in cur.fetchall():
        print(f"   {year}: {count} facts")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    verify_enriched_data()