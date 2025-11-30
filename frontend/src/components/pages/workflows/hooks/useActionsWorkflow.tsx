import { useState } from 'react';
import useModalsStore from '../../../../../store/modals.store';
import { useGetWorkflows } from './useGetWorkflows';

export const useActionsWorkflow = () => {
  const { openCreateWorkflowModal, openEditWorkflowModal, openDeleteWorkflowModal } = useModalsStore();
  const {
    workflows,
    isLoading,
    isError,
    error,
    refetch,
    selectedWorkflowId,
    setSelectedWorkflowId,
  } = useGetWorkflows();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleCreateWorkflow = () => {
    openCreateWorkflowModal();
  };

  const handleEditWorkflow = (id: number) => {
    const workflow = workflows.find(w => w.id === id);
    if (workflow) {
      openEditWorkflowModal(id, workflow.name, workflow.description);
    }
  };

  const handleDeleteWorkflow = (id: number) => {
    const workflow = workflows.find(w => w.id === id);
    if (workflow) {
      openDeleteWorkflowModal(id, workflow.name);
    }
  };

  const handleSelectWorkflow = (id: number) => {
    setSelectedWorkflowId(id);
  };

  const handleCloseSidebar = () => {
    setIsSidebarOpen(false);
  };

  return {
    // Data
    workflows,
    isLoading,
    isError,
    error,
    refetch,
    selectedWorkflowId,
    isSidebarOpen,
    setIsSidebarOpen,
    // Actions
    handleCreateWorkflow,
    handleEditWorkflow,
    handleDeleteWorkflow,
    handleSelectWorkflow,
    handleCloseSidebar,
  };
};

