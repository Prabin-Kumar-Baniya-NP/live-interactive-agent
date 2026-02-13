'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  ReactNode,
} from 'react';
import {
  Room,
  RoomEvent,
  ConnectionQuality as SDKConnectionQuality,
  Participant,
  RoomOptions,
  DisconnectReason,
} from 'livekit-client';
import { ConnectionStatus, ParticipantInfo, ConnectionQuality } from '@/types';
import { createRoom, connectToRoom, disconnectFromRoom } from '@/services';
import { classifyConnectionError } from '@/utils';

export interface LiveKitContextType {
  room: Room | null;
  status: ConnectionStatus;
  roomName: string | null;
  participants: ParticipantInfo[];
  connectionQuality: ConnectionQuality;
  error: string | null;
  connect: (url: string, token: string, options?: RoomOptions) => Promise<void>;
  disconnect: () => Promise<void>;
}

const LiveKitContext = createContext<LiveKitContextType | undefined>(undefined);

interface LiveKitProviderProps {
  children: ReactNode;
}

export const LiveKitProvider: React.FC<LiveKitProviderProps> = ({
  children,
}) => {
  const roomRef = useRef<Room | null>(null);

  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [roomName, setRoomName] = useState<string | null>(null);
  const [participants, setParticipants] = useState<ParticipantInfo[]>([]);
  const [connectionQuality, setConnectionQuality] =
    useState<ConnectionQuality>('unknown');
  const [error, setError] = useState<string | null>(null);

  const calculateParticipants = (room: Room) => {
    const remoteParticipants = Array.from(room.remoteParticipants.values()).map(
      (p) => ({
        identity: p.identity,
        name: p.name,
        metadata: p.metadata,
        isLocal: false,
      })
    );

    const localParticipant = {
      identity: room.localParticipant.identity,
      name: room.localParticipant.name,
      metadata: room.localParticipant.metadata,
      isLocal: true,
    };

    return [localParticipant, ...remoteParticipants];
  };

  const updateParticipants = () => {
    if (roomRef.current) {
      setParticipants(calculateParticipants(roomRef.current));
    }
  };

  const mapConnectionQuality = (
    quality: SDKConnectionQuality
  ): ConnectionQuality => {
    switch (quality) {
      case SDKConnectionQuality.Excellent:
        return 'excellent';
      case SDKConnectionQuality.Good:
        return 'good';
      case SDKConnectionQuality.Poor:
        return 'poor';
      default:
        return 'unknown';
    }
  };

  const handleRoomEvents = (room: Room) => {
    room
      .on(RoomEvent.Connected, () => {
        setStatus('connected');
        setRoomName(room.name || null);
        updateParticipants();
      })
      .on(RoomEvent.Disconnected, (reason?: DisconnectReason) => {
        setStatus('disconnected');
        setParticipants([]);
        setRoomName(null);
        setConnectionQuality('unknown');

        if (reason === DisconnectReason.CLIENT_INITIATED) {
          // Intentional disconnect, no error
          return;
        }

        if (reason === DisconnectReason.DUPLICATE_IDENTITY) {
          setError('You have connected from another device.');
        } else if (reason === DisconnectReason.ROOM_DELETED) {
          setError('The room was deleted.');
        } else if (reason === DisconnectReason.PARTICIPANT_REMOVED) {
          setError('You were removed from the room.');
        } else {
          // Fallback for connection lost or failed reconnection
          setError('Connection lost. Please rejoin the session.');
        }
      })
      .on(RoomEvent.Reconnecting, () => {
        setStatus('reconnecting');
      })
      .on(RoomEvent.Reconnected, () => {
        setStatus('connected');
        updateParticipants();
        setError(null); // Clear error on reconnection (Task 23.9)
      })
      .on(RoomEvent.ParticipantConnected, () => {
        updateParticipants();
      })
      .on(RoomEvent.ParticipantDisconnected, () => {
        updateParticipants();
      })
      .on(
        RoomEvent.ConnectionQualityChanged,
        (quality: SDKConnectionQuality, participant: Participant) => {
          if (participant.isLocal) {
            setConnectionQuality(mapConnectionQuality(quality));
          }
        }
      );
  };

  const connect = async (url: string, token: string, options?: RoomOptions) => {
    setStatus('connecting');
    setError(null);
    try {
      if (!roomRef.current) {
        roomRef.current = createRoom(options);
        handleRoomEvents(roomRef.current);
      }

      const room = roomRef.current;
      await connectToRoom(room, url, token);

      setStatus('connected');
      setRoomName(room.name || null);
      updateParticipants();
    } catch (e: any) {
      console.error('Connection failed:', e);
      setStatus('disconnected');
      setError(classifyConnectionError(e));
    }
  };

  const disconnect = async () => {
    if (roomRef.current) {
      await disconnectFromRoom(roomRef.current);
      roomRef.current = null;
    }
    resetState();
  };

  const resetState = () => {
    setStatus('disconnected');
    setRoomName(null);
    setParticipants([]);
    setConnectionQuality('unknown');
    setError(null);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        disconnectFromRoom(roomRef.current).catch(console.error);
      }
    };
  }, []);

  return (
    <LiveKitContext.Provider
      value={{
        room: roomRef.current,
        status,
        roomName,
        participants,
        connectionQuality,
        error,
        connect,
        disconnect,
      }}
    >
      {children}
    </LiveKitContext.Provider>
  );
};

export const useLiveKit = () => {
  const context = useContext(LiveKitContext);
  if (context === undefined) {
    throw new Error('useLiveKit must be used within a LiveKitProvider');
  }
  return context;
};
