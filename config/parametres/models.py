"""
App: config
Paramètres globaux du système. Aucune table n'était prévue pour ça dans le
schéma d'origine : voici une structure clé/valeur simple, typée, facile à
étendre depuis l'admin Django.
"""
from django.db import models


class Parametre(models.Model):
    class TypeValeur(models.TextChoices):
        TEXTE = "texte", "Texte"
        NOMBRE = "nombre", "Nombre"
        BOOLEEN = "booleen", "Booléen"
        JSON = "json", "JSON"

    cle = models.CharField(max_length=100, unique=True)
    valeur = models.TextField(blank=True, null=True)
    type_valeur = models.CharField(
        max_length=20, choices=TypeValeur.choices, default=TypeValeur.TEXTE
    )
    description = models.CharField(max_length=255, blank=True, null=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parametres"
        verbose_name = "Paramètre"
        verbose_name_plural = "Paramètres"

    def __str__(self):
        return self.cle