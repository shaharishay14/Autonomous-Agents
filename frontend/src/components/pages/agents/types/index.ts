export interface Agent {
  id: string;
  user: string;
  name: string;
  prompt: string;
  tools: string;
  app_connections: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  avatar_base64?: string;
}

