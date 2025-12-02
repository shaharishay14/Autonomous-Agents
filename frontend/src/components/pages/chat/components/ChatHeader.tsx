import { RotateCcw, Share2, MessageCircle, Send } from 'lucide-react';
import { DndContext } from '@dnd-kit/core';
import { formatAvatarUrl } from '../utils';
import { DraggableButton, useDraggableButton } from './drags';
import type { Agent } from '../types';

interface ChatHeaderProps {
  isDarkMode: boolean;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  agentData?: Agent;
  agentId: string;
  openResetMemoryModal: (id: string) => void;
  openShareAgentModal: (id: string, name: string) => void;
  openTelegramBotModal: (id: string) => void;
}

export const ChatHeader = ({
  isDarkMode,
  isSidebarOpen,
  onToggleSidebar,
  agentData,
  agentId,
  openResetMemoryModal,
  openShareAgentModal,
  openTelegramBotModal
}: ChatHeaderProps) => {
  const avatarUrl = formatAvatarUrl(agentData?.avatar_base64);
  
  // Use draggable button hook
  const { isMobile, buttonPosition, hasUserDragged, sensors, handleDragEnd } = useDraggableButton();

  return (
    <div className={`border-b backdrop-blur-sm relative ${
      isDarkMode
        ? 'border-white/[0.08] bg-gradient-to-r from-gray-900/50 to-gray-900/80'
        : 'border-purple-200 bg-gradient-to-r from-white/90 via-purple-50/50 to-pink-50/50'
    }`}>
      <div className="flex items-center justify-between p-2 md:p-4">
        <div className="flex items-center gap-2 md:gap-4 min-w-0 flex-1">
          <div className="flex items-center gap-2 md:gap-3 min-w-0 flex-1">
            <div 
              className={`w-8 h-8 md:w-10 md:h-10 rounded-xl flex items-center justify-center text-xl md:text-2xl overflow-hidden flex-shrink-0 ${
                isDarkMode
                  ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30'
                  : 'bg-gradient-to-br from-purple-400 to-pink-500 border-2 border-purple-300 shadow-lg'
              }`}
              style={avatarUrl ? { backgroundImage: `url(${avatarUrl})`, backgroundSize: 'cover', backgroundPosition: 'center' } : {}}
            >
              {!avatarUrl && '🤖'}
            </div>
            <div className="min-w-0 flex-1">
              <h1 className={`text-sm md:text-lg font-semibold truncate ${
                isDarkMode ? 'text-white' : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent'
              }`}>
                {agentData?.name || 'Agent'}
              </h1>
              <div className="flex items-center gap-1 md:gap-2 min-w-0">
                <div className={`w-1.5 h-1.5 md:w-2 md:h-2 rounded-full flex-shrink-0 ${
                  isDarkMode ? 'bg-green-400' : 'bg-green-500'
                }`}></div>
                <span className={`text-[10px] md:text-xs truncate ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  💎 still hasn't been shared with others
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
          <button 
            onClick={() => openResetMemoryModal(agentId)}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'bg-white/[0.05] hover:bg-white/[0.08]'
                : 'bg-gradient-to-r from-purple-100 to-pink-100 hover:from-purple-200 hover:to-pink-200 border border-purple-300'
            }`}
            title="Reset Memory"
          >
            <RotateCcw className={`w-4 h-4 md:w-5 md:h-5 ${isDarkMode ? 'text-white' : 'text-purple-700'}`} />
          </button>
          
          <button 
            onClick={() => {
              const url = window.location.href;
              window.open(`https://wa.me/?text=${encodeURIComponent(url)}`, '_blank');
            }}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'bg-green-500/20 hover:bg-green-500/30'
                : 'bg-green-100 hover:bg-green-200 border border-green-300'
            }`}
            title="Share on WhatsApp"
          >
            <MessageCircle className={`w-4 h-4 md:w-5 md:h-5 ${isDarkMode ? 'text-green-400' : 'text-green-600'}`} />
          </button>
          
          <button 
            onClick={() => openTelegramBotModal(agentId)}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'bg-blue-500/20 hover:bg-blue-500/30'
                : 'bg-blue-100 hover:bg-blue-200 border border-blue-300'
            }`}
            title="Connect to Telegram"
          >
            <Send className={`w-4 h-4 md:w-5 md:h-5 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`} />
          </button>
          
          <button 
            onClick={() => openShareAgentModal(agentId, agentData?.name || 'Agent')}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'bg-emerald-500/20 hover:bg-emerald-500/30'
                : 'bg-emerald-100 hover:bg-emerald-200 border border-emerald-300'
            }`}
            title="Share Agent"
          >
            <Share2 className={`w-4 h-4 md:w-5 md:h-5 ${isDarkMode ? 'text-emerald-400' : 'text-emerald-600'}`} />
          </button>
        </div>
      </div>

      {/* Sidebar Toggle Button - positioned at the bottom of header when closed */}
      {!isSidebarOpen && (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
          <DraggableButton
            isDarkMode={isDarkMode}
            onToggle={onToggleSidebar}
            isMobile={isMobile}
            position={buttonPosition}
            showHint={!hasUserDragged}
          />
        </DndContext>
      )}
    </div>
  );
};

