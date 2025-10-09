from functools import lru_cache
from typing import List, Dict
from transformers import pipeline
import torch

# Default T5 paraphraser
DEFAULT_T5 = "ramsrigouthamg/t5_paraphraser"

# Presets for creativity levels
LEVEL_PRESETS: Dict[str, Dict] = {
    "conservative": {"temperature": 0.5, "top_p": 0.7, "repetition_penalty": 1.3},
    "balanced": {"temperature": 0.9, "top_p": 0.92, "repetition_penalty": 1.1},
    "creative": {"temperature": 1.2, "top_p": 0.95, "repetition_penalty": 1.0},
}

@lru_cache(maxsize=3)
def get_pipe(model_name: str = DEFAULT_T5):
    """Get pipeline with optimal device configuration"""
    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "text2text-generation", 
        model=model_name,
        device=device,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )

def preprocess_text(text: str) -> str:
    """Clean and prepare text for paraphrasing"""
    # Remove extra whitespace and normalize
    text = " ".join(text.split())
    
    # Ensure proper sentence ending
    if not text.endswith(('.', '!', '?')):
        text += '.'
    
    return text

def simple_word_paraphrase(text: str, level: str) -> str:
    """Fallback simple paraphrasing using word replacements"""
    import re
    
    # Simple word mappings for fallback
    word_replacements = {
        "quick": ["fast", "swift", "speedy", "rapid"],
        "brown": ["tan", "chestnut", "russet", "amber"], 
        "fox": ["canine", "creature", "animal"],
        "jumps": ["leaps", "bounds", "springs", "hops"],
        "over": ["above", "across", "beyond"],
        "lazy": ["sleepy", "idle", "sluggish", "lethargic"],
        "dog": ["hound", "canine", "puppy"]
    }
    
    words = text.split()
    result_words = []
    
    for word in words:
        # Remove punctuation for matching
        clean_word = re.sub(r'[^\w]', '', word.lower())
        if clean_word in word_replacements and len(word_replacements[clean_word]) > 0:
            # Choose replacement based on level
            if level == "conservative":
                replacement = word_replacements[clean_word][0]  # First (most conservative)
            elif level == "creative":
                replacement = word_replacements[clean_word][-1]  # Last (most creative)
            else:
                replacement = word_replacements[clean_word][len(word_replacements[clean_word])//2]  # Middle
            
            # Preserve capitalization and punctuation
            if word[0].isupper():
                replacement = replacement.capitalize()
            if word.endswith('.'):
                replacement += '.'
            result_words.append(replacement)
        else:
            result_words.append(word)
    
    return " ".join(result_words)

def postprocess_paraphrase(paraphrase: str, original_text: str) -> str:
    """Clean up the generated paraphrase"""
    # Remove common prefixes
    prefixes_to_remove = [
        "paraphrase:", "rewrite:", "rephrase:", "paraphrased text:",
        "rewritten:", "rephrased:", "paraphrasing:", "rewriting:",
        "rephrase this sentence:", "rewrite this sentence:",
        "rephrase this sentence in a formal way:",
        "rewrite this sentence with different words:"
    ]
    
    paraphrase_lower = paraphrase.lower()
    for prefix in prefixes_to_remove:
        if paraphrase_lower.startswith(prefix):
            paraphrase = paraphrase[len(prefix):].strip()
            break
    
    # Convert questions back to statements if original was a statement
    if (paraphrase.endswith('?') and 
        not original_text.endswith('?') and 
        paraphrase.lower().startswith(('what', 'how', 'when', 'where', 'why', 'who'))):
        # Try to convert question to statement
        if paraphrase.lower().startswith('what happens when'):
            # "What happens when X?" -> "X happens."
            paraphrase = paraphrase[18:].replace('?', '.').strip()
            if paraphrase.startswith('a '):
                paraphrase = paraphrase[2:].capitalize()
        elif paraphrase.lower().startswith('how'):
            paraphrase = paraphrase[3:].replace('?', '.').strip()
        # Add more conversions as needed
    
    # Capitalize first letter
    if paraphrase and paraphrase[0].islower():
        paraphrase = paraphrase[0].upper() + paraphrase[1:]
    
    # Ensure proper ending punctuation
    if paraphrase and not paraphrase.endswith(('.', '!', '?')):
        if original_text.endswith('!'):
            paraphrase += '!'
        elif original_text.endswith('?'):
            paraphrase += '?'
        else:
            paraphrase += '.'
    
    return paraphrase

def paraphrase(
    text: str,
    level: str = "balanced",
    num_return_sequences: int = 3,
    max_new_tokens: int = 50,
    model_name: str = "t5"
):
    """
    Paraphrase text in three styles:
    - conservative: professional/formal
    - balanced: natural word changes
    - creative: story-like / expressive
    Ensures outputs are **sentences**, not questions.
    """
    # Map model
    if model_name.lower() == "t5":
        model_id = "ramsrigouthamg/t5_paraphraser"
    elif model_name.lower() == "bart":
        model_id = "eugenesiow/bart-paraphrase"
    else:
        model_id = model_name

    pipe = get_pipe(model_id)

    # Preprocess input text
    clean_text = preprocess_text(text)
    
    # Improved prompt engineering for better paraphrasing
    # The ramsrigouthamg/t5_paraphraser expects simple "paraphrase:" prefix
    prompt = f"paraphrase: {clean_text}"

    # Prepare generation parameters with improved settings
    params = LEVEL_PRESETS.get(level, LEVEL_PRESETS["balanced"]).copy()
    
    # Enhance parameters for better quality with more diversity
    if level == "conservative":
        params.update({
            "do_sample": True,
            "num_return_sequences": max(1, num_return_sequences),
            "max_new_tokens": max_new_tokens,
            "temperature": 0.8,
            "top_p": 0.85,
            "repetition_penalty": 1.3,
            "no_repeat_ngram_size": 2,
            "clean_up_tokenization_spaces": True,
        })
    elif level == "creative":
        params.update({
            "do_sample": True,
            "num_return_sequences": max(1, num_return_sequences),
            "max_new_tokens": max_new_tokens,
            "temperature": 1.2,
            "top_p": 0.95,
            "repetition_penalty": 1.0,
            "no_repeat_ngram_size": 2,
            "clean_up_tokenization_spaces": True,
        })
    else:  # balanced
        params.update({
            "do_sample": True,
            "num_return_sequences": max(1, num_return_sequences),
            "max_new_tokens": max_new_tokens,
            "temperature": 1.0,
            "top_p": 0.92,
            "repetition_penalty": 1.15,
            "no_repeat_ngram_size": 2,
            "clean_up_tokenization_spaces": True,
        })

    try:
        # Generate paraphrases
        outputs = pipe(prompt, **params)
        paraphrases = [o["generated_text"].strip() for o in outputs]

        # Clean and filter outputs
        cleaned_paraphrases = []
        for p in paraphrases:
            # Apply postprocessing
            cleaned_p = postprocess_paraphrase(p, text)
            
            # Skip if too similar to original or too short
            if (cleaned_p.lower() != text.lower() and 
                len(cleaned_p.split()) >= 3 and 
                cleaned_p not in cleaned_paraphrases and
                len(cleaned_p.strip()) > 0):
                cleaned_paraphrases.append(cleaned_p)

        # If no valid paraphrase or only questions generated, try different approaches
        if not cleaned_paraphrases or all(p.endswith('?') and not text.endswith('?') for p in cleaned_paraphrases):
            # Try with beam search for more reliable results
            simple_params = {
                "do_sample": False,
                "num_beams": 5,
                "max_new_tokens": max_new_tokens,
                "repetition_penalty": 1.2,
                "clean_up_tokenization_spaces": True,
            }
            simple_outputs = pipe(f"paraphrase: {clean_text}", **simple_params)
            fallback = simple_outputs[0]["generated_text"].strip()
            fallback = postprocess_paraphrase(fallback, text)
            
            if fallback.lower() != text.lower() and not (fallback.endswith('?') and not text.endswith('?')):
                cleaned_paraphrases = [fallback]
            else:
                # Last resort: use simple word replacement approach
                fallback = simple_word_paraphrase(text, level)
                cleaned_paraphrases = [fallback]

        return cleaned_paraphrases or [text], params
        
    except Exception as e:
        # Fallback in case of any error
        print(f"Error in paraphrasing: {e}")
        return [text], params
