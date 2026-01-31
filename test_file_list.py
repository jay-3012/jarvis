import requests
import json
import time

BASE_URL = "http://localhost:8000"
DEVICE_ID = "mac-agent-01"

def test_file_list():
    print(f"Testing File List on {DEVICE_ID}...")
    
    payload = {
        "device_id": DEVICE_ID,
        "action": "file_list",
        "params": {
            "path": "~"  # Home directory
        }
    }
    
    try:
        # 1. Send Command
        response = requests.post(
            f"{BASE_URL}/v1/commands/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Command Sent Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code != 200:
            print("❌ Failed to send command")
            return

        command_id = response.json()["command_id"]
        print(f"Command ID: {command_id}")
        
        # 2. In a real scenario, we would listen to WebSocket for the response.
        # Since we are just testing the API here, we can't easily see the async response 
        # unless we hook into the websocket or check logs/db.
        # For now, if the command sends successfully 200, it means the agent received it.
        # The Agent logs will show the actual file list execution.
        
        print("\n✅ Command sent successfully!")
        print("Check the Agent logs to see if it lists the files.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_file_list()
