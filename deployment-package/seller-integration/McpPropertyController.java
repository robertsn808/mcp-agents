package com.realconnect.controller;

import com.realconnect.service.McpPropertySearchService;
import com.realconnect.service.McpPropertySearchService.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.Map;
import java.util.HashMap;

/**
 * Controller for MCP Property Search Integration
 * Handles market analysis requests and property search triggers
 */
@Controller
@RequestMapping("/admin/property-analysis")
public class McpPropertyController {
    
    private static final Logger logger = LoggerFactory.getLogger(McpPropertyController.class);
    
    @Autowired
    private McpPropertySearchService mcpService;
    
    /**
     * Display the market analysis dashboard page
     */
    @GetMapping("")
    public String marketAnalysisDashboard(Model model) {
        logger.info("Displaying market analysis dashboard");
        
        // Get MCP agent status
        McpAgentStatus agentStatus = mcpService.getAgentStatus();
        model.addAttribute("agentStatus", agentStatus);
        model.addAttribute("agentAvailable", mcpService.isAgentAvailable());
        
        // Add navigation info
        model.addAttribute("pageTitle", "Market Analysis Dashboard");
        model.addAttribute("activeSection", "property-analysis");
        
        return "admin/property-analysis/dashboard";
    }
    
    /**
     * Trigger seller market analysis via AJAX
     */
    @PostMapping("/trigger-seller-analysis")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> triggerSellerAnalysis() {
        logger.info("Triggering seller market analysis");
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            // Check if agent is available first
            if (!mcpService.isAgentAvailable()) {
                response.put("success", false);
                response.put("message", "MCP agent is not available. Please check the service status.");
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
            }
            
            // Trigger the analysis
            CompletableFuture<PropertySearchResult> futureResult = mcpService.triggerSellerMarketAnalysis();
            
            // Wait for a short time to see if we get immediate results
            try {
                PropertySearchResult result = futureResult.get(3, TimeUnit.SECONDS);
                
                response.put("success", result.isSuccess());
                response.put("message", result.getMessage());
                
                if (result.getAnalysis() != null) {
                    response.put("totalProperties", result.getAnalysis().getTotalFound());
                    response.put("analysisTimestamp", result.getAnalysis().getTimestamp());
                    response.put("aiInsights", result.getAnalysis().getAiAnalysis());
                }
                
                return ResponseEntity.ok(response);
                
            } catch (java.util.concurrent.TimeoutException e) {
                // Analysis is taking longer, return accepted status
                response.put("success", true);
                response.put("message", "Market analysis started. Results will be available shortly.");
                response.put("status", "processing");
                
                return ResponseEntity.accepted().body(response);
            }
            
        } catch (Exception e) {
            logger.error("Error triggering seller market analysis", e);
            response.put("success", false);
            response.put("message", "Failed to start market analysis: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Trigger buyer property search via AJAX
     */
    @PostMapping("/trigger-buyer-search")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> triggerBuyerSearch() {
        logger.info("Triggering buyer property search");
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            if (!mcpService.isAgentAvailable()) {
                response.put("success", false);
                response.put("message", "MCP agent is not available. Please check the service status.");
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
            }
            
            CompletableFuture<PropertySearchResult> futureResult = mcpService.triggerBuyerPropertySearch();
            
            try {
                PropertySearchResult result = futureResult.get(3, TimeUnit.SECONDS);
                
                response.put("success", result.isSuccess());
                response.put("message", result.getMessage());
                
                if (result.getAnalysis() != null) {
                    response.put("totalProperties", result.getAnalysis().getTotalFound());
                    response.put("properties", result.getAnalysis().getProperties());
                }
                
                return ResponseEntity.ok(response);
                
            } catch (java.util.concurrent.TimeoutException e) {
                response.put("success", true);
                response.put("message", "Property search started. Results will be available shortly.");
                response.put("status", "processing");
                
                return ResponseEntity.accepted().body(response);
            }
            
        } catch (Exception e) {
            logger.error("Error triggering buyer property search", e);
            response.put("success", false);
            response.put("message", "Failed to start property search: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Custom property search with specific criteria
     */
    @PostMapping("/custom-search")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> customPropertySearch(@RequestBody PropertySearchCriteria criteria) {
        logger.info("Performing custom property search for location: {}", criteria.getLocation());
        
        Map<String, Object> response = new HashMap<>();
        
        try {
            if (!mcpService.isAgentAvailable()) {
                response.put("success", false);
                response.put("message", "MCP agent is not available. Please check the service status.");
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(response);
            }
            
            PropertySearchResult result = mcpService.searchWithCriteria(criteria);
            
            response.put("success", result.isSuccess());
            response.put("message", result.getMessage());
            
            if (result.getAnalysis() != null) {
                response.put("totalProperties", result.getAnalysis().getTotalFound());
                response.put("properties", result.getAnalysis().getProperties());
                response.put("aiAnalysis", result.getAnalysis().getAiAnalysis());
                response.put("timestamp", result.getAnalysis().getTimestamp());
            }
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error performing custom property search", e);
            response.put("success", false);
            response.put("message", "Custom search failed: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Get current MCP agent status via AJAX
     */
    @GetMapping("/agent-status")
    @ResponseBody
    public ResponseEntity<Map<String, Object>> getAgentStatus() {
        Map<String, Object> response = new HashMap<>();
        
        try {
            McpAgentStatus status = mcpService.getAgentStatus();
            boolean available = mcpService.isAgentAvailable();
            
            response.put("available", available);
            response.put("status", status.getStatus());
            response.put("message", status.getMessage());
            response.put("availableSources", status.getAvailableSources());
            response.put("timestamp", status.getTimestamp());
            
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting agent status", e);
            response.put("available", false);
            response.put("status", "error");
            response.put("message", "Failed to get agent status: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
        }
    }
    
    /**
     * Display market analysis results page
     */
    @GetMapping("/results")
    public String marketAnalysisResults(Model model, 
                                       @RequestParam(required = false) String type) {
        logger.info("Displaying market analysis results for type: {}", type);
        
        // Add navigation info
        model.addAttribute("pageTitle", "Market Analysis Results");
        model.addAttribute("activeSection", "property-analysis");
        model.addAttribute("analysisType", type != null ? type : "seller");
        
        // Get agent status for display
        McpAgentStatus agentStatus = mcpService.getAgentStatus();
        model.addAttribute("agentStatus", agentStatus);
        
        return "admin/property-analysis/results";
    }
    
    /**
     * Property search widget for embedding in other pages
     */
    @GetMapping("/widget")
    public String propertySearchWidget(Model model) {
        model.addAttribute("agentAvailable", mcpService.isAgentAvailable());
        return "admin/property-analysis/widget";
    }
}