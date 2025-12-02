import { useState, useRef, useMemo } from 'react';
import useDarkModeStore from '../../../../../store/darkmode.store';
import useModalsStore from '../../../../../store/modals.store';
import { useUpdateAgent, useGetAgentFiles, useUploadFiles, useDeleteFile, useDownloadFile, useGetAvailableAgentTools, useAddAgentTool, useRemoveAgentTool } from '../hooks';
import { formatAvatarUrl } from '../utils';
import { useConnectTool, useDisconnectTool } from '../../integrations/hooks';
import { mapUnifiedToolsToIntegrations, getGlowClass } from '../utils';
import { DeleteFileModal } from './modals';
import type { Agent, AgentFile, UnifiedTool } from '../types';
import type { Integration } from '../../integrations/components/types';

interface AgentSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  agent?: Agent;
}

interface SectionProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  isExpanded: boolean;
  onToggle: () => void;
  iconBgColor: string;
  agentName: string;
  setAgentName: (name: string) => void;
  agentPrompt: string;
  setAgentPrompt: (prompt: string) => void;
  onSaveSettings: () => void;
  isSaving: boolean;
  selectedFiles?: File[];
  onFileSelect?: (files: File[]) => void;
  onUploadFiles?: () => void;
  isUploading?: boolean;
  uploadedFiles?: AgentFile[];
  onDeleteFile?: (fileId: string | number, fileName: string) => void;
  onDownloadFile?: (fileId: string | number, fileName: string) => void;
  isDownloading?: boolean;
  onCreateTrigger?: () => void;
  tools?: UnifiedTool[];
  onAddTool?: (toolName: string) => void;
  onRemoveTool?: (toolName: string) => void;
  onConnectTool?: (toolName: string) => void;
  onDisconnectTool?: (toolName: string) => void;
  isConnecting?: boolean;
  connectingToolName?: string | null;
  isDisconnecting?: boolean;
  disconnectingToolName?: string | null;
  isAddingTool?: boolean;
  addingToolName?: string | null;
  isRemovingTool?: boolean;
  removingToolName?: string | null;
  selectedAvatar?: File | null;
  previewUrl?: string | null;
  onAvatarSelect?: (file: File | null) => void;
  agentAvatar?: string | null;
}

