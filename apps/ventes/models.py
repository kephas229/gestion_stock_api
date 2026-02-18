"""
Modèles pour la gestion des ventes
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    
    def update_montant_total(self):
        total = sum(ligne.montant_ligne for ligne in self.lignes.all())
        self.montant_total = total
        self.save(update_fields=["montant_total"])

    
    @property
    def montant_restant(self):
        total = self.montant_total or Decimal("0.00")
        paye = self.montant_paye or Decimal("0.00")
        return total - paye


    @property
    def montant_net(self):
        total = self.montant_total or Decimal("0.00")
        remise = self.remise or Decimal("0.00")
        return total - remise


    @property
    def est_payee(self):
        total = self.montant_total or Decimal("0.00")
        paye = self.montant_paye or Decimal("0.00")
        return paye >= total

    
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
    
    def clean(self):


    # Prix unitaire = prix de vente du produit
        if self.produit:
            self.prix_unitaire = self.produit.prix_vente

        # Vérifier stock
        if self.produit and self.quantite:
            if self.quantite > self.produit.quantite_stock:
                raise ValidationError(
                f"Stock insuffisant. Disponible : {self.produit.quantite_stock}"
            )

    @property
    def montant_ligne(self):
        """Calcul du montant de la ligne après remise"""
        prix = self.prix_unitaire or Decimal("0.00")
        quantite = self.quantite or 0
        remise = self.remise_ligne or Decimal("0.00")
        return (prix * quantite) - remise


    @property
    def montant_brut(self):
        """Calcul du montant brut de la ligne avant remise"""
        prix = self.prix_unitaire or Decimal("0.00")
        quantite = self.quantite or 0
        return prix * quantite

    
    def save(self, *args, **kwargs):
        # Mettre à jour le prix unitaire à partir du produit
        if self.produit:
            self.prix_unitaire = self.produit.prix_vente
        super().save(*args, **kwargs)
        # Mettre à jour le montant total de la vente
        self.vente.update_montant_total()