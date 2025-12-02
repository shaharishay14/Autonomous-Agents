import { useState, useEffect } from 'react';
import useDarkModeStore from '../../../../../../store/darkmode.store';
import useModalsStore from '../../../../../../store/modals.store';
import { useCreateWorkflow, useUpdateWorkflow } from '../../hooks';
import { Sparkles, Save } from 'lucide-react';

function CreateWorkflowModal() {
  const { isDarkMode } = useDarkModeStore();
  const { createWorkflowModal, closeCreateWorkflowModal } = useModalsStore();
  const { mutate: createWorkflow, isPending: isCreating } = useCreateWorkflow();
  const { mutate: updateWorkflow, isPending: isUpdating } = useUpdateWorkflow();
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const isEditMode = createWorkflowModal.workflowId !== null;
  const isPending = isCreating || isUpdating;

  // Load data when editing
  useEffect(() => {
    if (createWorkflowModal.workflowData) {
      setName(createWorkflowModal.workflowData.name);
      setDescription(createWorkflowModal.workflowData.description);
    } else {
      setName('');
      setDescription('');
    }
  }, [createWorkflowModal.workflowData, createWorkflowModal.isOpen]);

  if (!createWorkflowModal.isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      return;
    }

    if (isEditMode && createWorkflowModal.workflowId) {
      // Update existing workflow
      updateWorkflow({
        id: createWorkflowModal.workflowId,
        data: {
          name: name.trim(),
          description: description.trim(),
        }
      }, {
        onSuccess: () => {
          setName('');
          setDescription('');
          closeCreateWorkflowModal();
        },
      });
    } else {
      // Create new workflow
      createWorkflow({
        name: name.trim(),
        description: description.trim(),
        status: 'draft',
      }, {
        onSuccess: () => {
          setName('');
          setDescription('');
          closeCreateWorkflowModal();
        },
      });
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    closeCreateWorkflowModal();
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-2 sm:p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div 
        className={`relative w-full max-w-xl rounded-2xl sm:rounded-3xl shadow-2xl border-2 max-h-[95vh] overflow-y-auto ${
          isDarkMode 
            ? 'bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 border-gray-700/50' 
            : 'bg-white border-gray-200'
        }`}
      >
        <form onSubmit={handleSubmit} className="p-4 sm:p-6 md:p-8">
          {/* Header */}
          <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
            <div className={`p-2 sm:p-3 rounded-lg sm:rounded-xl flex-shrink-0 ${
              isDarkMode 
                ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                : 'bg-gradient-to-br from-purple-500 to-pink-500'
            }`}>
              <Sparkles className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <div className="min-w-0">
              <h2 className={`text-lg sm:text-xl md:text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent`}>
                {isEditMode ? 'Edit Workflow' : 'Create New Workflow'}
              </h2>
              <p className={`text-xs sm:text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                {isEditMode ? 'Update your workflow details' : 'Give your workflow a name and description'}
              </p>
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-4 sm:space-y-5 mb-6 sm:mb-8">
            {/* Workflow Name */}
            <div>
              <label 
                htmlFor="workflow-name"
                className={`block text-xs sm:text-sm font-medium mb-1.5 sm:mb-2 ${
                  isDarkMode ? 'text-gray-300' : 'text-gray-700'
                }`}
              >
                Workflow Name
              </label>
              <input
                id="workflow-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Daily Report Generator"
                className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg sm:rounded-xl border-2 transition-all outline-none text-sm sm:text-base ${
                  isDarkMode
                    ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:border-purple-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-purple-500'
                }`}
                required
                autoFocus
              />
            </div>

            {/* Description */}
            <div>
              <label 
                htmlFor="workflow-description"
                className={`block text-xs sm:text-sm font-medium mb-1.5 sm:mb-2 ${
                  isDarkMode ? 'text-gray-300' : 'text-gray-700'
                }`}
              >
                Description
              </label>
              <textarea
                id="workflow-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Briefly describe what this workflow does..."
                rows={3}
                className={`w-full px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg sm:rounded-xl border-2 transition-all outline-none resize-none text-sm sm:text-base ${
                  isDarkMode
                    ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:border-purple-500'
                    : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-purple-500'
                }`}
              />
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="flex gap-2 sm:gap-3">
            <button
              type="button"
              onClick={handleClose}
              className={`flex-1 py-2.5 sm:py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl font-medium transition-all text-sm sm:text-base ${
                isDarkMode
                  ? 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }`}
              disabled={isPending}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || isPending}
              className={`flex-1 py-2.5 sm:py-3 px-4 sm:px-6 rounded-lg sm:rounded-xl font-medium transition-all flex items-center justify-center gap-1.5 sm:gap-2 text-sm sm:text-base ${
                !name.trim() || isPending
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/50'
              }`}
            >
              {isEditMode ? <Save className="w-4 h-4 sm:w-5 sm:h-5" /> : <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />}
              <span className="hidden xs:inline">
                {isPending 
                  ? (isEditMode ? 'Saving...' : 'Creating...') 
                  : (isEditMode ? 'Save Changes' : 'Create Workflow')
                }
              </span>
              <span className="xs:hidden">
                {isPending 
                  ? '...' 
                  : (isEditMode ? 'Save' : 'Create')
                }
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CreateWorkflowModal;

