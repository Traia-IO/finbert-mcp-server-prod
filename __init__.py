"""
FinBERT MCP Server Model Initialization

This module handles the initialization of the FinBERT model for sentiment analysis.
Models are loaded during import to ensure they're ready for use.
"""

import logging
import os
from typing import Optional
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finbert_mcp_init')

# Global model instance
_finbert_classifier: Optional[pipeline] = None


def initialize_finbert_model(local_files_only: bool = True):
    """
    Initialize the FinBERT sentiment analysis model with retry logic.
    
    Uses the same model as crewai tool for consistency: yiyanghkust/finbert-tone
    This model provides sentiment analysis specifically tuned for financial text.
    
    Args:
        local_files_only: If True, only use cached model files (prevents Hugging Face API calls).
                         This server is designed to run with the model baked into the container
                         image (downloaded during Docker build). Runtime should always be local-only.
    
    Returns:
        pipeline: The initialized FinBERT sentiment analysis pipeline
    """
    global _finbert_classifier
    
    if _finbert_classifier is None:
        import time
        
        model_name = "yiyanghkust/finbert-tone"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                mode_str = "local-only" if local_files_only else "download-allowed"
                logger.info(f"Initializing FinBERT sentiment analysis model (attempt {attempt + 1}/{max_retries}, mode: {mode_str})...")
                
                # Initialize the sentiment analysis pipeline
                # When local_files_only=True, we will NOT hit huggingface.co at all.
                # When local_files_only=False, transformers may download missing artifacts.
                #
                # IMPORTANT:
                # Do NOT pass local_files_only to pipeline(...). Some transformers versions forward
                # unknown kwargs into tokenizer.encode(), causing runtime errors like:
                # "PreTrainedTokenizerFast._batch_encode_plus() got an unexpected keyword argument 'local_files_only'"
                #
                # Instead, force local-only behavior at the *from_pretrained* layer, then build the
                # pipeline from the fully loaded objects.
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    local_files_only=local_files_only,
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    local_files_only=local_files_only,
                )
                _finbert_classifier = pipeline(
                    "sentiment-analysis",
                    model=model,
                    tokenizer=tokenizer,
                )
                
                logger.info(f"FinBERT model '{model_name}' initialized successfully!")
                break
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to initialize FinBERT model after {max_retries} attempts: {e}")
                    if local_files_only:
                        logger.error(
                            "FinBERT is in local-only mode, but the model isn't present in the cache. "
                            "If this is a Docker runtime container, rebuild the image so preload_model.py "
                            "downloads the model during the build stage."
                        )
                    raise RuntimeError(f"Model initialization failed after {max_retries} attempts: {e}")
    
    return _finbert_classifier


def get_finbert_classifier():
    """
    Get the initialized FinBERT classifier.
    
    Returns:
        pipeline: The FinBERT sentiment analysis pipeline
    """
    if _finbert_classifier is None:
        return initialize_finbert_model()
    return _finbert_classifier


def is_model_loaded():
    """
    Check if the FinBERT model is loaded without triggering initialization.
    
    This is a lightweight check for health checks and status endpoints.
    
    Returns:
        bool: True if the model is loaded, False otherwise
    """
    return _finbert_classifier is not None


# Initialize the model on import (for production readiness)
# Use a more lenient approach - if it fails, the model will be initialized on first use
try:
    logger.info("Starting FinBERT model initialization on import...")
    initialize_finbert_model()
    logger.info("FinBERT model initialization completed successfully!")
except Exception as e:
    logger.warning(f"Failed to initialize FinBERT model during import: {e}")
    logger.info("Model will be initialized on first use instead")
    # Don't raise here to allow server to start, model will be initialized on first use 