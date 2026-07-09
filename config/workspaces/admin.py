from django.contrib import admin

from .models import AffectationPoste, Poste, Projet, Rack


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ["nom", "statut", "superviseur", "date_creation"]
    list_filter = ["statut"]
    search_fields = ["nom", "superviseur"]


class PosteInline(admin.TabularInline):
    model = Poste
    extra = 0


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ["nom", "total_postes", "postes_bas", "postes_haut"]
    search_fields = ["nom"]
    inlines = [PosteInline]


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ["code", "numero", "rack", "statut"]
    list_filter = ["statut", "rack"]
    search_fields = ["code"]
    autocomplete_fields = ["rack"]


@admin.register(AffectationPoste)
class AffectationPosteAdmin(admin.ModelAdmin):
    list_display = ["poste", "agent", "date_debut", "date_fin"]
    search_fields = ["poste__code", "agent__matricule"]
    autocomplete_fields = ["poste", "agent"]