import { useState } from 'react';
import type { Workflow } from '../types';
import useDarkModeStore from '../../../../../store/darkmode.store';
import useModalsStore from '../../../../../store/modals.store';

interface WorkflowCardProps {
  workflow: Workflow;
  isSelected: boolean;
  onSelect: (id: number) => void;
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
}

function WorkflowCard({ workflow, isSelected, onSelect, onEdit, onDelete }: WorkflowCardProps) {
  const { isDarkMode } = useDarkModeStore();
  const { openCreateTriggerModalForWorkflow } = useModalsStore();
  const [isTriggersExpanded, setIsTriggersExpanded] = useState(false);
  
  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(workflow.id);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(workflow.id);
  };

  const handleExpandTriggers = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsTriggersExpanded(!isTriggersExpanded);
  };

  const handleCreateTrigger = (e: React.MouseEvent) => {
    e.stopPropagation();
    openCreateTriggerModalForWorkflow(workflow.id);
  };

  return (
    <div 
      onClick={() => onSelect(workflow.id)}
      className={`
        relative rounded-2xl p-5 
        border transition-all duration-300 cursor-pointer group
        ${isSelected 
          ? isDarkMode
            ? 'border-purple-500/50 bg-purple-500/5'
            : 'border-purple-400 bg-purple-100'
          : isDarkMode
            ? 'bg-white/[0.03] border-white/[0.05] hover:border-white/[0.1] hover:bg-white/[0.05]'
            : 'bg-white/70 border-purple-200 hover:border-purple-300 hover:bg-white/90'
        }
      `}
    >
      <div className="flex items-start gap-3 mb-3">
        <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
          isDarkMode
            ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20'
            : 'bg-purple-100 border border-purple-200'
        }`}>
          <svg className={`w-6 h-6 ${
            isDarkMode ? 'text-purple-400' : 'text-purple-600'
          }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className={`text-base font-semibold mb-1 ${
            isDarkMode ? 'text-white' : 'text-gray-900'
          }`}>
            {workflow.name}
          </h3>
          <p className={`text-sm line-clamp-2 ${
            isDarkMode ? 'text-gray-400' : 'text-gray-700'
          }`}>
            {workflow.description}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-2">
          <span className={`
            px-2 py-1 rounded-lg text-xs font-medium
            ${workflow.status === 'active' 
              ? isDarkMode
                ? 'bg-green-500/20 text-green-400'
                : 'bg-green-100 text-green-700 border border-green-300'
              : isDarkMode
                ? 'bg-gray-500/20 text-gray-400'
                : 'bg-gray-100 text-gray-700 border border-gray-300'
            }
          `}>
            {workflow.status}
          </span>
          <span className={`px-2 py-1 rounded-lg text-xs font-medium ${
            isDarkMode
              ? 'bg-white/[0.05] text-gray-400'
              : 'bg-purple-100 text-purple-700 border border-purple-200'
          }`}>
            {workflow.node_count} nodes
          </span>
        </div>
        
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleEdit}
            className={`p-1.5 rounded-lg transition-colors ${
              isDarkMode
                ? 'hover:bg-white/[0.08] text-gray-400'
                : 'hover:bg-purple-100 text-purple-700'
            }`}
            aria-label="Edit workflow"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <button
            onClick={handleDelete}
            className="p-1.5 hover:bg-red-500/20 rounded-lg transition-colors text-red-400"
            aria-label="Delete workflow"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div>
        <button
          onClick={handleExpandTriggers}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-xl transition-colors ${
            isDarkMode
              ? 'bg-white/[0.03] hover:bg-white/[0.05]'
              : 'bg-purple-50 hover:bg-purple-100 border border-purple-200'
          }`}
        >
          <div className="flex items-center gap-2">
            <svg className={`w-4 h-4 ${
              isDarkMode ? 'text-orange-400' : 'text-orange-600'
            }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-700'
            }`}>Triggers</span>
          </div>
          <svg 
            className={`w-4 h-4 transition-transform ${
              isTriggersExpanded ? 'rotate-90' : ''
            } ${isDarkMode ? 'text-gray-400' : 'text-purple-600'}`} 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>

        {/* Expanded Triggers Section */}
        {isTriggersExpanded && (
          <div 
            className={`mt-3 p-4 rounded-xl border ${
              isDarkMode
                ? 'bg-white/[0.02] border-white/[0.05]'
                : 'bg-purple-50/50 border-purple-200'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className={`text-sm mb-3 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-700'
            }`}>
              Set up automated triggers to execute your workflow on a schedule.
            </div>
            
            <button
              onClick={handleCreateTrigger}
              className="w-full py-2.5 px-4 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 rounded-xl text-white font-medium transition-all flex items-center justify-center gap-2 shadow-lg hover:shadow-xl mb-4"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create Trigger
            </button>

            <div className="text-center py-6">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3 ${
                isDarkMode ? 'bg-white/[0.05]' : 'bg-purple-100'
              }`}>
                <svg className={`w-8 h-8 ${
                  isDarkMode ? 'text-gray-500' : 'text-purple-400'
                }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className={`text-sm font-medium mb-1 ${
                isDarkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                No triggers configured
              </p>
              <p className={`text-xs ${
                isDarkMode ? 'text-gray-500' : 'text-gray-600'
              }`}>
                Create your first trigger to get started
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WorkflowCard;

