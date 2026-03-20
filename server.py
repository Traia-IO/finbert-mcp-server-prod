#!/usr/bin/env python3
"""
FinBERT MCP Server - FastMCP with D402 Transport Wrapper

Uses FastMCP from official MCP SDK with D402MCPTransport wrapper for HTTP 402.

Architecture:
- FastMCP for tool decorators and Context objects
- D402MCPTransport wraps the /mcp route for HTTP 402 interception
- Proper HTTP 402 status codes (not JSON-RPC wrapped)
- FinBERT model for financial sentiment analysis

Environment Variables:
- FINBERT_API_KEY: Server's internal API key (for D402 auth when clients pay)
- SERVER_ADDRESS: Payment address (IATP wallet contract)
- MCP_OPERATOR_PRIVATE_KEY: Operator signing key
- D402_TESTING_MODE: Skip facilitator (default: true)
"""

import os
import logging
import sys
from typing import Dict, Any, List
from datetime import datetime

from dotenv import load_dotenv
import uvicorn

load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('finbert_mcp')

# FastMCP from official SDK
from mcp.server.fastmcp import FastMCP, Context
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# D402 payment protocol - using Starlette middleware
from traia_iatp.d402.starlette_middleware import D402PaymentMiddleware
from traia_iatp.d402.mcp_middleware import require_payment_for_tool, get_active_api_key
from traia_iatp.d402.payment_introspection import extract_payment_configs_from_mcp
from traia_iatp.d402.types import TokenAmount, TokenAsset, EIP712Domain

# Local imports - this will trigger model initialization
from __init__ import get_finbert_classifier, is_model_loaded, logger as init_logger

# Configuration
STAGE = os.getenv("STAGE", "MAINNET").upper()
PORT = int(os.getenv("PORT", "8080"))
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
if not SERVER_ADDRESS:
    raise ValueError("SERVER_ADDRESS required for payment protocol")

# FinBERT API Key (this is the "API key" for D402)
# Server's internal API key (for paid requests when clients pay via D402)
API_KEY = os.getenv("FINBERT_API_KEY")
if not API_KEY:
    logger.warning(f"⚠️  FINBERT_API_KEY not set - payment required for all requests")

logger.info("="*80)
logger.info(f"FinBERT MCP Server (FastMCP + D402 Wrapper)")
logger.info(f"Model: yiyanghkust/finbert-tone")
logger.info(f"Payment: {SERVER_ADDRESS}")
logger.info(f"API Key: {'✅' if API_KEY else '❌ Payment required'}")
logger.info("="*80)

# Create FastMCP server
mcp = FastMCP("FinBERT MCP Server", host="0.0.0.0")

logger.info(f"✅ FastMCP server created")


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================
# All tools use FinBERT model for financial sentiment analysis
# Model is loaded in __init__.py and accessed via get_finbert_classifier()

# D402 Payment Middleware
# The HTTP 402 payment protocol middleware is already configured in the server initialization.
# It's imported from traia_iatp.d402.mcp_middleware and auto-detects configuration from:
# - PAYMENT_ADDRESS or EVM_ADDRESS: Where to receive payments
# - EVM_NETWORK: Blockchain network (default: base-sepolia)
# - DEFAULT_PRICE_USD: Price per request (default: $0.001)
#
# All payment verification logic is handled by the traia_iatp.d402 module.
# No custom implementation needed!


# API Endpoint Tool Implementations


@mcp.tool()
@require_payment_for_tool(
    price=TokenAmount(
        amount="10",  # 1e-05 tokens
        asset=TokenAsset(
            address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            decimals=6,
            network="arbitrum_one",
            eip712=EIP712Domain(
                name="IATPWallet",
                version="1"
            )
        )
    ),
    description="Analyze sentiment of financial text using FinBERT"
)
async def finbert_sentiment_analysis(
        context: Context,
        text: str
) -> Dict[str, Any]:
    """
    Analyze sentiment of financial text using the FinBERT model.

    Analyzes sentiment of financial text using FinBERT model specifically trained
    on financial data for superior accuracy in financial sentiment analysis.
    
    This tool conforms to the crewai tool specification for output format.

    Args:
        context: MCP context (injected automatically)
        text: The financial text to analyze for sentiment

    Returns:
        Dictionary with sentiment analysis results: {"sentiment": label, "confidence": score}
        On error: {"error": error_message}
    """
    # Payment already verified by @require_payment_for_tool decorator
    # Get API key using helper (handles request.state fallback)
    api_key = get_active_api_key(context)

    try:
        # Validate input
        if not text or not text.strip():
            return {"error": "Text input is required and cannot be empty"}

        # Truncate text if too long (BERT has token limits)
        if len(text) > 512:
            text = text[:512]
            logger.warning("Text truncated to 512 characters for processing")

        # Get the pre-initialized model
        classifier = get_finbert_classifier()

        # Perform sentiment analysis
        results = classifier(text)

        # Extract the result - transformers pipeline returns a list with one result for single input
        if isinstance(results, list) and len(results) > 0:
            result = results[0]
        else:
            result = results

        # Extract sentiment and confidence (matching crewai tool format)
        sentiment = result['label']
        confidence = round(result['score'], 2)  # Round to 2 decimal places like crewai tool

        logger.info(f"Analyzed sentiment for text: '{text[:50]}...' -> {sentiment} ({confidence})")

        # Return format matching crewai tool specification
        return {
            "sentiment": sentiment,
            "confidence": confidence
        }

    except Exception as e:
        logger.error(f"Error performing sentiment analysis: {e}")
        return {"error": f"Error performing sentiment analysis: {str(e)}"}


