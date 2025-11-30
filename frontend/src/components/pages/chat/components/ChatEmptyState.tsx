import type { Agent } from '../types';

interface ChatEmptyStateProps {
  isDarkMode: boolean;
  agentData?: Agent;
  setMessageText: (text: string) => void;
}

export const ChatEmptyState = ({ isDarkMode, agentData, setMessageText }: ChatEmptyStateProps) => {
  return (
    <>
      <div className="text-center py-12">
        <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-4xl mx-auto mb-4 ${
          isDarkMode
            ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30'
            : 'bg-gradient-to-br from-purple-400 to-pink-500 border-2 border-purple-300 shadow-2xl'
        }`}>
          {'🤖'}
        </div>
        <h2 className={`text-2xl font-bold mb-2 ${
          isDarkMode ? 'text-white' : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent'
        }`}>
          {agentData?.name || 'Agent'}
        </h2>
        <p className={`mb-8 ${
          isDarkMode ? 'text-gray-400' : 'text-gray-700'
        }`}>
          התחל לשוחח עם האייג'נט שלך
        </p>
      </div>

      {/* Quick Action Buttons */}
      <div className="flex flex-wrap gap-3 justify-center mb-8">
        {['מה התגובות הטובות ממגזינים ישראליים?', 'איזה טלפונים זולים יותר?', 'המלץ על מוצרים במבצעים היום?'].map((text, i) => (
          <button 
            key={i} 
            onClick={() => setMessageText(text)}
            className={`px-4 py-2 rounded-full text-sm transition-all duration-200 ${
              isDarkMode
                ? 'bg-white/[0.05] hover:bg-white/[0.08] border border-white/[0.1] text-gray-300'
                : 'bg-gradient-to-r from-purple-100 to-pink-100 hover:from-purple-200 hover:to-pink-200 border border-purple-300 text-purple-700'
            }`}
          >
            {text}
          </button>
        ))}
      </div>
    </>
  );
};

