import { api } from '../../../../lib/axios';
import type { 
  CreateWorkflowRequest, 
  CreateWorkflowResponse, 
  UpdateWorkflowRequest,
  UpdateWorkflowResponse,
  Workflow 
} from '../types';

export const createWorkflow = async (data: CreateWorkflowRequest): Promise<CreateWorkflowResponse> => {
  const response = await api.post<CreateWorkflowResponse>('/workflows/', data);
  return response.data;
};

export const getWorkflows = async (): Promise<Workflow[]> => {
  const response = await api.get<Workflow[]>('/workflows/');
  return response.data;
};

export const updateWorkflow = async (id: number, data: UpdateWorkflowRequest): Promise<UpdateWorkflowResponse> => {
  const response = await api.patch<UpdateWorkflowResponse>(`/workflows/${id}/`, data);
  return response.data;
};

export const deleteWorkflow = async (id: number): Promise<void> => {
  await api.delete(`/workflows/${id}/`);
};

