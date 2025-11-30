from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import uuid


class User(AbstractUser):
    """Custom User model with UUID primary key and credit system"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the user")

    # Credit system fields
    total_credits = models.IntegerField(
        default=100,
        help_text="Current credit balance. Each message costs credits."
    )
    credits_used = models.IntegerField(
        default=0,
        help_text="Total credits used historically for tracking"
    )
    credit_refresh_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date when credits were last refreshed. Credits refresh monthly from this date."
    )

    class Meta:
        # Use a different table name to avoid conflicts during migration
        # Can be changed back to 'auth_user' after migration if needed
        db_table = 'api_agents_user'
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def has_credits(self, required_credits=1):
        """Check if user has enough credits"""
        return self.total_credits >= required_credits

    def deduct_credits(self, amount=1):
        """Deduct credits from user balance"""
        if not self.has_credits(amount):
            raise ValueError("Insufficient credits")
        self.total_credits -= amount
        self.credits_used += amount
        self.save(update_fields=['total_credits', 'credits_used'])

    def add_credits(self, amount):
        """Add credits to user balance"""
        self.total_credits += amount
        self.save(update_fields=['total_credits'])

    def check_and_refresh_credits(self):
        """
        Check if credits need to be refreshed (monthly).
        If credit_refresh_date is None, set it to now.
        If a month has passed since last refresh, reset credits to 100.
        """
        now = timezone.now()

        # First time - set the refresh date
        if self.credit_refresh_date is None:
            self.credit_refresh_date = now
            self.save(update_fields=['credit_refresh_date'])
            return

        # Calculate next refresh date (one month from last refresh)
        next_refresh_date = self.credit_refresh_date + relativedelta(months=1)

        # If current time has passed the next refresh date, refresh credits
        if now >= next_refresh_date:
            self.total_credits = 100  # Reset to default amount
            self.credit_refresh_date = now  # Update refresh date
            self.save(update_fields=['total_credits', 'credit_refresh_date'])

    def get_next_refresh_date(self):
        """
        Get the next credit refresh date.
        Returns None if credit_refresh_date is not set.
        """
        if self.credit_refresh_date is None:
            return None
        return self.credit_refresh_date + relativedelta(months=1)


class UserProfile(models.Model):
    """Extended user profile with verification status and token"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_verified = models.BooleanField(default=False, help_text="Whether the user's email is verified")
    verification_token = models.CharField(max_length=255, blank=True, null=True, help_text="Email verification token")
    verification_token_created_at = models.DateTimeField(null=True, blank=True, help_text="When the verification token was created")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Verified: {self.is_verified}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile and set credit refresh date when User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Set initial credit refresh date
        if instance.credit_refresh_date is None:
            instance.credit_refresh_date = timezone.now()
            instance.save(update_fields=['credit_refresh_date'])


