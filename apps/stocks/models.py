"""
Modèles pour la gestion des stocks
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


class Stock(models.Model):
    """
    Modèle représentant le stock d'un produit dans un magasin
    """
    produit = models.ForeignKey(
        'produits.Produit',
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('produit')
    )
    magasin = models.ForeignKey(
        'magasins.Magasin',
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_('magasin')
    )
    
    # Quantités
    quantite = models.IntegerField(
        _('quantité en stock'),
        default=0,
        validators=[MinValueValidator(0)]
    )
    quantite_reservee = models.IntegerField(
        _('quantité réservée'),
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Quantité réservée pour des commandes en attente')
    )
    
    # Emplacement dans le magasin
    emplacement = models.CharField(
        _('emplacement'),
        max_length=100,
        blank=True,
        help_text=_('Ex: Rayon A, Étagère 3')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    last_inventory_date = models.DateTimeField(
        _('dernier inventaire'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('stock')
        verbose_name_plural = _('stocks')
        unique_together = [['produit', 'magasin']]
        ordering = ['magasin', 'produit']
        indexes = [
            models.Index(fields=['produit', 'magasin']),
            models.Index(fields=['magasin']),
        ]
    
    def __str__(self):
        return f"{self.produit.nom} - {self.magasin.nom}: {self.quantite} {self.produit.unite_mesure}"
    
    @property
    def quantite_disponible(self):
        """Retourne la quantité réellement disponible (stock - réservé)"""
        return self.quantite - self.quantite_reservee
    
    @property
    def valeur_stock(self):
        """Calcule la valeur totale du stock"""
        return self.quantite * self.produit.prix_vente
    
    @property
    def est_en_alerte(self):
        """Vérifie si le stock est en dessous du seuil d'alerte"""
        return self.quantite <= self.produit.seuil_alerte
    
    @property
    def est_critique(self):
        """Vérifie si le stock est en dessous du stock minimal"""
        return self.quantite <= self.produit.stock_minimal
    
    def clean(self):
        """Validation personnalisée"""
        if self.quantite_reservee > self.quantite:
            raise ValidationError(
                _('La quantité réservée ne peut pas dépasser la quantité en stock')
            )
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class MouvementStock(models.Model):
    """
    Modèle pour enregistrer tous les mouvements de stock
    """
    TYPE_MOUVEMENT_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
        ('TRANSFERT', 'Transfert'),
        ('AJUSTEMENT', 'Ajustement'),
        ('RETOUR', 'Retour'),
    ]
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='mouvements',
        verbose_name=_('stock')
    )
    
    type_mouvement = models.CharField(
        _('type de mouvement'),
        max_length=15,
        choices=TYPE_MOUVEMENT_CHOICES
    )
    
    quantite = models.IntegerField(
        _('quantité'),
        validators=[MinValueValidator(1)]
    )
    
    quantite_avant = models.IntegerField(_('quantité avant'))
    quantite_apres = models.IntegerField(_('quantité après'))
    
    # Pour les transferts
    magasin_destination = models.ForeignKey(
        'magasins.Magasin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mouvements_entrants',
        verbose_name=_('magasin de destination')
    )
    
    # Référence à la vente si applicable
    vente = models.ForeignKey(
        'ventes.Vente',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mouvements_stock',
        verbose_name=_('vente associée')
    )
    
    # Informations complémentaires
    motif = models.TextField(_('motif'), blank=True)
    reference_document = models.CharField(
        _('référence document'),
        max_length=100,
        blank=True
    )
    
    # Timestamps et utilisateur
    date_mouvement = models.DateTimeField(_('date du mouvement'), auto_now_add=True)
    effectue_par = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='mouvements_effectues',
        verbose_name=_('effectué par')
    )
    
    class Meta:
        verbose_name = _('mouvement de stock')
        verbose_name_plural = _('mouvements de stock')
        ordering = ['-date_mouvement']
        indexes = [
            models.Index(fields=['stock', '-date_mouvement']),
            models.Index(fields=['type_mouvement']),
        ]
    
    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.stock.produit.nom} ({self.quantite})"
