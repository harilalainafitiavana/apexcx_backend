# agents/serializers.py - VERSION CORRIGÉE ET COMPLÈTE
from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import Profil
from .models import (
    Agent, Diplome, FormationSuivie, ContactUrgence, RibBancaire
)
from workspaces.models import Projet, Poste

Utilisateur = get_user_model()


class DiplomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diplome
        fields = ['id', 'intitule']


class FormationSuivieSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormationSuivie
        fields = ['id', 'intitule']


class ContactUrgenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUrgence
        fields = ['id', 'nom', 'lien_parente', 'telephone']


class RibBancaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = RibBancaire
        fields = ['id', 'type_banque', 'code_banque', 'code_agence', 
                 'numero_compte', 'cle_rib']


class ProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profil
        fields = [
            'id', 'nom', 'prenom', 'telephone', 'photo_profil',
            'date_naissance', 'lieu_naissance', 'cin', 'adresse',
            'sexe', 'situation_matrimoniale', 'conjoint_nom',
            'conjoint_telephone', 'nombre_enfants'
        ]


class AgentSerializer(serializers.ModelSerializer):
    # Relations imbriquées (pour la lecture)
    profil = ProfilSerializer(read_only=True)
    diplomes = DiplomeSerializer(many=True, read_only=True)
    formations_suivies = FormationSuivieSerializer(many=True, read_only=True)
    contact_urgence = ContactUrgenceSerializer(read_only=True)
    rib_bancaire = RibBancaireSerializer(read_only=True)
    
    # Champs pour l'écriture (on reçoit des IDs)
    projet_id = serializers.PrimaryKeyRelatedField(
        queryset=Projet.objects.all(),
        source='projet',
        write_only=True,
        required=False,
        allow_null=True
    )
    poste_id = serializers.PrimaryKeyRelatedField(
        queryset=Poste.objects.all(),
        source='poste',
        write_only=True,
        required=False,
        allow_null=True
    )
    profil_id = serializers.PrimaryKeyRelatedField(
        queryset=Profil.objects.all(),
        source='profil',
        write_only=True,
        required=True
    )
    
    # Champs pour les diplômes et formations (écriture)
    diplomes_list = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="Liste des intitulés de diplômes"
    )
    formations_list = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="Liste des intitulés de formations"
    )
    
    # Contact d'urgence (écriture)
    contact_urgence_data = serializers.DictField(
        write_only=True,
        required=False,
        help_text="Données du contact d'urgence"
    )
    
    # RIB (écriture)
    rib_data = serializers.DictField(
        write_only=True,
        required=False,
        help_text="Données du RIB"
    )

    class Meta:
        model = Agent
        fields = [
            'id', 'matricule', 'fonction', 'date_entree',
            'statut', 'statut_presence', 'carte_esia', 'cnaps',
            'type_contrat', 'superieur_hierarchique',
            'profil', 'projet', 'poste',
            'diplomes', 'formations_suivies',
            'contact_urgence', 'rib_bancaire',
            # Champs en écriture
            'profil_id', 'projet_id', 'poste_id',
            'diplomes_list', 'formations_list',
            'contact_urgence_data', 'rib_data',
        ]

    def create(self, validated_data):
        """Crée un Agent avec toutes ses relations."""
        # Extraire les données imbriquées
        diplomes_list = validated_data.pop('diplomes_list', [])
        formations_list = validated_data.pop('formations_list', [])
        contact_data = validated_data.pop('contact_urgence_data', None)
        rib_data = validated_data.pop('rib_data', None)
        profil = validated_data.pop('profil')
        
        # Créer l'agent
        agent = Agent.objects.create(profil=profil, **validated_data)
        
        # Gestion du mot de passe par défaut
        if hasattr(profil, 'utilisateur') and profil.utilisateur:
            utilisateur = profil.utilisateur
            utilisateur.set_password('123456')
            utilisateur.save()
        
        # Créer les diplômes
        for intitule in diplomes_list:
            Diplome.objects.create(agent=agent, intitule=intitule)
        
        # Créer les formations
        for intitule in formations_list:
            FormationSuivie.objects.create(agent=agent, intitule=intitule)
        
        # Créer le contact d'urgence
        if contact_data:
            ContactUrgence.objects.create(agent=agent, **contact_data)
        
        # Créer le RIB
        if rib_data:
            RibBancaire.objects.create(agent=agent, **rib_data)
        
        return agent

    def update(self, instance, validated_data):
        """Met à jour un Agent et ses relations."""
        # Extraire les données imbriquées
        diplomes_list = validated_data.pop('diplomes_list', None)
        formations_list = validated_data.pop('formations_list', None)
        contact_data = validated_data.pop('contact_urgence_data', None)
        rib_data = validated_data.pop('rib_data', None)
        profil = validated_data.pop('profil', None)
        
        # Mettre à jour le profil si fourni
        if profil:
            instance.profil = profil
        
        # Mettre à jour les champs de l'agent
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mettre à jour les diplômes
        if diplomes_list is not None:
            instance.diplomes.all().delete()
            for intitule in diplomes_list:
                Diplome.objects.create(agent=instance, intitule=intitule)
        
        # Mettre à jour les formations
        if formations_list is not None:
            instance.formations_suivies.all().delete()
            for intitule in formations_list:
                FormationSuivie.objects.create(agent=instance, intitule=intitule)
        
        # Mettre à jour le contact d'urgence
        if contact_data is not None:
            if hasattr(instance, 'contact_urgence'):
                contact = instance.contact_urgence
                for attr, value in contact_data.items():
                    setattr(contact, attr, value)
                contact.save()
            else:
                ContactUrgence.objects.create(agent=instance, **contact_data)
        
        # Mettre à jour le RIB
        if rib_data is not None:
            if hasattr(instance, 'rib_bancaire'):
                rib = instance.rib_bancaire
                for attr, value in rib_data.items():
                    setattr(rib, attr, value)
                rib.save()
            else:
                RibBancaire.objects.create(agent=instance, **rib_data)
        
        return instance


class AgentListSerializer(serializers.ModelSerializer):
    """Utilisé pour la liste des agents (moins de données)"""
    nom_complet = serializers.SerializerMethodField()
    projet_nom = serializers.CharField(source='projet.nom', read_only=True, default=None)
    poste_code = serializers.CharField(source='poste.code', read_only=True, default=None)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'matricule', 'nom_complet', 'fonction',
            'statut', 'statut_presence', 'carte_esia',
            'projet', 'projet_nom', 'poste_code'
        ]
    
    def get_nom_complet(self, obj):
        return f"{obj.profil.prenom} {obj.profil.nom}"