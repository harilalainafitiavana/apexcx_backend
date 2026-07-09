"""
App: it
Partie technique informatique : équipements et interventions.
"""
from django.db import models


class Equipement(models.Model):
    class Statut(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        AFFECTE = "affecte", "Affecté"
        EN_PANNE = "en_panne", "En panne"
        EN_MAINTENANCE = "en_maintenance", "En maintenance"
        HORS_SERVICE = "hors_service", "Hors service"

    type = models.CharField(max_length=100)
    marque = models.CharField(max_length=100, blank=True, null=True)
    modele = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, unique=True, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.DISPONIBLE)
    poste = models.ForeignKey(
        "workspaces.Poste",
        on_delete=models.SET_NULL,
        related_name="equipements",
        blank=True,
        null=True,
    )
    projet = models.ForeignKey(
        "workspaces.Projet",
        on_delete=models.SET_NULL,
        related_name="equipements",
        blank=True,
        null=True,
    )
    emplacement = models.CharField(max_length=150, blank=True, null=True)
    date_acquisition = models.DateField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "equipements"
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"

    def __str__(self):
        return f"{self.type} - {self.numero_serie or self.id}"


class InterventionIT(models.Model):
    class Priorite(models.TextChoices):
        BASSE = "basse", "Basse"
        MOYENNE = "moyenne", "Moyenne"
        HAUTE = "haute", "Haute"
        CRITIQUE = "critique", "Critique"

    class Statut(models.TextChoices):
        NOUVEAU = "nouveau", "Nouveau"
        EN_COURS = "en_cours", "En cours"
        RESOLU = "resolu", "Résolu"
        FERME = "ferme", "Fermé"

    equipement = models.ForeignKey(
        Equipement, on_delete=models.SET_NULL, related_name="interventions", blank=True, null=True
    )
    poste = models.ForeignKey(
        "workspaces.Poste",
        on_delete=models.SET_NULL,
        related_name="interventions",
        blank=True,
        null=True,
    )
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priorite = models.CharField(max_length=20, choices=Priorite.choices, default=Priorite.MOYENNE)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.NOUVEAU)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "interventions_it"
        verbose_name = "Intervention IT"
        verbose_name_plural = "Interventions IT"

    def __str__(self):
        return self.titre