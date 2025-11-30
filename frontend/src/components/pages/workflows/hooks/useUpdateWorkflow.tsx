import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { updateWorkflow } from '../requests';
import type { UpdateWorkflowRequest, UpdateWorkflowResponse } from '../types';

export const useUpdateWorkflow = () => {
  const queryClient = useQueryClient();
  
  return useMutation<UpdateWorkflowResponse, Error, { id: number; data: UpdateWorkflowRequest }>({
    mutationFn: ({ id, data }) => updateWorkflow(id, data),
    onSuccess: () => {
      toast.success('Workflow עודכן בהצלחה!');
      // Invalidate and refetch workflows
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error) => {
      toast.error('שגיאה בעדכון Workflow');
      console.error('Error updating workflow:', error);
    },
  });
};

