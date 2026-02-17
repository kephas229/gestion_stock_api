"""
Serializers pour la gestion des magasins
"""
from rest_framework import serializers
from apps.magasins.models import Magasin


class MagasinSerializer(serializers.ModelSerializer):
    """Serializer pour les magasins"""
    nombre_employes = serializers.IntegerField(read_only=True)
    nombre_produits = serializers.IntegerField(read_only=True)
    valeur_stock_total = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = Magasin
        fields = [
            'id', 'nom', 'code', 'adresse', 'ville', 'pays',
            'telephone', 'email', 'description', 'surface',
            'is_active', 'nombre_employes', 'nombre_produits',
            'valeur_stock_total', 'created_at', 'updated_at',
            'created_by', 'created_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate_code(self, value):
        """Valider que le code est en majuscules"""
        if not value.isupper():
            raise serializers.ValidationError(
                "Le code doit être en lettres majuscules."
            )
        return value


class MagasinCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de magasins"""
    class Meta:
        model = Magasin
        fields = [
            'nom', 'code', 'adresse', 'ville', 'pays',
            'telephone', 'email', 'description', 'surface'
        ]
    
    def validate_code(self, value):
        """Valider que le code est en majuscules"""
        return value.upper()


class MagasinStatistiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques d'un magasin"""
    magasin = MagasinSerializer()
    nombre_produits = serializers.IntegerField()
    nombre_ventes = serializers.IntegerField()
    montant_ventes_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    montant_ventes_jour = serializers.DecimalField(max_digits=15, decimal_places=2)
    montant_ventes_mois = serializers.DecimalField(max_digits=15, decimal_places=2)
    nombre_ventes_annulees = serializers.IntegerField()
    produits_en_alerte = serializers.IntegerField()
    valeur_stock_total = serializers.DecimalField(max_digits=15, decimal_places=2)
