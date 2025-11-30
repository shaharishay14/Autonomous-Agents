from django.db import models
from django.conf import settings


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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='triggers')
    agent = models.ForeignKey('api_agents.Agent', on_delete=models.CASCADE, related_name='triggers')
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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workflows')
    agent = models.ForeignKey('api_agents.Agent', on_delete=models.CASCADE, related_name='workflows', null=True, blank=True)
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
