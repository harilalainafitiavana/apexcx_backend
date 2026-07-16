# agents/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from agents.views import AgentViewSet, CongeViewSet, SoldeCongeViewSet

router = DefaultRouter()
router.register(r'agents', AgentViewSet, basename='agent')

router.register(r'conges', CongeViewSet, basename='conge')
router.register(r'soldes-conges', SoldeCongeViewSet, basename='solde-conge')

urlpatterns = [
    path('', include(router.urls)),
]