#!/usr/bin/env python3
"""
Test script for feedback system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.api.database import (
    add_user_feedback, 
    get_feedback_percentages, 
    get_best_feedbacks,
    get_user_feedback
)

def test_feedback_system():
    """Test the feedback system functionality"""
    print("Testing feedback system...")
    
    # First get a valid user_id and content_id from existing data
    from backend.api.database import create_connection
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, user_id, processing_type FROM processing_history LIMIT 1")
            history_record = cursor.fetchone()
            if history_record:
                user_id = history_record['user_id']
                content_id = history_record['id']
                content_type = history_record['processing_type']
                print(f"Using user_id: {user_id}, content_id: {content_id}, content_type: {content_type}")
                
                # Test adding feedback with valid IDs
                print("\n1. Testing add_user_feedback...")
                result = add_user_feedback(
                    user_id=user_id,
                    content_id=content_id,
                    content_type=content_type,
                    emoji_rating=5,
                    text_feedback="Great summarization! Very helpful and concise."
                )
                print(f"Add feedback result: {result}")
            else:
                print("No processing history found to test with")
                return
        finally:
            cursor.close()
            connection.close()
    else:
        print("Could not connect to database")
        return
    
    # Test getting feedback percentages
    print("\n2. Testing get_feedback_percentages...")
    percentages = get_feedback_percentages()
    print(f"Feedback percentages: {percentages}")
    
    # Test getting best feedbacks
    print("\n3. Testing get_best_feedbacks...")
    best_feedbacks = get_best_feedbacks()
    print(f"Best feedbacks: {best_feedbacks}")
    
    # Test getting all user feedback
    print("\n4. Testing get_user_feedback...")
    all_feedback = get_user_feedback()
    print(f"All feedback count: {len(all_feedback) if all_feedback else 0}")
    if all_feedback:
        for fb in all_feedback[:3]:  # Show first 3
            print(f"  - Rating: {fb['rating']}, Comments: {fb['comments']}")

if __name__ == "__main__":
    test_feedback_system()