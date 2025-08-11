package com.realconnect.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.client.RestClientException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * Service class for integrating with the MCP Property Search Agent
 * Handles property searches, market analysis, and AI-powered insights
 */
@Service
public class McpPropertySearchService {
    
    private static final Logger logger = LoggerFactory.getLogger(McpPropertySearchService.class);
    
    @Value("${mcp.agent.base-url:http://localhost:8000}")
    private String mcpBaseUrl;
    
    @Value("${mcp.agent.timeout:30000}")
    private int timeoutMs;
    
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    
    public McpPropertySearchService() {
        this.restTemplate = new RestTemplate();
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * Trigger property search for seller market analysis
     * @return Search job ID or null if failed
     */
    public CompletableFuture<PropertySearchResult> triggerSellerMarketAnalysis() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                logger.info("Triggering seller market analysis via MCP agent");
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                
                HttpEntity<String> request = new HttpEntity<>(headers);
                
                ResponseEntity<String> response = restTemplate.exchange(
                    mcpBaseUrl + "/property/search/seller",
                    HttpMethod.POST,
                    request,
                    String.class
                );
                
                if (response.getStatusCode() == HttpStatus.ACCEPTED) {
                    logger.info("Seller market analysis started successfully");
                    return new PropertySearchResult(true, "Market analysis started", null);
                } else {
                    logger.error("Failed to start seller market analysis: {}", response.getStatusCode());
                    return new PropertySearchResult(false, "Failed to start analysis", null);
                }
                
            } catch (RestClientException e) {
                logger.error("Error triggering seller market analysis", e);
                return new PropertySearchResult(false, "Service unavailable: " + e.getMessage(), null);
            }
        });
    }
    
    /**
     * Trigger property search for buyer criteria
     * @return Search result future
     */
    public CompletableFuture<PropertySearchResult> triggerBuyerPropertySearch() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                logger.info("Triggering buyer property search via MCP agent");
                
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.APPLICATION_JSON);
                
                HttpEntity<String> request = new HttpEntity<>(headers);
                
                ResponseEntity<String> response = restTemplate.exchange(
                    mcpBaseUrl + "/property/search/buyer",
                    HttpMethod.POST,
                    request,
                    String.class
                );
                
                if (response.getStatusCode() == HttpStatus.ACCEPTED) {
                    logger.info("Buyer property search started successfully");
                    return new PropertySearchResult(true, "Property search started", null);
                } else {
                    logger.error("Failed to start buyer property search: {}", response.getStatusCode());
                    return new PropertySearchResult(false, "Failed to start search", null);
                }
                
            } catch (RestClientException e) {
                logger.error("Error triggering buyer property search", e);
                return new PropertySearchResult(false, "Service unavailable: " + e.getMessage(), null);
            }
        });
    }
    
    /**
     * Get MCP agent status and recent search results
     * @return Agent status information
     */
    public McpAgentStatus getAgentStatus() {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                mcpBaseUrl + "/property/search/status",
                String.class
            );
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode statusJson = objectMapper.readTree(response.getBody());
                
                return new McpAgentStatus(
                    statusJson.get("status").asText(),
                    statusJson.get("message").asText(),
                    statusJson.get("available_sources").toString(),
                    statusJson.get("timestamp").asText()
                );
            }
            
        } catch (Exception e) {
            logger.error("Error getting MCP agent status", e);
        }
        
        return new McpAgentStatus("error", "Unable to connect to MCP agent", "[]", new Date().toString());
    }
    
    /**
     * Check if MCP agent is available
     * @return true if agent is reachable
     */
    public boolean isAgentAvailable() {
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(
                mcpBaseUrl + "/",
                String.class
            );
            return response.getStatusCode() == HttpStatus.OK;
        } catch (Exception e) {
            logger.warn("MCP agent not available: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * Send property criteria to MCP agent for enhanced search
     * @param criteria Property search criteria
     * @return Search result
     */
    public PropertySearchResult searchWithCriteria(PropertySearchCriteria criteria) {
        try {
            logger.info("Sending property criteria to MCP agent: {}", criteria.getLocation());
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            String requestBody = objectMapper.writeValueAsString(criteria);
            HttpEntity<String> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                mcpBaseUrl + "/property/search/custom",
                HttpMethod.POST,
                request,
                String.class
            );
            
            if (response.getStatusCode() == HttpStatus.OK) {
                JsonNode resultJson = objectMapper.readTree(response.getBody());
                
                List<PropertyData> properties = new ArrayList<>();
                JsonNode propertiesArray = resultJson.get("properties");
                
                if (propertiesArray != null && propertiesArray.isArray()) {
                    for (JsonNode propertyNode : propertiesArray) {
                        properties.add(parsePropertyData(propertyNode));
                    }
                }
                
                return new PropertySearchResult(
                    true,
                    "Search completed successfully",
                    new MarketAnalysis(
                        resultJson.get("total_found").asInt(),
                        properties,
                        resultJson.get("ai_analysis") != null ? 
                            resultJson.get("ai_analysis").get("analysis").asText() : 
                            "No AI analysis available",
                        resultJson.get("search_timestamp").asText()
                    )
                );
            }
            
        } catch (Exception e) {
            logger.error("Error searching with criteria", e);
        }
        
        return new PropertySearchResult(false, "Search failed", null);
    }
    
    /**
     * Parse property data from JSON response
     */
    private PropertyData parsePropertyData(JsonNode propertyNode) {
        return new PropertyData(
            propertyNode.get("id").asText(),
            propertyNode.get("address").asText(),
            propertyNode.get("city").asText(),
            propertyNode.get("state").asText(),
            propertyNode.get("price").asInt(),
            propertyNode.get("bedrooms").asInt(),
            propertyNode.get("bathrooms").asDouble(),
            propertyNode.get("square_feet") != null ? propertyNode.get("square_feet").asInt() : null,
            propertyNode.get("property_type").asText(),
            propertyNode.get("listing_url").asText(),
            propertyNode.get("source").asText(),
            propertyNode.get("description").asText()
        );
    }
    
    // Data Classes
    public static class PropertySearchResult {
        private final boolean success;
        private final String message;
        private final MarketAnalysis analysis;
        
        public PropertySearchResult(boolean success, String message, MarketAnalysis analysis) {
            this.success = success;
            this.message = message;
            this.analysis = analysis;
        }
        
        // Getters
        public boolean isSuccess() { return success; }
        public String getMessage() { return message; }
        public MarketAnalysis getAnalysis() { return analysis; }
    }
    
    public static class MarketAnalysis {
        private final int totalFound;
        private final List<PropertyData> properties;
        private final String aiAnalysis;
        private final String timestamp;
        
        public MarketAnalysis(int totalFound, List<PropertyData> properties, String aiAnalysis, String timestamp) {
            this.totalFound = totalFound;
            this.properties = properties;
            this.aiAnalysis = aiAnalysis;
            this.timestamp = timestamp;
        }
        
        // Getters
        public int getTotalFound() { return totalFound; }
        public List<PropertyData> getProperties() { return properties; }
        public String getAiAnalysis() { return aiAnalysis; }
        public String getTimestamp() { return timestamp; }
    }
    
    public static class PropertyData {
        private final String id;
        private final String address;
        private final String city;
        private final String state;
        private final int price;
        private final int bedrooms;
        private final double bathrooms;
        private final Integer squareFeet;
        private final String propertyType;
        private final String listingUrl;
        private final String source;
        private final String description;
        
        public PropertyData(String id, String address, String city, String state, int price,
                          int bedrooms, double bathrooms, Integer squareFeet, String propertyType,
                          String listingUrl, String source, String description) {
            this.id = id;
            this.address = address;
            this.city = city;
            this.state = state;
            this.price = price;
            this.bedrooms = bedrooms;
            this.bathrooms = bathrooms;
            this.squareFeet = squareFeet;
            this.propertyType = propertyType;
            this.listingUrl = listingUrl;
            this.source = source;
            this.description = description;
        }
        
        // Getters
        public String getId() { return id; }
        public String getAddress() { return address; }
        public String getCity() { return city; }
        public String getState() { return state; }
        public int getPrice() { return price; }
        public int getBedrooms() { return bedrooms; }
        public double getBathrooms() { return bathrooms; }
        public Integer getSquareFeet() { return squareFeet; }
        public String getPropertyType() { return propertyType; }
        public String getListingUrl() { return listingUrl; }
        public String getSource() { return source; }
        public String getDescription() { return description; }
    }
    
    public static class McpAgentStatus {
        private final String status;
        private final String message;
        private final String availableSources;
        private final String timestamp;
        
        public McpAgentStatus(String status, String message, String availableSources, String timestamp) {
            this.status = status;
            this.message = message;
            this.availableSources = availableSources;
            this.timestamp = timestamp;
        }
        
        // Getters
        public String getStatus() { return status; }
        public String getMessage() { return message; }
        public String getAvailableSources() { return availableSources; }
        public String getTimestamp() { return timestamp; }
    }
    
    public static class PropertySearchCriteria {
        private String location;
        private Integer minPrice;
        private Integer maxPrice;
        private Integer bedrooms;
        private Double bathrooms;
        private String propertyType;
        private Integer squareFeetMin;
        private Integer squareFeetMax;
        private List<String> keywords;
        
        // Default constructor
        public PropertySearchCriteria() {}
        
        // Constructor with basic parameters
        public PropertySearchCriteria(String location, Integer minPrice, Integer maxPrice, Integer bedrooms) {
            this.location = location;
            this.minPrice = minPrice;
            this.maxPrice = maxPrice;
            this.bedrooms = bedrooms;
        }
        
        // Getters and setters
        public String getLocation() { return location; }
        public void setLocation(String location) { this.location = location; }
        
        public Integer getMinPrice() { return minPrice; }
        public void setMinPrice(Integer minPrice) { this.minPrice = minPrice; }
        
        public Integer getMaxPrice() { return maxPrice; }
        public void setMaxPrice(Integer maxPrice) { this.maxPrice = maxPrice; }
        
        public Integer getBedrooms() { return bedrooms; }
        public void setBedrooms(Integer bedrooms) { this.bedrooms = bedrooms; }
        
        public Double getBathrooms() { return bathrooms; }
        public void setBathrooms(Double bathrooms) { this.bathrooms = bathrooms; }
        
        public String getPropertyType() { return propertyType; }
        public void setPropertyType(String propertyType) { this.propertyType = propertyType; }
        
        public Integer getSquareFeetMin() { return squareFeetMin; }
        public void setSquareFeetMin(Integer squareFeetMin) { this.squareFeetMin = squareFeetMin; }
        
        public Integer getSquareFeetMax() { return squareFeetMax; }
        public void setSquareFeetMax(Integer squareFeetMax) { this.squareFeetMax = squareFeetMax; }
        
        public List<String> getKeywords() { return keywords; }
        public void setKeywords(List<String> keywords) { this.keywords = keywords; }
    }
}