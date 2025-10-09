#!/usr/bin/env python3
"""Comprehensive paraphrasing test to isolate the issue"""

import sys
import os

# Add paths
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('backend'))

def test_direct_import():
    """Test direct import and execution"""
    print("=== TESTING DIRECT BACKEND SERVICE ===")
    
    try:
        from backend.paraphrasing.service import paraphrase
        print("✅ Successfully imported backend paraphrasing service")
        
        # Test with the exact same parameters that frontend uses
        test_text = "The artificial intelligence revolution is transforming the way we work and live."
        print(f"Testing with: {test_text}")
        
        levels = ["conservative", "balanced", "creative"]
        for level in levels:
            print(f"\n--- Testing {level} level ---")
            try:
                result, params = paraphrase(
                    text=test_text,
                    level=level,
                    num_return_sequences=2,
                    max_new_tokens=80,
                    model_name="t5"
                )
                print(f"Success! Generated {len(result)} paraphrases:")
                for i, p in enumerate(result, 1):
                    same_as_orig = (p.strip().lower() == test_text.strip().lower())
                    print(f"  {i}. '{p}' (same as original: {same_as_orig})")
                
            except Exception as e:
                print(f"❌ Error in {level}: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

def test_frontend_function():
    """Test the frontend wrapper function"""
    print("\n=== TESTING FRONTEND WRAPPER FUNCTION ===")
    
    try:
        # Mock streamlit to avoid GUI dependencies
        class MockStreamlit:
            def error(self, msg): print(f"ST_ERROR: {msg}")
            def warning(self, msg): print(f"ST_WARNING: {msg}")
            def success(self, msg): print(f"ST_SUCCESS: {msg}")
        
        # Temporarily replace streamlit
        import sys
        sys.modules['streamlit'] = MockStreamlit()
        
        # Now import the frontend function
        from frontend.app import generate_improved_paraphrase
        print("✅ Successfully imported frontend function")
        
        test_text = "The artificial intelligence revolution is transforming the way we work and live."
        print(f"Testing with: {test_text}")
        
        # Test the frontend function
        result = generate_improved_paraphrase(
            text=test_text,
            level="balanced",
            model_name="t5", 
            max_new_tokens=80,
            num_options=2
        )
        
        print(f"Frontend function returned {len(result)} results:")
        for i, p in enumerate(result, 1):
            same_as_orig = (p.strip().lower() == test_text.strip().lower())
            print(f"  {i}. '{p}' (same as original: {same_as_orig})")
        
    except Exception as e:
        print(f"❌ Frontend function error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success1 = test_direct_import()
    success2 = test_frontend_function()
    
    print(f"\n=== SUMMARY ===")
    print(f"Backend service test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Frontend function test: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("🎉 All tests passed! The issue may be in Streamlit session state or UI.")
    else:
        print("🚨 Issues found in paraphrasing pipeline.")