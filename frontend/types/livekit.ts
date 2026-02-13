import { RoomConnectOptions } from 'livekit-client';

export type ConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting';

export interface RoomConnectionConfig {
  url: string;
  token: string;
  options?: RoomConnectOptions;
}

export interface ParticipantInfo {
  identity: string;
  name?: string;
  metadata?: string;
  isLocal: boolean;
}

export type ConnectionQuality = 'excellent' | 'good' | 'poor' | 'unknown';

export interface RoomState {
  status: ConnectionStatus;
  roomName: string | null;
  participants: ParticipantInfo[];
  connectionQuality: ConnectionQuality;
  error: string | null;
}
