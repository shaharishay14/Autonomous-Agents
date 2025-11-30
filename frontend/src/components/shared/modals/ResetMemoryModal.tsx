import useDarkModeStore from '../../../../store/darkmode.store';
import useModalsStore from '../../../../store/modals.store';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { useResetMemory } from '../../pages/chat/hooks';

function ResetMemoryModal() {
  const { isDarkMode } = useDarkModeStore();
  const { resetMemoryModal, closeResetMemoryModal } = useModalsStore();
  const { resetMemory, isResetting } = useResetMemory();

  if (!resetMemoryModal.isOpen) return null;

  const handleConfirm = () => {
    if (resetMemoryModal.agentId) {
      resetMemory(resetMemoryModal.agentId);
      closeResetMemoryModal();
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/70 backdrop-blur-sm"
        onClick={closeResetMemoryModal}
      />
      
      {/* Modal */}
      <div 
        className={`relative w-full max-w-md rounded-2xl shadow-2xl border ${
          isDarkMode 
            ? 'bg-[#1a1a1a] border-gray-800' 
            : 'bg-white border-gray-200'
        }`}
      >
        <div className="p-6">
          {/* Header with Icon */}
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center mb-4">
              <RefreshCw className="w-8 h-8 text-white" />
            </div>
            <h2 className={`text-2xl font-bold text-center ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Reset Memory
            </h2>
            <p className={`text-center mt-2 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Are you sure you want to reset the conversation memory?
            </p>
          </div>

          {/* Warning Box */}
          <div className={`rounded-xl p-4 mb-6 border-2 ${
            isDarkMode 
              ? 'bg-orange-500/10 border-orange-500/30' 
              : 'bg-orange-50 border-orange-200'
          }`}>
            <div className="flex items-start gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
              <span className="font-semibold text-orange-500">
                This action will:
              </span>
            </div>
            <ul className={`space-y-2 text-sm ${
              isDarkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              <li className="flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">•</span>
                <span>Delete all conversation history</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">•</span>
                <span>Clear all stored memories</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">•</span>
                <span>Remove context from previous messages</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">•</span>
                <span>Start fresh with no conversation history</span>
              </li>
            </ul>
            <div className="mt-3 pt-3 border-t border-orange-500/30">
              <p className="text-sm font-medium text-orange-500">
                This action cannot be undone.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={closeResetMemoryModal}
              className={`flex-1 py-3 px-4 rounded-xl font-medium transition-all ${
                isDarkMode
                  ? 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
              }`}
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isResetting}
              className="flex-1 py-3 px-4 rounded-xl font-medium bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isResetting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Resetting...
                </>
              ) : (
                'Reset Memory'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResetMemoryModal;

