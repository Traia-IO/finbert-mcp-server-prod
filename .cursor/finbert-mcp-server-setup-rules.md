# FinBERT MCP Server Implementation Guide

You are working on implementing the FinBERT MCP (Model Context Protocol) server. The basic structure has been set up, and your task is to implement the actual API integration.

## API Information

- **API Name**: FinBERT
- **Documentation**: [https://github.com/ProsusAI/finBERT#readme](https://github.com/ProsusAI/finBERT#readme)
- **Website**: [https://huggingface.co/ProsusAI/finbert](https://huggingface.co/ProsusAI/finbert)
- **SDK**: `transformers>=4.0.0` (already included in pyproject.toml)
- **Authentication**: Not required
## Implementation Checklist

### 1. Update Deployment Configuration

**IMPORTANT**: Update the `deployment_params.json` file with all implemented capabilities:

```json
{
  "mcp_server": {
    "capabilities": [
      // Replace these with your actual implemented tool names
      "search_finbert",
      "get_finbert_info",
      // Add all other tools you implement
    ]
  },
  "tags": ["finbert", "api", /* add relevant tags like "search", "data", etc. */]
}
```

### 2. Study the API Documentation

First, thoroughly review the API documentation at https://github.com/ProsusAI/finBERT#readme to understand:
- Available endpoints
- Request/response formats
- Rate limits
- Error handling
- Specific features and capabilities to expose as tools

### 3. Implement API Client Functions

Add functions to call the FinBERT API. Example pattern:

```python
# Using the SDK
def call_finbert_api(endpoint: str, params: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """Call FinBERT API using the SDK."""
    # Initialize the SDK client
    client = transformers.Client(api_key=api_key)
    
    # Make the API call
    try:
        response = client.call_endpoint(params)
        return response.to_dict()
    except Exception as e:
        raise Exception(f"FinBERT API error: {str(e)}")
```

### 4. Create MCP Tools

Replace the `example_tool` placeholder with actual tools. **Each tool you implement MUST be added to the `capabilities` array in `deployment_params.json`**.

#### Search/Query Tool
```python
@mcp.tool()
async def search_finbert(
    context: Context,
    query: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search FinBERT for [specific data type].
    
    Args:
        context: MCP context (injected automatically)
        query: Search query
        limit: Maximum number of results
        
    Returns:
        Dictionary with search results
    """
    
    try:
        results = call_finbert_api(
            "search",  # TODO: Use actual endpoint
            {"q": query, "limit": limit},
None)  # Fixed parameter formatting
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}
```

#### Get/Fetch Tool
```python
@mcp.tool()
async def get_finbert_info(
    context: Context,
    item_id: str
) -> Dict[str, Any]:
    """
    Get detailed information about a specific item.
    
    Args:
        context: MCP context (injected automatically)
        item_id: ID of the item to fetch
        
    Returns:
        Dictionary with item details
    """
    # Similar implementation pattern
```

#### Create/Update Tool (if applicable)
```python
@mcp.tool()
async def create_finbert_item(
    context: Context,
    name: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a new item in FinBERT.
    
    Args:
        context: MCP context (injected automatically)
        name: Name of the item
        data: Additional data for the item
        
    Returns:
        Dictionary with creation result
    """
    # Implementation here
```

### 5. Best Practices

1. **Error Handling**: Always wrap API calls in try-except blocks and return user-friendly error messages
2. **Input Validation**: Validate parameters before making API calls
3. **Rate Limiting**: Respect API rate limits, implement delays if needed
4. **Response Formatting**: Return consistent response structures across all tools
5. **Logging**: Use the logger for debugging but don't log sensitive data like API keys
6. **Documentation**: Write clear docstrings for each tool explaining parameters and return values

### 6. Testing

After implementing tools, test them:

1. Run the server locally:
   ```bash
   ./run_local_docker.sh
   ```

2. Use the health check script:
   ```bash
   python mcp_health_check.py
   ```

3. Test with CrewAI:
   ```python
from traia_iatp.mcp.traia_mcp_adapter import create_mcp_adapter
   
   # Standard connection (no authentication)
   with create_mcp_adapter(
       url="http://localhost:8000/mcp/"
   ) as tools:
       # Test your tools
       for tool in tools:
           print(f"Tool: {tool.name}")
   ```

### 7. Update Documentation

After implementing the tools:

1. **Update README.md**:
   - List all implemented tools with descriptions
   - Add usage examples for each tool
   - Include any specific setup instructions

2. **Update deployment_params.json**:
   - Ensure ALL tool names are in the `capabilities` array
   - Add relevant tags based on functionality
   - Verify authentication settings match implementation

3. **Add Tool Examples** in README.md:
   ```python
   # Example usage of each tool
   result = await tool.search_finbert(query="example", limit=5)
   ```

### 8. Pre-Deployment Checklist

Before marking the implementation as complete:

- [ ] All placeholder code has been replaced with actual implementation
- [ ] All tools are properly documented with docstrings
- [ ] Error handling is implemented for all API calls
- [ ] `deployment_params.json` contains all tool names in capabilities
- [ ] README.md has been updated with usage examples
- [ ] Server runs successfully with `./run_local_docker.sh`
- [ ] Health check passes
- [ ] At least one tool works end-to-end

### 9. Common FinBERT Use Cases

Based on the API documentation, consider implementing tools for these common use cases:

1. **TODO**: List specific use cases based on FinBERT capabilities
2. **TODO**: Add more relevant use cases
3. **TODO**: Include any special features of this API

### 10. Example API Calls

Here are some example API calls from the FinBERT documentation that you should implement:

```
TODO: Add specific examples from the API docs
```

## Need Help?

- Check the FinBERT API documentation: https://github.com/ProsusAI/finBERT#readme
- Review the MCP specification: https://modelcontextprotocol.io
- Look at other MCP server examples in the Traia-IO organization

Remember: The goal is to make FinBERT's capabilities easily accessible to AI agents through standardized MCP tools. 