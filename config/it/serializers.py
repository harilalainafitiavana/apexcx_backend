# it/serializers.py
from rest_framework import serializers
from it.models import Equipement
from workspaces.models import Poste, Projet


class EquipementSerializer(serializers.ModelSerializer):
    """Serializer pour les équipements"""
    
    # Champs en lecture (avec noms lisibles)
    poste_code = serializers.CharField(source='poste.code', read_only=True, default=None)
    projet_nom = serializers.CharField(source='projet.nom', read_only=True, default=None)
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    type_equipement = serializers.CharField(source='type', read_only=True)
    
    # Champs en écriture (on reçoit des IDs)
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(),
        source='poste',
        write_only=True,
        required=False,
        allow_null=True
    )
    projet_id = serializers.PrimaryKeyRelatedField(
        queryset=Projet.objects.all(),
        source='projet',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Equipement
        fields = [
            'id', 'type', 'marque', 'modele', 'numero_serie',
            'statut', 'statut_label', 'date_acquisition',
            'commentaire', 'emplacement',
            'poste', 'poste_code', 'poste_id',
            'projet', 'projet_nom', 'projet_id',
            'date_creation'
        ]
        read_only_fields = ['date_creation']


class EquipementListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des équipements"""
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Equipement
        fields = [
            'id', 'type', 'marque', 'modele', 'numero_serie',
            'statut', 'statut_label', 'poste_code'
        ]


class EquipementStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des équipements"""
    total = serializers.IntegerField()
    par_statut = serializers.DictField()
    par_type = serializers.DictField()
    par_poste = serializers.DictField()