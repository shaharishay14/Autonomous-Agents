from rest_framework import serializers
from django.contrib.auth import get_user_model
from . import models

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    agent_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'agent_count', 'total_credits', 'credits_used']
        read_only_fields = ['total_credits', 'credits_used']

    def get_agent_count(self, obj) -> int:
        return obj.agents.count() if hasattr(obj, 'agents') else 0


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class RegistrationResponseSerializer(serializers.Serializer):
    user = UserSerializer()


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField()
    
    def validate(self, attrs):
        # Require either username or email
        if not attrs.get('username') and not attrs.get('email'):
            raise serializers.ValidationError("Provide either username or email.")
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()


class LogoutResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class GoogleLoginRequestSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=False, help_text="Google access token or ID token")
    id_token = serializers.CharField(required=False, help_text="Google ID token (JWT)")
    code = serializers.CharField(required=False, help_text="Authorization code from Google OAuth (for auth-code flow)")
    code_verifier = serializers.CharField(required=False, help_text="PKCE code verifier (if using PKCE)")


class OAuthLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()


class GitHubLoginRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    access_token = serializers.CharField(required=False)

class EmailVerificationResendResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

class EmailVerificationConfirmResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

class TokenRefreshCookieResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetRequestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()

class PasswordResetConfirmRequestSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

class PasswordResetConfirmResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AvailableToolSerializer(serializers.Serializer):
    """Serializer for individual tool in available tools response"""
    tool_name = serializers.CharField(help_text="Backend tool identifier (e.g., 'GMAIL', 'SLACK')")
    name = serializers.CharField(help_text="Display name of the tool (e.g., 'Gmail', 'Slack')")
    description = serializers.CharField(help_text="Description of what the tool does")
    category = serializers.CharField(help_text="Category classification (e.g., 'communication', 'productivity')")
    is_active = serializers.BooleanField(help_text="True if user is connected to this tool, false otherwise")
    connection_id = serializers.IntegerField(allow_null=True, help_text="Database ID of the connection. Null if not connected. Use this ID to delete the connection.")


class AvailableToolsResponseSerializer(serializers.Serializer):
    """Serializer for available tools endpoint response"""
    tools = serializers.ListField(
        child=AvailableToolSerializer(),
        help_text="List of all available tools with metadata and connection status"
    )
    count = serializers.IntegerField(
        help_text="Total number of available tools"
    )


class AgentAvailableToolSerializer(serializers.Serializer):
    """Serializer for individual tool in agent available tools response"""
    tool_name = serializers.CharField(help_text="Backend tool identifier (e.g., 'GMAIL', 'SLACK')")
    name = serializers.CharField(help_text="Display name of the tool (e.g., 'Gmail', 'Slack')")
    description = serializers.CharField(help_text="Description of what the tool does")
    category = serializers.CharField(help_text="Category classification (e.g., 'communication', 'productivity')")
    is_connected_to_account = serializers.BooleanField(help_text="True if tool is connected at account level (via /api/connections/)")
    is_connected_to_agent = serializers.BooleanField(help_text="True if this specific agent is using the tool")
    connection_id = serializers.IntegerField(allow_null=True, help_text="Database ID of the account-level connection. Null if not connected.")


class AgentAvailableToolsResponseSerializer(serializers.Serializer):
    """Serializer for agent available tools endpoint response"""
    tools = serializers.ListField(
        child=AgentAvailableToolSerializer(),
        help_text="List of all available tools with agent-specific connection status"
    )
    count = serializers.IntegerField(
        help_text="Total number of available tools"
    )


class AgentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for agent templates"""
    category_display_name = serializers.ReadOnlyField(help_text="Human-readable category name")
    category_icon = serializers.ReadOnlyField(help_text="Emoji icon for the category")

    class Meta:
        model = models.AgentTemplate
        fields = [
            'id', 'name', 'description', 'system_prompt',
            'category', 'category_display_name', 'category_icon',
            'default_tools', 'default_agent_tools', 'icon',
            'usage_count', 'created_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'category_display_name', 'category_icon']


class InstantiateTemplateRequestSerializer(serializers.Serializer):
    """Request serializer for instantiating a template"""
    template_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the agent template to instantiate"
    )


class FlexibleListField(serializers.ListField):
    """
    Custom ListField that handles both JSON string and array formats.
    Needed for multipart/form-data where arrays are sent as JSON strings.
    Frontend sends: ['["GMAIL"]'] (list with JSON string) via multipart data.
    """
    def to_internal_value(self, data):
        import json

        # If data is a string, try to parse it as JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                # If it's not valid JSON, treat it as a single-item list
                data = [data]

        # If data is a list, check if first item is a JSON string
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], str):
            try:
                # Try to parse the first item as JSON (common in multipart/form-data)
                parsed = json.loads(data[0])
                if isinstance(parsed, list):
                    data = parsed
            except (json.JSONDecodeError, ValueError):
                # Not JSON, leave as is
                pass

        # Now proceed with normal ListField validation
        return super().to_internal_value(data)


class AgentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    message_count = serializers.SerializerMethodField()
    avatar = serializers.ImageField(write_only=True, required=False, help_text="Avatar image file (JPG or PNG, max 5MB)")
    avatar_base64 = serializers.SerializerMethodField(help_text="Base64-encoded avatar image for display (read-only)")

    # Make 'tools' read-only, as it's set by the backend
    tools = serializers.JSONField(read_only=True)

    # 'app_connections' handles both JSON string (multipart/form-data) and array (application/json)
    # Use FlexibleListField to parse JSON strings from multipart data
    app_connections = FlexibleListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
        help_text="List of tool names to enable for this agent (e.g., ['GMAIL', 'SLACK']). Can be sent as JSON string in multipart data."
    )

    # Make 'name' optional - will be generated from prompt if not provided
    name = serializers.CharField(required=False, allow_blank=True, max_length=200)

    # Agent-specific tools (non-Composio) - read-only for now
    agent_tools = serializers.JSONField(read_only=True)

    class Meta:
        model = models.Agent
        fields = [
            'id', 'user', 'name', 'prompt',
            'tools', 'app_connections', 'agent_tools',
            'created_at', 'updated_at', 'message_count', 'avatar', 'avatar_base64'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_message_count(self, obj) -> int:
        return obj.messages.count()

    def get_avatar_base64(self, obj) -> str | None:
        """Returns the avatar image as a base64-encoded data URI, or None if no avatar exists"""
        if obj.avatar_image:
            import base64
            try:
                # Get the image data
                image_data = obj.get_avatar_content()
                if image_data:
                    # Encode to base64
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    # Return as data URI
                    mime_type = obj.avatar_mime_type or 'image/jpeg'
                    return f"data:{mime_type};base64,{base64_data}"
            except Exception as e:
                # Log error but don't fail the entire serialization
                print(f"Error encoding avatar to base64: {e}")
        return None
    
    def validate_avatar(self, value):
        """Validate avatar file size and type"""
        if value:
            # Validate file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f'File size exceeds maximum allowed size of 5MB. Your file is {value.size / (1024 * 1024):.2f}MB.'
                )

            # Validate file type
            if value.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                raise serializers.ValidationError(
                    f'Invalid file format. Only JPG and PNG images are supported. Your file type: {value.content_type}'
                )

        return value


class ManualAgentCreateSerializer(serializers.Serializer):
    """Serializer for creating an agent in Manual Mode"""
    name = serializers.CharField(
        required=True,
        max_length=200,
        help_text="Agent name (required in manual mode)"
    )
    prompt = serializers.CharField(
        required=True,
        help_text="System prompt for the agent"
    )
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Avatar image file (JPG or PNG, max 5MB)"
    )
    app_connections = FlexibleListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
        help_text="List of app connection slugs (e.g., ['GMAIL', 'SLACK']). Can be sent as JSON string in multipart data."
    )
    agent_tools = FlexibleListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
        help_text="List of agent tool names (e.g., ['weather', 'calculator']). Can be sent as JSON string in multipart data."
    )
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        allow_empty=True,
        help_text="List of files to attach to this agent (for persistent context)"
    )

    def validate_avatar(self, value):
        """Validate avatar file size and type"""
        if value:
            # Validate file size (5MB max)
            max_size = 5 * 1024 * 1024  # 5MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f'File size exceeds maximum allowed size of 5MB. Your file is {value.size / (1024 * 1024):.2f}MB.'
                )

            # Validate file type
            if value.content_type not in ['image/jpeg', 'image/jpg', 'image/png']:
                raise serializers.ValidationError(
                    f'Invalid file format. Only JPG and PNG images are supported. Your file type: {value.content_type}'
                )

        return value

    def validate_files(self, value):
        """Validate file attachments"""
        if value:
            max_file_size = 10 * 1024 * 1024  # 10MB per file
            for file in value:
                if file.size > max_file_size:
                    raise serializers.ValidationError(
                        f'File {file.name} exceeds maximum allowed size of 10MB. File is {file.size / (1024 * 1024):.2f}MB.'
                    )
        return value


class ManualAgentCreateResponseSerializer(serializers.Serializer):
    """Response serializer for manual agent creation"""
    agent = AgentSerializer(help_text="The newly created agent")
    message = serializers.CharField(help_text="Success message")
    files_attached = serializers.IntegerField(help_text="Number of files attached to the agent")


class InstantiateTemplateResponseSerializer(serializers.Serializer):
    """Response serializer for template instantiation"""
    agent = AgentSerializer(help_text="The newly created agent")
    message = serializers.CharField(help_text="Success message")
    missing_connections = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of tools that require connection at account level"
    )


class ComposioConnectionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = models.ComposioConnection
        fields = ['id', 'user', 'tool_name', 'auth_config_id', 'connected_at', 'last_used', 'is_active', 'metadata']
        read_only_fields = ['connected_at', 'last_used']


class ConnectionCreateRequestSerializer(serializers.Serializer):
    tool_name = serializers.CharField()
    waba_id = serializers.CharField(required=False, allow_blank=True)
    phone_number_id = serializers.CharField(required=False, allow_blank=True)


class ConnectionAuthResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    auth_url = serializers.CharField(required=False, allow_blank=True)
    connection = ComposioConnectionSerializer()


class DisconnectResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    # Explicitly define agent field to serialize UUID correctly
    agent = serializers.UUIDField(read_only=True, source='agent.id')
    
    class Meta:
        model = models.ChatMessage
        fields = ['id', 'agent', 'role', 'content', 'attachments', 'created_at']
        read_only_fields = ['created_at']


class FileAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for file attachments stored in database"""
    download_url = serializers.SerializerMethodField()
    agent_id = serializers.UUIDField(write_only=True, required=True, help_text="UUID of the agent this file belongs to")
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    is_temporary = serializers.BooleanField(default=False, required=False, help_text="If true, file will be auto-deleted after being used in a message")

    class Meta:
        model = models.FileAttachment
        fields = ['id', 'agent_id', 'agent_name', 'original_filename', 'file_size', 'mime_type', 'is_temporary', 'uploaded_at', 'download_url']
        read_only_fields = ['uploaded_at', 'download_url', 'agent_name']
        # Note: file_content is not included in serializer for security/performance

    def get_download_url(self, obj) -> str | None:
        """Returns the URL to download the file content"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/files/{obj.id}/download/')
        return None

    def validate_agent_id(self, value):
        """Validate that agent exists and belongs to the user"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required")

        try:
            agent = models.Agent.objects.get(id=value, user=request.user)
        except models.Agent.DoesNotExist:
            raise serializers.ValidationError("Agent not found or doesn't belong to you")

        return value


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    agent_id = serializers.IntegerField()
    file_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )

