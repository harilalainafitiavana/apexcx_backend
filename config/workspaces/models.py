from django.db import models
from .colors import PALETTE_COULEURS


class Projet(models.Model):
    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        TERMINE = "termine", "Terminé"
        SUSPENDU = "suspendu", "Suspendu"
        ARCHIVE = "archive", "Archivé"

    nom = models.CharField(max_length=150)
    couleur = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # Un agent supervise un projet (référence circulaire agents <-> workspaces,
    # gérée normalement par Django via les chaînes "app.Model").
    superviseur = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Nom du superviseur"
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ACTIF)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "projets"
        verbose_name = "Projet"
        verbose_name_plural = "Projets"

    def save(self, *args, **kwargs):
        # Auto-assignation d'une couleur de la palette si aucune n'est définie
        # (nouveau projet créé sans couleur, que ce soit via l'API ou l'admin).
        if not self.couleur:
            nb_projets = Projet.objects.count()
            self.couleur = PALETTE_COULEURS[nb_projets % len(PALETTE_COULEURS)]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Rack(models.Model):
    nom = models.CharField(max_length=100)
    total_postes = models.PositiveIntegerField(default=0)
    postes_bas = models.PositiveIntegerField(default=0)
    postes_haut = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "racks"
        ordering = ["nom"]

    def save(self, *args, **kwargs):
        """À chaque sauvegarde, répartit automatiquement les postes."""
        if self.total_postes:
            # Répartition : moitié en haut, moitié en bas (comme dans le frontend)
            self.postes_haut = (self.total_postes + 1) // 2  # arrondi supérieur
            self.postes_bas = self.total_postes - self.postes_haut
        super().save(*args, **kwargs)

    def generer_postes(self):
        """
        Génère automatiquement les postes pour ce rack.
        Si des postes existent déjà, les supprime et les recrée.
        """
        # Supprimer les postes existants
        self.postes.all().delete()
        
        # Créer les nouveaux postes
        postes_a_creer = []
        for i in range(1, self.total_postes + 1):
            code = f"{self.nom}-P{i}"  # Ex: "R1-P1"
            postes_a_creer.append(
                Poste(
                    code=code,
                    numero=i,
                    rack=self,
                    statut=Poste.Statut.LIBRE
                )
            )
        
        # Créer en bulk pour performance
        Poste.objects.bulk_create(postes_a_creer)
        
        return self.postes.all()
    
    def __str__(self):
        return self.nom


class Poste(models.Model):
    class Statut(models.TextChoices):
        LIBRE = "libre", "Libre"
        OCCUPE = "occupe", "Occupé"
        MAINTENANCE = "maintenance", "Maintenance"
        HORS_SERVICE = "hors_service", "Hors service"

    code = models.CharField(max_length=50, unique=True)
    numero = models.PositiveIntegerField()
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name="postes")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.LIBRE)

    class Meta:
        db_table = "postes"
        ordering = ["rack__nom", "numero"]
        unique_together = ["rack", "numero"] # Un rack ne peut pas avoir deux fois le même numéro

    def __str__(self):
        return self.code
    
    def assigner_agent(self, agent):
        """Assigne un agent à ce poste."""
        from agents.models import Agent  # Import ici pour éviter les imports circulaires
        if self.statut == self.Statut.OCCUPE:
            raise ValueError("Ce poste est déjà occupé")
        
        # Vérifier que l'agent n'a pas déjà un poste
        if agent.poste and agent.poste != self:
            raise ValueError("Cet agent a déjà un poste assigné")
        
        # Assigner le poste à l'agent
        agent.poste = self
        agent.save()
        
        # Mettre à jour le statut du poste
        self.statut = self.Statut.OCCUPE
        self.save()
        
        return self
    
    def liberer(self):
        """Libère le poste (enlève l'agent)."""
        if self.agent:
            agent = self.agent
            agent.poste = None
            agent.save()
        
        self.statut = self.Statut.LIBRE
        self.save()
        return self


class AffectationPoste(models.Model):
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name="affectations")
    agent = models.ForeignKey(
        "agents.Agent", on_delete=models.CASCADE, related_name="affectations_postes"
    )
    date_debut = models.DateTimeField(blank=True, null=True)
    date_fin = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "affectation_postes"

    def __str__(self):
        return f"{self.agent} → {self.poste}"