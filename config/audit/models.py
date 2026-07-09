"""
App: audit
Historique de tout ce qui se passe dans le système.
"""
from django.db import models


class JournalActivite(models.Model):
    utilisateur = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.SET_NULL,
        related_name="journal_activites",
        blank=True,
        null=True,
    )
    action = models.CharField(max_length=100)
    entite = models.CharField(max_length=100, help_text="Nom du modèle/table concerné")
    entite_id = models.PositiveIntegerField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "journal_activites"
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journal des activités"
        indexes = [
            models.Index(fields=["entite", "entite_id"]),
            models.Index(fields=["date_action"]),
        ]
        ordering = ["-date_action"]

    def __str__(self):
        return f"{self.utilisateur} - {self.action} - {self.entite}"