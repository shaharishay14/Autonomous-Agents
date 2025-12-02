import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { createManualAgent } from '../requests';
import type { AxiosError } from 'axios';
import type { Agent, CreateManualAgentPayload } from '../types';

interface ErrorResponse {
  message: string;
  errors?: Record<string, string[]>;
}

export const useCreateManualAgent = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { mutate, mutateAsync, isPending, isSuccess, isError, error, data } = useMutation<
    Agent,
    AxiosError<ErrorResponse>,
    CreateManualAgentPayload
  >({
    mutationFn: createManualAgent,
    onMutate: () => {
      // ניווט לדף טעינה כשה-mutation מתחיל
      navigate('/agent-loading');
    },
    onSuccess: (data) => {
      console.log('✅ סוכן נוצר בהצלחה:', data);
      toast.success('האייג\'נט נוצר בהצלחה! 🎉');
      
      // שמירת מידע האייג'נט ב-sessionStorage עבור דף הסיכום
      sessionStorage.setItem('newAgentData', JSON.stringify(data));
      
      // רענון רשימת ה-agents
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      
      // ניווט לדף הסיכום
      navigate('/agent-summary');
    },
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'שגיאה ביצירת האייג\'נט';
      const errors = error.response?.data?.errors;
      
      console.error('❌ שגיאה ביצירת agent:', { message, errors });
      
      // הצגת שגיאות ספציפיות אם קיימות
      if (errors) {
        Object.entries(errors).forEach(([field, messages]) => {
          messages.forEach(msg => toast.error(`${field}: ${msg}`));
        });
      } else {
        toast.error(message);
      }
      
      // ניווט חזרה לבנאי במקרה של שגיאה
      navigate('/builder');
    },
  });

  return {
    createManualAgent: mutate,
    createManualAgentAsync: mutateAsync,
    isCreating: isPending,
    isSuccess,
    isError,
    error,
    createdAgent: data,
  };
};

