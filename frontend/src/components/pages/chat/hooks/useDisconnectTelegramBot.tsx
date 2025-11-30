import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { disconnectTelegramBot } from '../requests';

export const useDisconnectTelegramBot = (agentId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (): Promise<void> => {
      await disconnectTelegramBot(agentId);
    },
    onSuccess: () => {
      toast.success('הבוט נותק בהצלחה מטלגרם');
      // עדכון cache
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      queryClient.setQueryData(['agent-telegram', agentId], null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.detail || 
                          'שגיאה בניתוק הבוט';
      toast.error(errorMessage);
    },
  });
};