class AgentChatRequestSerializer(serializers.Serializer):
    """Request serializer for agent chat endpoint (agent ID comes from URL)"""
    message = serializers.CharField(help_text="The message to send to the agent")
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        default=list,
        help_text="Optional list of files to upload inline with the message (automatically marked as temporary and deleted after use). All persistent files from the agent's database are automatically loaded."
    )
    is_ephemeral = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, the conversation will not be saved to the database (for embedded/public use)"
    )

class AgentChatResponseSerializer(serializers.Serializer):
    """Response serializer for agent chat endpoint"""
    user_message = ChatMessageSerializer(help_text="The user message that was sent")
    assistant_message = ChatMessageSerializer(help_text="The assistant's response message")


class TriggerSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    agent_name = serializers.ReadOnlyField(source='agent.name')
    
    class Meta:
        model = models.Trigger
        fields = [
            'id', 'user', 'agent', 'agent_name', 'name', 'description',
            'trigger_type', 'status', 'composio_trigger_id', 'trigger_slug',
            'trigger_config', 'action_prompt', 'trigger_count', 'last_triggered',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'trigger_count', 'last_triggered', 'composio_trigger_id']


class TriggerExecutionSerializer(serializers.ModelSerializer):
    trigger_name = serializers.ReadOnlyField(source='trigger.name')
    
    class Meta:
        model = models.TriggerExecution
        fields = [
            'id', 'trigger', 'trigger_name', 'triggered_at', 'event_data',
            'agent_response', 'success', 'error_message'
        ]
        read_only_fields = ['triggered_at']


class WorkflowSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    agent_name = serializers.ReadOnlyField(source='agent.name')
    execution_count = serializers.ReadOnlyField()
    node_count = serializers.SerializerMethodField()
    
    class Meta:
        model = models.Workflow
        fields = [
            'id', 'user', 'agent', 'agent_name', 'name', 'description', 'status',
            'nodes', 'edges', 'viewport', 'execution_count', 'last_executed',
            'node_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'execution_count', 'last_executed']
    
    def get_node_count(self, obj) -> int:
        return len(obj.nodes) if obj.nodes else 0


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    workflow_name = serializers.ReadOnlyField(source='workflow.name')

    class Meta:
        model = models.WorkflowExecution
        fields = [
            'id', 'workflow', 'workflow_name', 'executed_at', 'input_data',
            'output_data', 'execution_trace', 'success', 'error_message',
            'execution_time_ms'
        ]
        read_only_fields = ['executed_at']


class SuggestedPromptsRequestSerializer(serializers.Serializer):
    """Request serializer for generating suggested prompts"""
    prompt = serializers.CharField(
        help_text="The agent's purpose/prompt used to generate relevant example prompts"
    )
    app_connections = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
        allow_empty=True,
        help_text="List of tool names the agent will use (e.g., ['GMAIL', 'SLACK'])"
    )


class SuggestedPromptsResponseSerializer(serializers.Serializer):
    """Response serializer for suggested prompts"""
    suggested_prompts = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of 3 suggested prompts the user can use with this agent"
    )


class CreditBalanceSerializer(serializers.Serializer):
    """Serializer for user credit balance"""
    total_credits = serializers.IntegerField(help_text="Current credit balance")
    credits_used = serializers.IntegerField(help_text="Total credits used historically")
    credit_refresh_date = serializers.DateTimeField(help_text="Date when credits were last refreshed", allow_null=True)
    next_refresh_date = serializers.DateTimeField(help_text="Date when credits will refresh next", allow_null=True)


