import { useLiveKit } from '@/hooks/useLiveKit';

export const useConnectionQuality = () => {
  const { connectionQuality } = useLiveKit();

  const isGoodConnection =
    connectionQuality === 'excellent' || connectionQuality === 'good';

  return {
    quality: connectionQuality,
    isGoodConnection,
  };
};
