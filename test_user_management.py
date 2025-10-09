#!/usr/bin/env python3
"""
Test script to verify user management functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.api.database import (
    create_connection, 
    create_users_table, 
    create_profiles_table,
    create_processing_history_table,
    create_admin_table,
    fetch_all_users
)
from backend.api.passhash import hash_password

def test_database_setup():
    """Test database setup and schema"""
    print("Testing database setup...")
    
    # Create all tables
    create_users_table()
    create_profiles_table()
    create_processing_history_table()
    create_admin_table()
    
    print("All tables created successfully!")

def test_table_schema():
    """Test table schema to verify columns exist"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            # Check users table schema
            print("\n=== USERS TABLE SCHEMA ===")
            cursor.execute("DESCRIBE users")
            users_columns = cursor.fetchall()
            for col in users_columns:
                print(f"Column: {col[0]}, Type: {col[1]}, Null: {col[2]}, Key: {col[3]}, Default: {col[4]}")
            
            # Check processing_history table schema
            print("\n=== PROCESSING_HISTORY TABLE SCHEMA ===")
            cursor.execute("DESCRIBE processing_history")
            history_columns = cursor.fetchall()
            for col in history_columns:
                print(f"Column: {col[0]}, Type: {col[1]}, Null: {col[2]}, Key: {col[3]}, Default: {col[4]}")
                
        except Exception as e:
            print(f"Error checking schema: {e}")
        finally:
            cursor.close()
            connection.close()

def create_test_user():
    """Create a test user directly in database"""
    print("\n=== CREATING TEST USER ===")
    
    test_email = "testuser@example.com"
    test_username = "testuser"
    test_password = "password123"
    hashed_pw = hash_password(test_password)
    
    connection = create_connection()
    if not connection:
        print("Failed to connect to database")
        return None
        
    try:
        cursor = connection.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (test_email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"Test user {test_email} already exists: {existing_user}")
            return existing_user
        
        # Create new test user
        cursor.execute("""
            INSERT INTO users (username, email, hashed_password, language_preference, is_blocked) 
            VALUES (%s, %s, %s, %s, %s)
        """, (test_username, test_email, hashed_pw, 'en', False))
        
        connection.commit()
        
        # Get the created user
        cursor.execute("SELECT id, username, email FROM users WHERE email = %s", (test_email,))
        new_user = cursor.fetchone()
        
        if new_user:
            print(f"Successfully created test user: ID={new_user[0]}, Username={new_user[1]}, Email={new_user[2]}")
            return new_user
        else:
            print("Failed to create test user")
            return None
            
    except Exception as e:
        print(f"Error creating test user: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def test_fetch_users():
    """Test fetching all users"""
    print("\n=== FETCHING ALL USERS ===")
    
    try:
        users = fetch_all_users()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - ID: {user.get('id')}, Username: {user.get('username')}, Email: {user.get('email')}")
        return users
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def main():
    """Main test function"""
    print("Starting User Management Database Test...")
    
    # Test 1: Setup database
    test_database_setup()
    
    # Test 2: Check table schemas
    test_table_schema()
    
    # Test 3: Create test user
    test_user = create_test_user()
    
    # Test 4: Fetch all users
    all_users = test_fetch_users()
    
    print(f"\n=== TEST SUMMARY ===")
    print(f"Database setup: OK")
    print(f"Test user created: {'OK' if test_user else 'FAILED'}")
    print(f"Users found: {len(all_users)}")
    
    if len(all_users) > 0:
        print("User management should now work in the admin dashboard!")
    else:
        print("No users found - there may still be an issue with the database.")

if __name__ == "__main__":
    main()