from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import Role, Utilisateur, Profil, UtilisateurRole


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
    

# --- À AJOUTER dans accounts/serializers.py (garder le reste du fichier existant) ---
class RoleSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_nom_display", read_only=True)

    class Meta:
        model = Role
        fields = ["id", "nom", "label"]


# Partie pour les détails d'un utilisateur avec ses rôles

class ProfilSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour le profil"""
    class Meta:
        model = Profil
        fields = [
            'id', 'nom', 'prenom', 'telephone', 'photo_profil'
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
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
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
    """
    Crée un Utilisateur (email + mot de passe par défaut "123456"),
    son Profil, et lui assigne un rôle optionnel — en une seule requête.
    Utilisé par le formulaire "Ajouter un agent" du plan de salle.
    """
    email = serializers.EmailField(write_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Profil
        fields = [
            'id', 'email', 'role_id', 'nom', 'prenom', 'telephone',
            'date_naissance', 'lieu_naissance', 'cin', 'adresse', 'sexe',
            'situation_matrimoniale', 'conjoint_nom', 'conjoint_telephone',
            'nombre_enfants',
        ]

    def create(self, validated_data):
        email = validated_data.pop('email')
        role = validated_data.pop('role_id', None)

        utilisateur = Utilisateur.objects.create_user(email=email, password='123456')
        if role:
            UtilisateurRole.objects.create(utilisateur=utilisateur, role=role)

        profil = Profil.objects.create(utilisateur=utilisateur, **validated_data)
        return profil


