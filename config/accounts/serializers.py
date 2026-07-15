from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import Role, Utilisateur, Profil, UtilisateurRole

import base64
import uuid
from django.core.files.base import ContentFile


class Base64ImageField(serializers.ImageField):
    """
    Accepte soit un fichier classique (upload multipart), soit une chaîne
    base64 du type "data:image/png;base64,...." — c'est ce que génère
    FileReader.readAsDataURL() côté frontend (PhotoUpload).
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            header, imgstr = data.split(';base64,')
            ext = header.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')
        return super().to_internal_value(data)


class UtilisateurSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = ["id", "email", "first_name", "last_name", "role", "avatar"]

    def get_first_name(self, obj):
        return obj.profil.prenom if hasattr(obj, "profil") else ""

    def get_last_name(self, obj):
        return obj.profil.nom if hasattr(obj, "profil") else ""

    def get_role(self, obj):
        rel = obj.utilisateur_roles.select_related("role").first()
        return rel.role.get_nom_display() if rel else None

    def get_avatar(self, obj):
        """
        Retourne l'URL absolue de la photo de profil.
        """
        if not hasattr(obj, "profil") or not obj.profil.photo_profil:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.profil.photo_profil.url)

        return obj.profil.photo_profil.url


class LoginSerializer(TokenObtainPairSerializer):
    # Surcharge du message par défaut de SimpleJWT ("No active account found
    # with the given credentials") pour l'afficher en français. On garde
    # volontairement un message générique (sans préciser email ou mot de
    # passe) : c'est la bonne pratique de sécurité de SimpleJWT.
    default_error_messages = {
        "no_active_account": "Email ou mot de passe incorrect."
    }

    def validate(self, attrs):
        data = super().validate(attrs)  # vérifie email/mdp, génère access+refresh
        data["user"] = UtilisateurSerializer(self.user, context=self.context).data
        return data
    


class RoleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_nom_display", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "nom", "label"]


# Partie pour les détails d'un utilisateur avec ses rôles

class ProfilSimpleSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='utilisateur.email', read_only=True)

    class Meta:
        model = Profil
        fields = [
            'id', 'email', 'nom', 'prenom', 'telephone', 'photo_profil',
            'date_naissance', 'lieu_naissance', 'cin', 'adresse', 'sexe',
            'situation_matrimoniale', 'conjoint_nom', 'conjoint_telephone',
            'nombre_enfants',
        ]


class UtilisateurDetailSerializer(serializers.ModelSerializer):
    """Serializer pour les détails d'un utilisateur avec ses rôles"""
    profil = ProfilSimpleSerializer(read_only=True)
    roles = serializers.SerializerMethodField()
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'nom_complet', 'profil',
            'roles', 'is_active', 'is_staff',
            'date_creation', 'last_login'
        ]
    
    def get_roles(self, obj):
        """Récupère tous les rôles de l'utilisateur"""
        roles = obj.utilisateur_roles.all().select_related('role')
        return [{'id': r.role.id, 'nom': r.role.nom, 'label': r.role.get_nom_display()} for r in roles]


class UtilisateurListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des utilisateurs"""
    nom_complet = serializers.CharField(read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'email', 'nom_complet', 'is_active', 'roles'
        ]
    
    def get_roles(self, obj):
        """Récupère les noms des rôles pour l'affichage"""
        return [r.role.nom for r in obj.utilisateur_roles.all().select_related('role')]



class ProfilCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), write_only=True, required=False, allow_null=True
    )
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True, write_only=True, required=False
    )
    photo_profil = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Profil
        fields = [
            'id', 'email', 'role_id', 'role_ids', 'nom', 'prenom', 'telephone', 'photo_profil',
            'date_naissance', 'lieu_naissance', 'cin', 'adresse', 'sexe',
            'situation_matrimoniale', 'conjoint_nom', 'conjoint_telephone',
            'nombre_enfants',
        ]

    def create(self, validated_data):
        email = validated_data.pop('email')
        role = validated_data.pop('role_id', None)
        roles_list = list(validated_data.pop('role_ids', []))

        utilisateur = Utilisateur.objects.create_user(email=email, password='123456')

        if role and role not in roles_list:
            roles_list.append(role)
        for r in roles_list:
            UtilisateurRole.objects.create(utilisateur=utilisateur, role=r)

        profil = Profil.objects.create(utilisateur=utilisateur, **validated_data)
        return profil


class ProfilUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='utilisateur.email', required=False)
    actif = serializers.BooleanField(source='utilisateur.is_active', required=False)
    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), many=True, write_only=True, required=False
    )
    photo_profil = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Profil
        fields = [
            'id', 'email', 'actif', 'role_ids', 'nom', 'prenom', 'telephone', 'photo_profil',
            'date_naissance', 'lieu_naissance', 'cin', 'adresse', 'sexe',
            'situation_matrimoniale', 'conjoint_nom', 'conjoint_telephone',
            'nombre_enfants',
        ]

    def update(self, instance, validated_data):
        utilisateur_data = validated_data.pop('utilisateur', None)
        role_ids = validated_data.pop('role_ids', None)

        if utilisateur_data:
            if 'email' in utilisateur_data:
                instance.utilisateur.email = utilisateur_data['email']
            if 'is_active' in utilisateur_data:
                instance.utilisateur.is_active = utilisateur_data['is_active']
            instance.utilisateur.save()

        if role_ids is not None:
            UtilisateurRole.objects.filter(utilisateur=instance.utilisateur).delete()
            for role in role_ids:
                UtilisateurRole.objects.create(utilisateur=instance.utilisateur, role=role)

        return super().update(instance, validated_data)