function SidebarSection({ icon, title, subtitle, isExpanded, onToggle, iconBgColor, agentName, setAgentName, agentPrompt, setAgentPrompt, onSaveSettings, isSaving, selectedFiles = [], onFileSelect, onUploadFiles, isUploading = false, uploadedFiles = [], onDeleteFile, onDownloadFile, isDownloading = false, onCreateTrigger, tools = [], onAddTool, onRemoveTool, onConnectTool, onDisconnectTool, isConnecting = false, connectingToolName = null, isDisconnecting = false, disconnectingToolName = null, isAddingTool = false, addingToolName = null, isRemovingTool = false, removingToolName = null, selectedAvatar, previewUrl, onAvatarSelect, agentAvatar }: SectionProps) {
  const { isDarkMode } = useDarkModeStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const avatarInputRef = useRef<HTMLInputElement>(null);
  
  // המרת avatar ל-format מתאים
  const formattedAvatar = formatAvatarUrl(agentAvatar || null);
  
  // חלוקת הכלים לקטגוריות
  const agentTools = tools.filter(tool => tool.is_connected_to_agent);
  const availableTools = tools.filter(tool => !tool.is_connected_to_agent);
  
  return (
    <div className="mb-4 mx-4">
      <div className={`rounded-2xl overflow-hidden border transition-all duration-300 ${
        isDarkMode
          ? 'bg-white/[0.03] border-white/[0.05]'
          : 'bg-gradient-to-br from-white to-purple-50/30 border-purple-200 shadow-sm'
      } ${getGlowClass(iconBgColor)}`}>
        <button
          onClick={onToggle}
          className={`w-full flex items-center gap-4 p-5 transition-all duration-200 ${
            isDarkMode
              ? 'hover:bg-white/[0.03]'
              : 'hover:bg-gradient-to-br hover:from-purple-100/50 hover:to-pink-100/30'
          }`}
        >
          <div className={`flex-shrink-0 w-12 h-12 ${iconBgColor} rounded-xl flex items-center justify-center ${
            !isDarkMode && 'border-2 border-white shadow-md'
          }`}>
            {icon}
          </div>
          <div className="flex-1 text-left">
            <h3 className={`font-semibold text-base ${
              isDarkMode ? 'text-white' : 'text-gray-900'
            }`}>
              {title}
            </h3>
            <p className={`text-sm ${
              isDarkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              {subtitle}
            </p>
          </div>
          <svg
            className={`w-5 h-5 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''} ${
              isDarkMode ? 'text-gray-400' : 'text-purple-600'
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {isExpanded && title === 'Basic Settings' && (
          <div className="p-4 pt-0 space-y-4">
            {/* Avatar Section */}
            <div>
              <label className="block text-white dark:text-gray-100 text-sm font-semibold mb-2">
                Avatar
              </label>
              <input
                ref={avatarInputRef}
                type="file"
                accept="image/svg+xml,image/jpeg,image/jpg,image/png"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0] || null;
                  onAvatarSelect?.(file);
                }}
              />
              <div className="flex items-center gap-4">
                <div 
                  className="w-16 h-16 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl flex items-center justify-center text-3xl overflow-hidden"
                  style={previewUrl || formattedAvatar ? { backgroundImage: `url(${previewUrl || formattedAvatar})`, backgroundSize: 'cover', backgroundPosition: 'center' } : {}}
                >
                  {!previewUrl && !formattedAvatar && '🤖'}
                </div>
                {selectedAvatar ? (
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-green-500 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>Click Save Changes to save</span>
                    </div>
                    <button 
                      onClick={() => onAvatarSelect?.(null)}
                      className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-500 transition-colors"
                      title="Cancel"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <button 
                    onClick={() => avatarInputRef.current?.click()}
                    className="px-4 py-2 bg-white/[0.05] dark:bg-white/[0.03] hover:bg-white/[0.08] dark:hover:bg-white/[0.05] rounded-xl text-white text-xs font-medium transition-all duration-200 flex items-center gap-2"
                  >
                    <span>+</span>
                    <span>Select Image</span>
                  </button>
                )}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-600 mt-2">
                Supported formats: SVG, JPEG, PNG (max 5MB)
              </p>
            </div>

            {/* Agent Name */}
            <div>
              <label className="block text-white dark:text-gray-100 text-sm font-semibold mb-2">
                Agent Name
              </label>
              <input
                type="text"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                placeholder="Agent Name"
                className="w-full px-4 py-3 bg-white/[0.05] dark:bg-white/[0.03] border border-white/[0.1] dark:border-white/[0.05] rounded-xl text-white text-sm focus:outline-none focus:bg-white/[0.08] dark:focus:bg-white/[0.05] focus:border-purple-500/50 transition-all duration-200"
              />
            </div>

            {/* Prompt */}
            <div>
              <label className="block text-white dark:text-gray-100 text-sm font-semibold mb-2">
                Instructions (Prompt)
              </label>
              <textarea
                value={agentPrompt}
                onChange={(e) => setAgentPrompt(e.target.value)}
                placeholder="Enter agent instructions..."
                rows={6}
                className="w-full px-4 py-3 bg-white/[0.05] dark:bg-white/[0.03] border border-white/[0.1] dark:border-white/[0.05] rounded-xl text-white text-sm focus:outline-none focus:bg-white/[0.08] dark:focus:bg-white/[0.05] focus:border-purple-500/50 transition-all duration-200 resize-none"
              />
            </div>

            {/* Save Button */}
            <button 
              onClick={onSaveSettings}
              disabled={isSaving}
              className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 dark:from-purple-500 dark:to-purple-600 hover:from-purple-700 hover:to-purple-800 dark:hover:from-purple-600 dark:hover:to-purple-700 rounded-xl text-white text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-purple-600 disabled:hover:to-purple-700"
            >
              {isSaving ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  <span>Save Changes</span>
                </>
              )}
            </button>
          </div>
        )}
        
        {isExpanded && title === 'Tools' && (
          <div className="p-4 pt-0 space-y-4">
            {/* Description */}
            <div className={`p-3 border rounded-xl ${
              isDarkMode
                ? 'bg-blue-500/10 border-blue-500/30'
                : 'bg-blue-500/20 border-blue-500/30'
            }`}>
              <p className={`text-sm ${
                isDarkMode ? 'text-blue-200' : 'text-blue-300'
              }`}>
                Configure tools to enhance your agent's capabilities.
              </p>
            </div>

            {/* Agent Tools */}
            <div>
              <h4 className={`text-sm font-semibold mb-3 ${
                isDarkMode ? 'text-white' : 'text-gray-100'
              }`}>
                Agent Tools
              </h4>
              <div className="max-h-[240px] overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {agentTools.length === 0 ? (
                  <div className={`p-4 text-center rounded-xl ${
                    isDarkMode ? 'bg-white/[0.02]' : 'bg-white/[0.03]'
                  }`}>
                    <p className={`text-sm ${
                      isDarkMode ? 'text-gray-500' : 'text-gray-400'
                    }`}>
                      No tools connected yet
                    </p>
                  </div>
                ) : (
                  agentTools.map((tool) => (
                    <div key={tool.tool_name} className={`flex items-center justify-between p-3 rounded-xl ${
                      isDarkMode ? 'bg-white/[0.03]' : 'bg-white/[0.02]'
                    }`}>
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg flex-shrink-0 ${
                          isDarkMode ? 'bg-cyan-500/20' : 'bg-cyan-500/30'
                        }`}>
                          {tool.icon || '🔧'}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className={`text-sm font-medium truncate ${
                            isDarkMode ? 'text-white' : 'text-gray-900'
                          }`}>
                            {tool.name}
                          </p>
                          <p className={`text-xs truncate ${
                            isDarkMode ? 'text-gray-500' : 'text-gray-600'
                          }`}>
                            {tool.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        {tool.isToolRequirePremission && tool.is_connected_to_account && (
                          <button
                            onClick={() => onDisconnectTool?.(tool.tool_name)}
                            disabled={isDisconnecting && disconnectingToolName === tool.name}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                              isDarkMode
                                ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400'
                                : 'bg-yellow-500/30 hover:bg-yellow-500/40 text-yellow-600'
                            }`}
                          >
                            {isDisconnecting && disconnectingToolName === tool.name ? (
                              <>
                                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span>Disconnecting...</span>
                              </>
                            ) : (
                              'Disconnect'
                            )}
                          </button>
                        )}
                        <button
                          onClick={() => onRemoveTool?.(tool.tool_name)}
                          disabled={isRemovingTool && removingToolName === tool.name}
                          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                            isDarkMode
                              ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400'
                              : 'bg-red-500/30 hover:bg-red-500/40 text-red-600'
                          }`}
                        >
                          {isRemovingTool && removingToolName === tool.name ? (
                            <>
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              <span>Removing...</span>
                            </>
                          ) : (
                            'Remove'
                          )}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Available Tools */}
            <div>
              <h4 className={`text-sm font-semibold mb-3 ${
                isDarkMode ? 'text-white' : 'text-gray-100'
              }`}>
                Available Tools
              </h4>
              <div className="max-h-[240px] overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {availableTools.length === 0 ? (
                  <div className={`p-4 text-center rounded-xl ${
                    isDarkMode ? 'bg-white/[0.02]' : 'bg-white/[0.03]'
                  }`}>
                    <p className={`text-sm ${
                      isDarkMode ? 'text-gray-500' : 'text-gray-400'
                    }`}>
                      All tools are already connected
                    </p>
                  </div>
                ) : (
                  availableTools.map((tool) => (
                    <div key={tool.tool_name} className={`flex items-center justify-between p-3 rounded-xl ${
                      isDarkMode ? 'bg-white/[0.03]' : 'bg-white/[0.02]'
                    }`}>
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-lg flex-shrink-0 ${
                          isDarkMode ? 'bg-green-500/20' : 'bg-green-500/30'
                        }`}>
                          {tool.icon || '🔧'}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className={`text-sm font-medium truncate ${
                            isDarkMode ? 'text-white' : 'text-gray-900'
                          }`}>
                            {tool.name}
                          </p>
                          <p className={`text-xs truncate ${
                            isDarkMode ? 'text-gray-500' : 'text-gray-600'
                          }`}>
                            {tool.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 flex-shrink-0">
                        {tool.isToolRequirePremission && !tool.is_connected_to_account ? (
                          <button
                            onClick={() => onConnectTool?.(tool.tool_name)}
                            disabled={isConnecting && connectingToolName === tool.name}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                              isDarkMode
                                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                                : 'bg-blue-500 hover:bg-blue-600 text-white'
                            }`}
                          >
                            {isConnecting && connectingToolName === tool.name ? (
                              <>
                                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span>Connecting...</span>
                              </>
                            ) : (
                              'Connect'
                            )}
                          </button>
                        ) : tool.isToolRequirePremission && tool.is_connected_to_account ? (
                          <>
                            <button
                              onClick={() => onDisconnectTool?.(tool.tool_name)}
                              disabled={isDisconnecting && disconnectingToolName === tool.name}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                                isDarkMode
                                  ? 'bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400'
                                  : 'bg-yellow-500/30 hover:bg-yellow-500/40 text-yellow-600'
                              }`}
                            >
                              {isDisconnecting && disconnectingToolName === tool.name ? (
                                <>
                                  <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  <span>Disconnecting...</span>
                                </>
                              ) : (
                                'Disconnect'
                              )}
                            </button>
                            <button
                              onClick={() => onAddTool?.(tool.tool_name)}
                              disabled={isAddingTool && addingToolName === tool.name}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                                isDarkMode
                                  ? 'bg-purple-600 hover:bg-purple-700 text-white'
                                  : 'bg-purple-500 hover:bg-purple-600 text-white'
                              }`}
                            >
                              {isAddingTool && addingToolName === tool.name ? (
                                <>
                                  <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  <span>Adding...</span>
                                </>
                              ) : (
                                'Add'
                              )}
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => onAddTool?.(tool.tool_name)}
                            disabled={isAddingTool && addingToolName === tool.name}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                              isDarkMode
                                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                                : 'bg-purple-500 hover:bg-purple-600 text-white'
                            }`}
                          >
                            {isAddingTool && addingToolName === tool.name ? (
                              <>
                                <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span>Adding...</span>
                              </>
                            ) : (
                              'Add'
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
        
        {isExpanded && title === 'Files' && (
          <div className="p-4 pt-0 space-y-4">
            {/* Description */}
            <div className="p-3 bg-green-500/10 dark:bg-green-500/20 border border-green-500/30 rounded-xl">
              <p className="text-sm text-green-200 dark:text-green-300">
                Upload files to enrich your agent's knowledge base.
              </p>
            </div>

            {/* Upload Files Section */}
            <div className="p-4 bg-white/[0.03] dark:bg-white/[0.02] rounded-xl border border-white/[0.05]">
              <h4 className="text-white dark:text-gray-100 text-base font-semibold mb-3">
                Upload Files
              </h4>
              
              <input
                ref={fileInputRef}
                type="file"
                multiple
                className="hidden"
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
                  onFileSelect?.(files);
                }}
              />
              
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-xs font-medium transition-all duration-200"
                  type="button"
                >
                  יש לבחור קבצים
                </button>
                <span className="px-4 py-2 bg-white/[0.05] rounded-lg text-gray-400 text-xs flex items-center">
                  {selectedFiles.length > 0 
                    ? `${selectedFiles.length} ${selectedFiles.length === 1 ? 'קובץ נבחר' : 'קבצים נבחרו'}`
                    : 'לא נבחר קובץ'}
                </span>
              </div>

              {/* Selected Files Preview */}
              {selectedFiles.length > 0 && (
                <div className="mb-4 space-y-2">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="p-2 bg-white/[0.05] rounded-lg flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span className="text-white text-xs truncate">{file.name}</span>
                        <span className="text-gray-500 text-xs">({(file.size / 1024).toFixed(2)} KB)</span>
                      </div>
                      <button
                        onClick={() => {
                          const newFiles = selectedFiles.filter((_, i) => i !== index);
                          onFileSelect?.(newFiles);
                        }}
                        className="text-red-400 hover:text-red-300 text-xs ml-2"
                        type="button"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              <button
                onClick={onUploadFiles}
                disabled={selectedFiles.length === 0 || isUploading}
                className="w-full py-3 bg-gray-600 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2"
              >
                {isUploading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>מעלה...</span>
                  </>
                ) : (
                  <span>Upload File</span>
                )}
              </button>
            </div>

            {/* Uploaded Files Table */}
            {uploadedFiles.length > 0 ? (
              <div className={`overflow-x-auto table-scrollbar ${isDarkMode ? 'dark' : ''}`}>
                <table className="w-full min-w-[600px]">
                  <thead>
                    <tr className="border-b border-white/[0.1]">
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-400">FILENAME</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-400">STATUS</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-400">UPLOADED AT</th>
                      <th className="text-left py-2 px-3 text-xs font-semibold text-gray-400">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {uploadedFiles.map((file) => {
                      const fileId = file.id;
                      return (
                      <tr key={fileId} className="border-b border-white/[0.05]">
                        <td className="py-3 px-3 text-xs text-white truncate max-w-[150px]" title={file.original_filename}>
                          {file.original_filename}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400">
                            Active
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-gray-400 whitespace-nowrap">
                          {new Date(file.uploaded_at).toLocaleDateString('he-IL', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric'
                          })}
                        </td>
                        <td className="py-3 px-3 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => onDownloadFile?.(file.id, file.original_filename)}
                              className="text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                              title="הורד קובץ"
                              type="button"
                              disabled={isDownloading}
                            >
                              <svg 
                                className="w-4 h-4" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={2} 
                                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" 
                                />
                              </svg>
                            </button>
                            <button
                              onClick={() => onDeleteFile?.(file.id, file.original_filename)}
                              className="text-red-400 hover:text-red-300 transition-colors"
                              type="button"
                              title="מחק קובץ"
                            >
                              <svg 
                                className="w-4 h-4" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                              >
                                <path 
                                  strokeLinecap="round" 
                                  strokeLinejoin="round" 
                                  strokeWidth={2} 
                                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" 
                                />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-white/[0.05] rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-gray-400 text-sm">No files uploaded yet.</p>
              </div>
            )}
          </div>
        )}
        
        {isExpanded && title === 'Triggers' && (
          <div className="p-4 pt-0 space-y-4">
            {/* Description */}
            <div className="p-3 bg-orange-500/10 dark:bg-orange-500/20 border border-orange-500/30 rounded-xl">
              <p className="text-sm text-orange-200 dark:text-orange-300">
                Set up automated triggers to execute your agent on a schedule.
              </p>
            </div>

            {/* Create Trigger Button */}
            <button 
              onClick={onCreateTrigger}
              className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 rounded-xl text-white text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2"
            >
              <span className="text-lg">+</span>
              Create Trigger
            </button>

            {/* Empty State */}
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-white/[0.05] rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-gray-300 text-base font-semibold mb-1">No triggers configured</p>
              <p className="text-gray-500 text-sm">Create your first trigger to get started</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function AgentSidebar({ isOpen, onClose, agent }: AgentSidebarProps) {
  const { isDarkMode } = useDarkModeStore();
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [isAddingTool, setIsAddingTool] = useState(false);
  const [addingToolName, setAddingToolName] = useState<string | null>(null);
  const [isRemovingTool, setIsRemovingTool] = useState(false);
  const [removingToolName, setRemovingToolName] = useState<string | null>(null);

  const { isUpdating, agentName, setAgentName, agentPrompt, setAgentPrompt, handleSaveSettings, updateAgentAsync, selectedAvatar, previewUrl, handleAvatarSelect } = useUpdateAgent(agent?.id || '', agent);

  // Files hooks
  const { uploadedFiles } = useGetAgentFiles(agent?.id, expandedSection === 'files');
  const { selectedFiles, handleFileSelect, handleUploadFiles, isUploading } = useUploadFiles(agent?.id);
  const { handleDeleteFile, confirmDelete, isDeleting } = useDeleteFile(agent?.id);
  const { handleDownloadFile, isDownloading } = useDownloadFile();
  
  // Tools hooks
  const { data: tools } = useGetAvailableAgentTools(agent?.id || '');
  // handlers for CRUD tools
  const addAgentToolMutation = useAddAgentTool(agent?.id || '');
  const removeAgentToolMutation = useRemoveAgentTool(agent?.id || '');
  
  // המרת tools ל-integrations עבור useConnectTool
  const integrationsFromTools = useMemo<Integration[]>(() => {
    if (!tools) return [];
    return mapUnifiedToolsToIntegrations(tools);
  }, [tools]);

  const { connectTool:handleConnectTool, isConnecting, connectingToolName } = useConnectTool(integrationsFromTools);
  const { disconnectTool:handleDisconnectTool, isDisconnecting, disconnectingToolName } = useDisconnectTool(integrationsFromTools);
  
  
  // Modal state
  const { deleteFileModal, closeDeleteFileModal, openCreateTriggerModal } = useModalsStore();

  const handleAddTool = async (toolName: string) => {
    // מציאת הכלי כדי לבדוק אם הוא דורש הרשאה
    const tool = tools?.find(t => t.tool_name === toolName);
    
    if (!tool) {
      console.error('Tool not found:', toolName);
      return;
    }

    setIsAddingTool(true);
    setAddingToolName(tool.name);

    try {
      if (tool.isToolRequirePremission) {
        await updateAgentAsync({ app_connections: [...(agent?.app_connections || []), tool.tool_name] });
      } else {
        await addAgentToolMutation.mutateAsync({ tool_name: toolName });
      }
    } finally {
      setIsAddingTool(false);
      setAddingToolName(null);
    }
  };

  const handleRemoveToolWrapper = async (toolName: string) => {
    // מציאת הכלי כדי לבדוק אם הוא דורש הרשאה
    const tool = tools?.find(t => t.tool_name === toolName);
    
    if (!tool) {
      console.error('Tool not found:', toolName);
      return;
    }

    setIsRemovingTool(true);
    setRemovingToolName(tool.name);

    try {
      const newAppConnections = agent?.app_connections?.filter(connection => connection !== tool.tool_name) || [];
      // אם הכלי דורש הרשאה - גם מסירים אותו מ-app_connections
      if (tool.isToolRequirePremission) {
        await updateAgentAsync({ app_connections: newAppConnections });
      } else {
        await removeAgentToolMutation.mutateAsync(toolName);
      }
    } finally {
      setIsRemovingTool(false);
      setRemovingToolName(null);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className={`border-r backdrop-blur-sm flex flex-col transition-all duration-300 ease-in-out overflow-hidden ${
      isOpen ? 'w-full md:w-[420px]' : 'w-0 border-r-0'
    } ${
      isDarkMode
        ? 'border-white/[0.08] bg-gradient-to-b from-gray-900/50 to-gray-900/80'
        : 'border-purple-300/50 bg-white/80'
    } ${
      isOpen ? 'absolute md:relative inset-0 z-50 md:z-auto' : ''
    }`}>
      {/* Header */}
      <div className={`p-6 border-b ${
        isDarkMode ? 'border-white/[0.08]' : 'border-purple-200'
      }`}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              isDarkMode
                ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20'
                : 'bg-gradient-to-br from-purple-400 to-pink-500'
            }`}>
              <svg className={`w-5 h-5 ${
                isDarkMode ? 'text-purple-400' : 'text-white'
              }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h2 className={`text-xl font-bold ${
                isDarkMode ? 'text-white' : 'bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent'
              }`}>Agent Settings</h2>
              <p className={`text-sm ${
                isDarkMode ? 'text-gray-400' : 'text-gray-700'
              }`}>Configure your AI companion</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${
              isDarkMode
                ? 'hover:bg-white/[0.05] text-gray-400'
                : 'hover:bg-purple-100 text-purple-700'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Sections */}
      <div className="flex-1 overflow-y-auto py-4 custom-scrollbar">
        <SidebarSection
          icon={
            <svg className="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
          title="Basic Settings"
          subtitle="Name & prompt configuration"
          isExpanded={expandedSection === 'basic'}
          onToggle={() => toggleSection('basic')}
          iconBgColor="bg-purple-500/20"
          agentName={agentName}
          setAgentName={setAgentName}
          agentPrompt={agentPrompt}
          setAgentPrompt={setAgentPrompt}
          onSaveSettings={handleSaveSettings}
          isSaving={isUpdating}
          selectedAvatar={selectedAvatar}
          previewUrl={previewUrl}
          onAvatarSelect={handleAvatarSelect}
          agentAvatar={agent?.avatar_base64 || null}
        />

        <SidebarSection
          icon={
            <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          title="Tools"
          subtitle="Enhance agent capabilities"
          isExpanded={expandedSection === 'tools'}
          onToggle={() => toggleSection('tools')}
          iconBgColor="bg-blue-500/20"
          agentName={agentName}
          setAgentName={setAgentName}
          agentPrompt={agentPrompt}
          setAgentPrompt={setAgentPrompt}
          onSaveSettings={handleSaveSettings}
          isSaving={isUpdating}
          tools={tools}
          onAddTool={handleAddTool}
          onRemoveTool={handleRemoveToolWrapper}
          onConnectTool={handleConnectTool}
          onDisconnectTool={handleDisconnectTool}
          isConnecting={isConnecting}
          connectingToolName={connectingToolName}
          isDisconnecting={isDisconnecting}
          disconnectingToolName={disconnectingToolName}
          isAddingTool={isAddingTool}
          addingToolName={addingToolName}
          isRemovingTool={isRemovingTool}
          removingToolName={removingToolName}
        />

        <SidebarSection
          icon={
            <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          title="Files"
          subtitle="Knowledge base enrichment"
          isExpanded={expandedSection === 'files'}
          onToggle={() => toggleSection('files')}
          iconBgColor="bg-green-500/20"
          agentName={agentName}
          setAgentName={setAgentName}
          agentPrompt={agentPrompt}
          setAgentPrompt={setAgentPrompt}
          onSaveSettings={handleSaveSettings}
          isSaving={isUpdating}
          selectedFiles={selectedFiles}
          onFileSelect={handleFileSelect}
          onUploadFiles={handleUploadFiles}
          isUploading={isUploading}
          uploadedFiles={uploadedFiles}
          onDeleteFile={handleDeleteFile}
          onDownloadFile={handleDownloadFile}
          isDownloading={isDownloading}
        />

        <SidebarSection
          icon={
            <svg className="w-7 h-7 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          title="Triggers"
          subtitle="Automated execution"
          isExpanded={expandedSection === 'triggers'}
          onToggle={() => toggleSection('triggers')}
          iconBgColor="bg-red-500/20"
          agentName={agentName}
          setAgentName={setAgentName}
          agentPrompt={agentPrompt}
          setAgentPrompt={setAgentPrompt}
          onSaveSettings={handleSaveSettings}
          isSaving={isUpdating}
          onCreateTrigger={() => agent?.id && openCreateTriggerModal(agent.id)}
        />
      </div>

      {/* Delete File Modal */}
      <DeleteFileModal
        isOpen={deleteFileModal.isOpen}
        fileName={deleteFileModal.fileName || ''}
        onConfirm={() => {
          if (deleteFileModal.fileId) {
            confirmDelete(deleteFileModal.fileId);
          }
        }}
        onCancel={closeDeleteFileModal}
        isDeleting={isDeleting}
      />
    </div>
  );
}

export default AgentSidebar;

