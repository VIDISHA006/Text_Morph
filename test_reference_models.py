#!/usr/bin/env python3
"""Test script for reference models"""

import requests
import json

def test_reference_models():
    """Test the reference models API"""
    
    # Test text
    test_text = "John called Mary to discuss the meeting. They decided to postpone it until next week because of scheduling conflicts."
    
    # Test paraphrasing
    print("Testing Paraphrasing...")
    paraphrase_data = {
        "text": test_text,
        "level": "balanced"
    }
    
    try:
        response = requests.post("http://localhost:8000/paraphrase", json=paraphrase_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Paraphrase API working")
            print(f"Original: {test_text}")
            print(f"Paraphrased: {result.get('paraphrased_text', 'No result')}")
            print(f"Reference: {result.get('reference_text', 'No reference')}")
        else:
            print(f"❌ Paraphrase API failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Paraphrase API error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Test summarization  
    print("Testing Summarization...")
    summary_data = {
        "text": "Person A: Hey, did you finish the project report? Person B: Almost done, just need to add the conclusions. Person A: Great, the deadline is tomorrow. Person B: Don't worry, I'll have it ready by tonight. Person A: Perfect, thanks for handling this.",
        "summary_type": "general"
    }
    
    try:
        response = requests.post("http://localhost:8000/summarize", json=summary_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Summarization API working")
            print(f"Original: {summary_data['text']}")
            print(f"Summarized: {result.get('summarized_text', 'No result')}")
            print(f"Reference: {result.get('reference_text', 'No reference')}")
        else:
            print(f"❌ Summarization API failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Summarization API error: {e}")

if __name__ == "__main__":
    test_reference_models()