class AgentTemplate(models.Model):
    """Template agents that users can instantiate"""

    # Category choices
    CATEGORY_CHOICES = [
        ('research', 'Research & Information'),
        ('project_mgmt', 'Project Management'),
        ('developer', 'Developer & Code'),
        ('communication', 'Communication & Marketing'),
        ('document', 'Document & File Processing'),
        ('business', 'Business & Productivity'),
        ('education', 'Education & Learning'),
        ('creative', 'Creative & Writing'),
        ('personal', 'Personal Assistant'),
    ]

    CATEGORY_ICONS = {
        'research': '🔍',
        'project_mgmt': '💼',
        'developer': '👨‍💻',
        'communication': '📧',
        'document': '📄',
        'business': '💼',
        'education': '🎓',
        'creative': '🎨',
        'personal': '❤️',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the template")
    name = models.CharField(max_length=200, help_text="Template name (e.g., 'Email Assistant', 'Research Agent')")
    description = models.TextField(help_text="Description of what this template agent does")
    system_prompt = models.TextField(help_text="Pre-configured system prompt for this template")

    # Category
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='personal',
        help_text="Template category for organization"
    )

    # Default tools and connections
    default_tools = models.JSONField(
        default=list,
        help_text="List of app names for Composio connections, e.g., ['GMAIL', 'SLACK']"
    )
    default_agent_tools = models.JSONField(
        default=list,
        help_text="List of agent tool names, e.g., ['weather', 'calculator', 'web_search']"
    )

    # Visual representation
    icon = models.CharField(max_length=10, default='🤖', help_text="Emoji icon for the template")

    # Template metadata
    is_active = models.BooleanField(default=True, help_text="Whether this template is shown to users")
    usage_count = models.IntegerField(default=0, help_text="Number of times this template has been instantiated")
    sort_order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'sort_order', '-usage_count', 'name']

    def __str__(self):
        return f"{self.icon} {self.name}"

    @property
    def category_display_name(self):
        """Returns the display name for the category"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)

    @property
    def category_icon(self):
        """Returns the emoji icon for the category"""
        return self.CATEGORY_ICONS.get(self.category, '📁')


class Agent(models.Model):
    """AI Agent model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier for the agent")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agents')
    name = models.CharField(max_length=200)
    prompt = models.TextField(help_text="System prompt for the agent")
    avatar_image = models.BinaryField(null=True, blank=True, help_text="Agent avatar image stored as binary data")
    avatar_filename = models.CharField(max_length=255, blank=True, help_text="Original avatar filename")
    avatar_mime_type = models.CharField(max_length=100, blank=True, default='image/jpeg', help_text="MIME type of avatar image")
    
    # This field will store the specific slugs (e.g., "GMAIL_SEARCH")
    # generated by the AI in the background.
    tools = models.JSONField(
        default=list, 
        help_text="List of specific Composio action slugs"
    )
    
    # --- NEW FIELD ---
    # This field will store what the user selected (e.g., ["GMAIL"])
    # You will use this to populate the UI.
    app_connections = models.JSONField(
        default=list,
        help_text="List of app names, e.g., ['GMAIL', 'GOOGLEDRIVE']"
    )

    # Agent-specific tools (non-Composio)
    # These are tools like weather, calculator, yahoo_finance, etc.
    # that don't require external connections
    agent_tools = models.JSONField(
        default=list,
        help_text="List of agent tool names, e.g., ['weather', 'calculator', 'yahoo_finance']"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def get_avatar_content(self):
        """Returns the avatar image content as bytes"""
        if not self.avatar_image:
            return None
        # BinaryField can return bytes or memoryview depending on database backend
        if isinstance(self.avatar_image, bytes):
            return self.avatar_image
        elif isinstance(self.avatar_image, memoryview):
            return self.avatar_image.tobytes()
        else:
            return bytes(self.avatar_image)


class ComposioConnection(models.Model):
    """Tracks which Composio tools a user has connected"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='composio_connections')
    tool_name = models.CharField(max_length=100, help_text="Tool identifier (e.g., 'GMAIL', 'GITHUB')")
    auth_config_id = models.CharField(max_length=200, blank=True, help_text="Composio auth config ID")
    composio_connection_id = models.CharField(max_length=200, blank=True, help_text="Composio connection ID (from API)")
    composio_entity_id = models.CharField(max_length=200, blank=True, help_text="Composio entity/user ID (user_{django_user_id})")
    connected_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when connection was soft-deleted. Used to prevent immediate recreation from Composio sync.")
    metadata = models.JSONField(default=dict, help_text="Additional connection metadata")
    
    class Meta:
        unique_together = ['user', 'tool_name']
        ordering = ['-connected_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.tool_name}"


class ChatMessage(models.Model):
    """Chat messages for each agent"""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System')
    ])
    content = models.TextField()
    attachments = models.JSONField(default=list, help_text="List of file attachments")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.agent.name} - {self.role}: {self.content[:50]}"


class FileAttachment(models.Model):
    """File attachments for messages - stored in database as binary data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachments')
    agent = models.ForeignKey('Agent', on_delete=models.CASCADE, related_name='files', null=True, blank=True, help_text="Agent this file belongs to")
    file_content = models.BinaryField(help_text="Binary file content stored in database", null=True, blank=True)
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="Size in bytes", default=0)
    mime_type = models.CharField(max_length=100, default='application/octet-stream')
    is_temporary = models.BooleanField(default=False, help_text="If True, file will be auto-deleted after being used in a message")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        agent_name = self.agent.name if self.agent else 'No Agent'
        return f"{self.original_filename} ({self.user.username} - {agent_name})"
    
    def get_file_content(self):
        """Returns the file content as bytes"""
        if not self.file_content:
            return None
        # BinaryField can return bytes or memoryview depending on database backend
        if isinstance(self.file_content, bytes):
            return self.file_content
        elif isinstance(self.file_content, memoryview):
            return self.file_content.tobytes()
        else:
            return bytes(self.file_content)


