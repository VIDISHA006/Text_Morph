#!/usr/bin/env python3
"""
Test admin dashboard functions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.api.database import (
    get_feedback_percentages, 
    get_best_feedbacks,
    get_user_feedback,
    get_feedback_statistics
)

def test_admin_functions():
    """Test all admin dashboard functions"""
    print("🧪 Testing Admin Dashboard Functions")
    print("=" * 40)
    
    # Test feedback percentages
    print("\n1. Testing get_feedback_percentages...")
    try:
        percentages = get_feedback_percentages()
        print(f"✅ Percentages: {percentages}")
        print(f"   Keys: {list(percentages.keys())}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test best feedbacks
    print("\n2. Testing get_best_feedbacks...")
    try:
        best = get_best_feedbacks()
        print(f"✅ Best feedbacks count: {len(best) if best else 0}")
        if best:
            for i, fb in enumerate(best[:2]):
                print(f"   {i+1}. Rating {fb['rating']}: {fb['comments'][:50]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test user feedback
    print("\n3. Testing get_user_feedback...")
    try:
        feedback = get_user_feedback()
        print(f"✅ Total feedback count: {len(feedback) if feedback else 0}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test feedback statistics
    print("\n4. Testing get_feedback_statistics...")
    try:
        stats = get_feedback_statistics()
        print(f"✅ Stats type: {type(stats)}")
        print(f"   Keys: {list(stats.keys()) if stats else 'None'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 Admin dashboard function tests completed!")

if __name__ == "__main__":
    test_admin_functions()