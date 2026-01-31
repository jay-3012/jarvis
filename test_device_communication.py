#!/usr/bin/env python3
"""
Test Device Communication
Tests the Central Server API endpoints to verify device connectivity and command execution.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test the health check endpoint"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_devices():
    """Test listing all connected devices"""
    print_section("2. List Connected Devices")
    try:
        response = requests.get(f"{BASE_URL}/v1/devices")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Total Devices: {data.get('total', 0)}")
        print(f"\nDevices:")
        for device in data.get('devices', []):
            print(f"  - ID: {device['device_id']}")
            print(f"    Type: {device['device_type']}")
            print(f"    Status: {device['status']}")
            print(f"    Connected: {device['connected_at']}")
            print(f"    Last Ping: {device['last_ping']}")
            print()
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_execute_command(device_id="mac-agent-01"):
    """Test executing a command on a specific device"""
    print_section(f"3. Execute Command on {device_id}")
    try:
        payload = {
            "device_id": device_id,
            "command": {
                "type": "system_info",
                "action": "get_info"
            }
        }
        print(f"Sending command: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{BASE_URL}/v1/commands/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ping_device(device_id="mac-agent-01"):
    """Test pinging a specific device"""
    print_section(f"4. Ping Device {device_id}")
    try:
        payload = {
            "device_id": device_id,
            "command": {
                "type": "ping"
            }
        }
        print(f"Sending ping to {device_id}...")
        response = requests.post(
            f"{BASE_URL}/v1/commands/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_file_list(device_id="mac-agent-01"):
    """Test listing files on a specific device"""
    print_section(f"5. List Files on {device_id}")
    try:
        payload = {
            "device_id": device_id,
            "command": {
                "type": "file_list",
                "path": "~"
            }
        }
        print(f"Requesting file list from {device_id}...")
        response = requests.post(
            f"{BASE_URL}/v1/commands/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  JARVIS DEVICE COMMUNICATION TEST SUITE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    results.append(("List Devices", test_list_devices()))
    time.sleep(0.5)
    
    results.append(("Execute Command", test_execute_command()))
    time.sleep(0.5)
    
    results.append(("Ping Device", test_ping_device()))
    time.sleep(0.5)
    
    results.append(("List Files", test_file_list()))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Device communication is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
