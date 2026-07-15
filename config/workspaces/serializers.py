from rest_framework import serializers
from .models import Projet, Poste, Rack


class ProjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Projet
        fields = [
            "id",
            "nom",
            "couleur",
            "description",
            "superviseur",
            "statut",
            "date_creation",
        ]
        read_only_fields = ["id", "date_creation"]


class PosteSerializer(serializers.ModelSerializer):
    """Serializer pour un poste individuel"""
    # Informations sur l'agent occupant 
    agent_nom = serializers.SerializerMethodField()
    agent_id = serializers.SerializerMethodField()
    agent_matricule = serializers.SerializerMethodField()
    statut_label = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Poste
        fields = [
            'id', 'code', 'numero', 'statut', 'statut_label',
            'agent_nom', 'agent_id', 'agent_matricule'
        ]
    
    def get_agent_nom(self, obj):
        if hasattr(obj, 'agent') and obj.agent:
            return f"{obj.agent.profil.prenom} {obj.agent.profil.nom}"
        return None
    
    def get_agent_id(self, obj):
        if hasattr(obj, 'agent') and obj.agent:
            return obj.agent.id
        return None
    
    def get_agent_matricule(self, obj):
        if hasattr(obj, 'agent') and obj.agent:
            return obj.agent.matricule
        return None


class RackSerializer(serializers.ModelSerializer):
    """Serializer pour un rack avec ses postes"""
    postes = PosteSerializer(many=True, read_only=True)
    postes_occupes = serializers.SerializerMethodField()
    postes_libres = serializers.SerializerMethodField()
    taux_occupation = serializers.SerializerMethodField()
    
    class Meta:
        model = Rack
        fields = [
            'id', 'nom', 'total_postes', 'postes_bas', 'postes_haut',
            'postes', 'postes_occupes', 'postes_libres', 'taux_occupation'
        ]
    
    def get_postes_occupes(self, obj):
        return obj.postes.filter(statut=Poste.Statut.OCCUPE).count()
    
    def get_postes_libres(self, obj):
        return obj.postes.filter(statut=Poste.Statut.LIBRE).count()
    
    def get_taux_occupation(self, obj):
        if obj.total_postes == 0:
            return 0
        return round((obj.postes.filter(statut=Poste.Statut.OCCUPE).count() / obj.total_postes) * 100, 2)


class RackCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour créer/mettre à jour un rack avec gestion des postes"""
    
    class Meta:
        model = Rack
        fields = ['id', 'nom', 'total_postes']
    
    def create(self, validated_data):
        """Crée un rack et génère automatiquement les postes."""
        rack = Rack.objects.create(**validated_data)
        rack.generer_postes()  # Génération automatique des postes
        return rack
    
    def update(self, instance, validated_data):
        """Met à jour un rack et régénère les postes si total_postes change."""
        total_ancien = instance.total_postes
        instance.nom = validated_data.get('nom', instance.nom)
        instance.total_postes = validated_data.get('total_postes', instance.total_postes)
        instance.save()
        
        # Si le nombre de postes a changé, régénérer les postes
        if total_ancien != instance.total_postes:
            instance.generer_postes()
        
        return instance
