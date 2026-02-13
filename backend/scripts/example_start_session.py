import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("API_KEY", "your_api_key_here")  # Or auth token from login
TEMPLATE_ID = os.getenv("TEMPLATE_ID", "your_template_id_here")
USER_ID = "user_123"


def start_session():
    url = f"{API_URL}/sessions/start"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"session_template_id": TEMPLATE_ID, "user_id": USER_ID}

    print(f"Sending POST request to {url}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print("\nSession create successful!")
        print(f"Session ID: {data.get('session_id')}")
        print(f"Room Name: {data.get('room_name')}")
        print(f"LiveKit URL: {data.get('livekit_url')}")
        print(f"Access Token: {data.get('access_token')[:20]}...")
        # Now use livekit-client/sdk to connect
    else:
        print(f"\nError: {response.status_code}")
        print(f"Response: {response.text}")


if __name__ == "__main__":
    start_session()
