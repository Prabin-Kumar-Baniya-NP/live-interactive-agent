import sys

try:
    from livekit import agents  # noqa

    print("✅ livekit-agents imported successfully")
except ImportError as e:
    print(f"❌ Failed to import livekit-agents: {e}")
    sys.exit(1)
