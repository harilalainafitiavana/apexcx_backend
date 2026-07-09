from rest_framework import viewsets, permissions, filters, status
from .models import Projet
from .serializers import (ProjetSerializer, RackSerializer, RackCreateUpdateSerializer, 
    PosteSerializer)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from workspaces.models import Rack, Poste, Projet



class ProjetViewSet(viewsets.ModelViewSet):
    """
    CRUD complet sur les projets :
    - GET    /projets/          -> liste
    - POST   /projets/          -> création
    - GET    /projets/{id}/     -> détail
    - PUT    /projets/{id}/     -> modification complète
    - PATCH  /projets/{id}/     -> modification partielle
    - DELETE /projets/{id}/     -> suppression
    """
    queryset = Projet.objects.all().order_by("-date_creation")
    serializer_class = ProjetSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Recherche via ?search=... sur le nom et le superviseur (texte libre)
    filter_backends = [filters.SearchFilter]
    search_fields = ["nom", "superviseur"]


class RackViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les Racks.
    - GET /api/racks/ : Liste de tous les racks
    - POST /api/racks/ : Créer un nouveau rack
    - GET /api/racks/{id}/ : Détails d'un rack
    - PUT /api/racks/{id}/ : Mettre à jour un rack
    - DELETE /api/racks/{id}/ : Supprimer un rack
    - POST /api/racks/{id}/generer_postes/ : Régénérer les postes d'un rack
    """
    queryset = Rack.objects.all().prefetch_related('postes', 'postes__agent__profil')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RackCreateUpdateSerializer
        return RackSerializer
    
    @action(detail=True, methods=['post'])
    def generer_postes(self, request, pk=None):
        """
        Endpoint pour régénérer les postes d'un rack.
        Utile si la configuration a été modifiée manuellement.
        """
        rack = self.get_object()
        postes = rack.generer_postes()
        serializer = PosteSerializer(postes, many=True)
        return Response({
            'message': f'Postes régénérés pour {rack.nom}',
            'postes': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def postes_libres(self, request, pk=None):
        """
        Récupère tous les postes libres d'un rack.
        """
        rack = self.get_object()
        postes_libres = rack.postes.filter(statut=Poste.Statut.LIBRE)
        serializer = PosteSerializer(postes_libres, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """
        Statistiques d'occupation du rack.
        """
        rack = self.get_object()
        total = rack.total_postes
        occupes = rack.postes.filter(statut=Poste.Statut.OCCUPE).count()
        libres = rack.postes.filter(statut=Poste.Statut.LIBRE).count()
        maintenance = rack.postes.filter(statut=Poste.Statut.MAINTENANCE).count()
        
        return Response({
            'total': total,
            'occupes': occupes,
            'libres': libres,
            'maintenance': maintenance,
            'taux_occupation': round((occupes / total * 100) if total > 0 else 0, 2)
        })


class PosteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les Postes individuellement.
    - GET /api/postes/ : Liste de tous les postes
    - GET /api/postes/{id}/ : Détails d'un poste
    - PATCH /api/postes/{id}/ : Mettre à jour un poste (ex: changer statut)
    """
    queryset = Poste.objects.all().select_related('rack', 'agent__profil')
    serializer_class = PosteSerializer
    
    @action(detail=True, methods=['post'])
    def assigner_agent(self, request, pk=None):
        """
        Assigner un agent à ce poste.
        Body: {"agent_id": 123}
        """
        from agents.models import Agent
        
        poste = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response(
                {'error': "L'ID de l'agent est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            agent = Agent.objects.get(id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {'error': "Agent non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            poste.assigner_agent(agent)
            serializer = self.get_serializer(poste)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def liberer(self, request, pk=None):
        """
        Libérer le poste (enlever l'agent).
        """
        poste = self.get_object()
        poste.liberer()
        serializer = self.get_serializer(poste)
        return Response(serializer.data)

