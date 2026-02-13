import { useLiveKit } from '@/hooks/useLiveKit';
import { ConnectionStatus } from '@/types';

export const useConnectionStatus = () => {
  const { status, error } = useLiveKit();

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isReconnecting: status === 'reconnecting',
    isDisconnected: status === 'disconnected',
    error,
  };
};
