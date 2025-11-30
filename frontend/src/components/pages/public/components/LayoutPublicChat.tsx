interface LayoutPublicChatProps {
  children: React.ReactNode;
}

function LayoutPublicChat({ children }: LayoutPublicChatProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0a0a] p-6">
      {/* Main Frame - Contains Everything */}
      <div className="relative max-w-7xl w-full h-[95vh] flex flex-col rounded-3xl bg-gradient-to-br from-gray-900/40 to-gray-800/30 border-2 border-gray-700/40 shadow-2xl backdrop-blur-md overflow-hidden">
        {/* Decorative corner accents */}
        <div className="absolute top-0 left-0 w-12 h-12 border-t-2 border-l-2 border-purple-500/50 rounded-tl-3xl z-10"></div>
        <div className="absolute top-0 right-0 w-12 h-12 border-t-2 border-r-2 border-purple-500/50 rounded-tr-3xl z-10"></div>
        <div className="absolute bottom-0 left-0 w-12 h-12 border-b-2 border-l-2 border-pink-500/50 rounded-bl-3xl z-10"></div>
        <div className="absolute bottom-0 right-0 w-12 h-12 border-b-2 border-r-2 border-pink-500/50 rounded-br-3xl z-10"></div>
        
        {/* Subtle glow effects */}
        <div className="absolute -top-px left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-purple-500/40 to-transparent z-10"></div>
        <div className="absolute -bottom-px left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-pink-500/40 to-transparent z-10"></div>
        
        {/* Content */}
        {children}
      </div>
    </div>
  );
}

export default LayoutPublicChat;

