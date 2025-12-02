"""
Agent Service - Integrates Composio and OpenAI for agent functionality
"""

import os
import asyncio
from asgiref.sync import sync_to_async
import json
from typing import List, Dict, Any
from pathlib import Path
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from agents import Agent as ComposioAgent, Runner
from openai import AsyncOpenAI  # ✅ Changed from OpenAI to AsyncOpenAI
from django.conf import settings
from ...tools.composio_config import APP_SLUGS, TOP_SLUGS_BY_APP
from ..tools_config import get_openai_functions_for_tools
from .agent_tools_service import AgentToolsService


class AgentService:
    """
    Service for managing AI agents, tool connections, and chat logic for each user.
    """

    APP_SLUGS = APP_SLUGS
    TOP_SLUGS_BY_APP = TOP_SLUGS_BY_APP

    def __init__(self, user):
        """
        Initializes the service for a specific user.
        """
        self.user = user
        self.openai_client = None
        self.composio_client = None
        self.agent_tools_service = AgentToolsService()  # Initialize agent tools service
        self.auth_configs = self._load_auth_configs()
        self._tools_cache: Dict[str, list] = {}
        self._initialize_clients()

    def _load_auth_configs(self) -> Dict[str, str]:
        """
        Loads Composio Auth Config IDs from a JSON file in the backend directory.
        """
        try:
            # Navigate from backend/api_agents/agents/services/agent_service.py
            # up to backend/auth_configs.json
            config_path = Path(__file__).parent.parent.parent.parent / "auth_configs.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                    print(f"✅ Loaded {len(configs)} auth configs from {config_path}")
                    return configs
            else:
                print(f"⚠️  Auth configs file not found at {config_path}")
        except Exception as e:
            print(f"❌ Warning: Could not load auth configs: {e}")
        return {}

    def _initialize_clients(self):
        """
        Initializes the OpenAI and Composio clients using API keys from settings.
        """
        try:
            openai_api_key = settings.OPENAI_API_KEY
            if openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=openai_api_key)  # ✅ Use AsyncOpenAI

            composio_api_key = settings.COMPOSIO_API_KEY
            if composio_api_key:
                self.composio_client = Composio(
                    api_key=composio_api_key,
                    provider=OpenAIAgentsProvider()
                )
        except Exception as e:
            print(f"Error initializing clients: {e}")

    def _get_entity_id(self) -> str:
        """
        Returns the user-specific entity ID required by Composio.
        """
        return f"user_{self.user.id}"

    def _get_app_slug(self, app_name: str) -> str:
        """
        Maps a user-friendly app name (e.g., "GMAIL") to the Composio slug (e.g., "gmail").
        """
        app_key = (app_name or "").upper()
        if app_key in self.APP_SLUGS:
            return self.APP_SLUGS[app_key]
        return app_key.lower()

    def _get_tools_for_app(self, app_name: str) -> list:
        """
        Fetches all available Composio FunctionTool objects for a given app.
        """
        if not self.composio_client or not app_name:
            return []

        app_key = app_name.upper()
        if app_key in self._tools_cache:
            return self._tools_cache[app_key]

        slug = self._get_app_slug(app_name)

        try:
            response = self.composio_client.tools.get(
                user_id=self._get_entity_id(),
                toolkits=[slug],
                limit=500
            )
            tools_list = list(response)
            print(f"DEBUG: Fetched {len(tools_list)} tools for {app_key} ({slug})")
            self._tools_cache[app_key] = tools_list
            return tools_list

        except Exception as e:
            print(f"Error fetching Composio tools for {app_key} ({slug}): {e}")
            import traceback
            traceback.print_exc()
            self._tools_cache[app_key] = []
            return []

    async def _chat_without_tools(self, agent_model, message: str, chat_history: List[Dict[str, str]] = None, callback=None) -> str:
        """
        Runs a basic OpenAI chat (no tools) when tool selection fails or is empty.
        Now includes chat history for conversational context and streaming callbacks.

        Args:
            agent_model: Agent model instance
            message: User message
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
        """
        if not self.openai_client:
            return "OpenAI client not configured"

        try:
            if chat_history:
                # Add the system prompt to the beginning of the history
                messages = [{"role": "system", "content": agent_model.prompt}] + chat_history
            else:
                messages = [
                    {"role": "system", "content": agent_model.prompt},
                    {"role": "user", "content": message}
                ]

            # ✅ No sync_to_async wrapper needed - client is already async
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1000,
                stream=True
            )

            # Collect streaming content
            full_content = ""
            word_buffer = ""
            word_index = 0

            # ✅ Use async for - properly yields to event loop!
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content_delta = chunk.choices[0].delta.content
                    full_content += content_delta
                    word_buffer += content_delta

                    # Buffer and emit complete words if callback is provided
                    if callback:
                        # Check for word delimiters
                        delimiters = {' ', '\n', '\t', '.', ',', '!', '?', ';', ':'}
                        if any(d in word_buffer for d in delimiters):
                            # Find earliest delimiter
                            delimiter_positions = [(word_buffer.find(d), d) for d in delimiters if d in word_buffer]
                            delimiter_positions = [(pos, d) for pos, d in delimiter_positions if pos != -1]

                            if delimiter_positions:
                                pos, delimiter = min(delimiter_positions, key=lambda x: x[0])
                                word = word_buffer[:pos + 1]

                                if word.strip():
                                    await callback('content_delta', {
                                        'content': word,
                                        'index': word_index
                                    })
                                    word_index += 1

                                word_buffer = word_buffer[pos + 1:]

            # Emit any remaining buffer
            if callback and word_buffer.strip():
                await callback('content_delta', {
                    'content': word_buffer,
                    'index': word_index
                })

            return full_content

        except Exception as e:
            print(f"Error in (async) OpenAI chat: {e}")
            if callback:
                await callback('error', {'error': str(e)})
            return f"Error: {str(e)}"

    async def _chat_with_composio(self, agent_model, message: str, specific_tools_slugs: List[str], chat_history: List[Dict[str, str]] = None, callback=None, file_attachments: List[Dict] = None) -> str:
        """
        Runs the full agent execution with a specific set of tools and chat history.

        Args:
            agent_model: Agent model instance
            message: User message
            specific_tools_slugs: List of tool slugs to use
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
            file_attachments: List of file attachment dictionaries with file paths
        """
        try:
            if callback:
                await callback('status', {'status': 'tool_calling', 'message': 'Loading Composio tools...'})
            tools = await sync_to_async(self.composio_client.tools.get)(
                user_id=self._get_entity_id(),
                tools=specific_tools_slugs
            )

            print(f"✅ Loaded {len(tools)} specific tools for user {self.user.username}")

            if not tools:
                print("DEBUG: Composio.tools.get returned no tools. Falling back.")
                return await self._chat_without_tools(agent_model, message, chat_history, callback)

            enhanced_instructions = agent_model.prompt

            # === AUTONOMY ENHANCEMENT ===
            autonomy_instructions = (
                "\n\n--- AUTONOMOUS OPERATION MODE ---\n"
                "You are an autonomous AI assistant. When the user requests an action:\n"
                "1. Execute the action immediately without asking for permission\n"
                "2. Do not ask 'Would you like me to...' or 'Should I...'\n"
                "3. Proceed directly with the task using the available tools\n"
                "4. Only ask for clarification if critical information is missing (e.g., email recipient, file name)\n"
                "5. After completing the action, provide a brief confirmation of what was done\n"
                "6. If an error occurs, explain what happened and suggest a solution\n"
                "7. Work efficiently - complete multi-step tasks in sequence without pausing for approval\n"
            )
            enhanced_instructions += autonomy_instructions

            if "GOOGLEDRIVE" in agent_model.app_connections and "GMAIL" in agent_model.app_connections:
                enhanced_instructions += "\n\nIMPORTANT: When asked to send files from Google Drive via Gmail:\n"
                enhanced_instructions += "1. First use GOOGLEDRIVE_FIND_FILE or GOOGLEDRIVE_GET_FILE_BY_ID to locate the file\n"
                enhanced_instructions += "2. Use GOOGLEDRIVE_DOWNLOAD_FILE to get the file content\n"
                enhanced_instructions += "3. Then use GMAIL_SEND_EMAIL_WITH_ATTACHMENT to send the email with the file attached\n"
                enhanced_instructions += "Always perform these steps in sequence and confirm each step's success."

            # === FILE ATTACHMENTS HANDLING ===
            # If files are attached, append their paths to the message for Composio to access
            enhanced_message = message
            if file_attachments:
                file_context = "\n\n📎 **Attached Files:**\n"
                for file_info in file_attachments:
                    file_context += f"- **{file_info['filename']}**\n"
                    file_context += f"  Path: `{file_info['file_path']}`\n"
                    file_context += f"  Size: {file_info['size']} bytes\n"
                    file_context += f"  Type: {file_info['mime_type']}\n"
                enhanced_message += file_context
                print(f"📎 Added {len(file_attachments)} file(s) to Composio context")

            composio_agent = ComposioAgent(
                name=agent_model.name,
                instructions=enhanced_instructions,
                tools=tools,
                model="gpt-4o-mini"
            )

            runner = Runner()

            # Add the current user message (with file paths if any) to chat history
            full_chat_history = (chat_history or []) + [{"role": "user", "content": enhanced_message}]

            # Send heartbeats during Composio runner execution (opaque operation)
            # Since we can't see inside the runner, emit periodic status updates
            if callback:
                await callback('status', {'status': 'processing', 'message': 'Processing with Composio tools...'})

                # Run the runner with periodic heartbeats
                import time
                last_heartbeat = time.time()

                async def run_with_heartbeats():
                    # Create a task for the runner
                    runner_task = asyncio.create_task(
                        runner.run(composio_agent, full_chat_history)
                    )

                    # Periodically send heartbeats while runner is working
                    while not runner_task.done():
                        await asyncio.sleep(2)  # Check every 2 seconds
                        current_time = time.time()
                        if current_time - last_heartbeat >= 3:  # Send heartbeat every 3 seconds
                            await callback('heartbeat', {
                                'message': 'Still processing...',
                                'timestamp': current_time
                            })

                    return await runner_task

                result = await run_with_heartbeats()
            else:
                # Pass the *entire chat history* (including current message with files) to the runner.
                # runner.run() is async, so we await it directly
                result = await runner.run(composio_agent, full_chat_history)

            if hasattr(result, 'final_output'):
                return result.final_output
            elif hasattr(result, 'output'):
                return result.output
            elif hasattr(result, 'content'):
                return result.content
            elif hasattr(result, 'text'):
                return result.text
            elif hasattr(result, 'messages') and len(result.messages) > 0:
                last_message = result.messages[-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                return str(last_message)
            elif isinstance(result, str):
                return result
            else:
                print(f"🔍 RunResult type: {type(result)}")
                print(f"🔍 RunResult attributes: {dir(result)}")
                result_str = str(result)
                if "Final output (str):" in result_str:
                    lines = result_str.split('\n')
                    for i, line in enumerate(lines):
                        if "Final output (str):" in line and i + 2 < len(lines):
                            return lines[i + 2].strip()
                return result_str

        except Exception as e:
            print(f"Error in Composio chat: {e}")
            import traceback
            traceback.print_exc()
            if callback:
                await callback('error', {'error': str(e)})
            return await self._chat_without_tools(agent_model, message, chat_history, callback)

    async def _chat_with_agent_tools(self, agent_model, message: str, chat_history: List[Dict[str, str]] = None, callback=None) -> str:
        """
        Runs chat with agent-specific tools (weather, calculator, etc.).
        Uses OpenAI function calling to execute tools.

        Args:
            agent_model: Agent model instance
            message: User message
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
        """
        if not self.openai_client:
            return "OpenAI client not configured"

        try:
            # Get OpenAI function definitions for enabled agent tools
            agent_tools_functions = get_openai_functions_for_tools(agent_model.agent_tools)

            if not agent_tools_functions:
                # No agent tools enabled, fall back to basic chat
                return await self._chat_without_tools(agent_model, message, chat_history, callback)

            # Build messages with system prompt and history
            if chat_history:
                messages = [{"role": "system", "content": agent_model.prompt}] + chat_history
            else:
                messages = [
                    {"role": "system", "content": agent_model.prompt},
                    {"role": "user", "content": message}
                ]

            print(f"🔧 Chat with {len(agent_tools_functions)} agent tools enabled")

            # Make initial API call with function definitions
            # ✅ No sync_to_async wrapper needed
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=agent_tools_functions,
                tool_choice="auto",
                temperature=0.7,
                max_completion_tokens=1500
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # If no tool calls, return the response directly
            if not tool_calls:
                return response_message.content

            # Add assistant's response to messages
            messages.append(response_message)

            # Execute each tool call
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"🔨 Executing tool: {function_name} with args: {function_args}")

                # Emit tool call start event
                if callback:
                    await callback('tool_call_start', {
                        'tool': function_name,
                        'parameters': function_args
                    })

                # Execute the tool
                tool_result = await sync_to_async(self.agent_tools_service.execute_tool)(
                    function_name,
                    **function_args
                )

                # Emit tool call result event
                if callback:
                    await callback('tool_call_result', {
                        'tool': function_name,
                        'success': tool_result.get('success', False),
                        'result': tool_result.get('data') if tool_result.get('success') else None,
                        'error': tool_result.get('error') if not tool_result.get('success') else None
                    })

                # Format tool result for OpenAI
                if tool_result.get('success'):
                    result_content = json.dumps(tool_result['data'])
                else:
                    result_content = json.dumps({
                        'error': tool_result.get('error', 'Unknown error')
                    })

                # Add tool result to messages
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result_content
                })

            # Get final response from OpenAI with tool results
            if callback:
                await callback('status', {'status': 'responding', 'message': 'Generating response...'})

            # ✅ Use streaming for final response with async for
            final_response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_completion_tokens=1500,
                stream=True
            )

            # Collect streaming content
            full_content = ""
            word_buffer = ""
            word_index = 0

            # ✅ Use async for - properly yields to event loop!
            async for chunk in final_response:
                if chunk.choices[0].delta.content:
                    content_delta = chunk.choices[0].delta.content
                    full_content += content_delta
                    word_buffer += content_delta

                    # Buffer and emit complete words if callback is provided
                    if callback:
                        delimiters = {' ', '\n', '\t', '.', ',', '!', '?', ';', ':'}
                        if any(d in word_buffer for d in delimiters):
                            delimiter_positions = [(word_buffer.find(d), d) for d in delimiters if d in word_buffer]
                            delimiter_positions = [(pos, d) for pos, d in delimiter_positions if pos != -1]

                            if delimiter_positions:
                                pos, delimiter = min(delimiter_positions, key=lambda x: x[0])
                                word = word_buffer[:pos + 1]

                                if word.strip():
                                    await callback('content_delta', {
                                        'content': word,
                                        'index': word_index
                                    })
                                    word_index += 1

                                word_buffer = word_buffer[pos + 1:]

            # Emit any remaining buffer
            if callback and word_buffer.strip():
                await callback('content_delta', {
                    'content': word_buffer,
                    'index': word_index
                })

            return full_content

        except Exception as e:
            print(f"Error in agent tools chat: {e}")
            import traceback
            traceback.print_exc()
            if callback:
                await callback('error', {'error': str(e)})
            return f"Sorry, I encountered an error: {str(e)}"

    async def _chat_with_mixed_tools(self, agent_model, message: str, composio_tool_slugs: List[str], chat_history: List[Dict[str, str]] = None, callback=None) -> str:
        """
        Runs chat with BOTH Composio tools AND agent tools.
        This is the most complex scenario where the agent has both types of tools enabled.

        Strategy: Use OpenAI function calling for agent tools, and Composio runner for Composio tools.
        For now, we'll prioritize based on tool selection - if Composio tools are selected, use Composio;
        if not, use agent tools.

        Args:
            agent_model: Agent model instance
            message: User message
            composio_tool_slugs: List of Composio tool slugs to use
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
        """
        # For now, if we have Composio tools selected, use Composio
        # Agent tools will be handled separately
        if composio_tool_slugs:
            return await self._chat_with_composio(agent_model, message, composio_tool_slugs, chat_history, callback)
        elif agent_model.agent_tools:
            return await self._chat_with_agent_tools(agent_model, message, chat_history, callback)
        else:
            return await self._chat_without_tools(agent_model, message, chat_history, callback)

    def authenticate_tool(self, tool_name: str, additional_fields: Dict[str, Any] = None, redirect_url: str = None) -> Dict[str, Any]:
        """
        Initiates the Composio authentication flow for a specific tool.

        Args:
            tool_name: The name of the tool to authenticate
            additional_fields: Optional additional fields for the connection (e.g., WhatsApp fields)
            redirect_url: Optional URL to redirect to after OAuth completes
        """
        if not self.composio_client:
            return {
                "success": False,
                "error": "Composio client not configured"
            }

        try:
            tool_name = tool_name.upper()
            auth_config_id = self.auth_configs.get(tool_name)

            if not auth_config_id:
                return {
                    "success": False,
                    "error": f"{tool_name} is not yet configured. Please set up the auth config in Composio dashboard first."
                }

            initiate_params = {
                "auth_config_id": auth_config_id,
                "user_id": f"user_{self.user.id}",
            }

            # Add callback URL if provided
            if redirect_url:
                # If relative path, prepend FRONTEND_URL from environment
                if redirect_url.startswith('/'):
                    import os
                    frontend_url = os.environ.get('FRONTEND_URL', 'https://kgen21.com')
                    redirect_url = f"{frontend_url.rstrip('/')}{redirect_url}"

                initiate_params["callback_url"] = redirect_url
                print(f"🔄 OAuth will redirect to: {redirect_url}")

            if additional_fields:
                if 'waba_id' in additional_fields:
                    initiate_params['waba_id'] = additional_fields['waba_id']
                if 'phone_number_id' in additional_fields:
                    initiate_params['phone_number_id'] = additional_fields['phone_number_id']

                print(f"🔧 Initiating {tool_name} with additional fields: {list(additional_fields.keys())}")

            try:
                print(f"🔄 Initiating {tool_name} with auth_config_id: {auth_config_id}")
                response = self.composio_client.connected_accounts.initiate(**initiate_params)

                # Log the full response for debugging
                print(f"🔍 Composio initiate response for {tool_name}: {response}")
                print(f"🔍 Response attributes: {dir(response)}")

                # Extract auth URL
                auth_url = None
                if hasattr(response, 'redirectUrl'):
                    auth_url = response.redirectUrl
                elif hasattr(response, 'redirect_url'):
                    auth_url = response.redirect_url

                # Extract connection status for logging
                connection_status = None
                if hasattr(response, 'connectionStatus'):
                    connection_status = response.connectionStatus
                elif hasattr(response, 'connection_status'):
                    connection_status = response.connection_status
                elif hasattr(response, 'status'):
                    connection_status = response.status

                print(f"🔗 Auth URL: {auth_url}")
                print(f"📊 Connection status: {connection_status}")

                # Check if we have an auth URL
                if not auth_url:
                    print(f"❌ No auth_url found in Composio response for {tool_name}")
                    return {
                        "success": False,
                        "error": f"No authentication URL returned from Composio for {tool_name}"
                    }

                # Return success with auth_url so frontend can open OAuth popup
                # Note: Status will be INITIATED at this point - that's expected!
                # The user needs to complete OAuth to change status to ENABLED
                print(f"✅ Returning auth_url to frontend for OAuth flow")
                return {
                    "success": True,
                    "auth_url": auth_url,
                    "auth_config_id": auth_config_id,
                    "status": connection_status
                }
            except Exception as e:
                print(f"❌ Composio API error for {tool_name}")
                print(f"   Tool: {tool_name}")
                print(f"   Auth Config ID: {auth_config_id}")
                print(f"   Error type: {type(e).__name__}")
                print(f"   Error message: {str(e)}")
                import traceback
                traceback.print_exc()

                # Extract more detailed error if available
                error_detail = str(e)
                if hasattr(e, 'response') and e.response:
                    try:
                        error_detail = f"{error_detail} - Response: {e.response.text if hasattr(e.response, 'text') else e.response}"
                    except:
                        pass

                return {
                    "success": False,
                    "error": f"Failed to authenticate {tool_name}: {error_detail}",
                    "tool_name": tool_name,
                    "auth_config_id": auth_config_id
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def get_connected_tools(self) -> List[str]:
        """
        Gets a list of all actively connected tool names (e.g., ["GMAIL"]) for the user.
        """
        # ... (This function is unchanged and correct) ...
        if not self.composio_client: return []
        try:
            entity_id = f"user_{self.user.id}"
            try:
                response = self.composio_client.connected_accounts.list(entity_id=entity_id)
            except Exception:
                try:
                    response = self.composio_client.connected_accounts.list(user_id=entity_id)
                except Exception:
                    response = self.composio_client.connected_accounts.list()

            connections = None
            if hasattr(response, 'items'): connections = response.items
            elif hasattr(response, 'data'): connections = response.data
            elif hasattr(response, '__iter__'): connections = list(response)
            if not connections: return []

            connected_tools = []
            for conn in connections:
                conn_entity = None
                if hasattr(conn, 'entityId'): conn_entity = conn.entityId
                elif hasattr(conn, 'entity_id'): conn_entity = conn.entity_id
                elif hasattr(conn, 'userId'): conn_entity = conn.userId
                elif hasattr(conn, 'user_id'): conn_entity = conn.user_id
                if conn_entity and conn_entity != entity_id: continue
                integration = None
                if hasattr(conn, 'toolkit') and conn.toolkit:
                    integration = getattr(conn.toolkit, 'slug', None)
                if integration:
                    connected_tools.append(integration.upper())
            return connected_tools
        except Exception as e:
            print(f"Error getting connected tools: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_available_tools(self) -> List[str]:
        """
        Gets all possible tools from the local config file.
        """
        return sorted(self.APP_SLUGS.keys())

    def get_connection_details(self) -> List[Dict[str, Any]]:
        """
        Gets detailed connection info from Composio, including connection IDs.
        """
        # ... (This function is unchanged and correct) ...
        if not self.composio_client: return []
        try:
            entity_id = f"user_{self.user.id}"

            # List ALL connections without filters to find ghost connections
            print(f"🔍 Listing ALL connections for debugging...")
            response = self.composio_client.connected_accounts.list()

            connections = None
            if hasattr(response, 'items'): connections = response.items
            elif hasattr(response, 'data'): connections = response.data
            elif hasattr(response, '__iter__'): connections = list(response)
            if not connections: return []

            connection_details = []
            for conn in connections:
                conn_entity = None
                if hasattr(conn, 'entityId'): conn_entity = conn.entityId
                elif hasattr(conn, 'entity_id'): conn_entity = conn.entity_id
                elif hasattr(conn, 'userId'): conn_entity = conn.userId
                elif hasattr(conn, 'user_id'): conn_entity = conn.user_id

                # Get tool name and ID for logging ALL connections
                tool_name_all = "Unknown"
                conn_id_all = "Unknown"
                if hasattr(conn, 'toolkit') and conn.toolkit:
                    tool_name_all = getattr(conn.toolkit, 'slug', 'Unknown')
                if hasattr(conn, 'id'): conn_id_all = conn.id
                elif hasattr(conn, 'connectionId'): conn_id_all = conn.connectionId

                # Get status for logging
                conn_status_debug = "Unknown"
                if hasattr(conn, 'status'): conn_status_debug = conn.status
                elif hasattr(conn, 'connectionStatus'): conn_status_debug = conn.connectionStatus
                elif hasattr(conn, 'connection_status'): conn_status_debug = conn.connection_status

                print(f"🔍 Found connection: {tool_name_all} | Entity: {conn_entity} | Status: {conn_status_debug} | ID: {conn_id_all}")

                if conn_entity and conn_entity != entity_id: continue

                # Check connection status - only include ACTIVE/ENABLED connections
                # Skip INITIATED (OAuth not completed) or other non-active statuses
                conn_status = None
                if hasattr(conn, 'status'): conn_status = conn.status
                elif hasattr(conn, 'connectionStatus'): conn_status = conn.connectionStatus
                elif hasattr(conn, 'connection_status'): conn_status = conn.connection_status

                # Get tool name for logging
                tool_name_debug = "Unknown"
                if hasattr(conn, 'toolkit') and conn.toolkit:
                    tool_name_debug = getattr(conn.toolkit, 'slug', 'Unknown')

                # Convert status to string for comparison
                # Accept both ACTIVE and ENABLED as valid connection statuses
                if conn_status:
                    status_str = str(conn_status).upper()
                    if status_str not in ['ACTIVE', 'ENABLED']:
                        # Delete old INITIATED connections (ghost connections from incomplete OAuth)
                        if status_str == 'INITIATED':
                            try:
                                connection_id = None
                                if hasattr(conn, 'id'): connection_id = conn.id
                                elif hasattr(conn, 'connectionId'): connection_id = conn.connectionId

                                if connection_id:
                                    print(f"🗑️  Cleaning up INITIATED connection: {tool_name_debug} (ID: {connection_id})")
                                    self.composio_client.connected_accounts.delete(connected_account_id=connection_id)
                                    print(f"✅ Deleted ghost connection: {tool_name_debug}")
                            except Exception as delete_error:
                                print(f"❌ Failed to delete ghost connection {tool_name_debug}: {delete_error}")
                        else:
                            print(f"⏭️  Skipping {tool_name_debug} - status: {status_str} (expected ACTIVE or ENABLED)")
                        continue
                    else:
                        print(f"✅ Found {tool_name_debug} with status: {status_str}")

                integration = None
                connection_id = None
                if hasattr(conn, 'toolkit') and conn.toolkit:
                    integration = getattr(conn.toolkit, 'slug', None)
                if hasattr(conn, 'id'): connection_id = conn.id
                elif hasattr(conn, 'connectionId'): connection_id = conn.connectionId
                if integration and connection_id:
                    connection_details.append({
                        'tool_name': integration.upper(),
                        'connection_id': connection_id,
                        'integrationId': getattr(conn, 'integrationId', None),
                        'entity_id': conn_entity or entity_id,
                    })
            print(f"✅ Found {len(connection_details)} connections for entity {entity_id}")
            return connection_details
        except Exception as e:
            print(f"Error getting connection details: {e}")
            import traceback
            traceback.print_exc()
            return []

    def disconnect_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Disconnects a tool by deleting it from Composio.
        """
        # ... (This function is unchanged and correct) ...
        if not self.composio_client:
            return {"success": False, "error": "Composio client not configured"}
        try:
            tool_name = tool_name.upper()
            connections = self.get_connection_details()
            connection_to_delete = None
            for conn in connections:
                if conn['tool_name'] == tool_name:
                    connection_to_delete = conn
                    break
            if not connection_to_delete:
                return {"success": False, "error": f"No active connection found for {tool_name}"}
            connection_id = connection_to_delete['connection_id']
            try:
                self.composio_client.connected_accounts.delete(connection_id)
                print(f"✅ Disconnected {tool_name} (connection_id: {connection_id})")
                return {"success": True, "message": f"Successfully disconnected {tool_name}", "connection_id": connection_id}
            except Exception as delete_error:
                print(f"Error deleting connection: {delete_error}")
                return {"success": False, "error": f"Failed to disconnect: {str(delete_error)}"}
        except Exception as e:
            print(f"Error in disconnect_tool: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def create_trigger(self, trigger_model) -> dict:
        """
        Creates a new event-based trigger in Composio.
        """
        # ... (This function is unchanged and correct) ...
        try:
            print(f"🔔 Creating trigger: {trigger_model.name}")
            print(f"   Trigger slug: {trigger_model.trigger_slug}")
            print(f"   Config: {trigger_model.trigger_config}")
            result = self.composio_client.triggers.create(
                app=trigger_model.trigger_slug.split('_')[0],
                trigger_name=trigger_model.trigger_slug,
                config=trigger_model.trigger_config
            )
            trigger_id = None
            if hasattr(result, 'id'): trigger_id = result.id
            elif hasattr(result, 'triggerId'): trigger_id = result.triggerId
            elif isinstance(result, dict): trigger_id = result.get('id') or result.get('triggerId')
            print(f"✅ Trigger created: {trigger_id}")
            return {'success': True, 'trigger_id': trigger_id, 'message': 'Trigger created successfully'}
        except Exception as e:
            print(f"❌ Error creating trigger: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def get_available_triggers(self) -> dict:
        """
        Gets the hardcoded list of available triggers for the "Create Trigger" UI.
        """
        # ... (This function is unchanged and correct) ...
        return {
            'GMAIL': [{'slug': 'GMAIL_NEW_GMAIL_MESSAGE', 'name': 'New Email Received', 'type': 'event'}],
            'REDDIT': [
                {'slug': 'REDDIT_NEW_COMMENT_ON_POST', 'name': 'New Comment on Post', 'type': 'event'},
                {'slug': 'REDDIT_NEW_POST_IN_SUBREDDIT', 'name': 'New Post in Subreddit', 'type': 'event'},
            ],
            'GITHUB': [
                {'slug': 'GITHUB_NEW_ISSUE', 'name': 'New Issue Created', 'type': 'event'},
                {'slug': 'GITHUB_NEW_PR', 'name': 'New Pull Request', 'type': 'event'},
                {'slug': 'GITHUB_NEW_COMMIT', 'name': 'New Commit', 'type': 'event'},
            ],
            'SLACK': [
                {'slug': 'SLACK_NEW_MESSAGE', 'name': 'New Message in Channel', 'type': 'event'},
                {'slug': 'SLACK_NEW_MENTION', 'name': 'New Mention', 'type': 'event'},
            ],
            'TWITTER': [
                {'slug': 'TWITTER_NEW_MENTION', 'name': 'New Mention', 'type': 'event'},
                {'slug': 'TWITTER_NEW_FOLLOWER', 'name': 'New Follower', 'type': 'event'},
            ],
            'GOOGLEDRIVE': [{'slug': 'GOOGLEDRIVE_FILE_UPLOADED', 'name': 'New File Uploaded', 'type': 'event'}],
            'GOOGLECALENDAR': [
                {'slug': 'GOOGLECALENDAR_NEW_EVENT', 'name': 'New Calendar Event', 'type': 'event'},
                {'slug': 'GOOGLECALENDAR_EVENT_STARTING', 'name': 'Event Starting Soon', 'type': 'event'},
            ],
        }

    async def select_tools_for_prompt(self, user_prompt: str, app_names: List[str], chat_history: List[Dict[str, str]] = None, has_file_attachments: bool = False) -> List[str]:
        """
        Uses an AI call to select the specific tool slugs needed for a given prompt,
        using the hardcoded TOP_SLUGS_BY_APP dictionary AND chat history.

        Args:
            has_file_attachments: True if the current message has files attached

        ✅ Now async to work with AsyncOpenAI
        """
        if not self.openai_client:
            raise Exception("OpenAI client not configured")

        all_action_slugs = set()
        print(f"Selecting tools for apps: {app_names}")

        for app in app_names:
            if app in self.TOP_SLUGS_BY_APP:
                for slug in self.TOP_SLUGS_BY_APP[app]:
                    all_action_slugs.add(slug)

        if not all_action_slugs:
            print("No action slugs found in composio_config.py for these apps. Returning empty list.")
            return []

        all_action_slugs_list = list(all_action_slugs)
        print(f"Found {len(all_action_slugs_list)} total hardcoded slugs. Asking AI to select...")

        # --- (THIS IS THE FIX) ---
        # This new prompt is more robust and specifically handles multilingual
        # requests and the context of file attachments.
        system_prompt = (
            "You are an expert AI tool selector. Your job is to analyze a user's request "
            "and select the *exact* tool slugs needed to perform the task. "

            "RULES:\n"
            "1.  The user's prompt or history may be in *any language* (e.g., Hebrew, Spanish, English).\n"
            "2.  The 'Available Tools' list is *always* in English.\n"
            "3.  You MUST translate the user's intent to English and match it to the "
            "    correct tool slugs from the 'Available Tools' list.\n"

            "4.  **FILE ATTACHMENT RULE (CRITICAL):**\n"
            "    - If files are attached to the current message (indicated by 'FILES_ATTACHED: true'),\n"
            "      you MUST select attachment-specific tools:\n"
            "      * For Gmail: Use GMAIL_SEND_EMAIL_WITH_ATTACHMENT (NOT GMAIL_SEND_EMAIL)\n"
            "      * For Twitter: Use TWITTER_UPLOAD_MEDIA if uploading media\n"
            "      * For other platforms: Use the appropriate upload/attachment tool\n"
            "    - If the 'Conversation History' contains 'Attached files:' and the user mentions\n"
            "      posting, uploading, or using those files, also include the relevant tool.\n"

            "5.  Return a JSON object with a single key: 'tools'.\n"
            "6.  The value of 'tools' must be a JSON list of the required tool slugs (strings).\n"
            "7.  If no tools are needed, return {\"tools\": []}."
        )
        # --- (END OF FIX) ---

        history_str = ""
        if chat_history:
            history_str = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in chat_history]
            )

        # Add file attachment indicator
        files_indicator = "FILES_ATTACHED: true\n\n" if has_file_attachments else ""

        human_prompt = (
            f"{files_indicator}"
            f"--- Conversation History (for context) ---\n"
            f"{history_str}\n\n"
            f"--- Current User Prompt ---\n"
            f"{user_prompt}\n\n"
            f"--- Available Tools ---\n"
            f"{json.dumps(all_action_slugs_list)}"
        )

        try:
            # ✅ No sync wrapper needed - already async
            # Using gpt-4o-mini for tool selection as it's more reliable for structured JSON responses
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human_prompt}
                ],
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content
            print(f"AI Tool Selector response: {response_content}")

            selected_tools = []
            try:
                data = json.loads(response_content)
                if "tools" in data and isinstance(data["tools"], list):
                    selected_tools = data["tools"]
                elif isinstance(data, list):
                    selected_tools = data
                elif isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            selected_tools = value
                            break

                if not all(isinstance(tool, str) for tool in selected_tools):
                    raise ValueError("AI response was not a list of strings.")

                print(f"Successfully selected {len(selected_tools)} tools.")
                return selected_tools

            except Exception as e:
                print(f"Error parsing AI tool selection response: {e}. Returning empty list.")
                return []

        except Exception as e:
            print(f"Error calling OpenAI for tool selection: {e}")
            return []


    def run_chat_with_tools(self, agent_model, message: str, attachments: list, tool_slugs: List[str]) -> str:
        """
        This function is obsolete and no longer called by views.py.
        The logic has been moved into the 'chat' action in AgentViewSet.
        """
        print("--- [WARNING] Obsolete function 'run_chat_with_tools' was called. ---")
        try:
            message_with_context = message
            if attachments:
                file_context = "\n\nAttached files:\n"
                for att in attachments:
                    file_context += f"- {att['filename']} ({att['mime_type']}, {att['size']} bytes)\n"
                    file_context += f"  File path: {att['file_path']}\n"
                message_with_context = message + file_context

            if not tool_slugs or not self.composio_client:
                print("No tool_slugs provided or client not configured. Falling back to basic chat.")
                return asyncio.run(self._chat_without_tools(agent_model, message_with_context))

            print(f"Executing chat with {len(tool_slugs)} specific tools.")
            return asyncio.run(self._chat_with_composio(
                agent_model,
                message_with_context,
                specific_tools_slugs=tool_slugs
            ))

        except Exception as e:
            print(f"Error in run_chat_with_tools: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"

    async def generate_greeting_message(self, agent_model) -> str:
        """
        Generates a personalized greeting message for the agent.
        Uses agent name, purpose (from prompt), and available tools.

        Returns a warm, professional greeting that:
        - Introduces the agent by name
        - Explains what it can help with
        - Lists its capabilities based on connected tools

        ✅ Now async to work with AsyncOpenAI
        """
        if not self.openai_client:
            # Fallback greeting if OpenAI is not configured
            tools_text = ""
            all_tools = []
            if agent_model.app_connections:
                all_tools.extend(agent_model.app_connections)
            if agent_model.agent_tools:
                all_tools.extend(agent_model.agent_tools)
            if all_tools:
                tools_list = ", ".join(all_tools)
                tools_text = f" I have access to {tools_list} to assist you."
            return f"Hi! I'm {agent_model.name}. I'm here to help you.{tools_text}"

        try:
            # Build context about available tools (both Composio and agent tools)
            tools_context = ""
            all_tools = []

            if agent_model.app_connections:
                all_tools.extend(agent_model.app_connections)

            if agent_model.agent_tools:
                all_tools.extend(agent_model.agent_tools)

            if all_tools:
                tools_list = ", ".join(all_tools)
                tools_context = f"\nAvailable Tools: {tools_list}"
            else:
                tools_context = "\nAvailable Tools: General assistance (no specific tools)"

            system_prompt = (
                "You are a greeting assistant. Generate a warm, professional greeting message "
                "for an AI agent based on its name, purpose, and capabilities.\n\n"
                "The greeting should:\n"
                "1. Start with 'Hi! I'm [Agent Name]'\n"
                "2. Briefly describe the agent's purpose in one sentence\n"
                "3. Mention what specific things it can help with based on available tools\n"
                "4. Be 2-3 sentences maximum\n"
                "5. Be conversational, friendly, and helpful\n"
                "6. Focus on capabilities, not limitations\n\n"
                "Return ONLY the greeting message, nothing else."
            )

            user_prompt = (
                f"Agent Name: {agent_model.name}\n"
                f"Agent Purpose/Prompt: {agent_model.prompt}\n"
                f"{tools_context}\n\n"
                f"Generate a personalized greeting message for this agent."
            )

            # ✅ No sync wrapper needed - already async
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_completion_tokens=150
            )

            greeting = response.choices[0].message.content.strip()
            print(f"✅ Generated greeting for agent {agent_model.name}: {greeting[:50]}...")
            return greeting

        except Exception as e:
            print(f"Error generating greeting message: {e}")
            import traceback
            traceback.print_exc()

            # Fallback to simple greeting
            tools_text = ""
            all_tools = []
            if agent_model.app_connections:
                all_tools.extend(agent_model.app_connections)
            if agent_model.agent_tools:
                all_tools.extend(agent_model.agent_tools)
            if all_tools:
                tools_list = ", ".join(all_tools)
                tools_text = f" I have access to {tools_list} to assist you."
            return f"Hi! I'm {agent_model.name}. I'm here to help you.{tools_text}"
