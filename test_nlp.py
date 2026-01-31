import requests
import json
import time

BASE_URL = "http://localhost:8000"

def chat(text):
    print(f"\nUser: {text}")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/conversations/chat",
            json={"speaker": "user", "content": text},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Jarvis: {data['content']}")
            if data.get('data'):
                print(f"Data: {json.dumps(data['data'], indent=2)}")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def main():
    print("🤖 Jarvis NLP Test Interface")
    print("============================")
    
    # Test 1: Device Status
    chat("Which of my devices are online?")
    
    time.sleep(1)
    
    # Test 2: File Search (specific device)
    chat("Search for secret_plans.txt on mac")
    
    time.sleep(1)

    # Test 3: File Search (ambiguous - should default/ask)
    chat("Find my resume.pdf")

if __name__ == "__main__":
    main()
