import sqlite3
import os

db_path = 'data/conversations.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Delete all messages
    cursor.execute('DELETE FROM messages')
    print(f"Deleted {cursor.rowcount} messages")
    
    # Delete all conversations
    cursor.execute('DELETE FROM conversations')
    print(f"Deleted {cursor.rowcount} conversations")
    
    # Reset auto-increment counters
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="messages"')
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="conversations"')
    
    conn.commit()
    conn.close()
    
    print("Database cleared successfully!")
else:
    print(f"Database not found at {db_path}")
