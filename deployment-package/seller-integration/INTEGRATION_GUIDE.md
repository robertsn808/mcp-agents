# MCP Property Search Agent - Seller App Integration Guide

## Overview

This integration guide will help you add the MCP Property Search Agent functionality to your existing Spring Boot Real Estate CRM application.

## 🚀 Quick Setup

### 1. Copy Integration Files

Copy the following files from this `seller-integration` directory to your seller repo:

```bash
# Service Layer
src/main/java/com/realconnect/service/McpPropertySearchService.java

# Controllers
src/main/java/com/realconnect/controller/McpPropertyController.java
src/main/java/com/realconnect/controller/EnhancedSellerController.java

# Templates
src/main/resources/templates/admin/property-analysis/dashboard.html
src/main/resources/templates/admin/property-analysis/results.html

# Configuration
src/main/resources/application-mcp.properties
```

### 2. Update Configuration

Add the MCP configuration to your `application.properties`:

```properties
# Append content from application-mcp.properties
mcp.agent.base-url=http://localhost:8000
mcp.integration.enabled=true
# ... (see application-mcp.properties for full configuration)
```

### 3. Add Dependencies

Add to your `pom.xml`:

```xml
<dependencies>
    <!-- Existing dependencies... -->
    
    <!-- For REST Template configuration -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    
    <!-- For async operations -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-async</artifactId>
    </dependency>
</dependencies>
```

### 4. Configure REST Template Bean

Add to your main Application class or a Configuration class:

```java
@Configuration
public class McpConfiguration {
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @Bean
    @ConfigurationProperties(prefix = "mcp.agent")
    public McpAgentProperties mcpAgentProperties() {
        return new McpAgentProperties();
    }
}
```

## 📊 Features Added

### 1. Market Analysis Dashboard
- **URL**: `/admin/property-analysis`
- **Features**:
  - Real-time MCP agent status
  - One-click market analysis triggers
  - AI-powered property insights
  - Visual property search results

### 2. Enhanced API Endpoints
- **GET** `/seller` - Returns seller criteria for MCP agent
- **GET** `/buyer` - Returns buyer criteria for MCP agent  
- **POST** `/webhook/property-search` - Receives MCP search results
- **POST** `/seller/{id}/analyze-market` - Trigger analysis for specific seller

### 3. Property Search Integration
- **Seller Market Analysis**: Find comparable properties for sellers
- **Buyer Property Matching**: Search properties matching buyer criteria
- **Custom Search**: Advanced search with specific parameters
- **AI Analysis**: Claude-powered market insights and recommendations

## 🔧 Configuration Options

### MCP Agent Connection
```properties
# MCP Agent URL (where your webhook_server.py is running)
mcp.agent.base-url=http://localhost:8000

# Connection settings
mcp.agent.timeout=30000
mcp.agent.retry-attempts=3
```

### Integration Features
```properties
# Enable/disable MCP integration
mcp.integration.enabled=true

# Auto-sync with MCP agent
mcp.integration.auto-sync=true
mcp.integration.sync-interval=3600000

# Property search settings
property.search.default-radius=25
property.search.max-results=50
property.search.sources=zillow,realtor
```

## 📋 Usage Examples

### 1. Trigger Market Analysis (Java)
```java
@Autowired
private McpPropertySearchService mcpService;

public void analyzeMarketForSeller(Long sellerId) {
    Optional<Seller> seller = sellerRepository.findById(sellerId);
    
    if (seller.isPresent()) {
        PropertySearchCriteria criteria = new PropertySearchCriteria(
            seller.get().getCity() + ", " + seller.get().getState(),
            (int)(seller.get().getAskingPrice() * 0.8),
            (int)(seller.get().getAskingPrice() * 1.2),
            seller.get().getBedrooms()
        );
        
        PropertySearchResult result = mcpService.searchWithCriteria(criteria);
        
        if (result.isSuccess()) {
            // Process market analysis results
            processMarketAnalysis(result.getAnalysis());
        }
    }
}
```

### 2. Frontend Integration (JavaScript)
```javascript
// Trigger seller market analysis
async function analyzeMarket() {
    const response = await fetch('/admin/property-analysis/trigger-seller-analysis', {
        method: 'POST'
    });
    
    const result = await response.json();
    
    if (result.success) {
        console.log('Analysis started:', result.message);
        // Poll for results or wait for webhook
        pollForResults();
    }
}

// Get agent status
async function checkAgentStatus() {
    const response = await fetch('/admin/property-analysis/agent-status');
    const status = await response.json();
    
    console.log('Agent available:', status.available);
    console.log('Status message:', status.message);
}
```

### 3. Webhook Processing
Your seller app will automatically receive property search results via webhook:

