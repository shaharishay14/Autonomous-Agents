import { ArrowLeft, ArrowRight } from 'lucide-react';
import useDarkModeStore from '../../../../../../../store/darkmode.store';

interface ModalFooterProps {
  currentStep: number;
  canProceed: boolean;
  isCreating: boolean;
  isStep1Valid: boolean;
  onBack: () => void;
  onNext: () => void;
  onSubmit: () => void;
}

function ModalFooter({
  currentStep,
  canProceed,
  isCreating,
  isStep1Valid,
  onBack,
  onNext,
  onSubmit
}: ModalFooterProps) {
  const { isDarkMode } = useDarkModeStore();

  return (
    <div className={`px-8 py-6 border-t flex items-center justify-between flex-shrink-0 ${
      isDarkMode ? 'border-gray-800' : 'border-gray-200'
    }`}>
      <button
        onClick={onBack}
        disabled={currentStep === 1}
        className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
          currentStep === 1
            ? 'opacity-50 cursor-not-allowed'
            : isDarkMode
              ? 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
        }`}
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      {currentStep < 4 ? (
        <button
          onClick={onNext}
          disabled={!canProceed}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all ${
            !canProceed
              ? 'opacity-50 cursor-not-allowed bg-gray-400 text-white'
              : 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 text-white shadow-lg hover:shadow-xl'
          }`}
        >
          Next
          <ArrowRight className="w-4 h-4" />
        </button>
      ) : (
        <button
          onClick={onSubmit}
          disabled={isCreating || !isStep1Valid}
          className={`flex items-center gap-2 px-8 py-3 rounded-xl font-medium transition-all ${
            isCreating || !isStep1Valid
              ? 'opacity-50 cursor-not-allowed bg-gray-400 text-white'
              : 'bg-gradient-to-r from-purple-600 via-purple-500 to-orange-500 hover:from-purple-500 hover:via-purple-400 hover:to-orange-400 text-white shadow-lg hover:shadow-xl'
          }`}
        >
          {isCreating ? (
            <>
              <span className="animate-spin">⏳</span>
              Creating...
            </>
          ) : (
            <>
              Create Agent
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      )}
    </div>
  );
}

export default ModalFooter;

