"""
App: attendance
Tout ce qui touche à la présence / temps de travail.
"""
from django.db import models


class Presence(models.Model):
    class Statut(models.TextChoices):
        PRESENT = "present", "Présent"
        ABSENT = "absent", "Absent"
        RETARD = "retard", "Retard"
        CONGE = "conge", "Congé"

    agent = models.ForeignKey("agents.Agent", on_delete=models.CASCADE, related_name="presences")
    date = models.DateField()
    heure_arrivee = models.DateTimeField(blank=True, null=True)
    heure_depart = models.DateTimeField(blank=True, null=True)
    nombre_passages = models.PositiveIntegerField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, blank=True, null=True)
    source_calcul = models.CharField(max_length=100, blank=True, null=True)
    donnees_brutes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "presences"
        indexes = [models.Index(fields=["agent", "date"])]

    def __str__(self):
        return f"{self.agent} - {self.date}"


class Pointage(models.Model):
    class TypeAction(models.TextChoices):
        ENTREE = "entree", "Entrée"
        SORTIE = "sortie", "Sortie"

    class Source(models.TextChoices):
        BADGE = "badge", "Badge"
        MANUEL = "manuel", "Manuel"
        BIOMETRIE = "biometrie", "Biométrie"

    agent = models.ForeignKey("agents.Agent", on_delete=models.CASCADE, related_name="pointages")
    type_action = models.CharField(max_length=20, choices=TypeAction.choices)
    date_heure = models.DateTimeField()
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.BADGE)
    periode = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pointages"
        indexes = [models.Index(fields=["agent", "periode"])]

    def __str__(self):
        return f"{self.agent} - {self.type_action} - {self.date_heure}"