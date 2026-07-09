"""
App: agents
Données métiers de l'employé : fiche agent, diplômes, formations, contacts
d'urgence, RIB, congés.
"""
from django.db import models


class Agent(models.Model):
    class Statut(models.TextChoices):
        """Statut CONTRACTUEL / administratif de l'agent."""
        NOUVEAU = "nouveau", "Nouveau"
        ACTIF = "actif", "Actif"
        INACTIF = "inactif", "Inactif"
        SUSPENDU = "suspendu", "Suspendu"
        SORTI = "sorti", "Sorti"

    class StatutPresence(models.TextChoices):
        """Statut de PRÉSENCE du jour (distinct du statut contractuel ci-dessus)."""
        PRESENT = "present", "Présent"
        ABSCENT = "abscent", "Abscent"
        CONGES = "conges", "Congé"
        TT = "tt", "Télétravail"
        NOUVEAU = "nouveau", "Nouveau"
        EN_ATTENTE = "en-attente", "En attente"

    class TypeContrat(models.TextChoices):
        CDI = "CDI", "CDI"
        CDD = "CDD", "CDD"
        STAGE = "stage", "Stage"
        FREELANCE = "freelance", "Freelance"

    class CarteEsia(models.TextChoices):
        OUI = "oui", "Oui"
        EN_COURS = "en-cours", "En cours"
        NON = "non", "Non"

    profil = models.OneToOneField(
        "accounts.Profil", on_delete=models.CASCADE, related_name="agent"
    )
    matricule = models.CharField(max_length=50, unique=True)
    fonction = models.CharField(max_length=150, blank=True, null=True)
    date_entree = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.NOUVEAU)
    statut_presence = models.CharField(
        max_length=20, choices=StatutPresence.choices, default=StatutPresence.NOUVEAU
    )
    carte_esia = models.CharField(max_length=20, choices=CarteEsia.choices, default=CarteEsia.NON)
    cnaps = models.CharField(max_length=50, blank=True, null=True)

    # Contrat & hiérarchie
    type_contrat = models.CharField(
        max_length=20, choices=TypeContrat.choices, default=TypeContrat.CDI
    )
    superieur_hierarchique = models.CharField(max_length=100, default="team-leader")

    projet = models.ForeignKey(
        "workspaces.Projet",
        on_delete=models.SET_NULL,
        related_name="agents",
        blank=True,
        null=True,
    )
    poste = models.OneToOneField(
        "workspaces.Poste",
        on_delete=models.SET_NULL,
        related_name="agent",
        blank=True,
        null=True,
    )

    class SuperieurHierarchique(models.TextChoices):
        TEAM_LEADER = "team-leader", "Team Leader"
        DIRECTION_GENERALE = "direction-generale", "Direction Générale"

    superieur_hierarchique = models.CharField(
        max_length=20, 
        choices=SuperieurHierarchique.choices,
        default=SuperieurHierarchique.TEAM_LEADER
    )

    class Meta:
        db_table = "agents"
        verbose_name = "Agent"
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"{self.matricule} - {self.profil}"

class Diplome(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="diplomes")
    intitule = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "diplomes"

    def __str__(self):
        return self.intitule


class FormationSuivie(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="formations_suivies")
    intitule = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "formations_suivies"

    def __str__(self):
        return self.intitule


class ContactUrgence(models.Model):
    agent = models.OneToOneField(
        Agent, on_delete=models.CASCADE, related_name="contact_urgence"
    )
    nom = models.CharField(max_length=150, blank=True, null=True)
    lien_parente = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contacts_urgence"

    def __str__(self):
        return f"Contact urgence de {self.agent.matricule}"


class RibBancaire(models.Model):
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name="rib_bancaire")
    type_banque = models.CharField(max_length=100)
    code_banque = models.CharField(max_length=20)
    code_agence = models.CharField(max_length=20)
    numero_compte = models.CharField(max_length=50)
    cle_rib = models.CharField(max_length=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rib_bancaires"

    def __str__(self):
        return f"RIB de {self.agent.matricule}"


class Conge(models.Model):
    class TypeConge(models.TextChoices):
        ANNUEL = "annuel", "Annuel"
        MALADIE = "maladie", "Maladie"
        EXCEPTIONNEL = "exceptionnel", "Exceptionnel"
        FORMATION = "formation", "Formation"
        MATERNITE = "maternite", "Maternité"
        PATERNITE = "paternite", "Paternité"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        APPROUVE = "approuve", "Approuvé"
        REFUSE = "refuse", "Refusé"
        ANNULE = "annule", "Annulé"

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="conges")
    type_conge = models.CharField(max_length=20, choices=TypeConge.choices)
    date_debut = models.DateField()
    date_fin = models.DateField()
    duree_ouverte = models.FloatField(help_text="Nombre de jours ouvrés")
    duree_reelle = models.PositiveIntegerField(
        blank=True, null=True, help_text="Nombre de jours calendaires"
    )
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    motif = models.TextField(blank=True, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(blank=True, null=True)
    approuve_par = models.ForeignKey(
        "accounts.Utilisateur",
        on_delete=models.SET_NULL,
        related_name="conges_approuves",
        blank=True,
        null=True,
    )
    commentaire_validation = models.TextField(blank=True, null=True)
    annee_reference = models.PositiveIntegerField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conges"
        indexes = [
            models.Index(fields=["agent", "annee_reference"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["date_debut", "date_fin"]),
        ]

    def __str__(self):
        return f"Congé {self.type_conge} - {self.agent.matricule}"


class SoldeConge(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="soldes_conges")
    annee = models.PositiveIntegerField()
    total_jours = models.FloatField(default=30)
    jours_pris = models.FloatField(default=0)
    jours_restants = models.FloatField(default=30)
    jours_en_attente = models.FloatField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "soldes_conges"
        constraints = [
            models.UniqueConstraint(fields=["agent", "annee"], name="uniq_solde_agent_annee")
        ]

    def __str__(self):
        return f"Solde {self.annee} - {self.agent.matricule}"


class OnboardingTache(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="onboarding_taches")
    type = models.CharField(max_length=100)
    tache = models.CharField(max_length=255)
    statut = models.CharField(max_length=50, default="a_faire")

    class Meta:
        db_table = "onboarding_taches"

    def __str__(self):
        return self.tache


class OffboardingTache(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="offboarding_taches")
    type = models.CharField(max_length=100)
    tache = models.CharField(max_length=255)
    statut = models.CharField(max_length=50, default="a_faire")

    class Meta:
        db_table = "offboarding_taches"

    def __str__(self):
        return self.tache