# Tone analysis tool removed - heavy model not practical for production

# ESG analysis tool removed - heavy model not practical for production

@mcp.tool()
@require_payment_for_tool(
    price=TokenAmount(
        amount="20",  # 2e-05 tokens (higher for batch)
        asset=TokenAsset(
            address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            decimals=6,
            network="arbitrum_one",
            eip712=EIP712Domain(
                name="IATPWallet",
                version="1"
            )
        )
    ),
    description="Batch sentiment analysis of multiple financial texts"
)
async def analyze_financial_text_batch(
        context: Context,
        texts: List[str]
) -> Dict[str, Any]:
    """
    Analyze multiple financial texts in batch for sentiment analysis.

    Performs batch sentiment analysis of multiple financial texts using the FinBERT model.
    Each result follows the same format as the single text analysis tool.

    Args:
        context: MCP context (injected automatically)
        texts: List of financial texts to analyze (max 50 texts)

    Returns:
        Dictionary with batch analysis results: {"results": [{"sentiment": label, "confidence": score}, ...]}
        On error: {"error": error_message}
    """
    # Payment already verified by @require_payment_for_tool decorator
    # Get API key using helper (handles request.state fallback)
    api_key = get_active_api_key(context)

    try:
        # Validate input
        if not texts or not isinstance(texts, list):
            return {"error": "Texts input must be a non-empty list"}

        if len(texts) > 50:
            return {"error": "Batch size limited to 50 texts maximum"}

        # Get the pre-initialized model
        classifier = get_finbert_classifier()

        # Process each text
        results = []
        for i, text in enumerate(texts):
            try:
                # Truncate text if too long
                processed_text = text[:512] if len(text) > 512 else text

                # Perform analysis
                analysis_results = classifier(processed_text)

                # Extract the result
                if isinstance(analysis_results, list) and len(analysis_results) > 0:
                    result = analysis_results[0]
                else:
                    result = analysis_results

                # Format result to match single text tool output
                results.append({
                    "sentiment": result['label'],
                    "confidence": round(result['score'], 2)
                })

            except Exception as e:
                results.append({
                    "error": f"Error analyzing text {i}: {str(e)}"
                })

        logger.info(f"Completed batch sentiment analysis for {len(texts)} texts")

        return {
            "results": results,
            "total_texts": len(texts)
        }

    except Exception as e:
        logger.error(f"Error performing batch analysis: {e}")
        return {"error": f"Error performing batch analysis: {str(e)}"}


@mcp.tool()
@require_payment_for_tool(
    price=TokenAmount(
        amount="5",  # 5e-06 tokens (lower for info)
        asset=TokenAsset(
            address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            decimals=6,
            network="arbitrum_one",
            eip712=EIP712Domain(
                name="IATPWallet",
                version="1"
            )
        )
    ),
    description="Get FinBERT model information and status"
)
async def get_finbert_model_info(
        context: Context
) -> Dict[str, Any]:
    """
    Get information about the FinBERT sentiment model and its current status.

    Args:
        context: MCP context (injected automatically)

    Returns:
        Dictionary containing model information and loading status
    """
    # Payment already verified by @require_payment_for_tool decorator
    # Get API key using helper (handles request.state fallback)
    api_key = get_active_api_key(context)

    try:
        # Check if model is loaded without triggering initialization
        model_ready = is_model_loaded()
        
        return {
            "status": "ready" if model_ready else "not_ready",
            "service_name": "FinBERT MCP Server",
            "model": {
                "name": "yiyanghkust/finbert-tone",
                "description": "FinBERT model for financial sentiment analysis - compatible with crewai tools",
                "labels": ["positive", "negative", "neutral"],
                "loaded": model_ready,
                "use_cases": ["Financial news sentiment", "Corporate communication analysis",
                              "Market sentiment tracking"]
            },
            "supported_operations": [
                "finbert_sentiment_analysis",
                "analyze_financial_text_batch",
                "get_finbert_model_info"
            ],
            "limitations": {
                "max_text_length": 512,
                "max_batch_size": 50,
                "supported_languages": ["English"]
            },
            "output_format": {
                "single_text": {"sentiment": "string", "confidence": "number"},
                "batch_text": {"results": "array", "total_texts": "number"}
            },
            "documentation": {
                "original_paper": "https://arxiv.org/abs/1908.10063",
                "huggingface": "https://huggingface.co/yiyanghkust/finbert-tone",
                "crewai_compatible": True
            }
        }

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {"error": f"Error getting model info: {str(e)}"}


