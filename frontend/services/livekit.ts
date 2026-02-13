import { Room, RoomOptions } from 'livekit-client';

/**
 * Creates a new Room instance with default options.
 * @returns {Room} A configured Room instance.
 */
export const createRoom = (options?: RoomOptions): Room => {
  return new Room({
    adaptiveStream: true,
    dynacast: true,
    ...options,
  });
};

/**
 * Connects a room instance to the LiveKit server.
 * @param {Room} room - The Room instance to connect.
 * @param {string} url - The LiveKit server URL.
 * @param {string} token - The access token.
 * @returns {Promise<void>}
 * @throws {Error} If connection fails.
 */
export const connectToRoom = async (
  room: Room,
  url: string,
  token: string
): Promise<void> => {
  try {
    await room.connect(url, token);
  } catch (error) {
    console.error('Failed to connect to room:', error);
    throw new Error(
      `Failed to connect to LiveKit room: ${
        (error as Error).message || String(error)
      }`
    );
  }
};

/**
 * Disconnects a room instance and cleans up.
 * @param {Room} room - The Room instance to disconnect.
 * @returns {Promise<void>}
 */
export const disconnectFromRoom = async (room: Room): Promise<void> => {
  try {
    await room.disconnect();
    room.removeAllListeners();
  } catch (error) {
    console.warn('Error disconnecting from room:', error);
    // Do not throw, just log.
  }
};
