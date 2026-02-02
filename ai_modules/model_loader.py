"""Lazy loading wrapper for AI models to save memory"""
from functools import lru_cache
import gc
import os

class AIModelLoader:
    """Singleton lazy loader for heavy AI models"""
    
    _spacy_model = None
    _sentence_transformer = None
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_spacy_model(cls):
        """Load spaCy model only when needed"""
        if cls._spacy_model is None:
            import spacy
            
            # Get model name from env or use default
            model_name = os.environ.get('SPACY_MODEL', 'en_core_web_sm')
            
            try:
                cls._spacy_model = spacy.load(model_name)
                print(f"✅ spaCy model loaded: {model_name}")
            except Exception as e:
                print(f"❌ Failed to load spaCy: {e}")
                # Fallback: try to download
                import subprocess
                subprocess.run(['python', '-m', 'spacy', 'download', model_name])
                cls._spacy_model = spacy.load(model_name)
        
        return cls._spacy_model
    
    @classmethod
    @lru_cache(maxsize=1)
    def get_sentence_transformer(cls, model_name='all-MiniLM-L6-v2'):
        """Load sentence transformer only when needed"""
        if cls._sentence_transformer is None:
            from sentence_transformers import SentenceTransformer
            
            try:
                cls._sentence_transformer = SentenceTransformer(model_name)
                print(f"✅ Sentence Transformer loaded: {model_name}")
            except Exception as e:
                print(f"❌ Failed to load Sentence Transformer: {e}")
                raise
        
        return cls._sentence_transformer
    
    @classmethod
    def cleanup_models(cls):
        """Free memory by unloading models"""
        if cls._spacy_model is not None:
            del cls._spacy_model
            cls._spacy_model = None
        
        if cls._sentence_transformer is not None:
            del cls._sentence_transformer
            cls._sentence_transformer = None
        
        gc.collect()
        print("🧹 AI models cleaned from memory")