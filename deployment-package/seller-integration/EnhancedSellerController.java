package com.realconnect.controller;

import com.realconnect.service.McpPropertySearchService;
import com.realconnect.service.McpPropertySearchService.PropertySearchCriteria;
import com.realconnect.service.McpPropertySearchService.PropertySearchResult;
import com.realconnect.entity.Seller;
import com.realconnect.entity.Buyer;
import com.realconnect.repository.SellerRepository;
import com.realconnect.repository.BuyerRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Enhanced Seller Controller with MCP Property Search Integration
 * Extends existing seller functionality with AI-powered property intelligence
 */
@RestController
@CrossOrigin(origins = "*")
public class EnhancedSellerController {
    
    private static final Logger logger = LoggerFactory.getLogger(EnhancedSellerController.class);
    
    @Autowired
    private SellerRepository sellerRepository;
    
    @Autowired
    private BuyerRepository buyerRepository;
    
    @Autowired
    private McpPropertySearchService mcpPropertySearchService;
    
    /**
     * Enhanced seller endpoint that provides market intelligence data
     * Returns seller criteria for MCP agent consumption
     */
    @GetMapping("/seller")
    public ResponseEntity<Map<String, Object>> getSellerCriteria() {
        logger.info("Fetching seller criteria for MCP agent");
        
        try {
            // Get the most recent seller submission or default criteria
            Optional<Seller> latestSeller = sellerRepository.findFirstByOrderByCreatedAtDesc();
            
            Map<String, Object> criteria = new HashMap<>();
            
            if (latestSeller.isPresent()) {
                Seller seller = latestSeller.get();
                
                // Extract location from address
                String location = extractLocationFromAddress(
                    seller.getAddress(), 
                    seller.getCity(), 
                    seller.getState()
                );
                
                criteria.put("location", location);
                criteria.put("property_type", seller.getPropertyType());
                criteria.put("bedrooms", seller.getBedrooms());
                criteria.put("bathrooms", seller.getBathrooms());
                criteria.put("square_feet_min", seller.getSquareFootage() != null ? 
                    (int)(seller.getSquareFootage() * 0.8) : null);
                criteria.put("square_feet_max", seller.getSquareFootage() != null ? 
                    (int)(seller.getSquareFootage() * 1.2) : null);
                
                // Price range for competitive analysis
                if (seller.getAskingPrice() != null) {
                    criteria.put("min_price", (int)(seller.getAskingPrice() * 0.7));
                    criteria.put("max_price", (int)(seller.getAskingPrice() * 1.3));
                }
                
                // Add property condition and features as keywords
                criteria.put("keywords", generateKeywordsFromSeller(seller));
                
                logger.info("Generated seller criteria for location: {}", location);
                
            } else {
                // Default criteria if no sellers in database
                criteria.put("location", "United States");
                criteria.put("property_type", "house");
                criteria.put("bedrooms", 3);
                criteria.put("bathrooms", 2.0);
                criteria.put("min_price", 200000);
                criteria.put("max_price", 800000);
                
                logger.info("Using default seller criteria - no sellers found in database");
            }
            
            return ResponseEntity.ok(criteria);
            
        } catch (Exception e) {
            logger.error("Error fetching seller criteria", e);
            
            // Return default criteria on error
            Map<String, Object> defaultCriteria = new HashMap<>();
            defaultCriteria.put("location", "United States");
            defaultCriteria.put("property_type", "house");
            defaultCriteria.put("bedrooms", 3);
            defaultCriteria.put("bathrooms", 2.0);
            defaultCriteria.put("min_price", 200000);
            defaultCriteria.put("max_price", 800000);
            
            return ResponseEntity.ok(defaultCriteria);
        }
    }
    
