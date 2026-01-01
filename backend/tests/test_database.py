# test_db.py
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="learning_platform",
        user="postgres",
        password="Lavish_postgresql_95",  # Replace with your password
        port=5432
    )
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print("Available tables:")
    for table in tables:
        print(table[0])
        print("schema for table", table[0])
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table[0]}';
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]} ({col[1]}) - {col[2]}")

    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")