class Trigger(models.Model):
    """Automated triggers for agents"""
    TRIGGER_TYPES = [
        ('schedule', 'Scheduled'),
        ('event', 'Event-based'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('stopped', 'Stopped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='triggers')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='triggers')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Composio trigger configuration
    composio_trigger_id = models.CharField(max_length=200, blank=True, help_text="Composio trigger ID")
    trigger_slug = models.CharField(max_length=200, help_text="Composio trigger slug (e.g., GMAIL_NEW_GMAIL_MESSAGE)")
    trigger_config = models.JSONField(default=dict, help_text="Trigger configuration (e.g., schedule, filters)")
    
    # Action to perform when triggered
    action_prompt = models.TextField(help_text="What the agent should do when triggered")
    
    # Statistics
    trigger_count = models.IntegerField(default=0, help_text="Number of times triggered")
    last_triggered = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()}) - {self.status}"


class TriggerExecution(models.Model):
    """Log of trigger executions"""
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name='executions')
    triggered_at = models.DateTimeField(auto_now_add=True)
    event_data = models.JSONField(default=dict, help_text="Data that triggered the event")
    agent_response = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.trigger.name} - {self.triggered_at}"


class Workflow(models.Model):
    """Visual workflows - combine triggers, actions, and logic"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workflows')
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='workflows', null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # React Flow data structure
    nodes = models.JSONField(default=list, help_text="Workflow nodes (triggers, actions, conditions)")
    edges = models.JSONField(default=list, help_text="Connections between nodes")
    viewport = models.JSONField(default=dict, help_text="Viewport position and zoom")
    
    # Statistics
    execution_count = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} - {self.status} ({self.user.username})"


class WorkflowExecution(models.Model):
    """Log of workflow executions"""
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    executed_at = models.DateTimeField(auto_now_add=True)
    input_data = models.JSONField(default=dict, help_text="Input that started the workflow")
    output_data = models.JSONField(default=dict, help_text="Final workflow output")
    execution_trace = models.JSONField(default=list, help_text="Step-by-step execution log")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    execution_time_ms = models.IntegerField(default=0, help_text="Execution time in milliseconds")
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.workflow.name} - {self.executed_at}"


class UsageLog(models.Model):
    """Log of credit usage for tracking and analytics"""
    ACTION_TYPES = [
        ('message', 'Chat Message'),
        ('tool_call', 'Tool Execution'),
        ('admin_add', 'Admin Credit Addition'),
        ('purchase', 'Credit Purchase'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='usage_logs')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, default='message')
    credits_used = models.IntegerField(help_text="Number of credits used (positive) or added (negative)")
    credits_remaining = models.IntegerField(help_text="User's credit balance after this transaction")
    description = models.TextField(blank=True, help_text="Optional description of the action")
    metadata = models.JSONField(default=dict, help_text="Additional metadata (e.g., message length, tool name)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]

    def __str__(self):
        action = "used" if self.credits_used > 0 else "received"
        return f"{self.user.username} {action} {abs(self.credits_used)} credits - {self.get_action_type_display()}"


class MessagingChannel(models.Model):
    """Connect agents to messaging platforms (Telegram, WhatsApp)"""
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='messaging_channels')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)

    # Platform-specific credentials
    bot_token = models.CharField(max_length=500, blank=True, help_text="Telegram bot token")
    bot_username = models.CharField(max_length=200, blank=True, help_text="Telegram bot username")
    webhook_url = models.URLField(blank=True, max_length=500, help_text="Webhook URL for this channel")

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_error = models.TextField(blank=True, help_text="Last error message if status is 'error'")

    # Statistics
    message_count = models.IntegerField(default=0, help_text="Total messages processed")
    last_message_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['agent', 'platform']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent.name} - {self.get_platform_display()}"


class MessagingSession(models.Model):
    """Track active conversations on messaging platforms"""
    channel = models.ForeignKey(MessagingChannel, on_delete=models.CASCADE, related_name='sessions')

    # External user identification
    external_user_id = models.CharField(max_length=200, help_text="Platform user ID (Telegram user ID or WhatsApp phone)")
    external_chat_id = models.CharField(max_length=200, help_text="Platform chat ID for sending responses")
    external_username = models.CharField(max_length=200, blank=True, help_text="Username from the platform")

    # Session state
    is_active = models.BooleanField(default=True)
    message_count = models.IntegerField(default=0)

    # Conversation history (stored in ChatMessage model via agent)
    last_message_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['channel', 'external_user_id']
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['channel', 'is_active']),
            models.Index(fields=['external_user_id']),
        ]

    def __str__(self):
        return f"{self.channel.agent.name} - {self.external_username or self.external_user_id}"
