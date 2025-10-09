#!/usr/bin/env python3

import requests
import json

def test_regenerate_endpoints():
    """Test the Flask endpoints that the admin dashboard uses"""
    
    print("Testing Flask Text Processing Endpoints")
    print("="*50)
    
    # Test summarization endpoint
    print("1. Testing Summarization...")
    try:
        response = requests.post("http://localhost:5000/summarize", 
                               json={"text": "This is a test text for summarization. It should be summarized properly.", 
                                    "model_type": "auto"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary: {data.get('summary', 'No summary found')}")
        else:
            print(f"❌ Summarization failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Summarization error: {e}")
    
    print()
    
    # Test paraphrasing endpoint  
    print("2. Testing Paraphrasing...")
    try:
        response = requests.post("http://localhost:5000/paraphrase", 
                               json={"text": "This is a test sentence for paraphrasing."})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Paraphrase: {data.get('paraphrase', 'No paraphrase found')}")
        else:
            print(f"❌ Paraphrasing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Paraphrasing error: {e}")

if __name__ == "__main__":
    test_regenerate_endpoints()