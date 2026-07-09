from django.contrib import admin

from .models import JournalActivite


@admin.register(JournalActivite)
class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "action", "entite", "entite_id", "date_action"]
    list_filter = ["entite", "action"]
    search_fields = ["utilisateur__email", "action", "entite"]
    autocomplete_fields = ["utilisateur"]
    date_hierarchy = "date_action"

    # Le journal est généré automatiquement par le code applicatif :
    # pas de création/modification manuelle depuis l'admin.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False