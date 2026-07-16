# it/serializers.py
from rest_framework import serializers
from it.models import Equipement
from workspaces.models import Poste, Projet


class EquipementSerializer(serializers.ModelSerializer):
    """Serializer pour les équipements"""
    poste_code = serializers.CharField(source='poste.code', read_only=True, default=None)
    projet_nom = serializers.CharField(source='projet.nom', read_only=True, default=None)
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    type_equipement = serializers.CharField(source='type', read_only=True)

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
            'projet', 'projet_nom', 'projet_id', 'type_equipement',
            'date_creation'
        ]
        read_only_fields = ['date_creation']

    def validate(self, attrs):
        """
        Règle métier : un équipement n'est rattaché à un poste QUE si son
        statut est "affecté" (= "Occupé" côté UI). Pour tout autre statut,
        il retourne automatiquement au Stock (poste = None).
        """
        statut = attrs.get('statut', getattr(self.instance, 'statut', Equipement.Statut.DISPONIBLE))
        poste = attrs.get('poste', getattr(self.instance, 'poste', None)) if self.instance or 'poste' in attrs else attrs.get('poste')

        if statut == Equipement.Statut.AFFECTE:
            if not poste:
                raise serializers.ValidationError({
                    'poste_id': "Un poste est requis lorsque le statut est 'Affecté'."
                })
        else:
            # Statut disponible / en_panne / en_maintenance / hors_service
            attrs['poste'] = None
            if not attrs.get('emplacement') and not getattr(self.instance, 'emplacement', None):
                attrs['emplacement'] = 'Stock'

        return attrs


class EquipementListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des équipements"""
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    poste_code = serializers.CharField(source='poste.code', read_only=True, default=None)
    projet_nom = serializers.CharField(source='projet.nom', read_only=True, default=None)

    class Meta:
        model = Equipement
        fields = [
            'id', 'type', 'marque', 'modele', 'numero_serie',
            'statut', 'statut_label', 'poste_code', 'projet_nom', 'emplacement'
        ]


class EquipementStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des équipements"""
    total = serializers.IntegerField()
    par_statut = serializers.DictField()
    par_type = serializers.DictField()
    par_poste = serializers.DictField()