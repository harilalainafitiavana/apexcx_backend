# agents/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from agents.models import Agent, Diplome, FormationSuivie, ContactUrgence, RibBancaire
from agents.serializers import AgentSerializer, AgentListSerializer
from workspaces.models import Poste


class AgentViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les Agents.
    
    - GET /api/agents/ : Liste de tous les agents
    - POST /api/agents/ : Créer un nouvel agent
    - GET /api/agents/{id}/ : Détails d'un agent
    - PUT /api/agents/{id}/ : Mettre à jour un agent
    - PATCH /api/agents/{id}/ : Mise à jour partielle
    - DELETE /api/agents/{id}/ : Supprimer un agent
    - GET /api/agents/statistiques/ : Statistiques globales
    - GET /api/agents/recherche/?q=texte : Rechercher un agent
    """
    queryset = Agent.objects.all().select_related(
        'profil', 'projet', 'poste'
    ).prefetch_related(
        'diplomes', 'formations_suivies', 'contact_urgence', 'rib_bancaire'
    )
    
    """def get_serializer_class(self):
        Utilise un serializer différent pour la liste et les détails.
        if self.action == 'list':
            return AgentListSerializer
        return AgentSerializer"""
    
    def get_serializer_class(self):
        return AgentSerializer
    
    def get_queryset(self):
        """Filtre les agents par recherche si paramètre 'q' est présent."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('q', None)
        
        if search:
            queryset = queryset.filter(
                Q(matricule__icontains=search) |
                Q(profil__nom__icontains=search) |
                Q(profil__prenom__icontains=search) |
                Q(profil__utilisateur__email__icontains=search) |
                Q(profil__telephone__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne des statistiques sur les agents."""
        total = Agent.objects.count()
        actifs = Agent.objects.filter(statut=Agent.Statut.ACTIF).count()
        en_conge = Agent.objects.filter(statut_presence=Agent.StatutPresence.CONGES).count()
        en_tt = Agent.objects.filter(statut_presence=Agent.StatutPresence.TT).count()
        presents = Agent.objects.filter(statut_presence=Agent.StatutPresence.PRESENT).count()
        
        # Par projet
        projets_stats = {}
        for agent in Agent.objects.select_related('projet').all():
            if agent.projet:
                nom_projet = agent.projet.nom
                projets_stats[nom_projet] = projets_stats.get(nom_projet, 0) + 1
        
        # Par rôle
        roles_stats = {}
        for agent in Agent.objects.select_related('profil__utilisateur').all():
            if hasattr(agent.profil, 'utilisateur'):
                for role in agent.profil.utilisateur.utilisateur_roles.all():
                    nom_role = role.role.nom
                    roles_stats[nom_role] = roles_stats.get(nom_role, 0) + 1
        
        return Response({
            'total': total,
            'actifs': actifs,
            'presents': presents,
            'en_conge': en_conge,
            'en_tt': en_tt,
            'par_projet': projets_stats,
            'par_role': roles_stats
        })
    
    @action(detail=True, methods=['post'])
    def assigner_poste(self, request, pk=None):
        """
        Assigner un poste à un agent.
        Body: {"poste_id": 123}
        """
        agent = self.get_object()
        poste_id = request.data.get('poste_id')
        
        if not poste_id:
            return Response(
                {'error': "L'ID du poste est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            poste = Poste.objects.get(id=poste_id)
        except Poste.DoesNotExist:
            return Response(
                {'error': "Poste non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            poste.assigner_agent(agent)
            serializer = self.get_serializer(agent)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def liberer_poste(self, request, pk=None):
        """
        Libérer le poste de l'agent.
        """
        agent = self.get_object()
        
        if not agent.poste:
            return Response(
                {'error': "Cet agent n'a pas de poste assigné"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        poste = agent.poste
        poste.liberer()
        
        serializer = self.get_serializer(agent)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def changer_statut_presence(self, request, pk=None):
        """
        Changer le statut de présence d'un agent.
        Body: {"statut_presence": "present"}  # ou "abscent", "conges", "tt"
        """
        agent = self.get_object()
        nouveau_statut = request.data.get('statut_presence')
        
        if not nouveau_statut:
            return Response(
                {'error': "Le statut est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que le statut est valide
        statuts_valides = [choice[0] for choice in Agent.StatutPresence.choices]
        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f"Statut invalide. Choisir parmi: {', '.join(statuts_valides)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        agent.statut_presence = nouveau_statut
        agent.save()
        
        serializer = self.get_serializer(agent)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_projet(self, request):
        """
        Récupère les agents groupés par projet.
        """
        resultats = {}
        for agent in self.get_queryset().select_related('projet'):
            if agent.projet:
                nom_projet = agent.projet.nom
                if nom_projet not in resultats:
                    resultats[nom_projet] = []
                resultats[nom_projet].append({
                    'id': agent.id,
                    'nom_complet': f"{agent.profil.prenom} {agent.profil.nom}",
                    'matricule': agent.matricule,
                    'statut_presence': agent.statut_presence
                })
        
        return Response(resultats)
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un agent et libère son poste si nécessaire.
        """
        agent = self.get_object()
        
        # Si l'agent a un poste, le libérer
        if agent.poste:
            agent.poste.liberer()
        
        return super().destroy(request, *args, **kwargs)