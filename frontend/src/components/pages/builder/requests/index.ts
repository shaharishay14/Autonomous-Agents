import { api } from '../../../../lib/axios';
import type { CreateAgentPayload, CreateAgentResponse } from '../types';

export const createAgent = async (payload: CreateAgentPayload): Promise<CreateAgentResponse> => {
  const response = await api.post<CreateAgentResponse>('/agents/', {
    prompt: payload.prompt,
    name: payload.name || "",
    app_connections: payload.app_connections || [],
  });
  return response.data;
};

