from django.contrib import admin

from .models import Equipement, InterventionIT


@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    list_display = ["type", "marque", "modele", "numero_serie", "statut", "poste", "projet"]
    list_filter = ["statut", "type"]
    search_fields = ["numero_serie", "marque", "modele"]
    autocomplete_fields = ["poste", "projet"]


@admin.register(InterventionIT)
class InterventionITAdmin(admin.ModelAdmin):
    list_display = ["titre", "equipement", "poste", "priorite", "statut", "date_creation"]
    list_filter = ["priorite", "statut"]
    search_fields = ["titre", "description"]
    autocomplete_fields = ["equipement", "poste"]
    date_hierarchy = "date_creation"