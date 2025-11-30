import type { ModalFooterProps } from './types';

export function ModalFooter({ isDarkMode }: ModalFooterProps) {
  return (
    <div className={`mt-6 p-4 rounded-xl ${
      isDarkMode ? 'bg-purple-500/10 border border-purple-500/20' : 'bg-purple-50 border border-purple-200'
    }`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <span className="text-2xl">✨</span>
        </div>
        <div>
          <h4 className={`font-semibold mb-1 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            🚀 Ready to Go Viral!
          </h4>
          <p className={`text-sm ${isDarkMode ? 'text-purple-300' : 'text-purple-700'}`}>
            Share with confidence
          </p>
          <p className={`text-xs mt-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            ✨ <span className={isDarkMode ? 'text-purple-400' : 'text-purple-600'}>Pro tip:</span> Your agent data stays private while the chat experience goes public. Perfect for demos, showcases, and viral content!
          </p>
        </div>
      </div>
    </div>
  );
}

