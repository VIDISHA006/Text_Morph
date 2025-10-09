#!/usr/bin/env python3
"""
Lightweight model setup for Railway deployment.
"""
import os
import json
from pathlib import Path

def download_models():
    """Setup lightweight AI models for Railway deployment."""
    
    print("🤖 Text Morph AI - Railway Deployment Mode")
    print("📦 Using lightweight Hugging Face models")
    
    # Create basic model structure
    models_dir = Path("data")
    models_dir.mkdir(exist_ok=True)
    
    # Create model mapping file for lightweight models
    model_mapping = {
        "summarization": "sshleifer/distilbart-cnn-12-6",
        "paraphrasing": "ramsrigouthamg/t5_paraphraser", 
        "sentiment": "cardiffnlp/twitter-roberta-base-sentiment-latest"
    }
    
    with open(models_dir / "model_mapping.json", 'w') as f:
        json.dump(model_mapping, f, indent=2)
    
    print("\n✅ Lightweight model configuration complete!")
    print("🚀 Models will be loaded from Hugging Face on demand")
    print("💡 This keeps Docker image size minimal for Railway")

if __name__ == "__main__":
    download_models()