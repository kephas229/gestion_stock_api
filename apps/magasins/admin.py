"""
Configuration de l'interface d'administration pour les magasins
"""
from django.contrib import admin
from apps.magasins.models import Magasin


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'ville', 'pays', 'is_active', 'created_at']
    list_filter = ['is_active', 'ville', 'pays']
    search_fields = ['nom', 'code', 'adresse']
    ordering = ['nom']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code', 'description')
        }),
        ('Localisation', {
            'fields': ('adresse', 'ville', 'pays')
        }),
        ('Contact', {
            'fields': ('telephone', 'email')
        }),
        ('Détails', {
            'fields': ('surface', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
