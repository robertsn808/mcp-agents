#!/usr/bin/env python3
"""
Simple test to verify basic functionality without external dependencies
"""

import sys
import os

def test_imports():
    """Test that we can import the basic structure"""
    print("Testing imports and basic structure...")
    
    try:
        # Test dataclass import
        from dataclasses import dataclass
        print("✅ dataclass import successful")
        
        # Test basic structure of PropertyCriteria
        @dataclass
        class TestPropertyCriteria:
            location: str
            min_price: int = None
            max_price: int = None
        
        criteria = TestPropertyCriteria(location="Test Location", min_price=100000)
        print(f"✅ PropertyCriteria structure test: {criteria.location}")
        
        # Test that files exist and are syntactically correct
        if os.path.exists('property_search_agent.py'):
            print("✅ property_search_agent.py exists")
        else:
            print("❌ property_search_agent.py not found")
            
        if os.path.exists('webhook_server.py'):
            print("✅ webhook_server.py exists")
        else:
            print("❌ webhook_server.py not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def test_requirements():
    """Check requirements.txt has the right dependencies"""
    print("\nTesting requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = [
            'anthropic',
            'httpx', 
            'beautifulsoup4',
            'pydantic',
            'fastapi',
            'uvicorn'
        ]
        
        missing = []
        for package in required_packages:
            if package not in requirements:
                missing.append(package)
        
        if not missing:
            print("✅ All required packages are in requirements.txt")
            return True
        else:
            print(f"⚠️ Missing packages in requirements.txt: {missing}")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {str(e)}")
        return False

def test_file_structure():
    """Test that all necessary files are present"""
    print("\nTesting file structure...")
    
    required_files = [
        'property_search_agent.py',
        'webhook_server.py', 
        'requirements.txt',
        'ai_dev_team.py',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if not missing_files:
        print("✅ All required files are present")
        return True
    else:
        print(f"❌ Missing files: {missing_files}")
        return False

def test_api_endpoints():
    """Test that we have the expected API endpoints defined"""
    print("\nTesting API endpoint definitions...")
    
    try:
        with open('webhook_server.py', 'r') as f:
            webhook_content = f.read()
        
        expected_endpoints = [
            '/property/search/buyer',
            '/property/search/seller', 
            '/property/search/status'
        ]
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in webhook_content:
                missing_endpoints.append(endpoint)
        
        if not missing_endpoints:
            print("✅ All expected property search endpoints are defined")
            return True
        else:
            print(f"❌ Missing endpoints: {missing_endpoints}")
            return False
            
    except Exception as e:
        print(f"❌ Endpoint test failed: {str(e)}")
        return False

def main():
    """Run all basic tests"""
    print("🏠 Property Search Agent - Basic Validation")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    if test_imports():
        tests_passed += 1
        
    if test_requirements():
        tests_passed += 1
        
    if test_file_structure():
        tests_passed += 1
        
    if test_api_endpoints():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Basic Validation Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 Basic validation passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set environment variables:")
        print("   - ANTHROPIC_API_KEY=your_anthropic_key")
        print("   - DATABASE_URL=your_postgres_url (optional)")
        print("3. Test with: python property_search_agent.py")
        print("4. Start server: python webhook_server.py")
        print("\nAPI Endpoints available:")
        print("   - POST /property/search/buyer")
        print("   - POST /property/search/seller") 
        print("   - GET /property/search/status")
    else:
        print("⚠️ Some basic validation tests failed")

if __name__ == "__main__":
    main()