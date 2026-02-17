"""
Configuration de l'interface d'administration pour l'historique
"""
from django.contrib import admin
from apps.historique.models import Historique


@admin.register(Historique)
class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ['type_action', 'utilisateur', 'magasin', 'description', 'date_action']
    list_filter = ['type_action', 'magasin', 'date_action']
    search_fields = ['description', 'utilisateur__email']
    ordering = ['-date_action']
    readonly_fields = ['date_action', 'type_action', 'utilisateur', 'magasin', 
                      'description', 'donnees_avant', 'donnees_apres', 
                      'metadata', 'ip_address']
    
    def has_add_permission(self, request):
        # Empêcher l'ajout manuel d'historique
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression d'historique
        return False
