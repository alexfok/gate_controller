#!/usr/bin/env python3
"""Test script for BCG04 external token detection endpoint.

This script simulates a BCG04 gateway calling the token detection API.
"""

import asyncio
import httpx
import sys

# Configuration
CONTROLLER_URL = "http://192.168.100.185:8000"  # Change to your RPI IP
# CONTROLLER_URL = "http://localhost:8000"  # For local testing

# Test tokens (use your actual UUIDs)
TEST_TOKENS = [
    {
        "uuid": "426c7565-4368-6172-6d42-6561636f6e67",
        "name": "BCPro_Alex",
        "rssi": -45,
        "distance": 0.5
    },
    {
        "uuid": "426c7565-4368-6172-6d42-6561636f6e98",
        "name": "BCPro_Yuval",
        "rssi": -52,
        "distance": 1.2
    },
]


async def test_token_detected():
    """Test the /api/token/detected endpoint."""
    
    print("=" * 60)
    print("BCG04 Token Detection Endpoint Test")
    print("=" * 60)
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: GET - Valid token with all fields
        print("Test 1: GET - Valid token (all fields)")
        print("-" * 60)
        try:
            params = {
                "uuid": TEST_TOKENS[0]["uuid"],
                "rssi": TEST_TOKENS[0]["rssi"],
                "distance": TEST_TOKENS[0]["distance"]
            }
            response = await client.get(
                f"{CONTROLLER_URL}/api/token/detected",
                params=params
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 2: GET - Valid token (UUID only)
        print("Test 2: GET - Valid token (UUID only)")
        print("-" * 60)
        try:
            response = await client.get(
                f"{CONTROLLER_URL}/api/token/detected",
                params={"uuid": TEST_TOKENS[0]["uuid"]}
            )
            print(f"URL: {response.url}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 3: POST - Valid token with all fields
        print("Test 3: POST - Valid token (all fields)")
        print("-" * 60)
        try:
            response = await client.post(
                f"{CONTROLLER_URL}/api/token/detected",
                json=TEST_TOKENS[0]
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 3: Unregistered token
        print("Test 3: Unregistered token (should be ignored)")
        print("-" * 60)
        try:
            response = await client.post(
                f"{CONTROLLER_URL}/api/token/detected",
                json={"uuid": "00000000-0000-0000-0000-000000000000"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 4: Missing UUID
        print("Test 4: Missing UUID (should fail)")
        print("-" * 60)
        try:
            response = await client.post(
                f"{CONTROLLER_URL}/api/token/detected",
                json={"name": "Test"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
        
        # Test 5: Get activity log to verify
        print("Test 5: Check activity log")
        print("-" * 60)
        try:
            response = await client.get(f"{CONTROLLER_URL}/api/activity?limit=5")
            print(f"Status: {response.status_code}")
            data = response.json()
            print(f"Recent activity entries:")
            for entry in data.get('activity', [])[:3]:
                print(f"  - {entry.get('timestamp')}: {entry.get('event_type')} - {entry.get('description')}")
            print()
        except Exception as e:
            print(f"Error: {e}")
            print()
    
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


async def simulate_bcg04_detection():
    """Simulate BCG04 detecting a token."""
    
    print("\n" + "=" * 60)
    print("Simulating BCG04 Detection")
    print("=" * 60)
    
    token = TEST_TOKENS[0]
    print(f"Token: {token['name']} ({token['uuid']})")
    print(f"RSSI: {token['rssi']} dBm")
    print(f"Distance: ~{token['distance']}m")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{CONTROLLER_URL}/api/token/detected",
            json=token
        )
        
        result = response.json()
        if result.get('success'):
            print(f"✅ {result.get('message')}")
            print(f"   Token: {result.get('token')}")
            print(f"   Action: {result.get('action')}")
        else:
            print(f"❌ {result.get('message')}")
            print(f"   Action: {result.get('action')}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "simulate":
        # Simulate a single detection
        asyncio.run(simulate_bcg04_detection())
    else:
        # Run full test suite
        asyncio.run(test_token_detected())

