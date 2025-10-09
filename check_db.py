#!/usr/bin/env python3
"""
Check database state
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.api.database import create_connection

def check_database_state():
    """Check database tables and content"""
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            # Check users
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            print(f"Users: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, username FROM users LIMIT 3")
                users = cursor.fetchall()
                print("Sample users:")
                for user in users:
                    print(f"  ID: {user['id']}, Username: {user['username']}")
            
            # Check processing_history
            cursor.execute("SELECT COUNT(*) as count FROM processing_history")
            history_count = cursor.fetchone()['count']
            print(f"Processing History: {history_count}")
            
            if history_count > 0:
                cursor.execute("SELECT id, user_id, processing_type FROM processing_history LIMIT 3")
                history = cursor.fetchall()
                print("Sample processing history:")
                for record in history:
                    print(f"  ID: {record['id']}, User: {record['user_id']}, Type: {record['processing_type']}")
            
            # Check user_feedback
            cursor.execute("SELECT COUNT(*) as count FROM user_feedback")
            feedback_count = cursor.fetchone()['count']
            print(f"User Feedback: {feedback_count}")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    check_database_state()