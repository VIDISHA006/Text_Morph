#!/usr/bin/env python3

from backend.api.database import create_connection, update_user_text

def check_database():
    """Check database structure and test update"""
    conn = create_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check table structure
        print("=== PROCESSING_HISTORY TABLE STRUCTURE ===")
        cursor.execute("DESCRIBE processing_history")
        columns = cursor.fetchall()
        for col in columns:
            print(f"Column: {col['Field']}, Type: {col['Type']}, Key: {col['Key']}")
        
        # Check some records
        print("\n=== SAMPLE RECORDS ===")
        cursor.execute("SELECT id, user_id, processing_type, original_text, processed_text FROM processing_history LIMIT 5")
        records = cursor.fetchall()
        for record in records:
            print(f"ID: {record['id']}, User: {record['user_id']}, Type: {record['processing_type']}")
            print(f"  Input: {record['original_text'][:50] if record['original_text'] else 'None'}...")
            print(f"  Output: {record['processed_text'][:50] if record['processed_text'] else 'None'}...")
            print()
        
        # Test update function
        print("=== TESTING UPDATE FUNCTION ===")
        if records:
            test_record = records[0]
            print(f"Testing update on record ID: {test_record['id']}, User: {test_record['user_id']}")
            
            # Try to update
            result = update_user_text(
                test_record['id'], 
                test_record['user_id'], 
                "Updated input text by admin", 
                "Updated output text by admin"
            )
            print(f"Update result: {result}")
            
            # Check if it was actually updated
            cursor.execute("SELECT original_text, processed_text FROM processing_history WHERE id = %s", (test_record['id'],))
            updated_record = cursor.fetchone()
            print(f"After update - Input: {updated_record['original_text']}")
            print(f"After update - Output: {updated_record['processed_text']}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database()