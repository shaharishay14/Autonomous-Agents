"""
Agent Service - Integrates Composio and OpenAI for agent functionality
"""

import os
import asyncio
from asgiref.sync import sync_to_async
import json
import datetime
import random
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
from .context_injection_manager import get_context_manager
from .tool_dependency_engine import get_tool_dependency_engine
from .model_selection_strategy import get_model_selection_strategy
from .intent_resolution_engine import get_intent_engine
from .pre_execution_validator import get_validator
from .execution_logger import get_execution_logger


# Fun, user-friendly status messages (no "Composio" mentioned)
TOOL_LOADING_MESSAGES = [
    "Gathering my tools... 🔧",
    "Getting ready... ⚙️",
    "Preparing to help... 🛠️",
    "Loading capabilities... 💫",
    "Warming up... 🔥",
]

PROCESSING_MESSAGES = [
    "Working on it... 🤔",
    "Let me think... 💭",
    "Processing your request... ⚡",
    "On it! Just a moment... 🚀",
    "Crunching the data... 🧮",
    "Making magic happen... ✨",
]


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

        ENHANCED with:
        - Intent resolution for vague language
        - Pre-execution validation
        - Execution logging for debugging
        - Chain of Thought orchestration
        - Post-execution verification

        Args:
            agent_model: Agent model instance
            message: User message
            specific_tools_slugs: List of tool slugs to use
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
            file_attachments: List of file attachment dictionaries with file paths
        """
        import time
        start_time = time.time()

        try:
            # ============================================================
            # PHASE 1: INITIALIZATION & EXECUTION LOGGING
            # ============================================================

            # Start execution logging
            execution_logger = get_execution_logger()
            connected_apps = agent_model.app_connections if hasattr(agent_model, 'app_connections') else []
            agent_tools_list = agent_model.agent_tools if hasattr(agent_model, 'agent_tools') else []

            execution_logger.start_execution(
                agent_id=str(agent_model.id),
                user_id=str(self.user.id),
                user_message=message,
                connected_apps=connected_apps,
                available_files=file_attachments or [],
                agent_tools=agent_tools_list,
                chat_history=chat_history or []
            )

            # ============================================================
            # PHASE 2: INTENT RESOLUTION
            # ============================================================

            # Resolve intent for vague language
            intent_engine = get_intent_engine()
            intent_resolution = intent_engine.resolve_intent(
                user_message=message,
                chat_history=chat_history,
                connected_apps=connected_apps,
                available_files=file_attachments,
                agent_tools=agent_tools_list
            )

            execution_logger.log_intent_resolution(intent_resolution)
            print(f"🧠 Intent Resolution: {intent_resolution.reasoning} (Confidence: {intent_resolution.confidence}%)")

            # ============================================================
            # PHASE 3: PRE-EXECUTION VALIDATION
            # ============================================================

            # Validate requirements before execution
            validator = get_validator()
            validation_result = validator.validate(
                intent=intent_resolution,
                available_files=file_attachments or [],
                connected_apps=connected_apps,
                agent_tools=agent_tools_list,
                chat_history=chat_history or [],
                user_message=message
            )

            execution_logger.log_validation(validation_result)
            print(f"✅ Validation: {validation_result.validation_summary}")

            # If validation failed with blocking issues, inform user
            if not validation_result.passed:
                error_message = f"❌ Cannot execute: {validation_result.blocking_issues[0]}"
                execution_logger.log_execution_error(error_message)
                if callback:
                    await callback('error', {'error': error_message})
                return error_message

            # ============================================================
            # PHASE 4: TOOL LOADING
            # ============================================================

            if callback:
                await callback('status', {
                    'status': 'tool_calling',
                    'message': random.choice(TOOL_LOADING_MESSAGES)
                })

            tools = await sync_to_async(self.composio_client.tools.get)(
                user_id=self._get_entity_id(),
                tools=specific_tools_slugs
            )

            print(f"✅ Loaded {len(tools)} specific tools for user {self.user.username}")

            if not tools:
                print("DEBUG: Composio.tools.get returned no tools. Falling back.")
                execution_logger.log_execution_error("No tools available")
                return await self._chat_without_tools(agent_model, message, chat_history, callback)

            # Log tool selection
            tool_reasoning = f"Selected {len(specific_tools_slugs)} tools based on user prompt and intent resolution"
            execution_logger.log_tool_selection(specific_tools_slugs, tool_reasoning)

            # ============================================================
            # PHASE 5: CONTEXT INJECTION (ENHANCED)
            # ============================================================

            # Use enhanced context manager with conversation memory, intent patterns, data rules
            context_manager = get_context_manager()

            injected_context = context_manager.build_complete_context(
                user=self.user,
                agent_model=agent_model,
                connected_apps=connected_apps,
                agent_tools=agent_tools_list,
                chat_history=chat_history,  # NEW: Pass chat history for conversation memory
                user_message=message,  # NEW: Pass current message for intent analysis
                include_app_guidance=True,
                include_agent_tools_guidance=True
            )

            # ============================================================
            # PHASE 6: CHAIN OF THOUGHT ORCHESTRATION
            # ============================================================

            # Add Chain of Thought enforcement to system prompt
            chain_of_thought_protocol = """

