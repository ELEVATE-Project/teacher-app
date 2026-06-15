"""
Check Database Schema
=====================

Verify if the feedback_context table exists in the database.
"""

import sqlite3
import os

db_path = "data/conversations.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

print("="*60)
print("🔍 Checking Database Schema")
print("="*60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"\n📊 Tables in {db_path}:\n")
for table in tables:
    print(f"  ✓ {table[0]}")

# Check if feedback_context table exists
if ('feedback_context',) in tables:
    print("\n✅ feedback_context table EXISTS!\n")
    
    # Get schema
    cursor.execute("PRAGMA table_info(feedback_context)")
    columns = cursor.fetchall()
    
    print("📋 feedback_context schema:")
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  - {name}: {col_type}")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM feedback_context")
    count = cursor.fetchone()[0]
    print(f"\n📈 Total feedback records: {count}")
    
else:
    print("\n❌ feedback_context table DOES NOT EXIST")
    print("\n💡 The table will be created automatically on first use.")
    print("   Run: python tests/test_feedback_tool_simple.py")

# Check other tables too
print("\n" + "="*60)
print("📊 All Table Schemas:")
print("="*60)

for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        pk_marker = " (PK)" if pk else ""
        print(f"  - {name}: {col_type}{pk_marker}")

conn.close()

print("\n" + "="*60)
print("✅ Database check complete!")
print("="*60 + "\n")
