"""
Modèles pour la gestion des produits et catégories
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Categorie(models.Model):
    """
    Modèle représentant une catégorie de produits
    """
    nom = models.CharField(_('nom'), max_length=100, unique=True)
    code = models.CharField(_('code'), max_length=20, unique=True, db_index=True)
    description = models.TextField(_('description'), blank=True)
    
    # Catégorie parente pour créer une hiérarchie
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sous_categories',
        verbose_name=_('catégorie parente')
    )
    
    # Statut
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='categories_created',
        verbose_name=_('créé par')
    )
    
    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.nom} > {self.nom}"
        return self.nom
    
    @property
    def nombre_produits(self):
        """Retourne le nombre de produits dans cette catégorie"""
        return self.produits.filter(is_active=True).count()


class Produit(models.Model):
    """
    Modèle représentant un produit
    """
    # Informations de base
    nom = models.CharField(_('nom du produit'), max_length=200)
    code_barre = models.CharField(
        _('code-barres'),
        max_length=50,
        unique=True,
        db_index=True
    )
    reference = models.CharField(
        _('référence interne'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    # Catégorie
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='produits',
        verbose_name=_('catégorie')
    )
    
    # Description
    description = models.TextField(_('description'), blank=True)
    specifications = models.JSONField(
        _('spécifications techniques'),
        default=dict,
        blank=True,
        help_text=_('Stockage des caractéristiques techniques du produit')
    )
    
    # Prix
    prix_achat = models.DecimalField(
        _('prix d\'achat'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    prix_vente = models.DecimalField(
        _('prix de vente'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Unités
    UNITE_CHOICES = [
        ('PIECE', 'Pièce'),
        ('KG', 'Kilogramme'),
        ('G', 'Gramme'),
        ('L', 'Litre'),
        ('ML', 'Millilitre'),
        ('M', 'Mètre'),
        ('CM', 'Centimètre'),
        ('CARTON', 'Carton'),
        ('PACK', 'Pack'),
    ]
    unite_mesure = models.CharField(
        _('unité de mesure'),
        max_length=10,
        choices=UNITE_CHOICES,
        default='PIECE'
    )
    
    # Seuils de stock
    seuil_alerte = models.IntegerField(
        _('seuil d\'alerte'),
        default=10,
        validators=[MinValueValidator(0)],
        help_text=_('Niveau de stock minimum avant alerte')
    )
    stock_minimal = models.IntegerField(
        _('stock minimal'),
        default=5,
        validators=[MinValueValidator(0)]
    )
    stock_maximal = models.IntegerField(
        _('stock maximal'),
        default=1000,
        validators=[MinValueValidator(0)]
    )
    
    # Image du produit
    image = models.ImageField(
        _('image'),
        upload_to='produits/',
        null=True,
        blank=True
    )
    
    # Informations supplémentaires
    poids = models.DecimalField(
        _('poids (kg)'),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True
    )
    dimensions = models.CharField(
        _('dimensions (L x l x H)'),
        max_length=100,
        blank=True
    )
    
    # Fournisseur (optionnel - peut être étendu)
    fournisseur = models.CharField(_('fournisseur'), max_length=200, blank=True)
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    is_perishable = models.BooleanField(_('périssable'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='produits_created',
        verbose_name=_('créé par')
    )
    
    class Meta:
        verbose_name = _('produit')
        verbose_name_plural = _('produits')
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code_barre']),
            models.Index(fields=['reference']),
            models.Index(fields=['categorie']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.reference})"
    
    @property
    def marge_beneficiaire(self):
        if self.prix_achat is not None and self.prix_vente is not None:
            if self.prix_achat > 0:
                return ((self.prix_vente - self.prix_achat) / self.prix_achat) * 100
        return 0

    
    @property
    def benefice_unitaire(self):
        """Calcule le bénéfice unitaire"""
        return self.prix_vente - self.prix_achat
    
    def stock_total(self):
        """Retourne le stock total du produit dans tous les magasins"""
        from django.db.models import Sum
        total = self.stocks.aggregate(total=Sum('quantite'))['total']
        return total or 0
    
    def stock_par_magasin(self, magasin):
        """Retourne le stock du produit dans un magasin spécifique"""
        try:
            stock = self.stocks.get(magasin=magasin)
            return stock.quantite
        except:
            return 0
