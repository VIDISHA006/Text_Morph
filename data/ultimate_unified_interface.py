#!/usr/bin/env python3
"""
Ultimate Unified Interface
Combines Summarization (SAMSum + Multi-Domain) and Paraphrasing into one platform
"""

from flask import Flask, render_template, request, jsonify
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateTextProcessor:
    def __init__(self):
        """Initialize all models - SAMSum, Multi-Domain, and Paraphrase"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Model configurations
        self.models = {}
        self.tokenizers = {}
        
        # Load all available models
        self.load_summarization_models()
        self.load_paraphrase_model()
        
        logger.info(f"Models loaded: {list(self.models.keys())}")
    
    def load_summarization_models(self):
        """Load SAMSum and Multi-Domain summarization models"""
        # Determine the correct base path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # Parent directory of data/
        
        # Load SAMSum Dialogue Model
        samsum_path = os.path.join(base_dir, "data", "byt5-finetuned")
        if os.path.exists(samsum_path):
            try:
                logger.info("Loading SAMSum dialogue model...")
                # Try T5Tokenizer first, fallback to AutoTokenizer
                try:
                    self.tokenizers['samsum'] = T5Tokenizer.from_pretrained(samsum_path)
                except:
                    self.tokenizers['samsum'] = AutoTokenizer.from_pretrained(samsum_path)
                self.models['samsum'] = T5ForConditionalGeneration.from_pretrained(samsum_path)
                self.models['samsum'].to(self.device)
                self.models['samsum'].eval()
                logger.info("✅ SAMSum model loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load SAMSum model: {e}")
        else:
            logger.warning(f"❌ SAMSum model not found at {samsum_path}")
        
        # Load Multi-Domain Model
        multidomain_path = os.path.join(base_dir, "data", "t5-multi-domain-finetuned")
        if os.path.exists(multidomain_path):
            try:
                logger.info("Loading Multi-Domain model...")
                self.tokenizers['multidomain'] = T5Tokenizer.from_pretrained(multidomain_path)
                self.models['multidomain'] = T5ForConditionalGeneration.from_pretrained(multidomain_path)
                self.models['multidomain'].to(self.device)
                self.models['multidomain'].eval()
                logger.info("✅ Multi-Domain model loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load Multi-Domain model: {e}")
        else:
            logger.warning(f"❌ Multi-Domain model not found at {multidomain_path}")
    
    def load_paraphrase_model(self):
        """Load paraphrase model"""
        # Determine the correct base path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)  # Parent directory of data/
        
        paraphrase_path = os.path.join(base_dir, "data", "t5-paraphrase-finetuned")
        if os.path.exists(paraphrase_path):
            try:
                logger.info("Loading Paraphrase model...")
                self.tokenizers['paraphrase'] = T5Tokenizer.from_pretrained(paraphrase_path)
                self.models['paraphrase'] = T5ForConditionalGeneration.from_pretrained(paraphrase_path)
                self.models['paraphrase'].to(self.device)
                self.models['paraphrase'].eval()
                logger.info("✅ Paraphrase model loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load Paraphrase model: {e}")
        else:
            logger.warning(f"❌ Paraphrase model not found at {paraphrase_path}")
    
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
    
    def summarize_text(self, text, model_type='auto'):
        """Generate summary using specified model type"""
        try:
            if model_type == 'auto':
                # Auto-detect based on content
                if any(word in text.lower() for word in ['dialogue', 'conversation', 'chat', 'said', 'replied', 'asked']):
                    model_type = 'samsum'
                else:
                    model_type = 'multidomain'
            
            if model_type == 'samsum' and 'samsum' in self.models:
                return self._generate_summary(text, 'samsum', "summarize: ")
            elif model_type == 'multidomain' and 'multidomain' in self.models:
                domain = self.detect_domain(text)
                return self._generate_summary(text, 'multidomain', f"summarize {domain}: ")
            else:
                return "Model not available"
                
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            return f"Error: {str(e)}"
    
    def paraphrase_text(self, text, num_variations=1):
        """Generate paraphrases using paraphrase model"""
        try:
            if 'paraphrase' not in self.models:
                return ["Paraphrase model not available"]
            
            input_text = f"paraphrase: {text}"
            tokenizer = self.tokenizers['paraphrase']
            model = self.models['paraphrase']
            
            inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=512,
                    num_return_sequences=1,  # Generate only one paraphrase
                    num_beams=5,  # Increased beams for better quality
                    length_penalty=1.2,  # Slightly prefer longer outputs
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.8,  # Balanced creativity
                    top_p=0.9,
                    no_repeat_ngram_size=3  # Avoid repetition
                )
            
            paraphrases = []
            for output in outputs:
                paraphrase = tokenizer.decode(output, skip_special_tokens=True)
                paraphrases.append(paraphrase)
            
            return paraphrases
            
        except Exception as e:
            logger.error(f"Error in paraphrasing: {e}")
            return [f"Error: {str(e)}"]
    
    def _generate_summary(self, text, model_key, prefix):
        """Helper method to generate summary"""
        input_text = prefix + text
        tokenizer = self.tokenizers[model_key]
        model = self.models[model_key]
        
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.device)
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=128,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
                no_repeat_ngram_size=2
            )
        
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary

# Initialize Flask app
app = Flask(__name__)
text_processor = UltimateTextProcessor()

@app.route('/')
def index():
    """Ultimate unified interface"""
    return render_template('ultimate_interface.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    """API endpoint for text summarization"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        model_type = data.get('model_type', 'auto')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        summary = text_processor.summarize_text(text, model_type)
        detected_domain = text_processor.detect_domain(text) if model_type != 'samsum' else 'dialogue'
        
        return jsonify({
            'original_text': text,
            'summary': summary,
            'model_used': model_type,
            'detected_domain': detected_domain
        })
        
    except Exception as e:
        logger.error(f"Error in summarize endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/paraphrase', methods=['POST'])
def paraphrase():
    """API endpoint for text paraphrasing"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        paraphrases = text_processor.paraphrase_text(text, 1)  # Always generate 1
        
        return jsonify({
            'original_text': text,
            'paraphrase': paraphrases[0] if paraphrases else "No paraphrase generated",
            'success': len(paraphrases) > 0
        })
        
    except Exception as e:
        logger.error(f"Error in paraphrase endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'available_models': list(text_processor.models.keys()),
        'device': str(text_processor.device)
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 ULTIMATE TEXT PROCESSING WEB INTERFACE")
    print("="*70)
    
    # Display model status
    available_models = list(text_processor.models.keys())
    if 'samsum' in available_models:
        print("✅ SAMSum Dialogue Model: Loaded")
    else:
        print("❌ SAMSum Dialogue Model: Not available")
    
    if 'multidomain' in available_models:
        print("✅ Multi-Domain Model: Loaded")
    else:
        print("❌ Multi-Domain Model: Not available")
    
    if 'paraphrase' in available_models:
        print("✅ Paraphrase Model: Loaded")
    else:
        print("❌ Paraphrase Model: Not available")
    
    print(f"✅ Device: {text_processor.device}")
    print(f"✅ URL: http://localhost:5000")
    print("="*70)
    print("Features:")
    print("  • Dialogue Summarization (SAMSum)")
    print("  • Multi-Domain Summarization (6 domains)")
    print("  • Text Paraphrasing (Multiple variations)")
    print("  • Automatic model selection")
    print("  • Unified interface")
    print("="*70)
    print("Press Ctrl+C to stop the server")
    print("="*70)
    
    app.run(host='0.0.0.0', port=5000, debug=False)