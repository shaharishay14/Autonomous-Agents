import { Handle, Position } from '@xyflow/react';

interface AddAgentNodeProps {
  data: {
    onAddAgent?: () => void;
  };
}

function AddAgentNode({ data }: AddAgentNodeProps) {
  return (
    <div className="relative">
      <Handle 
        type="target" 
        position={Position.Left}
        className="!w-3 !h-3 !bg-pink-500 !border-2 !border-pink-400"
      />
      
      <button
        onClick={data.onAddAgent}
        className="w-24 h-24 bg-gradient-to-br from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-full flex flex-col items-center justify-center gap-1 transition-all duration-300 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-110 group"
      >
        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
      
      <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 whitespace-nowrap">
        <div className="text-white font-semibold text-sm">Add Agent</div>
        <div className="text-gray-400 text-xs">Click to add a new step</div>
      </div>
    </div>
  );
}

export default AddAgentNode;

