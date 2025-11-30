import { useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type OnConnect,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { StartNode, AgentNode, AddAgentNode } from './nodes';
import useDarkModeStore from '../../../../../store/darkmode.store';
import useModalsStore from '../../../../../store/modals.store';
import { useGetWorkflows } from '../hooks';

const nodeTypes = {
  startNode: StartNode,
  agentNode: AgentNode,
  addAgentNode: AddAgentNode,
};

interface WorkflowBuilderProps {
  workflowId: number;
}

function WorkflowBuilder({ workflowId }: WorkflowBuilderProps) {
  const { isDarkMode } = useDarkModeStore();
  const { openAddAgentToWorkflowModal, openRemoveAgentFromWorkflowModal } = useModalsStore();
  const { workflows } = useGetWorkflows();

  // מצא את ה-workflow הנוכחי
  const currentWorkflow = useMemo(() => 
    workflows.find(w => w.id === workflowId),
    [workflows, workflowId]
  );

  const handleAddAgent = useCallback(() => {
    openAddAgentToWorkflowModal(workflowId);
  }, [workflowId, openAddAgentToWorkflowModal]);

  const handleDeleteAgent = useCallback(() => {
    if (currentWorkflow?.id && currentWorkflow?.agent_name) {
      // פתח modal אישור למחיקה
      openRemoveAgentFromWorkflowModal(currentWorkflow.id, currentWorkflow.agent_name);
    }
  }, [currentWorkflow, openRemoveAgentFromWorkflowModal]);

  const handleOpenAgentInNewTab = useCallback(() => {
    if (currentWorkflow?.agent) {
      window.open(`/chat/${currentWorkflow.agent}`, '_blank');
    }
  }, [currentWorkflow]);

  // בנה את ה-nodes בהתאם לנתונים האמיתיים
  const buildNodes = useCallback(() => {
    const nodes: Node[] = [
      {
        id: '1',
        type: 'startNode',
        position: { x: 100, y: 200 },
        data: {},
      },
    ];

    let nextPosition = 500;

    // אם יש agent ב-workflow, הוסף אותו
    if (currentWorkflow?.agent && currentWorkflow?.agent_name) {
      nodes.push({
        id: '2',
        type: 'agentNode',
        position: { x: nextPosition, y: 200 },
        data: { 
          label: currentWorkflow.agent_name, 
          icon: '🤖',
          agentId: currentWorkflow.agent,
          onDelete: handleDeleteAgent,
          onOpenInNewTab: handleOpenAgentInNewTab,
        },
      });
      nextPosition += 350;
    }

    // תמיד הוסף את כפתור Add Agent
    nodes.push({
      id: 'add-agent',
      type: 'addAgentNode',
      position: { x: nextPosition, y: 220 },
      data: { onAddAgent: handleAddAgent },
    });

    return nodes;
  }, [currentWorkflow, handleAddAgent, handleDeleteAgent, handleOpenAgentInNewTab]);

  // בנה את ה-edges בהתאם ל-nodes
  const buildEdges = useCallback(() => {
    const edges: Edge[] = [];

    if (currentWorkflow?.agent) {
      // חבר Start -> Agent
      edges.push({
        id: 'e1-2',
        source: '1',
        target: '2',
        animated: true,
        style: { stroke: '#a855f7', strokeWidth: 2 },
      });
      // חבר Agent -> Add Button
      edges.push({
        id: 'e2-add',
        source: '2',
        target: 'add-agent',
        animated: true,
        style: { stroke: '#ec4899', strokeWidth: 2 },
      });
    } else {
      // חבר Start -> Add Button ישירות
      edges.push({
        id: 'e1-add',
        source: '1',
        target: 'add-agent',
        animated: true,
        style: { stroke: '#a855f7', strokeWidth: 2 },
      });
    }

    return edges;
  }, [currentWorkflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(buildNodes());
  const [edges, setEdges, onEdgesChange] = useEdgesState(buildEdges());

  // עדכן את ה-nodes וה-edges כשה-workflow משתנה
  useEffect(() => {
    setNodes(buildNodes());
    setEdges(buildEdges());
  }, [buildNodes, buildEdges, setNodes, setEdges]);

  const onConnect: OnConnect = useCallback(
    (connection) => {
      const edge = {
        ...connection,
        animated: true,
        style: { stroke: '#a855f7', strokeWidth: 2 },
      };
      setEdges((eds) => addEdge(edge, eds));
    },
    [setEdges]
  );

  return (
    <div className="flex-1 relative">
      {/* Header */}
      <div className={`absolute top-0 left-0 right-0 z-10 p-6 pointer-events-none ${
        isDarkMode
          ? 'bg-gradient-to-b from-gray-900/80 to-transparent'
          : 'bg-gradient-to-b from-white/90 to-transparent'
      }`}>
        <div className="flex items-center justify-between pointer-events-auto">
          <div>
            <h1 className={`text-2xl font-bold mb-1 ${
              isDarkMode ? 'text-white' : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent'
            }`}>{currentWorkflow?.name || 'Workflow'}</h1>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-700'
            }`}>
              {currentWorkflow?.description || 'No description'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${
              isDarkMode
                ? 'bg-purple-500/20 text-purple-400'
                : 'bg-purple-100 text-purple-700 border border-purple-300'
            }`}>
              🟣 {currentWorkflow?.node_count || 0} nodes
            </span>
          </div>
        </div>
      </div>

      {/* ReactFlow */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-transparent"
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color={isDarkMode ? "#a855f740" : "#a855f730"}
        />
        <Controls 
          className={
            isDarkMode
              ? "!bg-white/[0.05] !border-white/[0.1] [&_button]:!bg-white/[0.05] [&_button]:!border-white/[0.1] [&_button]:!text-white hover:[&_button]:!bg-white/[0.1]"
              : "!bg-white/90 !border-purple-300 [&_button]:!bg-white [&_button]:!border-purple-300 [&_button]:!text-purple-700 hover:[&_button]:!bg-purple-100"
          }
        />
      </ReactFlow>
    </div>
  );
}

export default WorkflowBuilder;

