#!/bin/bash

# Generates a LiveKit access token using the LiveKit CLI (lk).
# Requires LIVEKIT_API_KEY and LIVEKIT_API_SECRET to be set in environment or arguments.

# Load .env if it exists
if [ -f .env ]; then
  # Use grep to filter out comments and empty lines
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$LIVEKIT_API_KEY" ] || [ -z "$LIVEKIT_API_SECRET" ]; then
  echo "Error: LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set."
  echo "Please create a .env file or export these variables."
  exit 1
fi

if ! command -v lk &> /dev/null; then
    echo "Error: livekit-cli (lk) is not installed."
    echo "Please install it: curl -sSL https://get.livekit.io/cli | bash"
    exit 1
fi

echo "Generating token for room: test-room, identity: test-user..."

lk token create \
    --api-key $LIVEKIT_API_KEY \
    --api-secret $LIVEKIT_API_SECRET \
    --join --room test-room --identity test-user \
    --valid-for 24h
