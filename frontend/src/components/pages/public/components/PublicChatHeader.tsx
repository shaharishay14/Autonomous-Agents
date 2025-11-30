import { Link } from 'react-router-dom';

interface Agent {
  name: string;
  prompt: string;
}

interface PublicChatHeaderProps {
  agent: Agent;
}

function PublicChatHeader({ agent }: PublicChatHeaderProps) {
  return (
    <div className="relative border-b border-white/[0.08] bg-transparent">
      <div className="max-w-full mx-auto px-6 py-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 group">
            {/* Agent Avatar with glow effect */}
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-green-500 to-green-600 rounded-2xl blur-lg opacity-40 group-hover:opacity-60 transition-opacity"></div>
              <div className="relative w-14 h-14 rounded-2xl flex items-center justify-center text-3xl bg-gradient-to-br from-green-500 to-green-600 shadow-2xl transform group-hover:scale-105 transition-transform duration-300">
                {'😊'}
              </div>
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-white via-gray-100 to-white bg-clip-text text-transparent">
                  {agent.name}
                </h1>
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-lg shadow-green-500/50"></div>
              </div>
              <p className="text-sm text-gray-400 mt-1 line-clamp-1">
                {agent.prompt.substring(0, 80)}...
              </p>
            </div>
          </div>
          
          {/* Created by badge with special design */}
          <Link 
            to={import.meta.env.VITE_FRONT_URL || '/'} 
            target="_blank" 
            rel="noopener noreferrer"
            className="group relative px-5 py-2.5 rounded-xl text-xs font-medium border-2 border-gray-700/50 bg-gradient-to-br from-gray-800/50 to-gray-900/50 text-gray-300 hover:text-white hover:border-purple-500/50 transition-all duration-300 backdrop-blur-sm shadow-lg hover:shadow-purple-500/20 hover:scale-105"
          >
            <span className="relative z-10 flex items-center gap-2">
              <span className="text-gray-500 group-hover:text-purple-400 transition-colors">powered by</span>
              <span className="font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">kgen21</span>
            </span>
            {/* Hover glow effect */}
            <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-600/0 via-purple-600/10 to-pink-600/0 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default PublicChatHeader;

