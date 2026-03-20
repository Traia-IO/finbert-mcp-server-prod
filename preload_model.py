#!/usr/bin/env python3
"""
Pre-load FinBERT model during Docker build with retry logic.
"""

import sys
import time
import os

# Add app directory to Python path
sys.path.insert(0, '/app')

def download_with_retry():
    """Download FinBERT model with retry logic for rate limiting."""
    max_retries = 5
    model_name = "yiyanghkust/finbert-tone"
    
    for attempt in range(max_retries):
        try:
            print(f'Attempt {attempt + 1}/{max_retries}: Pre-loading FinBERT model during Docker build...')

            # IMPORTANT:
            # We explicitly download tokenizer + model weights here to ensure the cache is complete.
            # Relying on pipeline() alone can sometimes leave out artifacts that later loads expect.
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

            print("Downloading tokenizer...")
            AutoTokenizer.from_pretrained(model_name)

            print("Downloading model weights...")
            AutoModelForSequenceClassification.from_pretrained(model_name)

            print("Creating sentiment-analysis pipeline (verifies artifacts are usable)...")
            tok = AutoTokenizer.from_pretrained(model_name)
            mdl = AutoModelForSequenceClassification.from_pretrained(model_name)
            pipeline("sentiment-analysis", model=mdl, tokenizer=tok)

            # CRITICAL:
            # Prove the container can run in offline/local-only mode by doing a second load
            # after forcing offline. If this fails, your built image would fail at runtime.
            print("Verifying offline/local-only load...")
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            tok_offline = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            mdl_offline = AutoModelForSequenceClassification.from_pretrained(model_name, local_files_only=True)
            clf_offline = pipeline("sentiment-analysis", model=mdl_offline, tokenizer=tok_offline)

            # End-to-end verification: run a real inference in offline mode.
            # This matches the deployed server behavior (local-only, no network).
            print("Running offline inference sanity check...")
            sample_text = "Apple reported strong earnings and raised guidance."
            out = clf_offline(sample_text)
            if not isinstance(out, list) or not out or "label" not in out[0] or "score" not in out[0]:
                raise RuntimeError(f"Offline inference returned unexpected output: {out!r}")
            print(f"Offline inference OK: {out[0]}")
            
            print('FinBERT model pre-loaded successfully!')
            return
            
        except Exception as e:
            print(f'Attempt {attempt + 1} failed: {e}')
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f'Waiting {wait_time} seconds before retry...')
                time.sleep(wait_time)
            else:
                print('All attempts failed. Model will be downloaded at runtime.')
                raise

if __name__ == "__main__":
    download_with_retry()
