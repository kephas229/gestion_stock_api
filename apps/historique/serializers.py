"""
Serializer pour la gestion de l'historique
"""
from rest_framework import serializers
from apps.historique.models import Historique


class HistoriqueSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique"""
    type_action_display = serializers.CharField(
        source='get_type_action_display',
        read_only=True
    )
    utilisateur_nom = serializers.CharField(
        source='utilisateur.get_full_name',
        read_only=True
    )
    magasin_nom = serializers.CharField(
        source='magasin.nom',
        read_only=True
    )
    
    class Meta:
        model = Historique
        fields = [
            'id', 'type_action', 'type_action_display', 'utilisateur',
            'utilisateur_nom', 'magasin', 'magasin_nom', 'description',
            'donnees_avant', 'donnees_apres', 'metadata', 'ip_address',
            'date_action'
        ]
        read_only_fields = fields
