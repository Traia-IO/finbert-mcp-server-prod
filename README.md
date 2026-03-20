# FinBERT MCP Server

This is a lightweight MCP (Model Context Protocol) server that provides access to the FinBERT model for financial sentiment analysis. It enables AI agents and LLMs to analyze financial text using the specialized BERT model fine-tuned on financial data, optimized for production use.

## Features

- 🔧 **MCP Protocol**: Built on the Model Context Protocol for seamless AI integration
- 🤖 **Lightweight FinBERT Model**: Focuses on sentiment analysis for optimal performance
- 🚀 **Lazy Loading**: Model is loaded on-demand for efficient memory usage
- 📊 **Batch Processing**: Analyze multiple texts efficiently with batch sentiment operations
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- ⚡ **Async Operations**: Built with FastMCP for efficient async handling
- 🎯 **Production Ready**: Optimized for production environments with minimal resource usage

## Model Information

This server provides access to the lightweight FinBERT model:

- **ProsusAI/finbert**: Original FinBERT model for financial sentiment analysis - optimized for production use

## Available Tools

This lightweight server provides the following tools:

### 1. `finbert_sentiment_analysis`
Analyze sentiment of financial text using the FinBERT model.

**Parameters:**
- `text` (string): The financial text to analyze for sentiment

**Returns:**
- `sentiment`: Predicted sentiment (positive, negative, neutral)
- `confidence`: Confidence score (0-1)
- `all_scores`: Array of all sentiment predictions with scores
- `model_used`: Model name used for analysis
- `timestamp`: Analysis timestamp

### 2. `analyze_financial_text_batch`
Analyze multiple financial texts in batch for sentiment analysis efficiency.

**Parameters:**
- `texts` (array): List of financial texts to analyze (max 50)
- `analysis_type` (string): Type of analysis (only "sentiment" supported)

**Returns:**
- `results`: Array of sentiment analysis results for each text
- `analysis_type`: Type of analysis performed ("sentiment")
- `model_used`: Model name used for analysis
- `total_texts`: Number of texts processed

### 3. `get_finbert_model_info`
Get information about the FinBERT models and their current status.

**Returns:**
- `models`: Information about available models
- `supported_operations`: List of available tools
- `limitations`: Model limitations (text length, batch size)
- `documentation`: Links to relevant documentation

## Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```bash
   git clone https://github.com/Traia-IO/finbert-mcp-server.git
   cd finbert-mcp-server
   ```

2. Run with Docker:
   ```bash
   ./run_local_docker.sh
   ```

### Using Docker Compose

1. Create a `.env` file with your configuration:
   ```env
   PORT=8000
   LOG_LEVEL=INFO
   ```

2. Start the server:
   ```bash
   docker-compose up
   ```

### Manual Installation

1. Install dependencies using `uv`:
   ```bash
   uv pip install -e .
   ```

2. Run the server:
   ```bash
   uv run python -m server
   ```

## Usage

### Health Check

Test if the server is running:
```bash
python mcp_health_check.py
```

### Using with CrewAI

```python
from traia_iatp.mcp.traia_mcp_adapter import create_mcp_adapter

# Connect to the MCP server
with create_mcp_adapter(
    url="http://localhost:8000/mcp/"
) as tools:
    # Use the tools
    for tool in tools:
        print(f"Available tool: {tool.name}")
        
    # Example: Analyze sentiment of financial text
    result = await tool.finbert_sentiment_analysis(
        text="The company reported strong quarterly earnings, exceeding expectations."
    )
    print(f"Sentiment: {result['sentiment']}, Confidence: {result['confidence']}")
    
    # Example: Batch sentiment analysis
    texts = [
        "Revenue growth exceeded forecasts this quarter.",
        "The company faces regulatory challenges ahead.",
        "Investment in new technology platforms shows promise."
    ]
    result = await tool.analyze_financial_text_batch(
        texts=texts,
        analysis_type="sentiment"
    )
    print(f"Batch sentiment analysis completed for {result['total_texts']} texts")
    
    # Example: Get model information
    result = await tool.get_finbert_model_info()
    print(f"Available models: {list(result['models'].keys())}")
