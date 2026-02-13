import { useLiveKit } from '@/hooks/useLiveKit';
import { ParticipantInfo } from '@/types';

export const useParticipants = () => {
  const { participants } = useLiveKit();

  const localParticipant = participants.find((p) => p.isLocal) || null;
  const remoteParticipants = participants.filter((p) => !p.isLocal);

  return {
    participants,
    localParticipant,
    remoteParticipants,
    participantCount: participants.length,
  };
};
