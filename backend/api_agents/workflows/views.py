import traceback
import asyncio
import time

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from ..workflows.models import Trigger, TriggerExecution, Workflow, WorkflowExecution
from ..agents.models import Agent, ChatMessage
from ..agents.services.agent_service import AgentService
from . import serializers
from .serializers import (
    TriggerSerializer, TriggerExecutionSerializer,
    WorkflowSerializer, WorkflowExecutionSerializer
)


@extend_schema_view(
    list=extend_schema(
        tags=['triggers'],
        operation_id='triggers_list',
        summary='List all triggers',
        description='Returns list of all triggers owned by the authenticated user. Automation triggers API. All endpoints require authentication.',
        responses={
            200: OpenApiResponse(response=TriggerSerializer(many=True), description='List of triggers'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['triggers'],
        operation_id='triggers_create',
        summary='Create a new trigger',
        description='Creates a new automation trigger. All endpoints require authentication.',
        request=TriggerSerializer,
        responses={
            201: OpenApiResponse(response=TriggerSerializer, description='Trigger created'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    retrieve=extend_schema(
        tags=['triggers'],
        operation_id='triggers_retrieve',
        summary='Get trigger details',
        description='Returns details of a specific trigger by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger details'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    update=extend_schema(
        tags=['triggers'],
        operation_id='triggers_update',
        summary='Update trigger (full)',
        description='Fully updates a trigger. All fields are required. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        request=TriggerSerializer,
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    partial_update=extend_schema(
        tags=['triggers'],
        operation_id='triggers_partial_update',
        summary='Update trigger (partial)',
        description='Partially updates a trigger. Only provided fields will be updated. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        request=TriggerSerializer,
        responses={
            200: OpenApiResponse(response=TriggerSerializer, description='Trigger updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    ),
    destroy=extend_schema(
        tags=['triggers'],
        operation_id='triggers_destroy',
        summary='Delete trigger',
        description='Deletes a trigger by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Trigger ID (integer)',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='Trigger deleted successfully'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Trigger not found')
        }
    )
)
class TriggerViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Triggers (e.g., "on new email...").
    """
    serializer_class = TriggerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Ensures users can only see their own triggers.
        """
        return Trigger.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Returns the hardcoded list of available trigger types for the UI.
        """
        agent_service = AgentService(request.user)
        triggers = agent_service.get_available_triggers()
        return Response(triggers)

    def perform_create(self, serializer):
        """
        Called when a new trigger is created.
        """
        trigger = serializer.save(user=self.request.user)

        # If it's an event-based trigger, register it with Composio
        if trigger.trigger_type == 'event':
            try:
                agent_service = AgentService(self.request.user)
                result = agent_service.create_trigger(trigger)

                if result.get('success'):
                    trigger.composio_trigger_id = result.get('trigger_id', '')
                    trigger.save()
                    print(f"✅ Trigger created in Composio: {trigger.composio_trigger_id}")
                else:
                    print(f"⚠️ Failed to create trigger in Composio: {result.get('error')}")

            except Exception as e:
                print(f"❌ Error creating trigger in Composio: {e}")
                traceback.print_exc()

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Sets a trigger's status to 'active'.
        """
        trigger = self.get_object()
        trigger.status = 'active'
        trigger.save()
        return Response({'status': 'Trigger activated'})

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Sets a trigger's status to 'paused'.
        """
        trigger = self.get_object()
        trigger.status = 'paused'
        trigger.save()
        return Response({'status': 'Trigger paused'})

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """
        Sets a trigger's status to 'stopped'.
        """
        trigger = self.get_object()
        trigger.status = 'stopped'
        trigger.save()
        return Response({'status': 'Trigger stopped'})

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Gets the 50 most recent execution logs for a trigger.
        """
        trigger = self.get_object()
        executions = TriggerExecution.objects.filter(trigger=trigger)[:50]
        serializer = TriggerExecutionSerializer(executions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Manually runs a trigger's action prompt.
        """
        trigger = self.get_object()

        try:
            agent_service = AgentService(request.user)
            print("--- [TEST TRIGGER] ---")

            # 1. Get history (to provide context)
            chat_history_qs = ChatMessage.objects.filter(agent=trigger.agent).order_by('-created_at')[:6]
            chat_history = list(chat_history_qs)
            chat_history.reverse()
            chat_history_formatted = [{"role": msg.role, "content": msg.content} for msg in chat_history]

            # 2. Get test prompt
            test_prompt = f"[TEST TRIGGER] {trigger.action_prompt}"
            chat_history_formatted.append({"role": "user", "content": test_prompt})

            # 3. Select tools for this prompt
            specific_tools_slugs = agent_service.select_tools_for_prompt(
                user_prompt=test_prompt,
                app_names=trigger.agent.app_connections,
                chat_history=chat_history_formatted
            )

            # 4. Execute
            if not specific_tools_slugs:
                response = asyncio.run(agent_service._chat_without_tools(
                    agent_model=trigger.agent,
                    message=test_prompt,
                    chat_history=chat_history_formatted
                ))
            else:
                response = asyncio.run(agent_service._chat_with_composio(
                    agent_model=trigger.agent,
                    message=test_prompt,
                    specific_tools_slugs=specific_tools_slugs,
                    chat_history=chat_history_formatted
                ))

            # 5. Log the execution
            execution = TriggerExecution.objects.create(
                trigger=trigger,
                event_data={'test': True, 'manual_trigger': True},
                agent_response=response,
                success=True
            )

            trigger.trigger_count += 1
            trigger.save()

            return Response({
                'success': True,
                'response': response,
                'execution_id': execution.id
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        tags=['workflows'],
        operation_id='workflows_list',
        summary='List all workflows',
        description='Returns list of all workflows owned by the authenticated user. Visual workflow management API. All endpoints require authentication.',
        responses={
            200: OpenApiResponse(response=WorkflowSerializer(many=True), description='List of workflows'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['workflows'],
        operation_id='workflows_create',
        summary='Create a new workflow',
        description='Creates a new visual workflow. All endpoints require authentication.',
        request=WorkflowSerializer,
        responses={
            201: OpenApiResponse(response=WorkflowSerializer, description='Workflow created'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    retrieve=extend_schema(
        tags=['workflows'],
        operation_id='workflows_retrieve',
        summary='Get workflow details',
        description='Returns details of a specific workflow by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow details'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    update=extend_schema(
        tags=['workflows'],
        operation_id='workflows_update',
        summary='Update workflow (full)',
        description='Fully updates a workflow. All fields are required. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        request=WorkflowSerializer,
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    partial_update=extend_schema(
        tags=['workflows'],
        operation_id='workflows_partial_update',
        summary='Update workflow (partial)',
        description='Partially updates a workflow. Only provided fields will be updated. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        request=WorkflowSerializer,
        responses={
            200: OpenApiResponse(response=WorkflowSerializer, description='Workflow updated'),
            400: OpenApiResponse(description='Validation error'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    ),
    destroy=extend_schema(
        tags=['workflows'],
        operation_id='workflows_destroy',
        summary='Delete workflow',
        description='Deletes a workflow by ID. All endpoints require authentication.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Workflow ID (integer)',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='Workflow deleted successfully'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Workflow not found')
        }
    )
)
class WorkflowViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing visual Workflows (e.g., React Flow).
    """
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Ensures users can only see their own workflows.
        """
        return Workflow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Associates the workflow with the current user.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """
        Gets the 50 most recent execution logs for a workflow.
        """
        workflow = self.get_object()
        executions = WorkflowExecution.objects.filter(workflow=workflow)[:50]
        serializer = WorkflowExecutionSerializer(executions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        Manually executes a workflow.
        (Currently a mock implementation).
        """
        workflow = self.get_object()

        try:
            start_time = time.time()

            # TODO: Implement actual workflow execution logic
            input_data = request.data.get('input', {})

            execution = WorkflowExecution.objects.create(
                workflow=workflow,
                input_data=input_data,
                output_data={'status': 'success', 'message': 'Workflow executed successfully (MOCK)'},
                execution_trace=[
                    {'step': 1, 'node': 'start', 'status': 'completed'},
                    {'step': 2, 'node': 'action', 'status': 'completed'},
                ],
                success=True,
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

            workflow.execution_count += 1
            workflow.last_executed = execution.executed_at
            workflow.save()

            return Response({
                'success': True,
                'execution': WorkflowExecutionSerializer(execution).data
            })

        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Sets a workflow's status to 'active'.
        """
        workflow = self.get_object()
        workflow.status = 'active'
        workflow.save()
        return Response(WorkflowSerializer(workflow).data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """
        Sets a workflow's status to 'paused'.
        """
        workflow = self.get_object()
        workflow.status = 'paused'
        workflow.save()
        return Response(WorkflowSerializer(workflow).data)

    @action(detail=False, methods=['post'])
    def duplicate(self, request):
        """
        Creates a copy of an existing workflow.
        """
        try:
            workflow_id = request.data.get('workflow_id')
            original = Workflow.objects.get(id=workflow_id, user=request.user)

            # Create a copy
            workflow = Workflow.objects.create(
                user=request.user,
                agent=original.agent,
                name=f"{original.name} (Copy)",
                description=original.description,
                status='draft',
                nodes=original.nodes,
                edges=original.edges,
                viewport=original.viewport
            )

            return Response(WorkflowSerializer(workflow).data, status=status.HTTP_201_CREATED)

        except Workflow.DoesNotExist:
            return Response(
                {'error': 'Workflow not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
