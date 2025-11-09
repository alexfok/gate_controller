#!/usr/bin/env python3
"""
Test script for new backend API endpoints.
Tests the Phase 5 enhancements: active attribute, edit token, and full scan.
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8888"  # Change to your test server URL

def test_get_tokens():
    """Test getting all registered tokens."""
    print("\n📋 Testing GET /api/tokens...")
    response = requests.get(f"{BASE_URL}/api/tokens")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Tokens: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_full_scan():
    """Test full device scan."""
    print("\n🔍 Testing GET /api/scan/all...")
    print("Scanning for 5 seconds...")
    response = requests.get(f"{BASE_URL}/api/scan/all?duration=5")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data.get('ibeacons', []))} iBeacons")
    print(f"Found {len(data.get('devices', []))} regular devices")
    print(f"Total: {data.get('total', 0)} devices")
    
    # Show first 3 iBeacons
    if data.get('ibeacons'):
        print("\nSample iBeacons:")
        for beacon in data['ibeacons'][:3]:
            print(f"  - {beacon['name']}: {beacon['uuid']}")
    
    return response.status_code == 200

def test_register_token():
    """Test registering a new token with active attribute."""
    print("\n➕ Testing POST /api/tokens (with active=True)...")
    payload = {
        "uuid": "test-beacon-12345",
        "name": "Test Beacon",
        "active": True
    }
    response = requests.post(f"{BASE_URL}/api/tokens", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_update_token():
    """Test updating a token's attributes."""
    print("\n✏️  Testing PATCH /api/tokens/{uuid}...")
    
    # Update name
    print("  Updating name...")
    payload = {"name": "Test Beacon (Updated)"}
    response = requests.patch(f"{BASE_URL}/api/tokens/test-beacon-12345", json=payload)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    # Toggle active to False
    print("  Setting active=False...")
    payload = {"active": False}
    response = requests.patch(f"{BASE_URL}/api/tokens/test-beacon-12345", json=payload)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    # Toggle back to True
    print("  Setting active=True...")
    payload = {"active": True}
    response = requests.patch(f"{BASE_URL}/api/tokens/test-beacon-12345", json=payload)
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    
    return response.status_code == 200

def test_delete_token():
    """Test deleting the test token."""
    print("\n🗑️  Testing DELETE /api/tokens/{uuid}...")
    response = requests.delete(f"{BASE_URL}/api/tokens/test-beacon-12345")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def main():
    """Run all tests."""
    print("=" * 60)
    print("Backend API Test Suite - Phase 5 Enhancements")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    
    tests = [
        ("Get Tokens", test_get_tokens),
        ("Full Scan", test_full_scan),
        ("Register Token", test_register_token),
        ("Update Token", test_update_token),
        ("Delete Token", test_delete_token),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Error: Cannot connect to {BASE_URL}")
            print("Make sure the server is running:")
            print("  python3 -m gate_controller.web_main --config config/config.yaml --host 127.0.0.1 --port 8888")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()

