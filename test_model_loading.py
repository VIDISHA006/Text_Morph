#!/usr/bin/env python3
"""
Test model loading for debugging
"""

import os
import sys

print("Testing model loading...")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[0]}")

# Check if model directories exist
model_dirs = [
    "data/byt5-finetuned",
    "data/t5-multi-domain-finetuned", 
    "data/t5-paraphrase-finetuned"
]

for model_dir in model_dirs:
    exists = os.path.exists(model_dir)
    print(f"{model_dir}: {'✅' if exists else '❌'}")
    
    if exists:
        files = os.listdir(model_dir)
        print(f"  Files: {len(files)} found")
        required_files = ['config.json', 'model.safetensors', 'tokenizer_config.json']
        for req_file in required_files:
            file_exists = req_file in files
            print(f"    {req_file}: {'✅' if file_exists else '❌'}")

# Test PyTorch import
try:
    import torch
    print(f"\n✅ PyTorch {torch.__version__} imported successfully")
    print(f"Device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
except Exception as e:
    print(f"\n❌ PyTorch import failed: {e}")

# Test transformers import
try:
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    print("✅ Transformers imported successfully")
except Exception as e:
    print(f"❌ Transformers import failed: {e}")

# Test loading one model
try:
    print("\nTesting model loading...")
    from transformers import T5Tokenizer, T5ForConditionalGeneration
    
    model_path = "data/t5-paraphrase-finetuned"
    if os.path.exists(model_path):
        print(f"Loading tokenizer from {model_path}...")
        tokenizer = T5Tokenizer.from_pretrained(model_path)
        print("✅ Tokenizer loaded")
        
        print(f"Loading model from {model_path}...")
        model = T5ForConditionalGeneration.from_pretrained(model_path)
        print("✅ Model loaded")
        
        # Test inference
        input_text = "paraphrase: This is a test sentence."
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        with torch.no_grad():
            outputs = model.generate(inputs, max_length=50, num_beams=2, early_stopping=True)
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"✅ Test inference successful: {result}")
        
    else:
        print(f"❌ Model path {model_path} does not exist")
        
except Exception as e:
    print(f"❌ Model loading test failed: {e}")
    import traceback
    traceback.print_exc()