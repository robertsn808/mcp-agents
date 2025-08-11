#!/bin/bash

# MCP Property Search Agent - Seller App Integration Test Script
# This script tests the integration between the MCP agent and seller app

echo "🏠 MCP Property Search Agent - Integration Test"
echo "================================================"

# Configuration
MCP_AGENT_URL="http://localhost:8000"
SELLER_APP_URL="http://localhost:8080"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print test results
print_test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC} - $2"
    else
        echo -e "${RED}❌ FAIL${NC} - $2"
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$url" 2>/dev/null)
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC} (Status: $http_code)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Status: $http_code, Expected: $expected_status)"
        return 1
    fi
}

# Function to test POST endpoint
test_post_endpoint() {
    local url=$1
    local description=$2
    local data=$3
    local expected_status=${4:-200}
    
    echo -n "Testing $description... "
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null)
    http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    
    if [ "$http_code" -eq "$expected_status" ] || [ "$http_code" -eq "202" ]; then
        echo -e "${GREEN}✅ PASS${NC} (Status: $http_code)"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC} (Status: $http_code, Expected: $expected_status)"
        echo "Response: $(echo $response | sed -e 's/HTTPSTATUS:.*//')"
        return 1
    fi
}

# Test counters
total_tests=0
passed_tests=0

echo ""
echo -e "${BLUE}🔍 Phase 1: Testing MCP Agent Availability${NC}"
echo "----------------------------------------"

# Test 1: MCP Agent Health Check
total_tests=$((total_tests + 1))
if test_endpoint "$MCP_AGENT_URL/" "MCP Agent Health Check"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 2: MCP Agent Property Search Status  
total_tests=$((total_tests + 1))
if test_endpoint "$MCP_AGENT_URL/property/search/status" "MCP Agent Property Search Status"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo -e "${BLUE}🏢 Phase 2: Testing Seller App Endpoints${NC}"
echo "----------------------------------------"

# Test 3: Seller App Health Check
total_tests=$((total_tests + 1))
if test_endpoint "$SELLER_APP_URL/actuator/health" "Seller App Health Check" "200"; then
    passed_tests=$((passed_tests + 1))
else
    # Try alternative health endpoint
    if test_endpoint "$SELLER_APP_URL/" "Seller App Root Endpoint" "200"; then
        passed_tests=$((passed_tests + 1))
    fi
fi

# Test 4: Seller Criteria Endpoint
total_tests=$((total_tests + 1))
if test_endpoint "$SELLER_APP_URL/seller" "Seller Criteria Endpoint"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 5: Buyer Criteria Endpoint
total_tests=$((total_tests + 1))
if test_endpoint "$SELLER_APP_URL/buyer" "Buyer Criteria Endpoint"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 6: Market Analysis Dashboard (if accessible)
total_tests=$((total_tests + 1))
if test_endpoint "$SELLER_APP_URL/admin/property-analysis" "Market Analysis Dashboard" "200"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo -e "${BLUE}🔄 Phase 3: Testing Integration Functionality${NC}"
echo "--------------------------------------------"

# Test 7: Trigger Seller Market Analysis
total_tests=$((total_tests + 1))
if test_post_endpoint "$SELLER_APP_URL/admin/property-analysis/trigger-seller-analysis" "Trigger Seller Market Analysis" "{}" "202"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 8: Trigger Buyer Property Search
total_tests=$((total_tests + 1))
if test_post_endpoint "$SELLER_APP_URL/admin/property-analysis/trigger-buyer-search" "Trigger Buyer Property Search" "{}" "202"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 9: MCP Agent Status Check from Seller App
total_tests=$((total_tests + 1))
if test_endpoint "$SELLER_APP_URL/admin/property-analysis/agent-status" "MCP Agent Status from Seller App"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 10: Custom Property Search
total_tests=$((total_tests + 1))
custom_search_data='{
    "location": "San Francisco, CA",
    "minPrice": 500000,
    "maxPrice": 1000000,
    "bedrooms": 2,
    "propertyType": "condo"
}'
if test_post_endpoint "$SELLER_APP_URL/admin/property-analysis/custom-search" "Custom Property Search" "$custom_search_data"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo -e "${BLUE}📊 Phase 4: Testing Webhook Integration${NC}"
echo "----------------------------------------"

