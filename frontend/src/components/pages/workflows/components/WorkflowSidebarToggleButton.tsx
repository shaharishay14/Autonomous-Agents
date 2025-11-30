import { Workflow } from 'lucide-react';

interface WorkflowSidebarToggleButtonProps {
  isDarkMode: boolean;
  onToggle: () => void;
}

export const WorkflowSidebarToggleButton = ({ isDarkMode, onToggle }: WorkflowSidebarToggleButtonProps) => {
  return (
    <div className="absolute top-4 left-4 z-50">
      {/* Background layer */}
      <div className={`absolute inset-0 rounded-xl ${
        isDarkMode
          ? 'bg-gray-900'
          : 'bg-white'
      }`} style={{ transform: 'scale(1.1)' }} />
      
      {/* Button */}
      <button
        onClick={onToggle}
        className={`relative w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 hover:scale-110 ${
          isDarkMode
            ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 hover:from-purple-500/30 hover:to-pink-500/30 border border-purple-500/30 hover:border-purple-500/50 shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40'
            : 'bg-gradient-to-br from-purple-400 to-pink-500 hover:from-purple-500 hover:to-pink-600 border-2 border-purple-300 shadow-xl hover:shadow-2xl'
        }`}
        aria-label="Open workflow sidebar"
      >
        <Workflow 
          className={`w-6 h-6 ${isDarkMode ? 'text-purple-400' : 'text-white'}`}
        />
      </button>
    </div>
  );
};

export default WorkflowSidebarToggleButton;

