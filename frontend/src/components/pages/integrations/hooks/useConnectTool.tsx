import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { toast } from 'react-toastify';
import { useLocation } from 'react-router-dom';
import { connectTool } from '../requests';
import type { Integration } from '../components/types';
import type { AxiosError } from 'axios';

interface ConnectToolPayload {
  tool_name: string;
  redirect_url?: string;
}

interface ErrorResponse {
  message: string;
}

interface ConnectToolResponse {
  auth_url?: string;
  connection?: {
    id: number;
    user: string;
    tool_name: string;
    auth_config_id: string;
    connected_at: string;
  };
  success: boolean;
}

export const useConnectTool = (integrations: Integration[]) => {
  const [connectingToolName, setConnectingToolName] = useState<string | null>(null);
  const location = useLocation();

  const mutation = useMutation<ConnectToolResponse, AxiosError<ErrorResponse>, ConnectToolPayload>({
    mutationFn: connectTool,
    onSuccess: (data) => {      


      if (data.auth_url) {
        window.open(data.auth_url, '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
      }
      
      setConnectingToolName(null);
    },
    onError: (error, variables) => {
      console.error('❌ שגיאה בחיבור הכלי:', variables.tool_name);
      console.error('📄 פרטי השגיאה:', error.response?.data || error.message);
      
      // הצגת הודעת שגיאה ב-toast
      toast.error('Connection error. If this issue persists, please contact support.');
      
      setConnectingToolName(null);
    },
  });

  const handleConnect = (id: string) => {
    // מציאת שם הכלי לפי ה-id
    const integration = integrations.find(i => i.id === id);
    if (!integration) {
      console.error('❌ לא נמצא כלי עם ID:', id);
      return;
    }    

    // שליחת בקשה לחיבור עם redirect_url
    setConnectingToolName(integration.name);
    mutation.mutate({ 
      tool_name: integration.name,
      redirect_url: location.pathname
    });
  };

  return {
    connectTool: handleConnect,
    connectToolAsync: mutation.mutateAsync,
    isConnecting: mutation.isPending,
    connectingToolName,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    data: mutation.data,
    reset: mutation.reset,
  };
};