class UsageLogSerializer(serializers.ModelSerializer):
    """Serializer for usage logs"""
    agent_name = serializers.CharField(source='agent.name', read_only=True, allow_null=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = models.UsageLog
        fields = [
            'id', 'action_type', 'action_type_display', 'credits_used',
            'credits_remaining', 'description', 'metadata',
            'agent_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AddCreditsRequestSerializer(serializers.Serializer):
    """Request serializer for adding credits (admin only)"""
    user_id = serializers.UUIDField(required=True, help_text="UUID of the user to add credits to")
    amount = serializers.IntegerField(required=True, min_value=1, help_text="Number of credits to add")
    description = serializers.CharField(required=False, allow_blank=True, help_text="Optional reason for adding credits")


class AddCreditsResponseSerializer(serializers.Serializer):
    """Response serializer for adding credits"""
    message = serializers.CharField()
    user_id = serializers.UUIDField()
    credits_added = serializers.IntegerField()
    new_balance = serializers.IntegerField()


class AgentToolSerializer(serializers.Serializer):
    """Serializer for individual agent tool"""
    tool_name = serializers.CharField(help_text="Backend tool identifier (e.g., 'weather', 'calculator')")
    name = serializers.CharField(help_text="Display name of the tool (e.g., 'Weather', 'Calculator')")
    description = serializers.CharField(help_text="Description of what the tool does")
    icon = serializers.CharField(help_text="Emoji icon for the tool")
    category = serializers.CharField(help_text="Category classification (e.g., 'information', 'utility')")
    is_enabled = serializers.BooleanField(help_text="True if this tool is enabled for the agent")


class AppConnectionDisplaySerializer(serializers.Serializer):
    """Serializer for displaying available tools (Composio apps + agent tools) with connection status"""
    app_slug = serializers.CharField(help_text="Tool identifier (e.g., 'GMAIL', 'weather', 'calculator')")
    name = serializers.CharField(help_text="Display name (e.g., 'Gmail', 'Weather', 'Calculator')")
    description = serializers.CharField(help_text="Description of what the tool does")
    category = serializers.CharField(help_text="Category (e.g., 'email', 'productivity', 'information')")
    icon = serializers.CharField(required=False, allow_null=True, help_text="Icon emoji for agent tools (null for Composio apps)")
    is_connected = serializers.BooleanField(help_text="True if user has an active connection (always True for agent tools)")
    is_composio_app = serializers.BooleanField(help_text="True if this is a Composio app, False if it's an agent tool")
    requires_api_key = serializers.BooleanField(help_text="True if this agent tool requires an API key (only relevant for agent tools)")


class MessagingChannelSerializer(serializers.ModelSerializer):
    """Serializer for messaging channel connections"""
    platform_display = serializers.CharField(source='get_platform_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = models.MessagingChannel
        fields = [
            'id', 'platform', 'platform_display', 'bot_username',
            'status', 'status_display', 'message_count',
            'last_message_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'message_count', 'last_message_at', 'created_at', 'updated_at']


class ConnectTelegramBotSerializer(serializers.Serializer):
    """Serializer for connecting a Telegram bot to an agent"""
    bot_token = serializers.CharField(
        required=True,
        help_text="Telegram bot token from @BotFather (e.g., 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)"
    )

    def validate_bot_token(self, value):
        """Validate bot token format"""
        if ':' not in value or len(value) < 20:
            raise serializers.ValidationError("Invalid bot token format")
        return value


class DisconnectMessagingChannelSerializer(serializers.Serializer):
    """Serializer for disconnecting a messaging channel"""
    platform = serializers.ChoiceField(
        choices=['telegram', 'whatsapp'],
        required=True,
        help_text="Platform to disconnect (telegram or whatsapp)"
    )


class AgentToolsResponseSerializer(serializers.Serializer):
    """Response serializer for agent tools list"""
    tools = serializers.ListField(
        child=AgentToolSerializer(),
        help_text="List of all available agent tools with metadata and enabled status"
    )
    count = serializers.IntegerField(help_text="Total number of available agent tools")


class AddAgentToolRequestSerializer(serializers.Serializer):
    """Request serializer for adding an agent tool"""
    tool_name = serializers.CharField(
        help_text="Name of the tool to add (e.g., 'weather', 'calculator')"
    )


class AddAgentToolResponseSerializer(serializers.Serializer):
    """Response serializer for adding an agent tool"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    agent_tools = serializers.ListField(child=serializers.CharField())


