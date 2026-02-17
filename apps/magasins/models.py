"""
Modèle pour la gestion des magasins
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class Magasin(models.Model):
    """
    Modèle représentant un magasin
    """
    nom = models.CharField(_('nom du magasin'), max_length=200, unique=True)
    code = models.CharField(
        _('code magasin'),
        max_length=20,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex='^[A-Z0-9]+$',
                message=_('Le code doit contenir uniquement des lettres majuscules et des chiffres'),
            )
        ]
    )
    
    # Informations de localisation
    adresse = models.TextField(_('adresse'))
    ville = models.CharField(_('ville'), max_length=100)
    pays = models.CharField(_('pays'), max_length=100, default='Bénin')
    telephone = models.CharField(_('téléphone'), max_length=20)
    email = models.EmailField(_('email'), blank=True)
    
    # Informations complémentaires
    description = models.TextField(_('description'), blank=True)
    surface = models.DecimalField(
        _('surface (m²)'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Statut
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('date de création'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    created_by = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='magasins_created',
        verbose_name=_('créé par')
    )
    
    class Meta:
        verbose_name = _('magasin')
        verbose_name_plural = _('magasins')
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['ville']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    @property
    def nombre_employes(self):
        """Retourne le nombre d'employés du magasin"""
        return self.utilisateurs.count()
    
    @property
    def nombre_produits(self):
        """Retourne le nombre de produits en stock dans ce magasin"""
        return self.stocks.filter(quantite__gt=0).count()
    
    @property
    def valeur_stock_total(self):
        """Calcule la valeur totale du stock du magasin"""
        from django.db.models import Sum, F
        total = self.stocks.aggregate(
            total=Sum(F('quantite') * F('produit__prix_vente'))
        )['total']
        return total or 0
