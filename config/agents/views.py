# agents/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from agents.models import Agent, Diplome, FormationSuivie, ContactUrgence, RibBancaire, Conge, SoldeConge
from agents.serializers import AgentSerializer, AgentListSerializer, CongeSerializer, SoldeCongeSerializer
from workspaces.models import Poste
from django.utils import timezone



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
    


class CongeViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les congés.
    
    - GET /api/conges/ : Liste de tous les congés
    - POST /api/conges/ : Créer un nouveau congé
    - GET /api/conges/{id}/ : Détails d'un congé
    - PUT /api/conges/{id}/ : Mettre à jour un congé
    - PATCH /api/conges/{id}/ : Mise à jour partielle
    - DELETE /api/conges/{id}/ : Supprimer un congé
    - GET /api/conges/statistiques/ : Statistiques des congés
    - GET /api/conges/par_agent/{agent_id}/ : Congés d'un agent
    - GET /api/conges/par_annee/{annee}/ : Congés par année
    - POST /api/conges/{id}/approuver/ : Approuver un congé
    - POST /api/conges/{id}/refuser/ : Refuser un congé
    """
    queryset = Conge.objects.all().select_related('agent', 'agent__profil', 'approuve_par')
    serializer_class = CongeSerializer

    def get_queryset(self):
        """Filtre les congés par agent et/ou année."""
        queryset = super().get_queryset()
        
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        annee = self.request.query_params.get('annee')
        if annee:
            queryset = queryset.filter(annee_reference=annee)
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne des statistiques sur les congés."""
        total = self.get_queryset().count()
        en_attente = self.get_queryset().filter(statut=Conge.Statut.EN_ATTENTE).count()
        approuves = self.get_queryset().filter(statut=Conge.Statut.APPROUVE).count()
        refuses = self.get_queryset().filter(statut=Conge.Statut.REFUSE).count()
        annules = self.get_queryset().filter(statut=Conge.Statut.ANNULE).count()
        
        # Statistiques par type de congé
        par_type = {}
        for type_conge in Conge.TypeConge.choices:
            count = self.get_queryset().filter(type_conge=type_conge[0]).count()
            if count > 0:
                par_type[type_conge[1]] = count
        
        # Statistiques par agent (top 5)
        par_agent = {}
        top_agents = self.get_queryset().values('agent__matricule', 'agent__profil__prenom', 'agent__profil__nom')\
            .annotate(total=Sum('duree_ouverte'))\
            .order_by('-total')[:5]
        for item in top_agents:
            nom_complet = f"{item['agent__profil__prenom']} {item['agent__profil__nom']} ({item['agent__matricule']})"
            par_agent[nom_complet] = item['total']
        
        return Response({
            'total': total,
            'en_attente': en_attente,
            'approuves': approuves,
            'refuses': refuses,
            'annules': annules,
            'par_type': par_type,
            'par_agent': par_agent
        })

    @action(detail=False, methods=['get'], url_path='par_agent/(?P<agent_id>[^/.]+)')
    def par_agent(self, request, agent_id=None):
        """Récupère tous les congés d'un agent spécifique."""
        try:
            from agents.models import Agent
            agent = Agent.objects.get(id=agent_id)
            conges = Conge.objects.filter(agent=agent)
            serializer = self.get_serializer(conges, many=True)
            return Response(serializer.data)
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Agent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='par_annee/(?P<annee>[^/.]+)')
    def par_annee(self, request, annee=None):
        """Récupère tous les congés pour une année donnée."""
        try:
            annee_int = int(annee)
            conges = Conge.objects.filter(annee_reference=annee_int)
            serializer = self.get_serializer(conges, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Année invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        """
        Approuve un congé.
        Body: {"commentaire_validation": "Commentaire optionnel"}
        """
        conge = self.get_object()
        
        if conge.statut != Conge.Statut.EN_ATTENTE:
            return Response(
                {'error': 'Seul un congé en attente peut être approuvé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conge.statut = Conge.Statut.APPROUVE
        conge.date_traitement = timezone.now()
        conge.approuve_par = request.user if request.user.is_authenticated else None
        
        commentaire = request.data.get('commentaire_validation')
        if commentaire:
            conge.commentaire_validation = commentaire
        
        conge.save()
        
        # Mettre à jour le solde de congés
        self._update_solde_conge(conge.agent, conge.annee_reference, conge.duree_ouverte)
        
        serializer = self.get_serializer(conge)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """
        Refuse un congé.
        Body: {"commentaire_validation": "Motif du refus"}
        """
        conge = self.get_object()
        
        if conge.statut != Conge.Statut.EN_ATTENTE:
            return Response(
                {'error': 'Seul un congé en attente peut être refusé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conge.statut = Conge.Statut.REFUSE
        conge.date_traitement = timezone.now()
        conge.approuve_par = request.user if request.user.is_authenticated else None
        
        commentaire = request.data.get('commentaire_validation')
        if commentaire:
            conge.commentaire_validation = commentaire
        else:
            return Response(
                {'error': 'Un motif de refus est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conge.save()
        
        serializer = self.get_serializer(conge)
        return Response(serializer.data)

    def _update_solde_conge(self, agent, annee, duree):
        """Met à jour le solde de congés de l'agent."""
        solde, created = SoldeConge.objects.get_or_create(
            agent=agent,
            annee=annee,
            defaults={
                'total_jours': 30,
                'jours_pris': 0,
                'jours_restants': 30,
                'jours_en_attente': 0
            }
        )
        
        # Calculer les jours déjà pris (approuvés) pour cette année
        jours_pris_total = Conge.objects.filter(
            agent=agent,
            annee_reference=annee,
            statut=Conge.Statut.APPROUVE
        ).aggregate(total=Sum('duree_ouverte'))['total'] or 0
        
        # Calculer les jours en attente
        jours_en_attente = Conge.objects.filter(
            agent=agent,
            annee_reference=annee,
            statut=Conge.Statut.EN_ATTENTE
        ).aggregate(total=Sum('duree_ouverte'))['total'] or 0
        
        solde.jours_pris = jours_pris_total
        solde.jours_restants = solde.total_jours - jours_pris_total
        solde.jours_en_attente = jours_en_attente
        solde.save()


class SoldeCongeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter les soldes de congés.
    
    - GET /api/soldes-conges/ : Liste de tous les soldes
    - GET /api/soldes-conges/{id}/ : Détails d'un solde
    - GET /api/soldes-conges/par_agent/{agent_id}/ : Solde d'un agent
    - GET /api/soldes-conges/par_annee/{annee}/ : Soldes par année
    """
    queryset = SoldeConge.objects.all().select_related('agent', 'agent__profil')
    serializer_class = SoldeCongeSerializer

    def get_queryset(self):
        """Filtre les soldes par agent et/ou année."""
        queryset = super().get_queryset()
        
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        annee = self.request.query_params.get('annee')
        if annee:
            queryset = queryset.filter(annee=annee)
        
        return queryset

    @action(detail=False, methods=['get'], url_path='par_agent/(?P<agent_id>[^/.]+)')
    def par_agent(self, request, agent_id=None):
        """Récupère le solde d'un agent pour l'année en cours."""
        try:
            from agents.models import Agent
            agent = Agent.objects.get(id=agent_id)
            annee = request.query_params.get('annee', timezone.now().year)
            
            solde, created = SoldeConge.objects.get_or_create(
                agent=agent,
                annee=annee,
                defaults={
                    'total_jours': 30,
                    'jours_pris': 0,
                    'jours_restants': 30,
                    'jours_en_attente': 0
                }
            )
            
            # Recalculer les jours utilisés
            jours_pris = Conge.objects.filter(
                agent=agent,
                annee_reference=annee,
                statut=Conge.Statut.APPROUVE
            ).aggregate(total=Sum('duree_ouverte'))['total'] or 0
            
            jours_attente = Conge.objects.filter(
                agent=agent,
                annee_reference=annee,
                statut=Conge.Statut.EN_ATTENTE
            ).aggregate(total=Sum('duree_ouverte'))['total'] or 0
            
            solde.jours_pris = jours_pris
            solde.jours_restants = solde.total_jours - jours_pris
            solde.jours_en_attente = jours_attente
            solde.save()
            
            serializer = self.get_serializer(solde)
            return Response(serializer.data)
            
        except Agent.DoesNotExist:
            return Response(
                {'error': 'Agent non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='par_annee/(?P<annee>[^/.]+)')
    def par_annee(self, request, annee=None):
        """Récupère tous les soldes pour une année donnée."""
        try:
            annee_int = int(annee)
            soldes = SoldeConge.objects.filter(annee=annee_int)
            serializer = self.get_serializer(soldes, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Année invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )