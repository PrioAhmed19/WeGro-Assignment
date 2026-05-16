import os
from dotenv import load_dotenv
import mysql.connector
from tabulate import tabulate

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("HOST"),
    port=int(os.getenv("PORT")),
    user=os.getenv("USER"),
    password=os.getenv("PASSWORD"),
    database=os.getenv("DB")
)

cursor = conn.cursor()

cursor.execute("""
SELECT TABLE_NAME, TABLE_TYPE
FROM information_schema.tables
WHERE table_schema = %s
ORDER BY TABLE_TYPE, TABLE_NAME
""", (os.getenv("DB"),))

tables = cursor.fetchall()

print("\nDATABASE OVERVIEW")
print("=" * 100)

for table_name, table_type in tables:

    print(f"\n{table_name} ({table_type})")
    print("-" * 100)

    cursor.execute("""
    SELECT
        COLUMN_NAME,
        DATA_TYPE,
        IS_NULLABLE,
        COLUMN_KEY
    FROM information_schema.columns
    WHERE table_schema = %s
    AND table_name = %s
    ORDER BY ORDINAL_POSITION
    """, (os.getenv("DB"), table_name))

    columns = cursor.fetchall()

    print(tabulate(
        columns,
        headers=["Column", "Data Type", "Nullable", "Key"],
        tablefmt="grid"
    ))

cursor.close()
conn.close()

print("\nConnection closed.")