interface Agent {
  name: string;
  avatar?: string | null;
}

interface PublicChatWelcomeProps {
  agent: Agent;
}

function PublicChatWelcome({ agent }: PublicChatWelcomeProps) {
  return (
    <div className="text-center py-12">
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-4xl mx-auto mb-4 bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/30">
        {'🤖'}
      </div>
      <h2 className="text-2xl font-bold mb-2 text-white">
        {agent?.name || 'Agent'}
      </h2>
      <p className="mb-8 text-gray-400">
        התחל לשוחח עם האייג'נט שלך
      </p>
    </div>
  );
}

export default PublicChatWelcome;

