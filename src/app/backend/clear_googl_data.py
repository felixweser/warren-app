import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

def clear_googl_data():
    """Clear GOOGL data from the database"""
    
    print("🔗 Connecting to database...")
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    # First, check what data we have
    cur.execute("SELECT COUNT(*) FROM companies WHERE ticker = 'GOOGL';")
    company_count = cur.fetchone()[0]
    
    if company_count == 0:
        print("❌ No GOOGL data found in database")
        cur.close()
        conn.close()
        return
    
    # Get company ID
    cur.execute("SELECT id FROM companies WHERE ticker = 'GOOGL';")
    company_id = cur.fetchone()[0]
    
    # Check statements count
    cur.execute("SELECT COUNT(*) FROM statements WHERE company_id = %s;", (company_id,))
    statements_count = cur.fetchone()[0]
    
    print(f"📊 Found GOOGL company record with {statements_count} statements")
    
    # Delete statements first (due to foreign key constraint)
    print("🗑️  Deleting GOOGL statements...")
    cur.execute("DELETE FROM statements WHERE company_id = %s;", (company_id,))
    deleted_statements = cur.rowcount
    
    # Delete company record
    print("🗑️  Deleting GOOGL company record...")
    cur.execute("DELETE FROM companies WHERE ticker = 'GOOGL';")
    deleted_companies = cur.rowcount
    
    conn.commit()
    
    print(f"✅ Successfully deleted:")
    print(f"   📋 {deleted_statements} financial statements")
    print(f"   🏢 {deleted_companies} company record")
    
    # Verify deletion
    cur.execute("SELECT COUNT(*) FROM companies;")
    remaining_companies = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM statements;")
    remaining_statements = cur.fetchone()[0]
    
    print(f"📊 Database now contains:")
    print(f"   🏢 {remaining_companies} companies")
    print(f"   📋 {remaining_statements} statements")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    clear_googl_data()