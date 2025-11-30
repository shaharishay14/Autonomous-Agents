export interface Workflow {
  id: number;
  user: string;
  agent: string;
  agent_name: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'inactive';
  nodes: string;
  edges: string;
  viewport: string;
  execution_count: number;
  last_executed: string;
  node_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateWorkflowRequest {
  name: string;
  description: string;
  status: 'draft' | 'active' | 'inactive';
  nodes?: string;
  edges?: string;
  viewport?: string;
}

export interface CreateWorkflowResponse {
  id: string;
  name: string;
  description: string;
  status: string;
  nodes?: string;
  edges?: string;
  viewport?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  status?: 'draft' | 'active' | 'inactive';
  agent?: string;
  nodes?: string;
  edges?: string;
  viewport?: string;
  node_count?: number;
}

export interface UpdateWorkflowResponse {
  id: number;
  name: string;
  description: string;
  status: string;
  nodes?: string;
  edges?: string;
  viewport?: string;
  created_at?: string;
  updated_at?: string;
}

