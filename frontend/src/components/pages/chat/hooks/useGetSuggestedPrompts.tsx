import { useMutation } from '@tanstack/react-query';
import { useEffect } from 'react';
import { toast } from 'react-toastify';
import { getSuggestedPrompts } from '../requests';
import type { SuggestedPromptsPayload, SuggestedPromptsResponse } from '../types';
import type { AxiosError } from 'axios';
import type { Agent, Message } from '../types';

interface ErrorResponse {
  message: string;
}

export const useGetSuggestedPrompts = (messages: Message[], agent?: Agent) => {
  const { mutate, mutateAsync, isPending, isSuccess, isError, error, data, reset } = useMutation<
    SuggestedPromptsResponse,
    AxiosError<ErrorResponse>,
    SuggestedPromptsPayload
  >({
    mutationFn: (payload) => getSuggestedPrompts(payload),
    onSuccess: () => {},
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'שגיאה בקבלת הצעות פרומפטים';
      console.error('❌ שגיאה בקבלת הצעות פרומפטים:', message);
      toast.error(message);
    },
  });

  // כאשר משתמש שולח הודעה, נבקש הצעות לפרומפט הבא
  useEffect(() => {
    const fetchSuggestions = async () => {
      // אם יש הודעות ואנחנו לא בטעינה
      if (messages.length > 0 && agent) {
        // מצא את ההודעה האחרונה מהמשתמש
        const lastUserMessage = [...messages]
          .reverse()
          .find(msg => msg.role === 'user');
        
        if (lastUserMessage) {
          try {
            // המרת app_connections מ-string ל-array
            let appConnections: string[] = [];
            if (agent.app_connections) {
              try {
                // אם זה כבר array, השתמש בו, אחרת parse
                if (Array.isArray(agent.app_connections)) {
                  appConnections = agent.app_connections;
                } else if (typeof agent.app_connections === 'string') {
                  appConnections = JSON.parse(agent.app_connections);
                }
              } catch {
                appConnections = [];
              }
            }
            
            // קריאה להצעות פרומפטים
            await mutateAsync({
              prompt: lastUserMessage.content,
              app_connections: appConnections
            });
          } catch (error) {
            console.error('שגיאה בקבלת הצעות פרומפטים:', error);
          }
        }
      }
    };
    
    fetchSuggestions();
  }, [messages, agent, mutateAsync]);

  return {
    // Functions
    getSuggestedPrompts: mutate,
    getSuggestedPromptsAsync: mutateAsync,
    
    // Status
    isLoading: isPending,
    isSuccess,
    isError,
    error,
    suggestedPrompts: data?.suggested_prompts || [],
    reset,
  };
};

