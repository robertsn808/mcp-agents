#!/usr/bin/env python3
"""
Test script for property search agent
"""

import asyncio
import json
import os
from property_search_agent import PropertySearchAgent, PropertyCriteria

async def test_property_search():
    """Test the property search functionality"""
    print("Testing Property Search Agent...")
    
    # Create test criteria
    test_criteria = PropertyCriteria(
        location="San Francisco, CA",
        min_price=500000,
        max_price=1200000,
        bedrooms=2,
        bathrooms=2,
        property_type="condo",
        keywords=["downtown", "view"]
    )
    
    print(f"Search criteria: {test_criteria}")
    
    # Initialize agent
    agent = PropertySearchAgent()
    
    try:
        # Test property search
        print("\n1. Testing property search...")
        search_result = await agent.search_properties(test_criteria)
        
        print(f"Search completed:")
        print(f"  - Total properties found: {search_result.total_found}")
        print(f"  - Sources searched: {search_result.sources_searched}")
        print(f"  - Search timestamp: {search_result.search_timestamp}")
        
        if search_result.properties:
            print(f"  - First property: {search_result.properties[0]['address']}")
        
        # Test AI analysis (only if we have properties and API key)
        if search_result.properties and os.getenv('ANTHROPIC_API_KEY'):
            print("\n2. Testing AI analysis...")
            analysis_result = await agent.analyze_properties_with_ai(search_result)
            
            if 'ai_analysis' in analysis_result:
                print(f"  - AI analysis completed successfully")
                if isinstance(analysis_result['ai_analysis'], dict):
                    if 'analysis' in analysis_result['ai_analysis']:
                        print(f"  - Analysis preview: {analysis_result['ai_analysis']['analysis'][:100]}...")
                else:
                    print(f"  - Analysis: {str(analysis_result['ai_analysis'])[:100]}...")
            else:
                print(f"  - Analysis error: {analysis_result.get('error', 'Unknown error')}")
        else:
            if not os.getenv('ANTHROPIC_API_KEY'):
                print("\n2. Skipping AI analysis (no ANTHROPIC_API_KEY)")
            else:
                print("\n2. Skipping AI analysis (no properties found)")
        
        print("\n✅ Property search test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in property search test: {str(e)}")
        return False

async def test_realconnect_integration():
    """Test integration with realconnect.online endpoints"""
    print("\nTesting RealConnect Integration...")
    
    agent = PropertySearchAgent()
    
    try:
        # Test buyer criteria fetch
        print("1. Testing buyer criteria fetch...")
        buyer_criteria = await agent.get_buyer_criteria()
        
        if buyer_criteria:
            print(f"   ✅ Buyer criteria fetched: {buyer_criteria.location}")
        else:
            print(f"   ⚠️  Could not fetch buyer criteria (endpoint may be unavailable)")
        
        # Test seller criteria fetch
        print("2. Testing seller criteria fetch...")
        seller_criteria = await agent.get_seller_criteria()
        
        if seller_criteria:
            print(f"   ✅ Seller criteria fetched: {seller_criteria.location}")
        else:
            print(f"   ⚠️  Could not fetch seller criteria (endpoint may be unavailable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in RealConnect integration test: {str(e)}")
        return False

def test_data_models():
    """Test data model creation and serialization"""
    print("\nTesting Data Models...")
    
    try:
        # Test PropertyCriteria
        criteria = PropertyCriteria(
            location="Test City, CA",
            min_price=400000,
            max_price=800000,
            bedrooms=3,
            bathrooms=2.5
        )
        print(f"✅ PropertyCriteria created: {criteria.location}")
        
        # Test Property (from dataclass)
        from property_search_agent import Property
        
        test_property = Property(
            id="test123",
            address="123 Test St",
            city="Test City",
            state="CA",
            zip_code="12345",
            price=600000,
            bedrooms=3,
            bathrooms=2.5,
            square_feet=1800,
            lot_size=0.2,
            property_type="house",
            listing_url="https://test.com/listing",
            image_urls=["https://test.com/image.jpg"],
            description="Test property description",
            listing_date="2024-01-01",
            source="test"
        )
        print(f"✅ Property created: {test_property.address}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data model test: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🏠 Property Search Agent Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test data models
    if test_data_models():
        tests_passed += 1
    
    # Test property search
    if await test_property_search():
        tests_passed += 1
    
    # Test RealConnect integration
    if await test_realconnect_integration():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed or had warnings")
    
    print("\nNext steps:")
    print("1. Set ANTHROPIC_API_KEY environment variable for AI analysis")
    print("2. Ensure realconnect.online endpoints are accessible")
    print("3. Update scraper implementations for real-world usage")
    print("4. Deploy with: python webhook_server.py")

if __name__ == "__main__":
    asyncio.run(main())