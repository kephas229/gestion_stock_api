"""
Modèle pour la gestion de l'historique des actions
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Historique(models.Model):
    """
    Modèle pour enregistrer l'historique de toutes les actions importantes
    """
    TYPE_ACTION_CHOICES = [
        # Produits
        ('PRODUIT_CREE', 'Produit créé'),
        ('PRODUIT_MODIFIE', 'Produit modifié'),
        ('PRODUIT_SUPPRIME', 'Produit supprimé'),
        
        # Magasins
        ('MAGASIN_CREE', 'Magasin créé'),
        ('MAGASIN_MODIFIE', 'Magasin modifié'),
        ('MAGASIN_SUPPRIME', 'Magasin supprimé'),
        
        # Stock
        ('STOCK_REAPPROVISIONNE', 'Stock réapprovisionné'),
        ('STOCK_TRANSFERE', 'Stock transféré'),
        ('STOCK_AJUSTE', 'Stock ajusté'),
        
        # Ventes
        ('VENTE_EFFECTUEE', 'Vente effectuée'),
        ('VENTE_ANNULEE', 'Vente annulée'),
        
        # Utilisateurs
        ('UTILISATEUR_CREE', 'Utilisateur créé'),
        ('UTILISATEUR_MODIFIE', 'Utilisateur modifié'),
        ('UTILISATEUR_SUPPRIME', 'Utilisateur supprimé'),
        
        # Catégories
        ('CATEGORIE_CREEE', 'Catégorie créée'),
        ('CATEGORIE_MODIFIEE', 'Catégorie modifiée'),
        ('CATEGORIE_SUPPRIMEE', 'Catégorie supprimée'),
    ]
    
    # Type d'action
    type_action = models.CharField(
        _('type d\'action'),
        max_length=30,
        choices=TYPE_ACTION_CHOICES,
        db_index=True
    )
    
    # Utilisateur qui a effectué l'action
    utilisateur = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historique_actions',
        verbose_name=_('utilisateur')
    )
    
    # Magasin concerné (si applicable)
    magasin = models.ForeignKey(
        'magasins.Magasin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historique',
        verbose_name=_('magasin')
    )
    
    # Objet concerné par l'action (relation générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    objet_concerne = GenericForeignKey('content_type', 'object_id')
    
    # Description détaillée de l'action
    description = models.TextField(_('description'))
    
    # Données avant/après pour les modifications (JSON)
    donnees_avant = models.JSONField(
        _('données avant'),
        null=True,
        blank=True,
        help_text=_('État des données avant l\'action')
    )
    donnees_apres = models.JSONField(
        _('données après'),
        null=True,
        blank=True,
        help_text=_('État des données après l\'action')
    )
    
    # Métadonnées supplémentaires
    metadata = models.JSONField(
        _('métadonnées'),
        default=dict,
        blank=True,
        help_text=_('Informations supplémentaires sur l\'action')
    )
    
    # Adresse IP de l'utilisateur
    ip_address = models.GenericIPAddressField(
        _('adresse IP'),
        null=True,
        blank=True
    )
    
    # Timestamp
    date_action = models.DateTimeField(_('date de l\'action'), auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = _('historique')
        verbose_name_plural = _('historiques')
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['-date_action']),
            models.Index(fields=['type_action', '-date_action']),
            models.Index(fields=['utilisateur', '-date_action']),
            models.Index(fields=['magasin', '-date_action']),
        ]
    
    def __str__(self):
        if self.utilisateur:
            return f"{self.get_type_action_display()} par {self.utilisateur.get_full_name()} - {self.date_action}"
        return f"{self.get_type_action_display()} - {self.date_action}"
    
    @classmethod
    def enregistrer_action(cls, type_action, utilisateur, description, magasin=None, 
                          objet=None, donnees_avant=None, donnees_apres=None, 
                          metadata=None, ip_address=None):
        """
        Méthode utilitaire pour enregistrer une action dans l'historique
        """
        historique = cls(
            type_action=type_action,
            utilisateur=utilisateur,
            magasin=magasin,
            description=description,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            metadata=metadata or {},
            ip_address=ip_address
        )
        
        if objet:
            historique.objet_concerne = objet
        
        historique.save()
        return historique
