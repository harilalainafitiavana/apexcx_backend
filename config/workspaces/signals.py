# workspaces/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from workspaces.models import Rack, Poste


@receiver(post_save, sender=Rack)
def rack_post_save(sender, instance, created, **kwargs):
    """
    Quand un rack est créé, générer automatiquement ses postes.
    """
    if created:
        instance.generer_postes()


@receiver(post_delete, sender=Rack)
def rack_post_delete(sender, instance, **kwargs):
    """
    Quand un rack est supprimé, ses postes sont automatiquement supprimés
    grâce à on_delete=models.CASCADE
    """
    # Un message de log pourrait être ajouté ici
    pass