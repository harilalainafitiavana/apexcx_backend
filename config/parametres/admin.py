from django.contrib import admin

from .models import Parametre


@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ["cle", "valeur", "type_valeur", "date_modification"]
    list_filter = ["type_valeur"]
    search_fields = ["cle", "description"]