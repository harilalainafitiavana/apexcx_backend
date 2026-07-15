"""
App: accounts
Cœur de l'authentification — utilisateur custom (email + mdp, PAS de username),
profils, rôles, notifications.
"""
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models



class UtilisateurManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=False, blank=False)

    # `is_active` est le nom EXIGÉ par Django (auth backend, admin, permissions).
    # On garde la colonne DB nommée "actif" comme dans ton schéma via db_column.
    is_active = models.BooleanField(default=True, db_column="actif")
    is_staff = models.BooleanField(default=False)

    # On réécrit last_login pour qu'il porte le nom de colonne "derniere_connexion"
    # (mis à jour automatiquement par Django à chaque connexion réussie).
    last_login = models.DateTimeField(
        "derniere connexion", blank=True, null=True, db_column="derniere_connexion"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    objects = UtilisateurManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password suffisent (createsuperuser ne demande rien d'autre)

    class Meta:
        db_table = "utilisateurs"
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return self.email

    @property
    def nom_complet(self):
        if hasattr(self, "profil"):
            return f"{self.profil.prenom} {self.profil.nom}"
        return self.email


# NOTE — "Se souvenir de moi" (remember me) :
# Ce n'est PAS un champ de modèle, ça se gère au niveau de la vue de login /
# de la session :
#   if not request.POST.get("remember_me"):
#       request.session.set_expiry(0)  # expire à la fermeture du navigateur
#   else:
#       request.session.set_expiry(settings.SESSION_COOKIE_AGE)  # ex: 30 jours


# ------------------------------------------------------------------
# Profil (table: profils) — données personnelles, 1-1 avec Utilisateur
# ------------------------------------------------------------------
class Profil(models.Model):
    class Sexe(models.TextChoices):
        HOMME = "M", "Masculin"
        FEMME = "F", "Féminin"

    class SituationMatrimoniale(models.TextChoices):
        CELIBATAIRE = "celibataire", "Célibataire"
        MARIE = "marie", "Marié(e)"
        DIVORCE = "divorce", "Divorcé(e)"
        VEUF = "veuf", "Veuf/Veuve"

    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE, related_name="profil"
    )
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    telephone = models.CharField(max_length=30, blank=True, null=True)
    photo_profil = models.ImageField(upload_to="profils/%Y/%m/", blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    lieu_naissance = models.CharField(max_length=150, blank=True, null=True)
    cin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    sexe = models.CharField(max_length=1, choices=Sexe.choices, blank=True, null=True)

    # Situation familiale
    situation_matrimoniale = models.CharField(
        max_length=20,
        choices=SituationMatrimoniale.choices,
        default=SituationMatrimoniale.CELIBATAIRE,
    )
    conjoint_nom = models.CharField(max_length=150, blank=True, null=True)
    conjoint_telephone = models.CharField(max_length=30, blank=True, null=True)
    nombre_enfants = models.PositiveIntegerField(default=0)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profils"
        verbose_name = "Profil"
        verbose_name_plural = "Profils"

    def __str__(self):
        return f"{self.prenom} {self.nom}"


# ------------------------------------------------------------------
# Rôles (table: roles) — remplis par défaut via data migration
# ------------------------------------------------------------------
class Role(models.Model):
    class Nom(models.TextChoices):
        MANAGER = "manager", "Manager"
        TECHNICIEN = "technicien", "Technicien"
        ADMIN = "admin", "Admin"
        AGENT = "agent", "Agent"
        RH = "rh", "RH"
        DIRECTION = "direction", "Direction"
        DEVELOPPEUR = "developpeur", "Développeur"

    nom = models.CharField(max_length=50, unique=True, choices=Nom.choices)

    class Meta:
        db_table = "roles"
        verbose_name = "Rôle"
        verbose_name_plural = "Rôles"

    def __str__(self):
        return self.get_nom_display()


class UtilisateurRole(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="utilisateur_roles"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="utilisateur_roles")

    class Meta:
        db_table = "utilisateur_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "role"], name="uniq_utilisateur_role"
            )
        ]

    def __str__(self):
        return f"{self.utilisateur.email} → {self.role.nom}"


# ------------------------------------------------------------------
# Notifications (table: notifications)
# Rattachées ici car directement liées à l'expérience utilisateur/compte.
# ------------------------------------------------------------------
class Notification(models.Model):
    class Type(models.TextChoices):
        INFO = "info", "Information"
        ALERTE = "alerte", "Alerte"
        TACHE = "tache", "Tâche"
        SYSTEME = "systeme", "Système"

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO)
    lu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"[{self.type}] {self.utilisateur.email}"