    /**
     * Enhanced buyer endpoint that provides buyer criteria for property matching
     */
    @GetMapping("/buyer")
    public ResponseEntity<Map<String, Object>> getBuyerCriteria() {
        logger.info("Fetching buyer criteria for MCP agent");
        
        try {
            // Get the most recent active buyer or aggregate criteria from multiple buyers
            Optional<Buyer> latestBuyer = buyerRepository.findFirstByOrderByCreatedAtDesc();
            
            Map<String, Object> criteria = new HashMap<>();
            
            if (latestBuyer.isPresent()) {
                Buyer buyer = latestBuyer.get();
                
                criteria.put("location", buyer.getLocation() != null ? buyer.getLocation() : "United States");
                criteria.put("min_price", buyer.getBudgetMin());
                criteria.put("max_price", buyer.getBudgetMax());
                criteria.put("bedrooms", buyer.getBedroomsMin());
                criteria.put("bathrooms", buyer.getBathroomsMin());
                criteria.put("property_type", buyer.getPropertyType());
                
                // Add buyer-specific keywords
                criteria.put("keywords", generateKeywordsFromBuyer(buyer));
                
                logger.info("Generated buyer criteria for location: {}", buyer.getLocation());
                
            } else {
                // Default buyer criteria
                criteria.put("location", "United States");
                criteria.put("property_type", "house");
                criteria.put("bedrooms", 2);
                criteria.put("bathrooms", 2.0);
                criteria.put("min_price", 300000);
                criteria.put("max_price", 600000);
                
                logger.info("Using default buyer criteria - no buyers found in database");
            }
            
            return ResponseEntity.ok(criteria);
            
        } catch (Exception e) {
            logger.error("Error fetching buyer criteria", e);
            
            // Return default criteria on error
            Map<String, Object> defaultCriteria = new HashMap<>();
            defaultCriteria.put("location", "United States");
            defaultCriteria.put("property_type", "house");
            defaultCriteria.put("bedrooms", 2);
            defaultCriteria.put("bathrooms", 2.0);
            defaultCriteria.put("min_price", 300000);
            defaultCriteria.put("max_price", 600000);
            
            return ResponseEntity.ok(defaultCriteria);
        }
    }
    
