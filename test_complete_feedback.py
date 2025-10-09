#!/usr/bin/env python3
"""
Complete feedback system test
Tests the full flow: content generation -> save to processing_history -> feedback submission
"""

import sys
import os
import requests
import json
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.api.database import (
    add_user_feedback, 
    get_feedback_percentages, 
    get_best_feedbacks,
    get_user_feedback,
    create_connection
)

def test_complete_feedback_flow():
    """Test the complete feedback flow"""
    print("🧪 Testing Complete Feedback System Flow")
    print("=" * 50)
    
    # Step 1: Simulate content generation and processing_history creation
    print("\n1. 📝 Simulating content generation...")
    
    # First, let's create a test processing history entry
    connection = create_connection()
    if not connection:
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Insert test processing history
        test_original = "This is a test text that needs to be summarized for testing purposes."
        test_summary = "Test text for summarization testing."
        test_user_id = 2  # Use existing user ID
        
        cursor.execute("""
            INSERT INTO processing_history (user_id, original_text, processed_text, processing_type, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (test_user_id, test_original, test_summary, "summary"))
        connection.commit()
        
        processing_id = cursor.lastrowid
        print(f"✅ Created test processing history with ID: {processing_id}")
        
        # Step 2: Test feedback submission
        print("\n2. 💬 Testing feedback submission...")
        
        success = add_user_feedback(
            user_id=test_user_id,
            content_id=processing_id,
            content_type="summary",
            emoji_rating=5,
            text_feedback="Excellent summary! Very concise and accurate."
        )
        
        if success:
            print("✅ Feedback submitted successfully!")
        else:
            print("❌ Feedback submission failed!")
            return
        
        # Step 3: Test feedback retrieval
        print("\n3. 📊 Testing feedback analytics...")
        
        # Test percentages
        percentages = get_feedback_percentages()
        print(f"📈 Feedback percentages: {percentages}")
        
        # Test best feedbacks
        best_feedbacks = get_best_feedbacks()
        print(f"🏆 Best feedbacks count: {len(best_feedbacks) if best_feedbacks else 0}")
        if best_feedbacks:
            for fb in best_feedbacks[:3]:  # Show top 3
                print(f"   ⭐ {fb['rating']}/5: {fb['comments'][:50]}...")
        
        # Test user feedback retrieval
        user_feedback = get_user_feedback(user_id=test_user_id)
        print(f"👤 User {test_user_id} feedback count: {len(user_feedback) if user_feedback else 0}")
        
        print("\n🎉 All tests completed successfully!")
        
        # Clean up - remove test data
        print("\n4. 🧹 Cleaning up test data...")
        cursor.execute("DELETE FROM user_feedback WHERE content_id = %s", (processing_id,))
        cursor.execute("DELETE FROM processing_history WHERE id = %s", (processing_id,))
        connection.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        connection.close()

def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    # Test if backend is running
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI backend is running on port 8000")
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
    
    # Test if Flask server is running
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask AI server is running on port 5000")
        else:
            print(f"⚠️ Flask server responded with status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Flask server not accessible: {e}")

if __name__ == "__main__":
    test_api_endpoints()
    test_complete_feedback_flow()