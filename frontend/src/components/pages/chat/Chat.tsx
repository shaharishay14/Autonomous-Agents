import { useParams } from 'react-router-dom';
import { useState } from 'react';
import { AgentSidebar, ChatArea, ChatLayout } from './components';
import { CreateTriggerModal } from './components/modals';
import { ResetMemoryModal, ShareAgentModal, TelegramBotModal } from '../../shared/modals';
import useDarkModeStore from '../../../../store/darkmode.store';
import useModalsStore from '../../../../store/modals.store';
import { useGetAgent, useGetAvailableAgentTools, useGetAgentMessages, useGetSuggestedPrompts } from './hooks';
import { LoadingState, ErrorState } from '../../shared/components';

function Chat() {
  const { isDarkMode } = useDarkModeStore();
  const { id } = useParams<{ id: string }>();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  // שליפת נתוני האייג'נט
  const { agent, isLoading, isError } = useGetAgent(id || '');
  
  // שליפת הכלים הזמינים של האייג'נט - יודפס ב-console
  useGetAvailableAgentTools(id || '');
  
  // שליפת הודעות האייג'נט
  const { messages } = useGetAgentMessages(id || '');
  
  // hook להצעות פרומפטים - מטפל באופן אוטומטי בקבלת הצעות
  const { suggestedPrompts } = useGetSuggestedPrompts(messages, agent);
  
  // Modal state
  const { createTriggerModal, closeCreateTriggerModal } = useModalsStore();

  // הצגת loading
  if (isLoading) {
    return (
      <ChatLayout isDarkMode={isDarkMode}>
        <LoadingState />
      </ChatLayout>
    );
  }

  // הצגת שגיאה
  if (isError) {
    return (
      <ChatLayout isDarkMode={isDarkMode}>
        <ErrorState message="שגיאה בטעינת האייג'נט" />
      </ChatLayout>
    );
  }

  return (
    <>
      <ChatLayout isDarkMode={isDarkMode}>
        {/* Agent Settings Sidebar */}
        <AgentSidebar 
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          agent={agent}
        />
        
        {/* Chat Area */}
        <ChatArea 
          agentId={id || ''}
          agent={agent}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          isSidebarOpen={isSidebarOpen}
          suggestedPrompts={suggestedPrompts}
        />
      </ChatLayout>

      {/* Create Trigger Modal - Positioned at Chat level for full screen coverage */}
      <CreateTriggerModal
        isOpen={createTriggerModal.isOpen}
        onClose={closeCreateTriggerModal}
        agentId={createTriggerModal.agentId || undefined}
      />

      {/* Reset Memory Modal */}
      <ResetMemoryModal />

      {/* Share Agent Modal */}
      <ShareAgentModal />

      {/* Telegram Bot Modal */}
      <TelegramBotModal />
    </>
  );
}

export default Chat;

