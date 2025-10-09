#!/usr/bin/env python3
"""
Reference Models Service
Uses the trained models from data folder for comparison
"""

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferenceModelsService:
    def __init__(self):
        """Initialize trained reference models"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Model configurations
        self.models = {}
        self.tokenizers = {}
        
        # Load all available models
        self.load_models()
        
        logger.info(f"Reference models loaded: {list(self.models.keys())}")
    
    def load_models(self):
        """Load all trained reference models"""
        # Model paths relative to the project root
        model_paths = {
            'samsum': "data/byt5-finetuned",
            'multidomain': "data/t5-multi-domain-finetuned", 
            'paraphrase': "data/t5-paraphrase-finetuned"
        }
        
        for model_name, model_path in model_paths.items():
            if os.path.exists(model_path):
                try:
                    logger.info(f"Loading {model_name} reference model...")
                    
                    # Load tokenizer
                    try:
                        self.tokenizers[model_name] = T5Tokenizer.from_pretrained(model_path)
                    except:
                        self.tokenizers[model_name] = AutoTokenizer.from_pretrained(model_path)
                    
                    # Load model
                    self.models[model_name] = T5ForConditionalGeneration.from_pretrained(model_path)
                    self.models[model_name].to(self.device)
                    self.models[model_name].eval()
                    
                    logger.info(f"✅ {model_name} reference model loaded successfully!")
                except Exception as e:
                    logger.error(f"Failed to load {model_name} reference model: {e}")
            else:
                logger.warning(f"❌ {model_name} reference model not found at {model_path}")
    
    def detect_domain(self, text):
        """Automatically detect domain for multi-domain summarization"""
        text_lower = text.lower()
        
        # Domain keywords
        domain_keywords = {
            'finance': ['bank', 'money', 'investment', 'stock', 'market', 'financial', 'economy', 'trading', 'profit', 'revenue', 'budget', 'loan', 'credit', 'insurance', 'mortgage'],
            'health': ['health', 'medical', 'doctor', 'patient', 'medicine', 'treatment', 'disease', 'symptom', 'therapy', 'hospital', 'clinic', 'diagnosis', 'pharmaceutical', 'wellness'],
            'news': ['breaking', 'report', 'announcement', 'statement', 'official', 'government', 'politics', 'election', 'policy', 'minister', 'president', 'congress', 'parliament'],
            'science': ['research', 'study', 'experiment', 'scientific', 'discovery', 'technology', 'innovation', 'laboratory', 'analysis', 'data', 'methodology', 'hypothesis'],
            'technical': ['software', 'programming', 'algorithm', 'code', 'development', 'system', 'application', 'database', 'server', 'api', 'framework', 'technical', 'engineering']
        }
        
        # Score each domain
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            domain_scores[domain] = score
        
        # Return highest scoring domain or 'general' if no clear match
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain if domain_scores[best_domain] > 0 else 'general'
    
    def generate_reference_summary(self, text):
        """Generate reference summary using SAMSum trained model specifically"""
        try:
            # Always use SAMSum model for reference summaries
            model_type = 'samsum'
            
            if model_type not in self.models:
                return "SAMSum reference model not available"
            
            # Determine appropriate prefix based on text content
            if any(word in text.lower() for word in ['person a:', 'person b:', 'speaker', 'dialogue', 'conversation']):
                prefix = "summarize dialogue: "
            else:
                prefix = "summarize: "
            
            result = self._generate_text(text, model_type, prefix, max_length=100)
            
            # Ensure the result doesn't contain the word "summarize" or other artifacts
            while any(word in result.lower() for word in ['summarize', 'summary', 'dialogue']):
                result = result.replace('summarize', '').replace('summary', '').replace('dialogue', '').strip()
                if result.startswith(':'):
                    result = result[1:].strip()
            
            return result if result else "Could not generate reference summary"
                
        except Exception as e:
            logger.error(f"Error in reference summarization: {e}")
            return "Reference summary unavailable"
    
    def generate_reference_paraphrase(self, text):
        """Generate reference paraphrase using appropriate trained model"""
        try:
            # First try the paraphrase-specific model if available
            if 'paraphrase' in self.models:
                result = self._generate_text(text, 'paraphrase', "", max_length=min(len(text) * 2, 200))
            elif 'multi_domain' in self.models:
                result = self._generate_text(text, 'multi_domain', "rephrase: ", max_length=min(len(text) * 2, 200))
            elif 'samsum' in self.models:
                result = self._generate_text(text, 'samsum', "paraphrase: ", max_length=min(len(text) * 2, 200))
            else:
                return "No paraphrase reference model available"
            
            # Clean the result thoroughly
            original_words = ['paraphrase', 'rephrase', 'rewrite', 'reword']
            for word in original_words:
                result = result.replace(word, '').replace(word.capitalize(), '')
            
            # Remove colons and clean up
            result = result.replace(':', '').strip()
            
            # Ensure it's different from original and not empty
            if not result or result.lower() == text.lower():
                return "Could not generate distinct reference paraphrase"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in reference paraphrasing: {e}")
            return "Reference paraphrase unavailable"
    
    def _generate_text(self, text, model_key, prefix, max_length=128):
        """Helper method to generate text using reference models"""
        input_text = prefix + text
        tokenizer = self.tokenizers[model_key]
        model = self.models[model_key]
        
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=max_length,
                num_beams=5,
                length_penalty=1.0,
                early_stopping=True,
                no_repeat_ngram_size=3,
                do_sample=False,  # Use deterministic generation for consistency
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean the result by removing the input prefix
        if result.lower().startswith(prefix.lower()):
            result = result[len(prefix):].strip()
        
        # Remove any remaining artifacts
        result = self._clean_output(result, prefix)
        
        return result
    
    def _clean_output(self, text, original_prefix):
        """Clean generated output from artifacts"""
        # Remove common prefixes that shouldn't be in output
        prefixes_to_remove = [
            "summarize:", "paraphrase:", "rephrase:", "rewrite:", "reword:",
            "summarize general:", "summarize dialogue:", "summarize finance:", 
            "summarize health:", "summarize news:", "summarize science:", 
            "summarize technical:", original_prefix.strip()
        ]
        
        # Clean multiple times to catch nested artifacts
        for _ in range(3):  # Maximum 3 cleaning passes
            text_lower = text.lower()
            for prefix in prefixes_to_remove:
                if text_lower.startswith(prefix.lower()):
                    text = text[len(prefix):].strip()
                    break
            
            # Remove standalone task words
            task_words = ['summarize', 'paraphrase', 'rephrase', 'rewrite', 'reword', 'dialogue']
            for word in task_words:
                if text.lower().startswith(word.lower() + ' '):
                    text = text[len(word):].strip()
                elif text.lower().startswith(word.lower() + ':'):
                    text = text[len(word)+1:].strip()
        
        # Remove leading colons, spaces, or punctuation
        text = text.lstrip(':').strip()
        
        # Ensure first letter is capitalized if text exists
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Ensure proper punctuation only if text doesn't already end with punctuation
        if text and not text.endswith(('.', '!', '?', ':', ';')):
            text += '.'
        
        return text

# Global instance
reference_service = None

def get_reference_service():
    """Get or create reference service instance"""
    global reference_service
    if reference_service is None:
        reference_service = ReferenceModelsService()
    return reference_service

def generate_reference_summary(text):
    """Generate reference summary"""
    service = get_reference_service()
    return service.generate_reference_summary(text)

def generate_reference_paraphrase(text):
    """Generate reference paraphrase"""
    service = get_reference_service()
    return service.generate_reference_paraphrase(text)