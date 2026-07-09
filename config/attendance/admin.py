from django.contrib import admin

from .models import Pointage, Presence


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ["agent", "date", "heure_arrivee", "heure_depart", "statut", "nombre_passages"]
    list_filter = ["statut"]
    search_fields = ["agent__matricule"]
    autocomplete_fields = ["agent"]
    date_hierarchy = "date"


@admin.register(Pointage)
class PointageAdmin(admin.ModelAdmin):
    list_display = ["agent", "type_action", "date_heure", "source", "periode"]
    list_filter = ["type_action", "source"]
    search_fields = ["agent__matricule"]
    autocomplete_fields = ["agent"]
    date_hierarchy = "date_heure"