🧠 CHAIN OF THOUGHT EXECUTION PROTOCOL (MANDATORY)
{'='*80}

Before executing ANY tools, you MUST follow this structured thinking process:

**STEP 1: ANALYZE THE REQUEST**
- What exactly is the user asking?
- What action needs to be performed? (post, send, search, create, etc.)
- What platform/destination? (Twitter, Gmail, Calendar, etc.)
- What content/file? (Is it attached? Generated? Needs to be fetched?)
- What date/time? (If "yesterday" or "today", calculate the exact date)

**STEP 2: VALIDATE REQUIREMENTS**
- ✅ Do I have all required information?
- ✅ Do I have access to necessary files?
- ✅ Do I have the right tools for this task?
- ✅ If real-time data needed (stocks, weather, news), do I have search tools?

**STEP 3: PLAN EXECUTION**
List the exact steps you will take:
1. [First action with specific tool]
2. [Second action if needed]
3. [Final confirmation]

**STEP 4: EXECUTE (NO SIMULATION)**
- Actually call the tools
- Do NOT say "I will..." or "I would..."
- Execute and confirm what was done

**CRITICAL RULES:**
- If user says "this" or "it", refer to CONVERSATION MEMORY to understand what they mean
- If user says "yesterday", calculate the exact date using SYSTEM CONTEXT (current date provided above)
- If asking for "current stock price" or "latest news", you MUST use search tools - never guess
- If sharing/sending a file, ensure you have downloaded it first (use DOWNLOAD tool)
- After execution, provide brief confirmation of what was accomplished

