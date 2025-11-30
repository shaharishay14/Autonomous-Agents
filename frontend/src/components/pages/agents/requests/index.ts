import { api } from '../../../../lib/axios';
import type { Agent } from '../types';

export const getAgents = async (): Promise<Agent[]> => {
  const response = await api.get<Agent[]>('/agents/');
  return response.data;
};

export const deleteAgent = async (id: string): Promise<void> => {
  await api.delete(`/agents/${id}/`);
};

