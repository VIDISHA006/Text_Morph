#!/usr/bin/env python3
"""
Translation Service
Provides translation capabilities for summaries and paraphrases
"""

from googletrans import Translator
import logging
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        """Initialize translation service"""
        self.translator = Translator()
        
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return {
            'af': 'Afrikaans',
            'sq': 'Albanian', 
            'am': 'Amharic',
            'ar': 'Arabic',
            'hy': 'Armenian',
            'az': 'Azerbaijani',
            'eu': 'Basque',
            'be': 'Belarusian',
            'bn': 'Bengali',
            'bs': 'Bosnian',
            'bg': 'Bulgarian',
            'ca': 'Catalan',
            'ceb': 'Cebuano',
            'ny': 'Chichewa',
            'zh': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'co': 'Corsican',
            'hr': 'Croatian',
            'cs': 'Czech',
            'da': 'Danish',
            'nl': 'Dutch',
            'en': 'English',
            'eo': 'Esperanto',
            'et': 'Estonian',
            'tl': 'Filipino',
            'fi': 'Finnish',
            'fr': 'French',
            'fy': 'Frisian',
            'gl': 'Galician',
            'ka': 'Georgian',
            'de': 'German',
            'el': 'Greek',
            'gu': 'Gujarati',
            'ht': 'Haitian Creole',
            'ha': 'Hausa',
            'haw': 'Hawaiian',
            'iw': 'Hebrew',
            'hi': 'Hindi',
            'hmn': 'Hmong',
            'hu': 'Hungarian',
            'is': 'Icelandic',
            'ig': 'Igbo',
            'id': 'Indonesian',
            'ga': 'Irish',
            'it': 'Italian',
            'ja': 'Japanese',
            'jw': 'Javanese',
            'kn': 'Kannada',
            'kk': 'Kazakh',
            'km': 'Khmer',
            'ko': 'Korean',
            'ku': 'Kurdish (Kurmanji)',
            'ky': 'Kyrgyz',
            'lo': 'Lao',
            'la': 'Latin',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'lb': 'Luxembourgish',
            'mk': 'Macedonian',
            'mg': 'Malagasy',
            'ms': 'Malay',
            'ml': 'Malayalam',
            'mt': 'Maltese',
            'mi': 'Maori',
            'mr': 'Marathi',
            'mn': 'Mongolian',
            'my': 'Myanmar (Burmese)',
            'ne': 'Nepali',
            'no': 'Norwegian',
            'or': 'Odia',
            'ps': 'Pashto',
            'fa': 'Persian',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'pa': 'Punjabi',
            'ro': 'Romanian', 
            'ru': 'Russian',
            'sm': 'Samoan',
            'gd': 'Scots Gaelic',
            'sr': 'Serbian',
            'st': 'Sesotho',
            'sn': 'Shona',
            'sd': 'Sindhi',
            'si': 'Sinhala',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'so': 'Somali',
            'es': 'Spanish',
            'su': 'Sundanese',
            'sw': 'Swahili',
            'sv': 'Swedish',
            'tg': 'Tajik',
            'ta': 'Tamil',
            'te': 'Telugu',
            'th': 'Thai',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'ur': 'Urdu',
            'ug': 'Uyghur',
            'uz': 'Uzbek',
            'vi': 'Vietnamese',
            'cy': 'Welsh',
            'xh': 'Xhosa',
            'yi': 'Yiddish',
            'yo': 'Yoruba',
            'zu': 'Zulu'
        }
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of input text"""
        try:
            detection = self.translator.detect(text)
            return detection.lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return None
    
    def translate_text(self, text: str, target_language: str, source_language: str = 'auto') -> Dict[str, str]:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_language: Source language code ('auto' for auto-detection)
            
        Returns:
            Dict with translation result and metadata
        """
        try:
            if not text or not text.strip():
                return {
                    'translated_text': '',
                    'source_language': 'unknown',
                    'target_language': target_language,
                    'success': False,
                    'error': 'Empty text provided'
                }
            
            # Skip translation if target is same as source
            if source_language != 'auto' and source_language == target_language:
                return {
                    'translated_text': text,
                    'source_language': source_language,
                    'target_language': target_language,
                    'success': True,
                    'error': None
                }
            
            # Perform translation
            result = self.translator.translate(
                text,
                dest=target_language,
                src=source_language
            )
            
            return {
                'translated_text': result.text,
                'source_language': result.src,
                'target_language': target_language,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                'translated_text': text,  # Return original on failure
                'source_language': 'unknown',
                'target_language': target_language,
                'success': False,
                'error': str(e)
            }
    
    def translate_summary(self, summary_text: str, target_language: str) -> Dict[str, str]:
        """Translate summary text with summary-specific handling"""
        return self.translate_text(summary_text, target_language)
    
    def translate_paraphrase(self, paraphrase_text: str, target_language: str) -> Dict[str, str]:
        """Translate paraphrase text with paraphrase-specific handling"""
        return self.translate_text(paraphrase_text, target_language)
    
    def batch_translate(self, texts: List[str], target_language: str) -> List[Dict[str, str]]:
        """Translate multiple texts at once"""
        results = []
        for text in texts:
            result = self.translate_text(text, target_language)
            results.append(result)
        return results
    
    def get_popular_languages(self) -> Dict[str, str]:
        """Get most commonly used languages for quick access"""
        return {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese (Simplified)',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'tr': 'Turkish',
            'th': 'Thai'
        }

# Global instance
translation_service = None

def get_translation_service():
    """Get or create translation service instance"""
    global translation_service
    if translation_service is None:
        translation_service = TranslationService()
    return translation_service

def translate_text(text: str, target_language: str, source_language: str = 'auto') -> Dict[str, str]:
    """Translate text using the translation service"""
    service = get_translation_service()
    return service.translate_text(text, target_language, source_language)

def get_supported_languages() -> Dict[str, str]:
    """Get supported languages"""
    service = get_translation_service()
    return service.get_supported_languages()

def get_popular_languages() -> Dict[str, str]:
    """Get popular languages"""
    service = get_translation_service()
    return service.get_popular_languages()

def detect_language(text: str) -> Optional[str]:
    """Detect language of text"""
    service = get_translation_service()
    return service.detect_language(text)