    /**
     * Webhook endpoint to receive property search results from MCP agent
     */
    @PostMapping("/webhook/property-search")
    public ResponseEntity<Map<String, Object>> receivePropertySearchResults(
            @RequestBody Map<String, Object> searchResults) {
        
        logger.info("Received property search results from MCP agent");
        
        try {
            // Process the search results
            String searchType = (String) searchResults.get("search_type"); // "seller" or "buyer"
            Integer totalProperties = (Integer) searchResults.get("total_found");
            String analysisText = (String) searchResults.get("ai_analysis");
            
            logger.info("Processing {} search results: {} properties found", 
                searchType, totalProperties);
            
            // Store results in database or trigger follow-up actions
            if ("seller".equals(searchType)) {
                handleSellerMarketResults(searchResults);
            } else if ("buyer".equals(searchType)) {
                handleBuyerMatchResults(searchResults);
            }
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Search results processed successfully");
            response.put("processed_properties", totalProperties);
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error processing property search results", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Manual trigger for property search with enhanced seller data
     */
    @PostMapping("/seller/{id}/analyze-market")
    public ResponseEntity<Map<String, Object>> analyzeMarketForSeller(@PathVariable Long id) {
        logger.info("Triggering market analysis for seller ID: {}", id);
        
        try {
            Optional<Seller> sellerOpt = sellerRepository.findById(id);
            
            if (!sellerOpt.isPresent()) {
                Map<String, Object> response = new HashMap<>();
                response.put("success", false);
                response.put("error", "Seller not found");
                return ResponseEntity.notFound().build();
            }
            
            Seller seller = sellerOpt.get();
            
            // Create specific search criteria for this seller
            PropertySearchCriteria criteria = new PropertySearchCriteria(
                extractLocationFromAddress(seller.getAddress(), seller.getCity(), seller.getState()),
                seller.getAskingPrice() != null ? (int)(seller.getAskingPrice() * 0.7) : null,
                seller.getAskingPrice() != null ? (int)(seller.getAskingPrice() * 1.3) : null,
                seller.getBedrooms()
            );
            
            criteria.setBathrooms(seller.getBathrooms() != null ? seller.getBathrooms().doubleValue() : null);
            criteria.setPropertyType(seller.getPropertyType());
            criteria.setSquareFeetMin(seller.getSquareFootage() != null ? 
                (int)(seller.getSquareFootage() * 0.8) : null);
            criteria.setSquareFeetMax(seller.getSquareFootage() != null ? 
                (int)(seller.getSquareFootage() * 1.2) : null);
            criteria.setKeywords(generateKeywordsFromSeller(seller));
            
            // Trigger search via MCP agent
            PropertySearchResult result = mcpPropertySearchService.searchWithCriteria(criteria);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", result.isSuccess());
            response.put("message", result.getMessage());
            
            if (result.getAnalysis() != null) {
                response.put("total_properties", result.getAnalysis().getTotalFound());
                response.put("ai_analysis", result.getAnalysis().getAiAnalysis());
                response.put("properties", result.getAnalysis().getProperties());
            }
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error analyzing market for seller", e);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", false);
            response.put("error", e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    // Helper methods
    
    private String extractLocationFromAddress(String address, String city, String state) {
        StringBuilder location = new StringBuilder();
        
        if (city != null && !city.trim().isEmpty()) {
            location.append(city.trim());
        }
        
        if (state != null && !state.trim().isEmpty()) {
            if (location.length() > 0) {
                location.append(", ");
            }
            location.append(state.trim());
        }
        
        if (location.length() == 0 && address != null && !address.trim().isEmpty()) {
            // Try to extract city/state from address
            location.append(address.trim());
        }
        
        return location.length() > 0 ? location.toString() : "United States";
    }
    
    private String[] generateKeywordsFromSeller(Seller seller) {
        java.util.List<String> keywords = new java.util.ArrayList<>();
        
        if (seller.getPropertyCondition() != null) {
            keywords.add(seller.getPropertyCondition().toLowerCase());
        }
        
        if (seller.getCreativeFinancing() != null && seller.getCreativeFinancing()) {
            keywords.add("owner financing");
            keywords.add("creative financing");
        }
        
        if (seller.getPropertyType() != null) {
            keywords.add(seller.getPropertyType().toLowerCase());
        }
        
        // Add timeline urgency keywords
        if (seller.getSellTimeframe() != null) {
            if (seller.getSellTimeframe().toLowerCase().contains("asap") || 
                seller.getSellTimeframe().toLowerCase().contains("immediately")) {
                keywords.add("motivated seller");
            }
        }
        
        return keywords.toArray(new String[0]);
    }
    
    private String[] generateKeywordsFromBuyer(Buyer buyer) {
        java.util.List<String> keywords = new java.util.ArrayList<>();
        
        if (buyer.getPropertyType() != null) {
            keywords.add(buyer.getPropertyType().toLowerCase());
        }
        
        if (buyer.getPurchasePurpose() != null) {
            keywords.add(buyer.getPurchasePurpose().toLowerCase());
        }
        
        // Add financing preferences
        if (buyer.getFinancingType() != null) {
            keywords.add(buyer.getFinancingType().toLowerCase());
        }
        
        return keywords.toArray(new String[0]);
    }
    
    private void handleSellerMarketResults(Map<String, Object> results) {
        // Process seller market analysis results
        // This could involve:
        // - Updating seller records with market insights
        // - Triggering marketing campaigns
        // - Sending notifications to sellers
        
        logger.info("Processing seller market analysis results");
        
        // Example: Update seller with market intelligence
        // You could extend the Seller entity to include market analysis fields
    }
    
    private void handleBuyerMatchResults(Map<String, Object> results) {
        // Process buyer property matching results
        // This could involve:
        // - Notifying matching buyers about new properties
        // - Creating automated follow-up tasks
        // - Scoring leads based on property availability
        
        logger.info("Processing buyer property matching results");
        
        // Example: Create buyer notifications or lead scoring updates
    }
}