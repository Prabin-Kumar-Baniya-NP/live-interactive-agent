export const config = {
  livekitUrl: process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880',
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
} as const;

if (!process.env.NEXT_PUBLIC_LIVEKIT_URL) {
  console.warn(
    'Warning: NEXT_PUBLIC_LIVEKIT_URL is not defined in environment variables. Using default: ws://localhost:7880'
  );
}

if (!process.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    'Warning: NEXT_PUBLIC_API_URL is not defined in environment variables. Using default: http://localhost:8000/api/v1'
  );
}
