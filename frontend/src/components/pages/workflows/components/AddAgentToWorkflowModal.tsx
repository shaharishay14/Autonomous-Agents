import { useState } from 'react';
import useDarkModeStore from '../../../../../store/darkmode.store';
import useModalsStore from '../../../../../store/modals.store';
import { useUpdateWorkflow } from '../hooks';
import { useGetAgents } from '../../agents/hooks';
import { useCreateAgent } from '../../builder/hooks';
import { Plus, Search, ArrowRight } from 'lucide-react';

type TabType = 'existing' | 'new';

function AddAgentToWorkflowModal() {
  const { isDarkMode } = useDarkModeStore();
  const { addAgentToWorkflowModal, closeAddAgentToWorkflowModal } = useModalsStore();
  const { mutate: updateWorkflow, isPending: isUpdating } = useUpdateWorkflow();
  const { agents = [], isLoading: isLoadingAgents } = useGetAgents();
  const { createAgentAsync, isCreating } = useCreateAgent();
  
  const [activeTab, setActiveTab] = useState<TabType>('existing');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [newAgentPrompt, setNewAgentPrompt] = useState('');

  const isPending = isUpdating || isCreating;

  if (!addAgentToWorkflowModal.isOpen) return null;

  const filteredAgents = agents?.filter(agent => 
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.prompt.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const handleSelectExistingAgent = () => {
    if (selectedAgentId && addAgentToWorkflowModal.workflowId) {
      // חשב את מספר ה-nodes החדש (start node + agent node)
      const newNodeCount = 2; // start node + agent node
      
      updateWorkflow({
        id: addAgentToWorkflowModal.workflowId,
        data: { 
          agent: selectedAgentId,
          node_count: newNodeCount
        }
      }, {
        onSuccess: () => {
          closeAddAgentToWorkflowModal();
          setSelectedAgentId(null);
          setSearchQuery('');
        },
      });
    }
  };

  const handleCreateNewAgent = async () => {
    if (!newAgentPrompt.trim() || !addAgentToWorkflowModal.workflowId) {
      return;
    }

    try {
      const newAgent = await createAgentAsync({ prompt: newAgentPrompt.trim() });
      
      // חשב את מספר ה-nodes החדש (start node + agent node)
      const newNodeCount = 2; // start node + agent node
      
      // עדכן את ה-workflow עם ה-agent החדש
      updateWorkflow({
        id: addAgentToWorkflowModal.workflowId,
        data: { 
          agent: newAgent.id,
          node_count: newNodeCount
        }
      }, {
        onSuccess: () => {
          closeAddAgentToWorkflowModal();
          setNewAgentPrompt('');
        },
      });
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const handleClose = () => {
    setSelectedAgentId(null);
    setSearchQuery('');
    setNewAgentPrompt('');
    setActiveTab('existing');
    closeAddAgentToWorkflowModal();
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Modal */}
      <div 
        className={`relative w-full max-w-2xl rounded-3xl shadow-2xl border-2 ${
          isDarkMode 
            ? 'bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 border-gray-700/50' 
            : 'bg-white border-gray-200'
        }`}
      >
        <div className="p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-xl ${
                isDarkMode 
                  ? 'bg-gradient-to-br from-purple-500 to-pink-500' 
                  : 'bg-gradient-to-br from-purple-500 to-pink-500'
              }`}>
                <Plus className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className={`text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent`}>
                  Add Agent to Workflow
                </h2>
              </div>
            </div>
            <button
              onClick={handleClose}
              className={`p-2 rounded-lg transition-colors ${
                isDarkMode
                  ? 'text-gray-400 hover:text-white hover:bg-white/10'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
              }`}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveTab('existing')}
              className={`flex-1 py-3 px-6 rounded-xl font-medium transition-all ${
                activeTab === 'existing'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                  : isDarkMode
                    ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Select Existing
            </button>
            <button
              onClick={() => setActiveTab('new')}
              className={`flex-1 py-3 px-6 rounded-xl font-medium transition-all ${
                activeTab === 'new'
                  ? 'bg-gradient-to-r from-purple-500 to-orange-500 text-white shadow-lg'
                  : isDarkMode
                    ? 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Create New
            </button>
          </div>

          {/* Content */}
          <div className="min-h-[400px]">
            {activeTab === 'existing' ? (
              <div>
                {/* Search Bar */}
                <div className="mb-4 relative">
                  <Search className={`absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 ${
                    isDarkMode ? 'text-gray-400' : 'text-gray-500'
                  }`} />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search agents..."
                    className={`w-full pl-12 pr-4 py-3 rounded-xl border-2 transition-all outline-none ${
                      isDarkMode
                        ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:border-purple-500'
                        : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-purple-500'
                    }`}
                  />
                </div>

                {/* Agents List */}
                <div className="space-y-3 max-h-[320px] overflow-y-auto custom-scrollbar">
                  {isLoadingAgents ? (
                    <div className="text-center py-8">
                      <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto"></div>
                      <p className={`mt-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        Loading agents...
                      </p>
                    </div>
                  ) : filteredAgents.length === 0 ? (
                    <div className="text-center py-12">
                      <p className={`text-lg ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                        {searchQuery ? 'No agents found' : 'No agents available'}
                      </p>
                    </div>
                  ) : (
                    filteredAgents.map((agent) => (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgentId(agent.id)}
                        className={`w-full p-4 rounded-xl border-2 transition-all text-left ${
                          selectedAgentId === agent.id
                            ? isDarkMode
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-purple-500 bg-purple-50'
                            : isDarkMode
                              ? 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
                              : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${
                            isDarkMode
                              ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20'
                              : 'bg-purple-100 border border-purple-200'
                          }`}>
                            <span className="text-2xl">🤖</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className={`font-semibold mb-1 ${
                              isDarkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              {agent.name}
                            </h3>
                            <p className={`text-sm line-clamp-2 ${
                              isDarkMode ? 'text-gray-400' : 'text-gray-600'
                            }`}>
                              {agent.prompt}
                            </p>
                          </div>
                          {selectedAgentId === agent.id && (
                            <ArrowRight className="flex-shrink-0 w-5 h-5 text-purple-500" />
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            ) : (
              <div>
                {/* Create New Agent Form */}
                <div className={`border-2 rounded-2xl p-6 ${
                  isDarkMode
                    ? 'border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-pink-500/10'
                    : 'border-purple-300 bg-gradient-to-br from-purple-50 to-pink-50'
                }`}>
                  <label 
                    htmlFor="agent-prompt"
                    className={`block text-sm font-medium mb-3 ${
                      isDarkMode ? 'text-gray-300' : 'text-gray-700'
                    }`}
                  >
                    Build an agent that can extract key information from documents
                  </label>
                  <textarea
                    id="agent-prompt"
                    value={newAgentPrompt}
                    onChange={(e) => setNewAgentPrompt(e.target.value)}
                    placeholder="Describe what your agent should do..."
                    rows={8}
                    className={`w-full px-4 py-3 rounded-xl border-2 transition-all outline-none resize-none ${
                      isDarkMode
                        ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500 focus:border-purple-500'
                        : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400 focus:border-purple-500'
                    }`}
                  />
                  <div className="mt-4 flex items-center gap-2">
                    <span className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
                      isDarkMode
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-yellow-100 text-yellow-700 border border-yellow-300'
                    }`}>
                      ⚡ YOLO
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer Buttons */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={handleClose}
              disabled={isPending}
              className={`flex-1 py-3 px-6 rounded-xl font-medium transition-all ${
                isDarkMode
                  ? 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              Cancel
            </button>
            <button
              onClick={activeTab === 'existing' ? handleSelectExistingAgent : handleCreateNewAgent}
              disabled={
                isPending || 
                (activeTab === 'existing' ? !selectedAgentId : !newAgentPrompt.trim())
              }
              className={`flex-1 py-3 px-6 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${
                isPending || (activeTab === 'existing' ? !selectedAgentId : !newAgentPrompt.trim())
                  ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/50'
              }`}
            >
              <ArrowRight className="w-5 h-5" />
              {isPending 
                ? (activeTab === 'new' ? 'Creating...' : 'Adding...') 
                : (activeTab === 'new' ? 'Create' : 'Add Agent')
              }
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AddAgentToWorkflowModal;