{'='*80}
"""

            # Build final instructions: base prompt + chain of thought + injected context
            enhanced_instructions = (
                agent_model.prompt + "\n" +
                chain_of_thought_protocol + "\n" +
                injected_context
            )

            # ============================================================
            # PHASE 7: DYNAMIC MODEL SELECTION
            # ============================================================

            # Select appropriate model based on task complexity
            model_strategy = get_model_selection_strategy()
            selected_model = model_strategy.select_model(
                user_prompt=message,
                connected_apps=connected_apps,
                chat_history=chat_history
            )

            # Log model selection with reasoning
            model_reasoning = model_strategy.get_selection_reasoning(
                user_prompt=message,
                selected_model=selected_model,
                complexity_score=model_strategy._calculate_complexity_score(message, connected_apps, chat_history),
                connected_apps=connected_apps
            )
            execution_logger.log_model_selection(selected_model, model_reasoning)

            # === FILE ATTACHMENTS HANDLING ===
            # If files are attached, append their paths to the message for Composio to access
            enhanced_message = message
            if file_attachments:
                file_context = "\n\n📎 **Attached Files:**\n"
                for file_info in file_attachments:
                    file_context += f"\n**{file_info['filename']}** ({file_info['mime_type']}, {file_info['size']} bytes)\n"
                    file_context += f"  📍 Path: `{file_info['file_path']}`\n"

                    # Add extracted text preview if available
                    if file_info.get('extraction_status') == 'success' and file_info.get('extracted_text'):
                        preview = file_info['extracted_text'][:800]  # First 800 chars
                        file_context += f"  📝 Content Preview:\n```\n{preview}\n```\n"
                        if len(file_info['extracted_text']) > 800:
                            file_context += f"  _(Total: {len(file_info['extracted_text'])} characters)_\n"
                    elif file_info.get('extraction_status') == 'not_applicable':
                        file_context += f"  ℹ️  Binary file (image/video/audio)\n"

                enhanced_message += file_context
                print(f"📎 Added context for {len(file_attachments)} file(s) to Composio prompt")

            # ============================================================
            # PHASE 8: AGENT CREATION & EXECUTION
            # ============================================================

            composio_agent = ComposioAgent(
                name=agent_model.name,
                instructions=enhanced_instructions,
                tools=tools,
                model=selected_model  # Use dynamically selected model
            )

            runner = Runner()

            # Add the current user message (with file paths if any) to chat history
            full_chat_history = (chat_history or []) + [{"role": "user", "content": enhanced_message}]

            # Mark execution as started
            execution_logger.log_execution_start()

            # Send heartbeats during Composio runner execution (opaque operation)
            # Since we can't see inside the runner, emit periodic status updates
            if callback:
                await callback('status', {
                    'status': 'processing',
                    'message': random.choice(PROCESSING_MESSAGES)
                })

                # Run the runner with periodic heartbeats
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

            # ============================================================
            # PHASE 9: EXTRACT RESULT & POST-EXECUTION VERIFICATION
            # ============================================================

            # Extract output from result
            output = None
            if hasattr(result, 'final_output'):
                output = result.final_output
            elif hasattr(result, 'output'):
                output = result.output
            elif hasattr(result, 'content'):
                output = result.content
            elif hasattr(result, 'text'):
                output = result.text
            elif hasattr(result, 'messages') and len(result.messages) > 0:
                last_message = result.messages[-1]
                if hasattr(last_message, 'content'):
                    output = last_message.content
                else:
                    output = str(last_message)
            elif isinstance(result, str):
                output = result
            else:
                print(f"🔍 RunResult type: {type(result)}")
                print(f"🔍 RunResult attributes: {dir(result)}")
                result_str = str(result)
                if "Final output (str):" in result_str:
                    lines = result_str.split('\n')
                    for i, line in enumerate(lines):
                        if "Final output (str):" in line and i + 2 < len(lines):
                            output = lines[i + 2].strip()
                            break
                if not output:
                    output = result_str

            # Post-Execution Verification
            # 1. Detect simulated actions (agent saying "I will" instead of doing)
            self._detect_simulated_actions(output, tools)

            # 2. Verify execution success (basic heuristics)
            execution_success = self._verify_execution_success(output, intent_resolution)
            if not execution_success:
                print(f"⚠️  Execution may not have completed successfully")

            # ============================================================
            # PHASE 10: COMPLETION LOGGING
            # ============================================================

            # Calculate execution duration
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            # Log completion
            execution_logger.log_execution_complete(output, duration_ms)
            print(f"✅ Execution completed in {duration_ms}ms")

            # Print execution summary for debugging
            if execution_logger.current_log:
                print("\n" + "="*80)
                print("📊 EXECUTION SUMMARY")
                print("="*80)
                print(execution_logger.get_execution_summary(execution_logger.current_log))
                print("="*80 + "\n")

            return output

        except Exception as e:
            print(f"Error in Composio chat: {e}")
            import traceback
            traceback.print_exc()

            # Log error
            execution_logger = get_execution_logger()
            if execution_logger.current_log:
                execution_logger.log_execution_error(str(e))

            if callback:
                await callback('error', {'error': str(e)})
            return await self._chat_without_tools(agent_model, message, chat_history, callback)

    async def _chat_with_agent_tools(self, agent_model, message: str, chat_history: List[Dict[str, str]] = None, callback=None, file_attachments: List[Dict] = None) -> str:
        """
        Runs chat with agent-specific tools (weather, calculator, etc.).
        Uses OpenAI function calling to execute tools.

        Args:
            agent_model: Agent model instance
            message: User message
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
            file_attachments: Optional list of file attachment dictionaries
        """
        if not self.openai_client:
            return "OpenAI client not configured"

        try:
            # Get OpenAI function definitions for enabled agent tools
            agent_tools_functions = get_openai_functions_for_tools(agent_model.agent_tools)

            if not agent_tools_functions:
                # No agent tools enabled, fall back to basic chat
                return await self._chat_without_tools(agent_model, message, chat_history, callback)

            # === USE CONTEXT INJECTION MANAGER ===
            # Add same context as Composio tools for consistency
            context_manager = get_context_manager()
            connected_apps = agent_model.app_connections if hasattr(agent_model, 'app_connections') else []
            agent_tools_list = agent_model.agent_tools if hasattr(agent_model, 'agent_tools') else []

            injected_context = context_manager.build_complete_context(
                user=self.user,
                agent_model=agent_model,
                connected_apps=connected_apps,
                agent_tools=agent_tools_list,
                include_app_guidance=False,  # Don't include Composio app guidance for agent tools
                include_agent_tools_guidance=True  # Include agent tools guidance
            )

            # Build enhanced prompt with context
            enhanced_prompt = agent_model.prompt + "\n" + injected_context

            # === ADD FILE CONTEXT TO MESSAGE ===
            # If files are attached, add file information to the message
            enhanced_message = message
            if file_attachments:
                file_context = "\n\n📎 **Attached Files:**\n"
                for file_info in file_attachments:
                    file_context += f"\n**{file_info['filename']}** ({file_info['mime_type']}, {file_info['size']} bytes)\n"
                    file_context += f"  📍 Path: `{file_info['file_path']}`\n"

                    # Add extracted text preview if available
                    if file_info.get('extraction_status') == 'success' and file_info.get('extracted_text'):
                        preview = file_info['extracted_text'][:800]  # First 800 chars
                        file_context += f"  📝 Content Preview:\n```\n{preview}\n```\n"
                        if len(file_info['extracted_text']) > 800:
                            file_context += f"  _(Total: {len(file_info['extracted_text'])} characters)_\n"
                    elif file_info.get('extraction_status') == 'not_applicable':
                        file_context += f"  ℹ️  Binary file (image/video/audio)\n"

                enhanced_message = message + file_context
                print(f"📎 Added context for {len(file_attachments)} file(s) to agent tools prompt")
            # ====================================

            # Build messages with enhanced prompt and history
            if chat_history:
                messages = [{"role": "system", "content": enhanced_prompt}] + chat_history
            else:
                messages = [
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": enhanced_message}
                ]

            print(f"🔧 Chat with {len(agent_tools_functions)} agent tools enabled")

            # === ADD TIMEOUT (60 seconds) ===
            # Make initial API call with function definitions
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=agent_tools_functions,
                    tool_choice="auto",
                    temperature=0.7,
                    max_completion_tokens=1500,
                    timeout=45  # OpenAI client timeout
                ),
                timeout=60  # asyncio timeout (outer)
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

            # === ADD TIMEOUT (60 seconds) ===
            # ✅ Use streaming for final response with async for
            final_response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_completion_tokens=1500,
                    stream=True,
                    timeout=45  # OpenAI client timeout
                ),
                timeout=60  # asyncio timeout (outer)
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

        except asyncio.TimeoutError:
            print("⏱️ Agent tools chat timed out after 60 seconds")
            if callback:
                await callback('error', {'error': 'Request timed out after 60 seconds'})
            return "Sorry, the request took too long and timed out. Please try again with a simpler query."

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

        Strategy:
        1. If Composio tools are selected, use Composio (handles connected apps)
        2. If no Composio tools selected BUT agent tools are available, use agent tools
        3. If neither, fallback to basic chat

        This prioritization ensures agent tools (like yahoo_finance, weather, calculator)
        are used when Composio doesn't have relevant tools.

        Args:
            agent_model: Agent model instance
            message: User message
            composio_tool_slugs: List of Composio tool slugs to use
            chat_history: Previous chat messages
            callback: Optional async callback function for streaming updates
        """
        # Smart routing: prioritize based on what tools are available
        has_composio_tools = composio_tool_slugs and len(composio_tool_slugs) > 0
        has_agent_tools = agent_model.agent_tools and len(agent_model.agent_tools) > 0

        print(f"🔀 Mixed tools routing: Composio={has_composio_tools}, Agent={has_agent_tools}")

        if has_composio_tools and has_agent_tools:
            # Both available - prefer Composio for connected apps
            print("  → Using Composio tools (connected apps take precedence)")
            return await self._chat_with_composio(agent_model, message, composio_tool_slugs, chat_history, callback)
        elif has_composio_tools:
            # Only Composio
            print("  → Using Composio tools only")
            return await self._chat_with_composio(agent_model, message, composio_tool_slugs, chat_history, callback)
        elif has_agent_tools:
            # Only agent tools (THIS FIXES THE STOCK PRICE ISSUE)
            print("  → Using agent tools only (no relevant Composio tools)")
            return await self._chat_with_agent_tools(agent_model, message, chat_history, callback)
        else:
            # No tools at all
            print("  → No tools available, using basic chat")
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
                "allow_multiple": True,  # Allow multiple connections to bypass Composio's duplicate check
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
                print(f"🔄 Initiating {tool_name} with auth_config_id: {auth_config_id}, allow_multiple=True")
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

                error_message = str(e)

                # Handle "Multiple connected accounts" error with cleanup strategy
                # NOTE: With allow_multiple=True, this should rarely/never happen
                # But we keep this as a safety fallback
                if "Multiple connected accounts" in error_message or "ComposioMultipleConnectedAccountsError" in type(e).__name__:
                    print(f"⚠️  UNEXPECTED: Got multiple connections error despite allow_multiple=True")
                    print(f"🔍 Attempting fallback cleanup strategy...")

                    try:
                        # Get existing connections for this user/tool from Composio
                        entity_id = f"user_{self.user.id}"

                        # Try to clean up duplicates using our new method
                        cleanup_result = self._cleanup_duplicate_connections(entity_id, tool_name)

                        if cleanup_result.get('cleaned'):
                            print(f"✅ Cleanup successful: kept {cleanup_result['kept_connection_id']}, deleted {cleanup_result['deleted_count']}")
                            print(f"🔄 Retrying initiate after cleanup...")
                        else:
                            print(f"⚠️  Cleanup didn't find/remove duplicates: {cleanup_result.get('reason', 'unknown')}")
                            print(f"🔄 Trying legacy cleanup method...")

                            # Fallback to old method for ghost connections
                            existing_connections = self._get_composio_connections_for_tool(entity_id, tool_name)

                            if existing_connections:
                                print(f"📋 Found {len(existing_connections)} existing connection(s) in Composio")

                                # Try to adopt the first valid connection
                                adopted = False
                                for conn in existing_connections:
                                    if self._try_adopt_connection(conn, tool_name):
                                        print(f"✅ Adopted existing connection for {tool_name}")
                                        adopted = True
                                        break

                                # If adoption succeeded, return success
                                if adopted:
                                    return {
                                        "success": True,
                                        "adopted": True,
                                        "message": f"Connected to {tool_name} using existing account"
                                    }

                                # If no valid connection found, delete all zombie connections
                                print(f"🗑️  No valid connections found - deleting zombie connections...")
                                for conn in existing_connections:
                                    self._delete_composio_connection(conn)
                            else:
                                # Ghost connections that don't appear in list()
                                print(f"⚠️  No connections returned by list(), but Composio says they exist")
                                print(f"🧹 Attempting to delete ghost connections...")
                                self._delete_all_connections_for_entity(entity_id, tool_name)

                        # Retry the connection after cleanup
                        print(f"🔄 Retrying connection after cleanup...")
                        response = self.composio_client.connected_accounts.initiate(**initiate_params)

                        # Extract auth URL from retry
                        auth_url = getattr(response, 'redirectUrl', None) or getattr(response, 'redirect_url', None)
                        connection_status = getattr(response, 'connectionStatus', None) or getattr(response, 'connection_status', None) or getattr(response, 'status', None)

                        if auth_url:
                            print(f"✅ Retry successful after cleanup")
                            return {
                                "success": True,
                                "auth_url": auth_url,
                                "auth_config_id": auth_config_id,
                                "status": connection_status,
                                "cleaned_up": True
                            }
                    except Exception as cleanup_error:
                        print(f"❌ Failed to resolve multiple connections issue: {cleanup_error}")
                        import traceback
                        traceback.print_exc()

                # If not a multiple connections error, or cleanup failed, return original error
                import traceback
                traceback.print_exc()

                # Extract more detailed error if available
                error_detail = error_message
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

    def _get_composio_connections_for_tool(self, entity_id: str, tool_name: str) -> List:
        """
        Fetches all Composio connections for a specific user and tool.
        Returns a list of connection objects from Composio.
        """
        try:
            # Try different API parameter variations (Composio API is inconsistent)
            response = None
            try:
                # Try with no parameters first (gets all for this API key)
                print(f"🔍 Calling composio_client.connected_accounts.list()...")
                response = self.composio_client.connected_accounts.list()
                print(f"✅ Got response: {type(response)}")
            except Exception as e1:
                print(f"⚠️  list() failed: {e1}")
                try:
                    # Try with user_id parameter
                    print(f"🔍 Trying with user_id={entity_id}...")
                    response = self.composio_client.connected_accounts.list(user_id=entity_id)
                    print(f"✅ Got response: {type(response)}")
                except Exception as e2:
                    print(f"❌ Failed to list connections: {e1}, {e2}")
                    return []

            # Extract connections from response
            connections = None
            if hasattr(response, 'items'):
                connections = response.items
                print(f"📋 Extracted {len(connections) if connections else 0} connections from response.items")
            elif hasattr(response, 'data'):
                connections = response.data
                print(f"📋 Extracted {len(connections) if connections else 0} connections from response.data")
            elif hasattr(response, '__iter__'):
                connections = list(response)
                print(f"📋 Extracted {len(connections) if connections else 0} connections from iterable response")

            if not connections:
                print(f"ℹ️  No connections found in Composio response")
                return []

            print(f"🔍 Filtering {len(connections)} total connections for entity_id={entity_id}, tool={tool_name}")

            # Filter for the specific user and tool
            tool_connections = []
            for i, conn in enumerate(connections):
                # Check if connection belongs to this user
                conn_entity = None
                if hasattr(conn, 'entityId'):
                    conn_entity = conn.entityId
                elif hasattr(conn, 'entity_id'):
                    conn_entity = conn.entity_id
                elif hasattr(conn, 'userId'):
                    conn_entity = conn.userId
                elif hasattr(conn, 'user_id'):
                    conn_entity = conn.user_id

                # Check if this is the tool we're looking for
                conn_app = None
                if hasattr(conn, 'toolkit') and conn.toolkit:
                    conn_app = getattr(conn.toolkit, 'slug', None)
                elif hasattr(conn, 'integration') and conn.integration:
                    conn_app = getattr(conn.integration, 'slug', None)
                elif hasattr(conn, 'app'):
                    conn_app = conn.app

                print(f"  Connection {i+1}: entity={conn_entity}, app={conn_app}, match_entity={conn_entity == entity_id if conn_entity else 'N/A'}, match_app={conn_app.upper() == tool_name.upper() if conn_app else 'N/A'}")

                # Skip if not this user's connection
                if conn_entity and conn_entity != entity_id:
                    print(f"    ⏭️  Skipped - different user")
                    continue

                if conn_app and conn_app.upper() == tool_name.upper():
                    print(f"    ✅ Matched! Adding to results")
                    tool_connections.append(conn)
                else:
                    print(f"    ⏭️  Skipped - different tool")

            print(f"ℹ️  Found {len(tool_connections)} connection(s) for {tool_name}")
            return tool_connections

        except Exception as e:
            print(f"❌ Error fetching Composio connections: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _try_adopt_connection(self, conn, tool_name: str) -> bool:
        """
        Tries to adopt an existing Composio connection by updating the local database.
        Returns True if successful, False otherwise.
        """
        try:
            from api_agents.tools.models import ComposioConnection

            # Extract connection ID
            conn_id = getattr(conn, 'id', None)
            if not conn_id:
                print(f"⚠️  Connection missing ID, cannot adopt")
                return False

            # Check connection status - only adopt ACTIVE connections
            status = getattr(conn, 'status', None) or getattr(conn, 'connectionStatus', None)
            if status and status.upper() not in ['ACTIVE', 'ENABLED']:
                print(f"⚠️  Connection {conn_id} has status {status}, not adopting")
                return False

            # Check if we already have this connection in our DB
            existing = ComposioConnection.objects.filter(
                user=self.user,
                tool_name=tool_name.upper(),
                connection_id=conn_id
            ).first()

            if existing:
                # Update to active
                existing.is_active = True
                existing.deleted_at = None
                existing.save()
                print(f"✅ Re-activated existing connection {conn_id}")
            else:
                # Create new local record
                ComposioConnection.objects.create(
                    user=self.user,
                    tool_name=tool_name.upper(),
                    connection_id=conn_id,
                    is_active=True
                )
                print(f"✅ Adopted new connection {conn_id}")

            return True

        except Exception as e:
            print(f"❌ Error adopting connection: {e}")
            return False

    def _delete_composio_connection(self, conn):
        """
        Deletes a connection from Composio's database.
        """
        try:
            conn_id = getattr(conn, 'id', None)
            if not conn_id:
                print(f"⚠️  Connection missing ID, cannot delete")
                return

            print(f"🗑️  Deleting Composio connection: {conn_id}")
            self.composio_client.connected_accounts.delete(connection_id=conn_id)
            print(f"✅ Deleted connection {conn_id} from Composio")

        except Exception as e:
            print(f"❌ Error deleting Composio connection: {e}")

    def _delete_all_connections_for_entity(self, entity_id: str, tool_name: str):
        """
        Attempts to delete all connections for an entity/tool, including ghost connections.
        This is called when list() returns empty but Composio says connections exist.
        """
        try:
            print(f"🔍 Fetching ALL connections (including non-active) for {entity_id}...")

            # Try to get connected accounts with different approaches
            all_connections = []

            # Approach 1: Try getting by entity_id and app
            try:
                response = self.composio_client.connected_accounts.list()
                if hasattr(response, 'items'):
                    all_connections = response.items
                elif hasattr(response, 'data'):
                    all_connections = response.data
                elif hasattr(response, '__iter__'):
                    all_connections = list(response)

                print(f"📋 Got {len(all_connections)} total connections from Composio")

                # Filter and delete matching connections
                deleted_count = 0
                for conn in all_connections:
                    conn_entity = getattr(conn, 'entityId', None) or getattr(conn, 'entity_id', None) or getattr(conn, 'userId', None) or getattr(conn, 'user_id', None)

                    if conn_entity == entity_id:
                        conn_app = None
                        if hasattr(conn, 'toolkit') and conn.toolkit:
                            conn_app = getattr(conn.toolkit, 'slug', None)
                        elif hasattr(conn, 'integration') and conn.integration:
                            conn_app = getattr(conn.integration, 'slug', None)
                        elif hasattr(conn, 'app'):
                            conn_app = conn.app

                        if conn_app and conn_app.upper() == tool_name.upper():
                            conn_id = getattr(conn, 'id', None)
                            if conn_id:
                                print(f"🗑️  Deleting connection {conn_id} (app={conn_app}, entity={conn_entity})")
                                try:
                                    self.composio_client.connected_accounts.delete(connection_id=conn_id)
                                    deleted_count += 1
                                    print(f"✅ Deleted connection {conn_id}")
                                except Exception as del_err:
                                    print(f"❌ Failed to delete {conn_id}: {del_err}")

                print(f"🧹 Deleted {deleted_count} ghost connection(s)")

            except Exception as list_err:
                print(f"❌ Failed to list connections for deletion: {list_err}")

        except Exception as e:
            print(f"❌ Error in _delete_all_connections_for_entity: {e}")
            import traceback
            traceback.print_exc()

    def _cleanup_duplicate_connections(self, entity_id: str, tool_name: str, keep_connection_id: str = None):
        """
        Deletes all duplicate connections for a user/tool, keeping only one.

        This enforces the constraint: ONE connection per tool per user.

        Args:
            entity_id: The user's entity ID (e.g., "user_123")
            tool_name: The tool name (e.g., "GMAIL")
            keep_connection_id: Optional specific connection ID to keep. If None, keeps the newest.

        Returns:
            Dict with cleanup results: {
                'cleaned': bool,
                'kept_connection_id': str,
                'deleted_count': int
            }
        """
        try:
            print(f"🧹 Cleaning up duplicate connections for {tool_name}...")

            # Get all connections for this user/tool
            all_connections = self._get_composio_connections_for_tool(entity_id, tool_name)

            if not all_connections:
                print(f"ℹ️  No connections found for {tool_name}")
                return {'cleaned': False, 'deleted_count': 0, 'reason': 'no_connections'}

            if len(all_connections) == 1:
                kept_id = getattr(all_connections[0], 'id', 'unknown')
                print(f"ℹ️  Only 1 connection found for {tool_name}, no cleanup needed")
                return {'cleaned': False, 'kept_connection_id': kept_id, 'deleted_count': 0, 'reason': 'only_one'}

            print(f"⚠️  Found {len(all_connections)} connections for {tool_name} - cleaning up duplicates...")

            # Determine which connection to keep
            connection_to_keep = None

            if keep_connection_id:
                # Keep the specified connection
                for conn in all_connections:
                    conn_id = getattr(conn, 'id', None)
                    if conn_id == keep_connection_id:
                        connection_to_keep = conn
                        print(f"🎯 Keeping specified connection: {keep_connection_id}")
                        break

            if not connection_to_keep:
                # Keep the newest connection (by creation timestamp)
                # Sort by createdAt or created_at field (most recent first)
                try:
                    sorted_connections = sorted(
                        all_connections,
                        key=lambda c: getattr(c, 'createdAt', '') or getattr(c, 'created_at', '') or '',
                        reverse=True  # Newest first
                    )
                    connection_to_keep = sorted_connections[0]
                    keep_id = getattr(connection_to_keep, 'id', 'unknown')
                    print(f"🎯 Keeping newest connection: {keep_id}")
                except Exception as sort_err:
                    # Fallback: just keep the first one
                    print(f"⚠️  Couldn't sort by timestamp ({sort_err}), keeping first connection")
                    connection_to_keep = all_connections[0]
                    keep_id = getattr(connection_to_keep, 'id', 'unknown')
                    print(f"🎯 Keeping first connection: {keep_id}")

            # Delete all other connections
            deleted_count = 0
            deleted_ids = []
            keep_conn_id = getattr(connection_to_keep, 'id', None)

            for conn in all_connections:
                conn_id = getattr(conn, 'id', None)
                if conn_id and conn_id != keep_conn_id:
                    try:
                        print(f"🗑️  Deleting duplicate connection: {conn_id}")
                        self._delete_composio_connection(conn)
                        deleted_count += 1
                        deleted_ids.append(conn_id)
                    except Exception as del_err:
                        print(f"❌ Failed to delete connection {conn_id}: {del_err}")
                        # Continue trying to delete other connections

            print(f"✅ Cleanup complete: Kept {keep_conn_id}, deleted {deleted_count} duplicate(s)")

            # Try to adopt the kept connection in local database
            try:
                self._try_adopt_connection(connection_to_keep, tool_name)
            except Exception as adopt_err:
                print(f"⚠️  Failed to adopt kept connection: {adopt_err}")

            return {
                'cleaned': True,
                'kept_connection_id': keep_conn_id,
                'deleted_count': deleted_count,
                'deleted_ids': deleted_ids
            }

        except Exception as e:
            print(f"❌ Error in _cleanup_duplicate_connections: {e}")
            import traceback
            traceback.print_exc()
            # Don't raise - cleanup failure shouldn't break the flow
            return {'cleaned': False, 'deleted_count': 0, 'error': str(e)}

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
                                    self.composio_client.connected_accounts.delete(connection_id)
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

                print(f"Successfully selected {len(selected_tools)} tools by AI.")

                # === APPLY TOOL DEPENDENCY ENGINE ===
                # Automatically add required dependency tools
                dependency_engine = get_tool_dependency_engine()
                enhanced_tools = dependency_engine.enforce_dependencies(
                    selected_tools=selected_tools,
                    connected_apps=app_names
                )

                return enhanced_tools

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

    def _detect_simulated_actions(self, output: str, available_tools: list) -> None:
        """
        Task 6: Detect when agent simulates actions instead of executing tools.
        Logs warnings to help identify and debug simulation behavior.
        """
        if not output or not available_tools:
            return

        # Keywords indicating simulation/description instead of execution
        simulation_keywords = [
            "I'll send", "I will send", "I would send",
            "I'll create", "I will create", "I would create",
            "I'll search", "I will search", "I would search",
            "I can help you send", "I can help you create",
            "Here's what I would", "Here's what I'll",
            "Let me send", "Let me create", "Let me search",
            "I'm going to send", "I'm going to create",
        ]

        output_lower = output.lower()
        detected_simulations = []

        for keyword in simulation_keywords:
            if keyword.lower() in output_lower:
                detected_simulations.append(keyword)

        if detected_simulations:
            print(f"⚠️  SIMULATION DETECTED: Agent described action instead of executing")
            print(f"   Keywords found: {detected_simulations}")
            print(f"   Available tools: {[t.split('_')[0] for t in available_tools[:3]]}")
            print(f"   Response preview: {output[:200]}...")
            print(f"   💡 TIP: Agent should USE tools, not describe them!")

    def _verify_execution_success(self, output: str, intent_resolution) -> bool:
        """
        Post-execution verification - Check if agent successfully completed the task.

        Returns:
            True if execution appears successful, False otherwise
        """
        if not output:
            return False

        output_lower = output.lower()

        # Success indicators
        success_keywords = [
            "successfully", "completed", "done", "sent", "posted", "created",
            "scheduled", "uploaded", "downloaded", "shared", "email sent",
            "tweet posted", "event created", "file uploaded"
        ]

        # Failure indicators
        failure_keywords = [
            "error", "failed", "couldn't", "cannot", "unable to",
            "not found", "invalid", "problem", "issue"
        ]

        has_success = any(keyword in output_lower for keyword in success_keywords)
        has_failure = any(keyword in output_lower for keyword in failure_keywords)

        if has_failure:
            print(f"⚠️  Execution may have failed - failure keywords detected")
            return False

        if has_success:
            print(f"✅ Execution appears successful - success keywords detected")
            return True

        # If no clear indicators, assume success (benefit of doubt)
        print(f"ℹ️  Execution status unclear - no definitive success/failure indicators")
        return True

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
