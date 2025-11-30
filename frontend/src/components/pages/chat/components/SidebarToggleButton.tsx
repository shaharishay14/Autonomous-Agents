interface SidebarToggleButtonProps {
  isDarkMode: boolean;
  onToggle: () => void;
}

export const SidebarToggleButton = ({ isDarkMode, onToggle }: SidebarToggleButtonProps) => {
  return (
    <div className="relative w-20 flex justify-center">
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
        aria-label="Open settings"
      >
      <svg 
        className={`w-6 h-6 ${isDarkMode ? 'text-purple-400' : 'text-white'}`} 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
      >
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" 
        />
        <path 
          strokeLinecap="round" 
          strokeLinejoin="round" 
          strokeWidth={2} 
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" 
        />
      </svg>
      </button>
    </div>
  );
};

