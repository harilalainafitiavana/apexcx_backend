from django.contrib import admin

from .models import (
    Agent,
    Conge,
    ContactUrgence,
    Diplome,
    FormationSuivie,
    OffboardingTache,
    OnboardingTache,
    RibBancaire,
    SoldeConge,
)


class DiplomeInline(admin.TabularInline):
    model = Diplome
    extra = 0


class FormationSuivieInline(admin.TabularInline):
    model = FormationSuivie
    extra = 0


class ContactUrgenceInline(admin.StackedInline):
    model = ContactUrgence
    can_delete = False
    extra = 0


class RibBancaireInline(admin.StackedInline):
    model = RibBancaire
    can_delete = False
    extra = 0


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = [
        "matricule", "profil", "fonction", "statut", "type_contrat", "projet", "poste",
    ]
    list_filter = ["statut", "type_contrat", "carte_esia"]
    search_fields = ["matricule", "profil__nom", "profil__prenom", "cnaps"]
    autocomplete_fields = ["profil", "projet", "poste"]
    inlines = [DiplomeInline, FormationSuivieInline, ContactUrgenceInline, RibBancaireInline]


@admin.register(Conge)
class CongeAdmin(admin.ModelAdmin):
    list_display = ["agent", "type_conge", "date_debut", "date_fin", "statut", "duree_ouverte"]
    list_filter = ["type_conge", "statut"]
    search_fields = ["agent__matricule", "agent__profil__nom"]
    autocomplete_fields = ["agent", "approuve_par"]
    date_hierarchy = "date_debut"


@admin.register(SoldeConge)
class SoldeCongeAdmin(admin.ModelAdmin):
    list_display = ["agent", "annee", "total_jours", "jours_pris", "jours_restants", "jours_en_attente"]
    list_filter = ["annee"]
    search_fields = ["agent__matricule"]
    autocomplete_fields = ["agent"]


@admin.register(OnboardingTache)
class OnboardingTacheAdmin(admin.ModelAdmin):
    list_display = ["agent", "type", "tache", "statut"]
    list_filter = ["statut", "type"]
    search_fields = ["agent__matricule", "tache"]
    autocomplete_fields = ["agent"]


@admin.register(OffboardingTache)
class OffboardingTacheAdmin(admin.ModelAdmin):
    list_display = ["agent", "type", "tache", "statut"]
    list_filter = ["statut", "type"]
    search_fields = ["agent__matricule", "tache"]
    autocomplete_fields = ["agent"]