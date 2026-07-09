# accounts/urls.py - VERSION COMPLÈTE
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, MeView, LogoutView, RoleViewSet, UtilisateurViewSet, ProfilViewSet


# Router pour les rôles
router = DefaultRouter()
router.register(r"roles", RoleViewSet, basename="role")
router.register("profils", ProfilViewSet, basename="profil")

# Router pour les utilisateurs
utilisateur_router = DefaultRouter()
utilisateur_router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateur')

urlpatterns = [
    # Routes d'authentification
    path("auth/login/", LoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    
    # Routes pour les rôles 
    path("", include(router.urls)),
    
    # Routes pour les utilisateurs 
    path("", include(utilisateur_router.urls)),
]