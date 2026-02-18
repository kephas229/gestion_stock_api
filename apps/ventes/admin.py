"""
Configuration de l'interface d'administration pour les ventes
"""
from django.contrib import admin
from apps.ventes.models import Vente, LigneVente


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    readonly_fields = ['prix_unitaire','montant_ligne']


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['numero_vente', 'magasin', 'vendeur', 'montant_total', 'statut', 'est_annulee', 'date_vente']
    list_filter = ['statut', 'est_annulee', 'magasin', 'methode_paiement', 'date_vente']
    search_fields = ['numero_vente', 'nom_client', 'telephone_client']
    ordering = ['-date_vente']
    readonly_fields = ['numero_vente', 'created_at', 'updated_at', 'montant_restant', 'montant_net']
    inlines = [LigneVenteInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero_vente', 'magasin', 'vendeur', 'statut')
        }),
        ('Client', {
            'fields': ('nom_client', 'telephone_client', 'email_client')
        }),
        ('Montants', {
            'fields': ('montant_total', 'montant_paye', 'remise', 'montant_restant', 'montant_net')
        }),
        ('Paiement', {
            'fields': ('methode_paiement',)
        }),
        ('Annulation', {
            'fields': ('est_annulee', 'date_annulation', 'motif_annulation', 'annulee_par'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('date_vente', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LigneVente)
class LigneVenteAdmin(admin.ModelAdmin):
    list_display = ['vente', 'produit', 'quantite', 'prix_unitaire', 'montant_ligne']
    list_filter = ['vente__magasin']
    search_fields = ['vente__numero_vente', 'produit__nom']
    readonly_fields = ['montant_ligne', 'montant_brut']
