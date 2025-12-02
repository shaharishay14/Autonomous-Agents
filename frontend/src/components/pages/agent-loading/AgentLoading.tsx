import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Bot, Sparkles } from 'lucide-react';

function AgentLoading() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const agentId = searchParams.get('id');

  useEffect(() => {
    // If no agent ID in query params, this page was accessed incorrectly
    if (!agentId) {
      navigate('/builder');
    }
  }, [agentId, navigate]);

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      <div className="relative max-w-md w-full mx-4">
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl shadow-2xl p-8 border border-gray-700/50">
          {/* Animated Agent Icon */}
          <div className="flex justify-center mb-8">
            <div className="relative">
              {/* Orbiting dots */}
              <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s' }}>
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-purple-500 rounded-full"></div>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-pink-500 rounded-full"></div>
              </div>
              <div className="absolute inset-0 animate-spin" style={{ animationDuration: '4s', animationDirection: 'reverse' }}>
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-orange-500 rounded-full"></div>
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-blue-500 rounded-full"></div>
              </div>

              {/* Center Icon */}
              <div className="relative bg-gradient-to-br from-pink-500 via-purple-500 to-orange-500 rounded-full p-1 shadow-xl">
                <div className="bg-gray-900 rounded-full p-8">
                  <Bot className="w-16 h-16 text-white animate-pulse" />
                </div>
              </div>
            </div>
          </div>

          {/* Title with animated dots */}
          <div className="text-center mb-4">
            <h2 className="text-2xl md:text-3xl font-bold text-white flex items-center justify-center gap-2">
              Creating your agent
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-2 h-2 bg-pink-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </span>
            </h2>
          </div>

          {/* Progress Bar */}
          <div className="relative w-full h-2 bg-gray-700 rounded-full overflow-hidden mb-6">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 animate-progress"></div>
          </div>

          {/* Status Messages */}
          <div className="space-y-3 text-center">
            <p className="text-gray-300 text-lg flex items-center justify-center gap-2">
              <Sparkles className="w-5 h-5 text-yellow-400 animate-pulse" />
              Analyzing your requirements...
            </p>
            <p className="text-gray-500 text-sm">
              This may take a few moments
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes progress {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-progress {
          animation: progress 1.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}

export default AgentLoading;

