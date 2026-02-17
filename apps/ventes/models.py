"""
Modèles pour la gestion des ventes
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


class Vente(models.Model):
    """
    Modèle représentant une vente
    """
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('VALIDEE', 'Validée'),
        ('ANNULEE', 'Annulée'),
    ]
    
    METHODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CARTE', 'Carte bancaire'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('CHEQUE', 'Chèque'),
        ('VIREMENT', 'Virement'),
    ]
    
    # Numéro de vente unique
    numero_vente = models.CharField(
        _('numéro de vente'),
        max_length=50,
        unique=True,
        db_index=True
    )
    
    # Magasin et utilisateur
    magasin = models.ForeignKey(
        'magasins.Magasin',
        on_delete=models.PROTECT,
        related_name='ventes',
        verbose_name=_('magasin')
    )
    vendeur = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ventes_effectuees',
        verbose_name=_('vendeur')
    )
    
    # Client (optionnel - peut être anonyme)
    nom_client = models.CharField(_('nom du client'), max_length=200, blank=True)
    telephone_client = models.CharField(_('téléphone client'), max_length=20, blank=True)
    email_client = models.EmailField(_('email client'), blank=True)
    
    # Montants
    montant_total = models.DecimalField(
        _('montant total'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    montant_paye = models.DecimalField(
        _('montant payé'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    remise = models.DecimalField(
        _('remise'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Méthode de paiement
    methode_paiement = models.CharField(
        _('méthode de paiement'),
        max_length=20,
        choices=METHODE_PAIEMENT_CHOICES
    )
    
    # Statut
    statut = models.CharField(
        _('statut'),
        max_length=15,
        choices=STATUT_CHOICES,
        default='EN_COURS'
    )
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Annulation
    est_annulee = models.BooleanField(_('annulée'), default=False)
    date_annulation = models.DateTimeField(_('date d\'annulation'), null=True, blank=True)
    motif_annulation = models.TextField(_('motif d\'annulation'), blank=True)
    annulee_par = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventes_annulees',
        verbose_name=_('annulée par')
    )
    
    # Timestamps
    date_vente = models.DateTimeField(_('date de vente'), default=timezone.now)
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    
    class Meta:
        verbose_name = _('vente')
        verbose_name_plural = _('ventes')
        ordering = ['-date_vente']
        indexes = [
            models.Index(fields=['numero_vente']),
            models.Index(fields=['magasin', '-date_vente']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"Vente #{self.numero_vente} - {self.magasin.nom}"
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à payer"""
        return self.montant_total - self.montant_paye
    
    @property
    def montant_net(self):
        """Calcule le montant net après remise"""
        return self.montant_total - self.remise
    
    @property
    def est_payee(self):
        """Vérifie si la vente est entièrement payée"""
        return self.montant_paye >= self.montant_total
    
    def annuler(self, utilisateur, motif):
        """Annule la vente"""
        if self.est_annulee:
            raise ValueError(_('Cette vente est déjà annulée'))
        
        self.est_annulee = True
        self.statut = 'ANNULEE'
        self.date_annulation = timezone.now()
        self.motif_annulation = motif
        self.annulee_par = utilisateur
        self.save()
    
    def save(self, *args, **kwargs):
        # Générer un numéro de vente si ce n'est pas fait
        if not self.numero_vente:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            last_vente = Vente.objects.filter(
                numero_vente__startswith=f'V{date_str}'
            ).order_by('-numero_vente').first()
            
            if last_vente:
                last_num = int(last_vente.numero_vente[-4:])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.numero_vente = f'V{date_str}{new_num:04d}'
        
        super().save(*args, **kwargs)


class LigneVente(models.Model):
    """
    Modèle représentant une ligne de vente (un produit dans une vente)
    """
    vente = models.ForeignKey(
        Vente,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name=_('vente')
    )
    produit = models.ForeignKey(
        'produits.Produit',
        on_delete=models.PROTECT,
        related_name='lignes_vente',
        verbose_name=_('produit')
    )
    
    # Quantité et prix
    quantite = models.IntegerField(
        _('quantité'),
        validators=[MinValueValidator(1)]
    )
    prix_unitaire = models.DecimalField(
        _('prix unitaire'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    remise_ligne = models.DecimalField(
        _('remise sur la ligne'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('ligne de vente')
        verbose_name_plural = _('lignes de vente')
        ordering = ['vente', 'id']
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
    
    @property
    def montant_ligne(self):
        """Calcule le montant total de la ligne"""
        return (self.prix_unitaire * self.quantite) - self.remise_ligne
    
    @property
    def montant_brut(self):
        """Calcule le montant brut avant remise"""
        return self.prix_unitaire * self.quantite
    
    def save(self, *args, **kwargs):
        # Définir le prix unitaire au prix de vente actuel du produit si non spécifié
        if not self.prix_unitaire:
            self.prix_unitaire = self.produit.prix_vente
        super().save(*args, **kwargs)
