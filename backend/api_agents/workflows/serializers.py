from rest_framework import serializers
from ..workflows import models as workflow_models


class TriggerSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    agent_name = serializers.ReadOnlyField(source='agent.name')

    class Meta:
        model = workflow_models.Trigger
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
        model = workflow_models.TriggerExecution
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
        model = workflow_models.Workflow
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
        model = workflow_models.WorkflowExecution
        fields = [
            'id', 'workflow', 'workflow_name', 'executed_at', 'input_data',
            'output_data', 'execution_trace', 'success', 'error_message',
            'execution_time_ms'
        ]
        read_only_fields = ['executed_at']
