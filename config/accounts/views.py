from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from .models import Role
from .serializers import LoginSerializer, ProfilUpdateSerializer, UtilisateurSerializer, RoleSerializer

# Partie pour la gestion des agents et de leurs rôles
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import Profil
from .serializers import (
    UtilisateurDetailSerializer, UtilisateurListSerializer,
    ProfilSimpleSerializer, ProfilCreateSerializer
)

from django.db import transaction

Utilisateur = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class MeView(APIView):
    def get(self, request):
        return Response(UtilisateurSerializer(request.user, context={"request": request}).data)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response(status=204)
    
class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lecture seule : les rôles sont gérés en base (data migration),
    pas via l'API. On expose juste la liste pour peupler les <select>.
    GET /roles/       -> liste de tous les rôles disponibles
    GET /roles/{id}/  -> détail d'un rôle
    """
    queryset = Role.objects.all().order_by("nom")
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]




# Pour la gestion des utilisateurs et de leurs rôles, on crée un ViewSet dédié.
class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour consulter les utilisateurs et leurs rôles.
    Uniquement en lecture (ReadOnly).
    """
    queryset = Utilisateur.objects.all().select_related('profil').prefetch_related('utilisateur_roles__role')
    
    def get_permissions(self):
        if self.action in ('me', 'destroy'):
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UtilisateurListSerializer
        return UtilisateurDetailSerializer
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Récupère l'utilisateur actuellement connecté."""
        user = request.user
        serializer = UtilisateurDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def profils(self, request):
        """Récupère tous les profils (utile pour le formulaire d'ajout d'agent)."""
        profils = Profil.objects.all()
        serializer = ProfilSimpleSerializer(profils, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def changer_mot_de_passe(self, request):
        """
        Permet à un utilisateur de changer lui-même son mot de passe (ancien + nouveau).
        """
        email = request.data.get('email')
        ancien_mot_de_passe = request.data.get('ancien_mot_de_passe')
        nouveau_mot_de_passe = request.data.get('nouveau_mot_de_passe')

        if not email or not ancien_mot_de_passe or not nouveau_mot_de_passe:
            return Response(
                {'error': 'Email, ancien mot de passe et nouveau mot de passe sont requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        if not user.check_password(ancien_mot_de_passe):
            return Response({'error': 'Ancien mot de passe incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(nouveau_mot_de_passe)
        user.save()

        # L'agent vient de définir un vrai mot de passe : il n'est plus "nouveau".
        self._marquer_agent_actif_si_nouveau(user)

        return Response({'message': 'Mot de passe changé avec succès.'})

    @action(detail=False, methods=['post'])
    def reinitialiser_mot_de_passe(self, request):
        """
        Réinitialise le mot de passe d'un utilisateur à "123456" (admin, sans
        connaître l'ancien mot de passe) et remet l'agent lié au statut "nouveau"
        (son mot de passe redevient la valeur par défaut).
        """
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password('123456')
        user.save()

        profil = getattr(user, 'profil', None)
        agent = getattr(profil, 'agent', None) if profil else None
        if agent:
            agent.statut = agent.Statut.NOUVEAU
            agent.save()

        return Response({'message': 'Mot de passe réinitialisé à "123456".'})

    @action(detail=False, methods=['post'])
    def definir_mot_de_passe(self, request):
        """
        Permet à un admin de définir directement un nouveau mot de passe pour
        un utilisateur (agent ou non), sans connaître l'ancien.
        Body: {"email": "...", "nouveau_mot_de_passe": "..."}
        """
        email = request.data.get('email')
        nouveau = request.data.get('nouveau_mot_de_passe')
        if not email or not nouveau:
            return Response({'error': 'Email et nouveau mot de passe requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(nouveau)
        user.save()

        self._marquer_agent_actif_si_nouveau(user)

        return Response({'message': 'Mot de passe défini avec succès.'})

    def _marquer_agent_actif_si_nouveau(self, user):
        """Fait passer l'Agent lié (s'il existe et est encore 'nouveau') à 'actif'."""
        profil = getattr(user, 'profil', None)
        agent = getattr(profil, 'agent', None) if profil else None
        if agent and agent.statut == agent.Statut.NOUVEAU:
            agent.statut = agent.Statut.ACTIF
            agent.save()




class ProfilViewSet(viewsets.ModelViewSet):
    queryset = Profil.objects.all().prefetch_related('utilisateur__utilisateur_roles__role')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ProfilCreateSerializer
        if self.action in ('update', 'partial_update'):
            return ProfilUpdateSerializer
        return ProfilSimpleSerializer

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            return super().create(request, *args, **kwargs)