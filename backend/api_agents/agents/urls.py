"""
Agents URL Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, AgentTemplateViewSet


router = DefaultRouter()
router.register(r'templates', AgentTemplateViewSet, basename='agent-template')
router.register(r'', AgentViewSet, basename='agent')

urlpatterns = [
    path('', include(router.urls)),
]
