# agents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from agents.views import AgentViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')

urlpatterns = [
    path('', include(router.urls)),
]