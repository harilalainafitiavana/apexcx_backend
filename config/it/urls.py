from django.urls import path, include
from rest_framework.routers import DefaultRouter
from it.views import EquipementViewSet

router = DefaultRouter()
router.register(r'equipements', EquipementViewSet, basename='equipement')

urlpatterns = [
    path('', include(router.urls)),
]