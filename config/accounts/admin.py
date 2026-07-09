from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UtilisateurChangeForm, UtilisateurCreationForm
from .models import Notification, Profil, Role, Utilisateur, UtilisateurRole


class ProfilInline(admin.StackedInline):
    model = Profil
    can_delete = False
    extra = 0


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    """
    UserAdmin standard de Django adapté : pas de username, login = email.
    """
    add_form = UtilisateurCreationForm
    form = UtilisateurChangeForm
    model = Utilisateur
    ordering = ["email"]
    list_display = ["email", "is_active", "is_staff", "last_login", "date_creation"]
    list_filter = ["is_active", "is_staff", "is_superuser"]
    search_fields = ["email"]
    readonly_fields = ["date_creation", "last_login"]
    inlines = [ProfilInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Dates", {"fields": ("last_login", "date_creation")}),
    )
    # Formulaire utilisé lors de la création d'un utilisateur depuis l'admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ["prenom", "nom", "telephone", "cin", "utilisateur"]
    search_fields = ["nom", "prenom", "cin", "utilisateur__email"]
    autocomplete_fields = ["utilisateur"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["nom"]
    search_fields = ["nom"]


@admin.register(UtilisateurRole)
class UtilisateurRoleAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "role"]
    autocomplete_fields = ["utilisateur", "role"]
    search_fields = ["utilisateur__email", "role__nom"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "type", "lu", "date_creation"]
    list_filter = ["type", "lu"]
    search_fields = ["utilisateur__email", "message"]
    autocomplete_fields = ["utilisateur"]
    date_hierarchy = "date_creation"