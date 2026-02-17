"""
Configuration de l'interface d'administration pour les stocks
"""
from django.contrib import admin
from apps.stocks.models import Stock, MouvementStock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'magasin', 'quantite', 'quantite_disponible', 'est_en_alerte']
    list_filter = ['magasin', 'produit__categorie']
    search_fields = ['produit__nom', 'magasin__nom']
    ordering = ['magasin', 'produit']
    readonly_fields = ['created_at', 'updated_at', 'quantite_disponible', 'valeur_stock']


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ['stock', 'type_mouvement', 'quantite', 'date_mouvement', 'effectue_par']
    list_filter = ['type_mouvement', 'date_mouvement']
    search_fields = ['stock__produit__nom', 'motif']
    ordering = ['-date_mouvement']
    readonly_fields = ['date_mouvement']
