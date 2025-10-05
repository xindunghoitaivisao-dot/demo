#!/usr/bin/env python3
"""
Backend API Testing Script
Tests the backend endpoints as specified in test_result.md
"""

import requests
import json
import sys
from typing import Dict, Any

# Backend URL - testing locally since we're in the same container
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"

def test_health_endpoint():
    """Test GET /api/ health endpoint"""
    print("Testing GET /api/ (health endpoint)...")
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected status 200, got {response.status_code}")
            return False
            
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check required keys
            if "message" not in data:
                print("❌ FAILED: Missing 'message' key in response")
                return False
                
            if "status" not in data:
                print("❌ FAILED: Missing 'status' key in response")
                return False
                
            print("✅ PASSED: Health endpoint working correctly")
            return True
            
        except json.JSONDecodeError:
            print("❌ FAILED: Response is not valid JSON")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {str(e)}")
        return False

def test_landing_endpoint():
    """Test GET /api/landing endpoint"""
    print("\nTesting GET /api/landing...")
    
    try:
        response = requests.get(f"{API_BASE}/landing", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAILED: Expected status 200, got {response.status_code}")
            return False
            
        try:
            data = response.json()
            
            # Check required top-level keys
            required_keys = ["hero", "approach", "pillars", "solutions", "logos", "stats", "blogPosts"]
            missing_keys = []
            
            for key in required_keys:
                if key not in data:
                    missing_keys.append(key)
            
            if missing_keys:
                print(f"❌ FAILED: Missing required keys: {missing_keys}")
                return False
            
            # Check array lengths
            checks = [
                ("pillars", 3),
                ("solutions", 6), 
                ("logos", 6),
                ("stats", 4),
                ("blogPosts", 3)
            ]
            
            for key, expected_length in checks:
                if not isinstance(data[key], list):
                    print(f"❌ FAILED: {key} is not a list")
                    return False
                    
                actual_length = len(data[key])
                if actual_length != expected_length:
                    print(f"❌ FAILED: {key} has length {actual_length}, expected {expected_length}")
                    return False
            
            print("✅ PASSED: Landing endpoint structure is correct")
            print(f"  - hero: {type(data['hero']).__name__}")
            print(f"  - approach: {type(data['approach']).__name__}")
            print(f"  - pillars: {len(data['pillars'])} items")
            print(f"  - solutions: {len(data['solutions'])} items")
            print(f"  - logos: {len(data['logos'])} items")
            print(f"  - stats: {len(data['stats'])} items")
            print(f"  - blogPosts: {len(data['blogPosts'])} items")
            
            return True
            
        except json.JSONDecodeError:
            print("❌ FAILED: Response is not valid JSON")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error - {str(e)}")
        return False

def test_no_auth_required():
    """Test that endpoints work without authentication when DB is missing"""
    print("\nTesting endpoints work without authentication...")
    
    # Test both endpoints without any auth headers
    endpoints = [
        ("/", "health"),
        ("/landing", "landing")
    ]
    
    all_passed = True
    
    for endpoint, name in endpoints:
        try:
            # Make request without any authentication
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ PASSED: {name} endpoint accessible without auth")
            else:
                print(f"❌ FAILED: {name} endpoint returned {response.status_code} (should be 200)")
                all_passed = False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: {name} endpoint request error - {str(e)}")
            all_passed = False
    
    return all_passed

def main():
    """Run all backend tests"""
    print("=" * 60)
    print("BACKEND API TESTING")
    print("=" * 60)
    print(f"Testing against: {API_BASE}")
    print()
    
    results = []
    
    # Test health endpoint
    results.append(("Health Endpoint", test_health_endpoint()))
    
    # Test landing endpoint  
    results.append(("Landing Endpoint", test_landing_endpoint()))
    
    # Test no auth required
    results.append(("No Auth Required", test_no_auth_required()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend tests PASSED!")
        return 0
    else:
        print("⚠️  Some backend tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(main())