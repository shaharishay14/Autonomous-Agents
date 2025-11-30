import { Link } from 'react-router-dom';
import useDarkModeStore from '../../../../../store/darkmode.store';

function AgentsHeader() {
  const { isDarkMode } = useDarkModeStore();

  return (
    <div className="mb-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-start justify-between">
          <div>
            <h1 className={`text-5xl font-bold mb-3 ${
              isDarkMode 
                ? 'text-white' 
                : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent'
            }`}>
              Your Agents
            </h1>
            <p className={`text-lg ${
              isDarkMode ? 'text-gray-400' : 'text-gray-700'
            }`}>
              Manage and interact with your AI agents
            </p>
          </div>
          
          <Link
            to="/builder"
            className={`flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 rounded-2xl text-white font-medium hover:-translate-y-0.5 hover:shadow-xl transition-all duration-300 ${
              isDarkMode
                ? 'hover:shadow-purple-500/40'
                : 'hover:shadow-purple-500/50'
            }`}
          >
            <span className="text-xl">+</span>
            <span>Create Agent</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default AgentsHeader;

