import { useMutation } from '@tanstack/react-query';
// import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { createAgent } from '../requests';
import type { CreateAgentPayload, CreateAgentResponse } from '../types';
import type { AxiosError } from 'axios';

interface ErrorResponse {
  message: string;
}

export const useCreateAgent = () => {
  // const navigate = useNavigate();

  const mutation = useMutation<CreateAgentResponse, AxiosError<ErrorResponse>, CreateAgentPayload>({
    mutationFn: createAgent,
    onSuccess: (data) => {
      console.log('✅ Agent נוצר בהצלחה:', data);
      toast.success('האייג\'נט נוצר בהצלחה!');
      
      // ניווט לדף המתאים (למשל agents או chat)
      // navigate('/agents');
      // או
      // navigate(`/chat/${data.id}`);
    },
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'שגיאה ביצירת האייג\'נט';
      console.error('❌ שגיאה ביצירת agent:', message);
      toast.error(message);
    },
  });

  const handleCreate = (prompt: string) => {
    if (!prompt.trim()) {
      return;
    }
    
    mutation.mutate({ prompt });
  };

  return {
    createAgent: mutation.mutate,
    createAgentAsync: mutation.mutateAsync,
    handleCreate,
    isCreating: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    data: mutation.data,
    reset: mutation.reset,
  };
};