```

## Example Responses

### Sentiment Analysis
```json
{
  "status": "success",
  "sentiment": "positive",
  "confidence": 0.8945,
  "all_scores": [
    {"label": "positive", "score": 0.8945},
    {"label": "neutral", "score": 0.0892},
    {"label": "negative", "score": 0.0163}
  ],
  "text_length": 67,
  "model_used": "ProsusAI/finbert",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Batch Analysis
```json
{
  "status": "success",
  "analysis_type": "sentiment",
  "model_used": "ProsusAI/finbert",
  "total_texts": 3,
  "results": [
    {
      "index": 0,
      "text": "Revenue growth exceeded forecasts this quarter.",
      "prediction": "positive",
      "confidence": 0.9234,
      "all_scores": [...]
    },
    // ... more results
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Development

### Testing the Server

1. Start the server locally
2. Run the health check: `python mcp_health_check.py`
3. Test individual tools using the CrewAI adapter

### Model Loading

Models are loaded lazily on first use and cached for subsequent requests. The server starts a background thread to pre-load models after startup for better performance.

### Adding New Tools

To add new tools, edit `server.py` and:

1. Create new model initialization functions if needed
2. Add `@mcp.tool()` decorated functions
3. Update this README with the new tools
4. Update `deployment_params.json` with the tool names in the capabilities array

## Deployment

### Deployment Configuration

The `deployment_params.json` file contains the deployment configuration for this MCP server:

```json
{
  "github_url": "https://github.com/Traia-IO/finbert-mcp-server",
  "mcp_server": {
    "name": "finbert-mcp",
    "description": "Lightweight pre-trained BERT-based model fine‑tuned on financial text for sentiment analysis (positive/negative/neutral), optimized for production use.",
    "server_type": "streamable-http",
    "requires_api_key": false,
    "capabilities": [
      "finbert_sentiment_analysis",
      "analyze_financial_text_batch",
      "get_finbert_model_info"
    ]
  },
  "deployment_method": "cloud_run",
  "gcp_project_id": "traia-mcp-servers",
  "gcp_region": "us-central1",
  "tags": ["finbert", "financial", "sentiment", "analysis", "bert", "nlp", "ai", "text-processing", "lightweight", "production-ready"],
  "ref": "main"
}
```

**Important**: Always update the `capabilities` array when you add or remove tools!

### Google Cloud Run

This server is designed to be deployed on Google Cloud Run. The deployment will:

1. Build a container from the Dockerfile
2. Deploy to Cloud Run with the specified configuration
3. Expose the `/mcp` endpoint for client connections

## Environment Variables

- `PORT`: Server port (default: 8000)
- `STAGE`: Environment stage (default: MAINNET, options: MAINNET, TESTNET)
- `LOG_LEVEL`: Logging level (default: INFO)

## Model Specifications

### Text Limitations
- **Maximum text length**: 512 characters (texts are automatically truncated)
- **Batch size limit**: 50 texts per batch request
- **Supported languages**: English only

### Performance
- Models are loaded on-demand (lazy loading)
- Background pre-loading for better performance
- Cached models for subsequent requests
- Efficient batch processing

## Troubleshooting

1. **Server not starting**: Check Docker logs with `docker logs <container-id>`
2. **Connection errors**: Ensure the server is running on the expected port
3. **Tool errors**: Check the server logs for detailed error messages
4. **Model loading issues**: Ensure sufficient memory and disk space for model downloads
5. **CUDA errors**: GPU support is optional; models will run on CPU if CUDA is unavailable

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement new tools or improvements
4. Update the README and deployment_params.json
5. Submit a pull request

## License

[MIT License](LICENSE)