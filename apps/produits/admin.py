"""
Configuration de l'interface d'administration pour les produits et catégories
"""
from django.contrib import admin
from apps.produits.models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'parent', 'is_active', 'nombre_produits']
    list_filter = ['is_active', 'parent']
    search_fields = ['nom', 'code']
    ordering = ['nom']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'reference', 'categorie', 'prix_vente', 'unite_mesure', 'is_active']
    list_filter = ['is_active', 'categorie', 'unite_mesure', 'is_perishable']
    search_fields = ['nom', 'code_barre', 'reference']
    ordering = ['nom']
    readonly_fields = ['created_at', 'updated_at', 'marge_beneficiaire', 'benefice_unitaire']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code_barre', 'reference', 'categorie', 'description')
        }),
        ('Prix', {
            'fields': ('prix_achat', 'prix_vente', 'marge_beneficiaire', 'benefice_unitaire')
        }),
        ('Stock', {
            'fields': ('unite_mesure', 'seuil_alerte', 'stock_minimal', 'stock_maximal')
        }),
        ('Détails', {
            'fields': ('poids', 'dimensions', 'fournisseur', 'specifications')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Statuts', {
            'fields': ('is_active', 'is_perishable')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
