import os

from dotenv import load_dotenv


def validate_env():
    load_dotenv()

    required = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]

    missing = []
    print("Checking LiveKit environment variables for Agent Runtime...")
    for key in required:
        val = os.getenv(key)
        if not val:
            missing.append(key)
        else:
            print(f"✅ {key} is set.")

    if missing:
        print(f"❌ Missing required environment variables: {', '.join(missing)}")
        exit(1)

    print("✅ All LiveKit env variables are configured correctly for Agent Runtime.")


if __name__ == "__main__":
    validate_env()
