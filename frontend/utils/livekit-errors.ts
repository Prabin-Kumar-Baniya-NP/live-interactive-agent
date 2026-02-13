export const isTokenError = (error: unknown): boolean => {
  const message = error instanceof Error ? error.message : String(error);
  return (
    message.toLowerCase().includes('token') ||
    message.toLowerCase().includes('authorization') ||
    message.toLowerCase().includes('expired')
  );
};

export const classifyConnectionError = (error: unknown): string => {
  const message = error instanceof Error ? error.message : String(error);
  const lowerMessage = message.toLowerCase();

  if (isTokenError(error)) {
    return 'Session token is invalid or expired. Please start a new session.';
  }

  if (
    lowerMessage.includes('network') ||
    lowerMessage.includes('timeout') ||
    lowerMessage.includes('refused') ||
    lowerMessage.includes('failed to fetch')
  ) {
    return 'Unable to connect to the server. Please check your network connection.';
  }

  if (
    lowerMessage.includes('unavailable') ||
    lowerMessage.includes('server') ||
    lowerMessage.includes('500') ||
    lowerMessage.includes('bad gateway')
  ) {
    return 'The server is currently unavailable. Please try again later.';
  }

  return message;
};
