import { Handle, Position } from '@xyflow/react';

interface AgentNodeProps {
  data: {
    label: string;
    icon?: string;
    agentId?: string;
    onDelete?: () => void;
    onOpenInNewTab?: () => void;
  };
}

function AgentNode({ data }: AgentNodeProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    data.onDelete?.();
  };

  const handleOpenInNewTab = (e: React.MouseEvent) => {
    e.stopPropagation();
    data.onOpenInNewTab?.();
  };

  return (
    <div className="relative group">
      <div className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 border-2 border-purple-500/50 rounded-2xl p-4 min-w-[200px] transition-all duration-200 group-hover:border-purple-400 group-hover:shadow-lg group-hover:shadow-purple-500/30">
        <Handle 
          type="target" 
          position={Position.Left}
          className="!w-3 !h-3 !bg-purple-500 !border-2 !border-purple-400"
        />
        
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="px-2 py-1 bg-purple-500/20 rounded-lg text-purple-400 text-xs font-semibold">
            Agent
          </div>
          
          {/* Hover Actions */}
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
              onClick={handleOpenInNewTab}
              className="p-1.5 bg-purple-600 hover:bg-purple-500 rounded-lg transition-all shadow-lg"
              title="Open in new tab"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </button>
            <button 
              onClick={handleDelete}
              className="p-1.5 bg-red-600 hover:bg-red-500 rounded-lg transition-all shadow-lg"
              title="Remove from workflow"
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500/30 to-cyan-500/30 rounded-xl flex items-center justify-center text-xl border border-blue-500/30">
            {data.icon || '🤖'}
          </div>
          <div className="flex-1">
            <div className="text-white font-semibold text-sm">{data.label}</div>
          </div>
        </div>
        
        <Handle 
          type="source" 
          position={Position.Right}
          className="!w-3 !h-3 !bg-purple-500 !border-2 !border-purple-400"
        />
      </div>
    </div>
  );
}

export default AgentNode;

