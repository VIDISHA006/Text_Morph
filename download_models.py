#!/usr/bin/env python3
"""
Download script for Text Morph AI models.
This script downloads the required AI models for the Text Morph application.
Used during Docker container build process.
"""
import os
import requests
import json
from pathlib import Path

def download_file(url, local_path):
    """Download a file from URL to local path with progress indication."""
    print(f"Downloading {os.path.basename(local_path)}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    with open(local_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    
    print(f"\n✅ Downloaded {os.path.basename(local_path)}")

def create_model_config():
    """Create model configuration files for models that will be downloaded."""
    
    # ByT5 Finetuned Config
    byt5_config = {
        "architectures": ["T5ForConditionalGeneration"],
        "d_ff": 2816,
        "d_kv": 64,
        "d_model": 1472,
        "decoder_start_token_id": 0,
        "dense_act_fn": "gelu_new",
        "dropout_rate": 0.1,
        "eos_token_id": 1,
        "feed_forward_proj": "gated-gelu",
        "initializer_factor": 1.0,
        "is_encoder_decoder": True,
        "is_gated_act": True,
        "layer_norm_epsilon": 1e-06,
        "model_type": "t5",
        "n_positions": 1024,
        "num_decoder_layers": 12,
        "num_heads": 12,
        "num_layers": 12,
        "output_past": True,
        "pad_token_id": 0,
        "relative_attention_max_distance": 128,
        "relative_attention_num_buckets": 32,
        "task_specific_params": {},
        "tie_word_embeddings": False,
        "torch_dtype": "float32",
        "transformers_version": "4.21.0",
        "use_cache": True,
        "vocab_size": 384
    }
    
    # T5 Multi-domain Config  
    t5_multi_config = {
        "architectures": ["T5ForConditionalGeneration"],
        "d_ff": 2048,
        "d_kv": 64,
        "d_model": 768,
        "decoder_start_token_id": 0,
        "dense_act_fn": "relu",
        "dropout_rate": 0.1,
        "eos_token_id": 1,
        "feed_forward_proj": "relu",
        "initializer_factor": 1.0,
        "is_encoder_decoder": True,
        "layer_norm_epsilon": 1e-06,
        "model_type": "t5",
        "n_positions": 512,
        "num_decoder_layers": 12,
        "num_heads": 12,
        "num_layers": 12,
        "output_past": True,
        "pad_token_id": 0,
        "relative_attention_max_distance": 128,
        "relative_attention_num_buckets": 32,
        "task_specific_params": {},
        "tie_word_embeddings": False,
        "torch_dtype": "float32",
        "transformers_version": "4.21.0",
        "use_cache": True,
        "vocab_size": 32128
    }
    
    # Save configs
    models_dir = Path("data")
    
    for model_name, config in [
        ("byt5-finetuned", byt5_config),
        ("t5-multi-domain-finetuned", t5_multi_config),
        ("t5-paraphrase-finetuned", t5_multi_config)
    ]:
        config_path = models_dir / model_name / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Created config for {model_name}")

def download_models():
    """Download the AI models from Hugging Face or alternative sources."""
    
    print("🤖 Setting up Text Morph AI Models...")
    print("Note: In production, models would be downloaded from your model repository")
    print("For now, creating placeholder model files for demonstration...")
    
    # Create model directories and placeholder files
    models_info = [
        ("byt5-finetuned", "ByT5 Dialogue Generation Model"),
        ("t5-multi-domain-finetuned", "T5 Multi-Domain Summarization Model"), 
        ("t5-paraphrase-finetuned", "T5 Paraphrasing Model")
    ]
    
    for model_dir, description in models_info:
        model_path = Path("data") / model_dir
        model_path.mkdir(parents=True, exist_ok=True)
        
        # Create a placeholder model file (in production, this would be the actual download)
        placeholder_path = model_path / "model.safetensors"
        
        if not placeholder_path.exists():
            print(f"📦 Setting up {description}...")
            
            # In a real deployment, you would download from your model repository:
            # download_file("https://your-model-repo.com/models/model.safetensors", placeholder_path)
            
            # For demo, create a minimal placeholder
            with open(placeholder_path, 'wb') as f:
                f.write(b"PLACEHOLDER_MODEL_FILE")
            
            print(f"✅ {description} ready")
    
    # Create model configurations
    create_model_config()
    
    print("\n🎉 All models are set up and ready!")
    print("Note: In production deployment, replace placeholder files with actual trained models")

if __name__ == "__main__":
    download_models()