from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'agent-templates', views.AgentTemplateViewSet, basename='agent-template')
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'connections', views.ComposioConnectionViewSet, basename='connection')
router.register(r'files', views.FileAttachmentViewSet, basename='file')
router.register(r'triggers', views.TriggerViewSet, basename='trigger')
router.register(r'workflows', views.WorkflowViewSet, basename='workflow')

urlpatterns = [
    # Auth endpoints are defined in config/urls.py to avoid duplicates
    # Router URLs
    path('', include(router.urls)),

    # Telegram Bot Integration
    path('agents/<uuid:agent_id>/telegram/connect/', views.connect_telegram_bot, name='telegram_connect'),
    path('agents/<uuid:agent_id>/messaging/disconnect/', views.disconnect_messaging_channel, name='messaging_disconnect'),
    path('agents/<uuid:agent_id>/messaging/channels/', views.get_messaging_channels, name='messaging_channels'),
    path('telegram/webhook/<uuid:agent_id>/', views.telegram_webhook, name='telegram_webhook'),
]

