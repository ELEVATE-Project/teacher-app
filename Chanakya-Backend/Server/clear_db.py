import os
import psycopg2

dsn = os.getenv("DB_URL") or "postgresql://teacher_user:securepass123@localhost:5432/Shikshalokam"

print("="*60)
print("🧹 Clearing PostgreSQL Tables")
print("="*60)

try:
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    
    # Delete all feedback
    cursor.execute('DELETE FROM teaching_feedback')
    print(f"✓ Deleted {cursor.rowcount} feedback records from teaching_feedback")

    # Truncate messages and feedback context
    cursor.execute('TRUNCATE TABLE messages CASCADE')
    print("✓ Truncated messages table")

    cursor.execute('TRUNCATE TABLE conversations CASCADE')
    print("✓ Truncated conversations table")
    
    cursor.execute('TRUNCATE TABLE feedback_context CASCADE')
    print("✓ Truncated feedback_context table")
    
    conn.commit()
    conn.close()
    
    print("\n✅ PostgreSQL Database cleared successfully!")
except Exception as e:
    print(f"❌ Error clearing PostgreSQL database: {e}")
