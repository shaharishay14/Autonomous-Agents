import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { sendMessage } from '../requests';
import type { SendMessagePayload, SendMessageResponse, Message } from '../types';
import type { AxiosError } from 'axios';

interface ErrorResponse {
  message: string;
}

export const useSendMessage = (agentId: string) => {
  const queryClient = useQueryClient();
  const [messageText, setMessageText] = useState('');

  const { mutate, mutateAsync, isPending, isSuccess, isError, error, data, reset } = useMutation<SendMessageResponse, AxiosError<ErrorResponse>, SendMessagePayload>({
    mutationFn: (payload) => sendMessage(agentId, payload),
    onSuccess: (data) => {
      console.log('✅ הודעה נשלחה בהצלחה:', data);
      
      // עדכון הודעות בקאש
      queryClient.setQueryData<Message[]>(['agent-messages', agentId], (oldMessages = []) => {
        return [...oldMessages, data.user_message, data.assistant_message];
      });
      
      // עדכון מספר ההודעות של האייג'נט
      queryClient.invalidateQueries({ queryKey: ['agent', agentId] });
      
      // ניקוי השדה אחרי שליחה מוצלחת
      setMessageText('');
    },
    onError: (error) => {
      const message = error.response?.data?.message || error.message || 'שגיאה בשליחת ההודעה';
      console.error('❌ שגיאה בשליחת הודעה:', message);
      toast.error(message);
    },
  });

  const handleSendMessage = (message: string, fileIds: number[] = []) => {
    if (!message.trim()) {
      return;
    }
    
    mutate({ message, file_ids: fileIds });
  };

  // פונקציה לשליחת הודעה
  const onSendMessage = () => {
    if (!messageText.trim() || isPending) return;
    
    handleSendMessage(messageText);
  };

  // טיפול ב-Enter
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return {
    // State
    messageText,
    setMessageText,
    
    // Functions
    sendMessage: mutate,
    sendMessageAsync: mutateAsync,
    handleSendMessage,
    onSendMessage,
    handleKeyPress,
    
    // Status
    isSending: isPending,
    isSuccess,
    isError,
    error,
    data,
    reset,
  };
};

