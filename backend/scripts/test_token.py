import os
import sys

from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
    print("Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")
    sys.exit(1)

try:
    from livekit import api
except ImportError:
    print(
        """
        Error: livekit-api not installed.
        Please run `poetry add livekit-api` in backend dir.
        """
    )
    sys.exit(1)

token = (
    api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    .with_identity("test-user")
    .with_name("Test User")
    .with_grants(api.VideoGrants(room_join=True, room="test-room"))
    .to_jwt()
)

print(f"Generated LiveKit Token:\n{token}")
