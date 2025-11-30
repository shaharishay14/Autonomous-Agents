import { Plus, Settings as SettingsIcon } from 'lucide-react';
import useDarkModeStore from '../../../../../../../store/darkmode.store';

interface TriggersStepProps {
  onAddTrigger: () => void;
}

function TriggersStep({ onAddTrigger }: TriggersStepProps) {
  const { isDarkMode } = useDarkModeStore();

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className={`text-lg font-semibold mb-2 ${
            isDarkMode ? 'text-gray-200' : 'text-gray-800'
          }`}>
            Automated Triggers
          </h3>
          <p className={`text-sm ${
            isDarkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Set up automated messages and actions for your agent
          </p>
        </div>
        <button
          onClick={onAddTrigger}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
            isDarkMode
              ? 'bg-orange-500 hover:bg-orange-600 text-white'
              : 'bg-orange-500 hover:bg-orange-600 text-white'
          } shadow-lg hover:shadow-xl`}
        >
          <Plus className="w-4 h-4" />
          Add Trigger
        </button>
      </div>

      {/* Empty State */}
      <div className="text-center py-16">
        <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${
          isDarkMode ? 'bg-gray-800' : 'bg-gray-100'
        }`}>
          <SettingsIcon className={`w-10 h-10 ${
            isDarkMode ? 'text-gray-600' : 'text-gray-400'
          }`} />
        </div>
        
        <h4 className={`text-base font-semibold mb-2 ${
          isDarkMode ? 'text-gray-300' : 'text-gray-700'
        }`}>
          No triggers configured yet
        </h4>
        
        <p className={`text-sm ${
          isDarkMode ? 'text-gray-500' : 'text-gray-500'
        }`}>
          Add automated triggers to make your agent proactive
        </p>
      </div>
    </div>
  );
}

export default TriggersStep;

