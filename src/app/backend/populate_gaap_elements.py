import os
import csv
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_CONN = os.getenv("DB_CONN")

def populate_gaap_elements():
    """Populate the gaap_elements table from the trimmed CSV file"""
    
    csv_file = '../../us_gaap_trimmed.csv'
    
    print("🔗 Connecting to database...")
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()
    
    # First, create the table if it doesn't exist
    print("📋 Creating gaap_elements table if not exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gaap_elements (
            id SERIAL PRIMARY KEY,
            element_name TEXT UNIQUE NOT NULL,
            standard_label TEXT,
            documentation TEXT,
            financial_statement TEXT
        );
    """)
    
    # Clear existing data
    print("🧹 Clearing existing data...")
    cur.execute("DELETE FROM gaap_elements;")
    
    print("📖 Reading CSV file...")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        batch_size = 1000
        batch = []
        total_inserted = 0
        
        for row in reader:
            batch.append((
                row['element_name'],
                row['standard_label'] if row['standard_label'] else None,
                row['documentation'] if row['documentation'] else None,
                row['financial_statement'] if row['financial_statement'] else None
            ))
            
            if len(batch) >= batch_size:
                # Insert batch
                cur.executemany("""
                    INSERT INTO gaap_elements (element_name, standard_label, documentation, financial_statement)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (element_name) DO UPDATE SET
                        standard_label = EXCLUDED.standard_label,
                        documentation = EXCLUDED.documentation,
                        financial_statement = EXCLUDED.financial_statement;
                """, batch)
                
                total_inserted += len(batch)
                print(f"   Inserted {total_inserted} elements...")
                
                batch = []
        
        # Insert remaining batch
        if batch:
            cur.executemany("""
                INSERT INTO gaap_elements (element_name, standard_label, documentation, financial_statement)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (element_name) DO UPDATE SET
                    standard_label = EXCLUDED.standard_label,
                    documentation = EXCLUDED.documentation,
                    financial_statement = EXCLUDED.financial_statement;
            """, batch)
            total_inserted += len(batch)
    
    conn.commit()
    
    # Get final count
    cur.execute("SELECT COUNT(*) FROM gaap_elements;")
    final_count = cur.fetchone()[0]
    
    # Show some statistics
    cur.execute("""
        SELECT financial_statement, COUNT(*) 
        FROM gaap_elements 
        WHERE financial_statement IS NOT NULL 
        GROUP BY financial_statement 
        ORDER BY COUNT(*) DESC;
    """)
    
    print(f"✅ Successfully populated gaap_elements table!")
    print(f"📊 Total elements: {final_count}")
    print(f"📋 Financial statement breakdown:")
    
    for stmt, count in cur.fetchall():
        print(f"   {stmt}: {count}")
    
    # Show sample elements
    cur.execute("""
        SELECT element_name, standard_label, financial_statement 
        FROM gaap_elements 
        WHERE standard_label IS NOT NULL 
        LIMIT 5;
    """)
    
    print(f"\n🎯 Sample elements:")
    for element, label, stmt in cur.fetchall():
        print(f"   {element}: {label} ({stmt})")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    populate_gaap_elements()