def create_app_with_middleware():
    """
    Create Starlette app with d402 payment middleware.
    
    Strategy:
    1. Get FastMCP's Starlette app via streamable_http_app()
    2. Extract payment configs from @require_payment_for_tool decorators
    3. Add Starlette middleware with extracted configs
    4. Single source of truth - no duplication!
    """
    logger.info("🔧 Creating FastMCP app with middleware...")
    
    # Get FastMCP's Starlette app
    app = mcp.streamable_http_app()
    logger.info(f"✅ Got FastMCP Starlette app")
    
    # Extract payment configs from decorators (single source of truth!)
    tool_payment_configs = extract_payment_configs_from_mcp(mcp, SERVER_ADDRESS)
    logger.info(f"📊 Extracted {len(tool_payment_configs)} payment configs from @require_payment_for_tool decorators")
    
    # D402 Configuration
    facilitator_url = os.getenv("FACILITATOR_URL") or os.getenv("D402_FACILITATOR_URL")
    operator_key = os.getenv("MCP_OPERATOR_PRIVATE_KEY")
    network = os.getenv("NETWORK", "sepolia")
    testing_mode = os.getenv("D402_TESTING_MODE", "false").lower() == "true"
    
    # Log D402 configuration with prominent facilitator info
    logger.info("="*60)
    logger.info("D402 Payment Protocol Configuration:")
    logger.info(f"  Server Address: {SERVER_ADDRESS}")
    logger.info(f"  Network: {network}")
    logger.info(f"  Operator Key: {'✅ Set' if operator_key else '❌ Not set'}")
    logger.info(f"  Testing Mode: {'⚠️  ENABLED (bypasses facilitator)' if testing_mode else '✅ DISABLED (uses facilitator)'}")
    logger.info(f"  Internal API Key (FINBERT_API_KEY): {'✅ Set' if API_KEY else '❌ Not set'}")
    logger.info("="*60)
    
    # Require a facilitator URL in production mode for proper verification.
    if not facilitator_url and not testing_mode:
        logger.error("❌ FACILITATOR_URL required when testing_mode is disabled!")
        raise ValueError("Set FACILITATOR_URL or enable D402_TESTING_MODE=true")
    
    if facilitator_url:
        logger.info(f"🌐 FACILITATOR: {facilitator_url}")
        if "localhost" in facilitator_url or "127.0.0.1" in facilitator_url or "host.docker.internal" in facilitator_url:
            logger.info(f"   📍 Using LOCAL facilitator for development")
        else:
            logger.info(f"   🌍 Using REMOTE facilitator for production")
    else:
        logger.warning("⚠️  D402 Testing Mode - Facilitator bypassed")
    logger.info("="*60)
    
    # Add CORS middleware first (processes before other middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["mcp-session-id"],  # Expose custom headers to browser
    )
    logger.info("✅ Added CORS middleware (allow all origins, expose mcp-session-id)")
    
    # Add D402 payment middleware with extracted configs
    app.add_middleware(
        D402PaymentMiddleware,
        tool_payment_configs=tool_payment_configs,
        server_address=SERVER_ADDRESS,
        requires_auth=True,  # Extracts API keys + checks payment
        internal_api_key=API_KEY,  # Server's internal key (for Mode 2: paid access)
        testing_mode=testing_mode,
        facilitator_url=facilitator_url,
        facilitator_api_key=os.getenv("D402_FACILITATOR_API_KEY"),
        server_name="finbert-mcp-server"  # MCP server ID for tracking
    )
    logger.info("✅ Added D402PaymentMiddleware")
    logger.info("   - Auth extraction: Enabled")
    logger.info("   - Dual mode: API key OR payment")
    
    # Add health check endpoint (bypasses middleware)
    @app.route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint for container orchestration."""
        # Check if FinBERT model is loaded
        model_ready = is_model_loaded()
        
        return JSONResponse(
            content={
                "status": "healthy" if model_ready else "degraded",
                "service": "finbert-mcp-server",
                "timestamp": datetime.now().isoformat(),
                "model_ready": model_ready
            }
        )
    logger.info("✅ Added /health endpoint")
    
    return app


if __name__ == "__main__":
    logger.info("="*80)
    logger.info("Starting FinBERT MCP Server with D402 Payment Protocol")
    logger.info("="*80)
    
    # Create app with middleware
    app = create_app_with_middleware()
    
    # Run the server
    logger.info(f"🚀 Starting server on 0.0.0.0:{PORT}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    ) 