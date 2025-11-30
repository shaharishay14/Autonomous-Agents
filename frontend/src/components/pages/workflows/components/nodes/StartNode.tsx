import { Handle, Position } from '@xyflow/react';

function StartNode() {
  return (
    <div className="bg-gradient-to-br from-green-900/40 to-emerald-900/40 border-2 border-green-500/50 rounded-2xl p-6 min-w-[280px]">
      <div className="flex flex-col items-center gap-4">
        <button className="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-xl text-white font-semibold transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-green-500/30">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          Execute Workflow
        </button>
        
        <div className="w-full">
          <div className="text-white font-semibold text-sm mb-2">Start</div>
          <div className="text-green-400 text-xs mb-1">Click to execute workflow</div>
          
          <div className="mt-3">
            <div className="text-green-400 text-xs font-semibold mb-1">Initial Message</div>
            <div className="bg-black/30 border border-green-500/30 rounded-lg p-3 text-gray-300 text-xs">
              Enter the initial message for the workflow...
            </div>
          </div>
        </div>
      </div>
      
      <Handle 
        type="source" 
        position={Position.Right}
        className="!w-3 !h-3 !bg-green-500 !border-2 !border-green-400"
      />
    </div>
  );
}

export default StartNode;

