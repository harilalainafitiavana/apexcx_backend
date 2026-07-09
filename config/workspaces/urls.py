# workspaces/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RackViewSet, PosteViewSet, ProjetViewSet

router = DefaultRouter()
router.register(r'racks', RackViewSet, basename='rack')
router.register(r'postes', PosteViewSet, basename='poste')
router.register(r'projets', ProjetViewSet, basename='projet')

urlpatterns = [
    path('', include(router.urls)),
]