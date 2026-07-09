# it/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from it.models import Equipement
from it.serializers import EquipementSerializer, EquipementListSerializer, EquipementStatsSerializer


class EquipementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les équipements (matériel IT).
    
    - GET /api/it/equipements/ : Liste de tous les équipements
    - POST /api/it/equipements/ : Créer un nouvel équipement
    - GET /api/it/equipements/{id}/ : Détails d'un équipement
    - PUT /api/it/equipements/{id}/ : Mettre à jour un équipement
    - PATCH /api/it/equipements/{id}/ : Mise à jour partielle
    - DELETE /api/it/equipements/{id}/ : Supprimer un équipement
    - GET /api/it/equipements/statistiques/ : Statistiques des équipements
    - GET /api/it/equipements/recherche/?q=texte : Rechercher un équipement
    - GET /api/it/equipements/par_poste/{poste_id}/ : Équipements d'un poste
    """
    
    queryset = Equipement.objects.all().select_related('poste', 'projet')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EquipementListSerializer
        return EquipementSerializer
    
    def get_queryset(self):
        """Filtre les équipements par recherche si paramètre 'q' est présent."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('q', None)
        
        if search:
            queryset = queryset.filter(
                Q(type__icontains=search) |
                Q(marque__icontains=search) |
                Q(modele__icontains=search) |
                Q(numero_serie__icontains=search) |
                Q(emplacement__icontains=search)
            )
        
        # Filtre par statut
        statut = self.request.query_params.get('statut', None)
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre par poste
        poste_id = self.request.query_params.get('poste_id', None)
        if poste_id:
            queryset = queryset.filter(poste_id=poste_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne des statistiques sur les équipements."""
        total = Equipement.objects.count()
        
        # Statistiques par statut
        par_statut = {}
        for statut in Equipement.Statut.choices:
            count = Equipement.objects.filter(statut=statut[0]).count()
            if count > 0:
                par_statut[statut[1]] = count
        
        # Statistiques par type
        par_type = {}
        types = Equipement.objects.values('type').annotate(count=Count('type'))
        for item in types:
            par_type[item['type']] = item['count']
        
        # Statistiques par poste (top 5 postes avec le plus d'équipements)
        par_poste = {}
        postes = Equipement.objects.values('poste__code').annotate(count=Count('poste')).order_by('-count')[:5]
        for item in postes:
            if item['poste__code']:
                par_poste[item['poste__code']] = item['count']
        
        return Response({
            'total': total,
            'par_statut': par_statut,
            'par_type': par_type,
            'par_poste': par_poste
        })
    
    @action(detail=False, methods=['get'], url_path='par-poste/(?P<poste_id>[^/.]+)')
    def par_poste(self, request, poste_id=None):
        """
        Récupère tous les équipements d'un poste spécifique.
        """
        try:
            from workspaces.models import Poste
            poste = Poste.objects.get(id=poste_id)
            equipements = Equipement.objects.filter(poste=poste)
            serializer = EquipementListSerializer(equipements, many=True)
            return Response(serializer.data)
        except Poste.DoesNotExist:
            return Response(
                {'error': 'Poste non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """
        Changer le statut d'un équipement.
        Body: {"statut": "en_panne"}  # ou "disponible", "affecte", "en_maintenance", "hors_service"
        """
        equipement = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if not nouveau_statut:
            return Response(
                {'error': "Le statut est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que le statut est valide
        statuts_valides = [choice[0] for choice in Equipement.Statut.choices]
        if nouveau_statut not in statuts_valides:
            return Response(
                {'error': f"Statut invalide. Choisir parmi: {', '.join(statuts_valides)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equipement.statut = nouveau_statut
        equipement.save()
        
        serializer = self.get_serializer(equipement)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def affecter_poste(self, request, pk=None):
        """
        Affecter un équipement à un poste.
        Body: {"poste_id": 123}
        """
        equipement = self.get_object()
        poste_id = request.data.get('poste_id')
        
        if not poste_id:
            return Response(
                {'error': "L'ID du poste est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from workspaces.models import Poste
            poste = Poste.objects.get(id=poste_id)
        except Poste.DoesNotExist:
            return Response(
                {'error': "Poste non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        equipement.poste = poste
        if equipement.statut == Equipement.Statut.DISPONIBLE:
            equipement.statut = Equipement.Statut.AFFECTE
        equipement.save()
        
        serializer = self.get_serializer(equipement)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def liberer_poste(self, request, pk=None):
        """
        Libérer un équipement de son poste.
        """
        equipement = self.get_object()
        equipement.poste = None
        equipement.statut = Equipement.Statut.DISPONIBLE
        equipement.save()
        
        serializer = self.get_serializer(equipement)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """
        Création d'un équipement avec validation supplémentaire.
        """
        # Vérifier que le numéro de série est unique
        numero_serie = request.data.get('numero_serie')
        if numero_serie and Equipement.objects.filter(numero_serie=numero_serie).exists():
            return Response(
                {'error': f"Un équipement avec le numéro de série '{numero_serie}' existe déjà."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)