# Test 11: Webhook Endpoint Accessibility
total_tests=$((total_tests + 1))
webhook_test_data='{
    "search_type": "test",
    "total_found": 5,
    "ai_analysis": "Test analysis",
    "properties": []
}'
if test_post_endpoint "$SELLER_APP_URL/webhook/property-search" "Webhook Property Search Results" "$webhook_test_data"; then
    passed_tests=$((passed_tests + 1))
fi

# Test 12: Direct MCP Agent Property Search Trigger
total_tests=$((total_tests + 1))
if test_post_endpoint "$MCP_AGENT_URL/property/search/seller" "MCP Agent Seller Search Trigger" "{}" "202"; then
    passed_tests=$((passed_tests + 1))
fi

echo ""
echo -e "${BLUE}🧪 Phase 5: Data Flow Verification${NC}"
echo "-----------------------------------"

# Test 13: Verify Seller Data Format
echo -n "Verifying seller data format... "
seller_response=$(curl -s "$SELLER_APP_URL/seller" 2>/dev/null)
if echo "$seller_response" | grep -q "location" && echo "$seller_response" | grep -q "property_type"; then
    echo -e "${GREEN}✅ PASS${NC} - Seller data contains required fields"
    passed_tests=$((passed_tests + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Seller data missing required fields"
fi
total_tests=$((total_tests + 1))

# Test 14: Verify Buyer Data Format
echo -n "Verifying buyer data format... "
buyer_response=$(curl -s "$SELLER_APP_URL/buyer" 2>/dev/null)
if echo "$buyer_response" | grep -q "location" && echo "$buyer_response" | grep -q "min_price"; then
    echo -e "${GREEN}✅ PASS${NC} - Buyer data contains required fields"
    passed_tests=$((passed_tests + 1))
else
    echo -e "${RED}❌ FAIL${NC} - Buyer data missing required fields"
fi
total_tests=$((total_tests + 1))

echo ""
echo -e "${BLUE}📝 Integration Test Summary${NC}"
echo "=========================="

# Calculate success rate
success_rate=$((passed_tests * 100 / total_tests))

echo "Total Tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $((total_tests - passed_tests))"
echo "Success Rate: $success_rate%"

echo ""

if [ $success_rate -ge 80 ]; then
    echo -e "${GREEN}🎉 Integration Status: SUCCESS${NC}"
    echo "The MCP Property Search Agent is successfully integrated with your seller app!"
    echo ""
    echo "✅ Next Steps:"
    echo "   1. Access the Market Analysis Dashboard at: $SELLER_APP_URL/admin/property-analysis"
    echo "   2. Trigger property searches from the dashboard"
    echo "   3. Monitor logs for detailed search results"
    echo "   4. Configure webhook notifications if needed"
elif [ $success_rate -ge 60 ]; then
    echo -e "${YELLOW}⚠️ Integration Status: PARTIAL${NC}"
    echo "The integration is partially working. Some features may need attention."
    echo ""
    echo "🔧 Recommended Actions:"
    echo "   1. Check failed tests above"
    echo "   2. Verify both services are running"
    echo "   3. Check network connectivity"
    echo "   4. Review configuration files"
else
    echo -e "${RED}❌ Integration Status: FAILED${NC}"
    echo "The integration has significant issues that need to be resolved."
    echo ""
    echo "🚨 Required Actions:"
    echo "   1. Ensure both MCP Agent and Seller App are running"
    echo "   2. Check service URLs and ports"
    echo "   3. Verify all integration files are properly installed"
    echo "   4. Review logs for error details"
fi

echo ""
echo -e "${BLUE}📚 Useful Commands:${NC}"
echo "   • View MCP Agent logs: tail -f webhook_server.log"
echo "   • View Seller App logs: tail -f logs/application.log"  
echo "   • Test individual endpoints: curl -v [URL]"
echo "   • Check Java processes: jps -l"
echo "   • Check Python processes: ps aux | grep python"

echo ""
echo -e "${BLUE}🔧 Troubleshooting:${NC}"
echo "   • If MCP Agent tests fail: Check if webhook_server.py is running on port 8000"
echo "   • If Seller App tests fail: Check if Spring Boot app is running on port 8080"
echo "   • If integration tests fail: Verify configuration in application.properties"
echo "   • If webhook tests fail: Check firewall settings and network connectivity"

exit $((total_tests - passed_tests))