```java
@PostMapping("/webhook/property-search")
public ResponseEntity<Map<String, Object>> receivePropertySearchResults(
        @RequestBody Map<String, Object> searchResults) {
    
    String searchType = (String) searchResults.get("search_type");
    Integer totalProperties = (Integer) searchResults.get("total_found");
    
    if ("seller".equals(searchType)) {
        // Process seller market analysis
        handleSellerMarketResults(searchResults);
    } else if ("buyer".equals(searchType)) {
        // Process buyer property matches  
        handleBuyerMatchResults(searchResults);
    }
    
    return ResponseEntity.ok(Map.of("success", true));
}
```

## 🎨 UI Integration

### Adding Market Analysis to Existing Pages

#### 1. Add Navigation Link
```html
<!-- In your admin navigation -->
<li class="nav-item">
    <a class="nav-link" href="/admin/property-analysis">
        <i class="fas fa-chart-line me-2"></i>Market Analysis
    </a>
</li>
```

#### 2. Embed Property Search Widget
```html
<!-- In any admin page -->
<div class="row">
    <div class="col-12">
        <div th:replace="admin/property-analysis/widget :: propertySearchWidget"></div>
    </div>
</div>
```

#### 3. Add Quick Actions to Seller Details
```html
<!-- In seller detail page -->
<div class="card">
    <div class="card-header">
        <h5>Market Analysis</h5>
    </div>
    <div class="card-body">
        <button class="btn btn-primary" 
                onclick="analyzeSeller([[${seller.id}]])">
            <i class="fas fa-chart-bar me-2"></i>
            Analyze Market for This Property
        </button>
    </div>
</div>

<script>
async function analyzeSeller(sellerId) {
    const response = await fetch(`/seller/${sellerId}/analyze-market`, {
        method: 'POST'
    });
    
    const result = await response.json();
    
    if (result.success) {
        alert(`Found ${result.total_properties} comparable properties!`);
        // Redirect to results page
        window.location.href = '/admin/property-analysis/results?type=seller';
    }
}
</script>
```

## 🧪 Testing Integration

### 1. Start MCP Agent
```bash
# In your mcp-agents-repo directory
python webhook_server.py
```

### 2. Test Agent Connection
```bash
curl http://localhost:8000/property/search/status
```

### 3. Test Seller Integration
```bash
# Test seller criteria endpoint
curl http://localhost:8080/seller

# Test market analysis trigger  
curl -X POST http://localhost:8080/admin/property-analysis/trigger-seller-analysis
```

### 4. Check Logs
Monitor both applications:
```bash
# MCP Agent logs
tail -f server.log

# Seller app logs  
tail -f logs/application.log
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Agent Connection Failed
**Problem**: `MCP agent is not available`
**Solution**: 
- Check if webhook_server.py is running
- Verify mcp.agent.base-url in configuration
- Check firewall/network connectivity

#### 2. No Properties Found
**Problem**: Search returns 0 results
**Solution**:
- Verify seller/buyer data exists in database
- Check search criteria in logs
- Test with broader location (e.g., state instead of city)

#### 3. Webhook Not Receiving Data
**Problem**: Results not appearing in seller app
**Solution**:
- Verify webhook endpoint is accessible
- Check webhook URL in MCP agent configuration
- Ensure webhook secret matches (if configured)

### Debug Mode

Enable debug logging:
```properties
logging.level.com.realconnect.service.McpPropertySearchService=DEBUG
logging.level.com.realconnect.controller.McpPropertyController=DEBUG
```

## 🚀 Deployment

### Production Configuration

#### 1. Environment Variables
```bash
export MCP_AGENT_BASE_URL=https://your-mcp-agent-domain.com
export MCP_WEBHOOK_SECRET=your-secure-webhook-secret
export ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### 2. Security Considerations
- Enable webhook signature verification
- Use HTTPS for all MCP agent communication
- Implement rate limiting for property searches
- Set up monitoring and alerting

#### 3. Performance Optimization
```properties
# Cache property search results
mcp.performance.cache-enabled=true
mcp.performance.cache-ttl=1800

# Parallel searches for better performance
mcp.performance.parallel-searches=true
mcp.performance.max-concurrent-searches=5
```

## 📞 Support

If you encounter issues:

1. Check the logs for both applications
2. Verify network connectivity between services
3. Test individual endpoints with curl/Postman
4. Review configuration settings
5. Check MCP agent status via health endpoint

## 🔄 Updates

To update the integration:

1. Pull latest changes from MCP agent repository
2. Update service classes with any new features
3. Run tests to ensure compatibility
4. Deploy updated configuration

The integration is designed to be backward compatible and fail gracefully when the MCP agent is unavailable.