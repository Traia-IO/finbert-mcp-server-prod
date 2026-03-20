#!/bin/bash

# Detailed test script for FinBERT MCP Server tools
# This script tests all available MCP tools and shows detailed responses

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVER_URL="http://localhost:8000/mcp"
TEST_RESULTS=()

echo -e "${BLUE}🧪 Testing FinBERT MCP Server Tools (Detailed)${NC}"
echo -e "${BLUE}Server URL: ${SERVER_URL}${NC}"
echo

# Function to make MCP tool calls with detailed output
make_mcp_call() {
    local tool_name=$1
    local arguments=$2
    local description=$3
    
    echo -e "${YELLOW}📋 Testing: ${description}${NC}"
    
    # Create JSON-RPC 2.0 request
    local request_data=$(cat <<EOF
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "${tool_name}",
        "arguments": ${arguments}
    }
}
EOF
)
    
    echo -e "${CYAN}📤 Request:${NC}"
    echo "${request_data}" | jq '.'
    echo
    
    # Make the request
    local response=$(curl -s -X POST "${SERVER_URL}" \
        -H "Content-Type: application/json" \
        -d "${request_data}" \
        --max-time 30)
    
    echo -e "${CYAN}📥 Response:${NC}"
    
    # Check if response is valid JSON
    if echo "${response}" | jq empty 2>/dev/null; then
        # Pretty print the response
        echo "${response}" | jq '.'
        
        # Check for errors in response
        local error=$(echo "${response}" | jq -r '.error // empty')
        if [ -n "${error}" ]; then
            echo -e "${RED}❌ Error detected in response${NC}"
            TEST_RESULTS+=("❌ ${description}")
            return 1
        fi
        
        echo -e "${GREEN}✅ Success${NC}"
        TEST_RESULTS+=("✅ ${description}")
        return 0
    else
        echo -e "${RED}❌ Invalid JSON response${NC}"
        echo -e "${RED}Raw response: ${response}${NC}"
        TEST_RESULTS+=("❌ ${description}")
        return 1
    fi
}

# Test 1: Get model info
echo -e "${BLUE}=== Test 1: Get FinBERT Model Info ===${NC}"
make_mcp_call "get_finbert_model_info" "{}" "Get model information and status"
echo -e "${BLUE}========================================${NC}"
echo

# Test 2: Single text sentiment analysis (positive)
echo -e "${BLUE}=== Test 2: Positive Sentiment Analysis ===${NC}"
make_mcp_call "finbert_sentiment_analysis" '{"text": "Apple Inc. reported strong quarterly earnings, beating analyst expectations with revenue growth of 15%."}' "Analyze positive financial text"
echo -e "${BLUE}===========================================${NC}"
echo

# Test 3: Single text sentiment analysis (negative)
echo -e "${BLUE}=== Test 3: Negative Sentiment Analysis ===${NC}"
make_mcp_call "finbert_sentiment_analysis" '{"text": "The company faced significant losses due to market volatility and declining investor confidence."}' "Analyze negative financial text"
echo -e "${BLUE}===========================================${NC}"
echo

# Test 4: Neutral sentiment analysis
echo -e "${BLUE}=== Test 4: Neutral Sentiment Analysis ===${NC}"
make_mcp_call "finbert_sentiment_analysis" '{"text": "The quarterly report will be released next Tuesday according to the company schedule."}' "Analyze neutral financial text"
echo -e "${BLUE}==========================================${NC}"
echo

# Test 5: Batch text analysis
echo -e "${BLUE}=== Test 5: Batch Text Analysis ===${NC}"
batch_texts='["Tesla stock surged 12% following strong delivery numbers.", "Oil prices dropped amid global economic concerns.", "The Federal Reserve maintained interest rates at current levels."]'
make_mcp_call "analyze_financial_text_batch" "{\"texts\": ${batch_texts}}" "Analyze multiple financial texts in batch"
echo -e "${BLUE}===================================${NC}"
echo

# Test 6: Error handling - empty text
echo -e "${BLUE}=== Test 6: Error Handling - Empty Text ===${NC}"
make_mcp_call "finbert_sentiment_analysis" '{"text": ""}' "Test error handling with empty text"
echo -e "${BLUE}===========================================${NC}"
echo

# Print summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo
total_tests=${#TEST_RESULTS[@]}
passed_tests=0
failed_tests=0

for result in "${TEST_RESULTS[@]}"; do
    echo -e "${result}"
    if [[ $result == ✅* ]]; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
done

echo
echo -e "${BLUE}📊 Results: ${GREEN}${passed_tests} passed${NC}, ${RED}${failed_tests} failed${NC} out of ${total_tests} tests"

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! FinBERT MCP Server is working correctly.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the server logs for details.${NC}"
    exit 1
fi 