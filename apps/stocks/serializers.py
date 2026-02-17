"""
Serializers pour la gestion des stocks
"""
from rest_framework import serializers
from apps.stocks.models import Stock, MouvementStock
from apps.produits.models import Produit
from apps.magasins.models import Magasin


class StockSerializer(serializers.ModelSerializer):
    """Serializer pour les stocks"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_reference = serializers.CharField(source='produit.reference', read_only=True)
    magasin_nom = serializers.CharField(source='magasin.nom', read_only=True)
    quantite_disponible = serializers.IntegerField(read_only=True)
    valeur_stock = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    est_en_alerte = serializers.BooleanField(read_only=True)
    est_critique = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'produit', 'produit_nom', 'produit_reference',
            'magasin', 'magasin_nom', 'quantite', 'quantite_reservee',
            'quantite_disponible', 'emplacement', 'valeur_stock',
            'est_en_alerte', 'est_critique', 'last_inventory_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de stocks"""
    class Meta:
        model = Stock
        fields = ['produit', 'magasin', 'quantite', 'emplacement']
    
    def validate(self, attrs):
        """Validation personnalisée"""
        # Vérifier que le stock n'existe pas déjà
        produit = attrs.get('produit')
        magasin = attrs.get('magasin')
        
        if Stock.objects.filter(produit=produit, magasin=magasin).exists():
            raise serializers.ValidationError(
                'Un stock existe déjà pour ce produit dans ce magasin.'
            )
        
        return attrs


class StockUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des stocks"""
    class Meta:
        model = Stock
        fields = ['quantite', 'quantite_reservee', 'emplacement']
    
    def validate(self, attrs):
        """Validation personnalisée"""
        quantite = attrs.get('quantite', self.instance.quantite)
        quantite_reservee = attrs.get('quantite_reservee', self.instance.quantite_reservee)
        
        if quantite_reservee > quantite:
            raise serializers.ValidationError({
                'quantite_reservee': 'La quantité réservée ne peut pas dépasser la quantité en stock.'
            })
        
        return attrs


class MouvementStockSerializer(serializers.ModelSerializer):
    """Serializer pour les mouvements de stock"""
    produit_nom = serializers.CharField(source='stock.produit.nom', read_only=True)
    magasin_nom = serializers.CharField(source='stock.magasin.nom', read_only=True)
    type_mouvement_display = serializers.CharField(
        source='get_type_mouvement_display',
        read_only=True
    )
    effectue_par_nom = serializers.CharField(
        source='effectue_par.get_full_name',
        read_only=True
    )
    magasin_destination_nom = serializers.CharField(
        source='magasin_destination.nom',
        read_only=True
    )
    
    class Meta:
        model = MouvementStock
        fields = [
            'id', 'stock', 'produit_nom', 'magasin_nom', 'type_mouvement',
            'type_mouvement_display', 'quantite', 'quantite_avant',
            'quantite_apres', 'magasin_destination', 'magasin_destination_nom',
            'vente', 'motif', 'reference_document', 'date_mouvement',
            'effectue_par', 'effectue_par_nom'
        ]
        read_only_fields = ['id', 'date_mouvement', 'effectue_par']


class ReapprovisionnementSerializer(serializers.Serializer):
    """Serializer pour le réapprovisionnement de stock"""
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    magasin = serializers.PrimaryKeyRelatedField(queryset=Magasin.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    motif = serializers.CharField(required=False, allow_blank=True)
    reference_document = serializers.CharField(required=False, allow_blank=True)
    
    def validate_quantite(self, value):
        """Valider la quantité"""
        if value <= 0:
            raise serializers.ValidationError('La quantité doit être supérieure à 0.')
        return value


class TransfertStockSerializer(serializers.Serializer):
    """Serializer pour le transfert de stock entre magasins"""
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    magasin_source = serializers.PrimaryKeyRelatedField(queryset=Magasin.objects.all())
    magasin_destination = serializers.PrimaryKeyRelatedField(queryset=Magasin.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    motif = serializers.CharField(required=False, allow_blank=True)
    reference_document = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validation personnalisée"""
        magasin_source = attrs.get('magasin_source')
        magasin_destination = attrs.get('magasin_destination')
        
        if magasin_source == magasin_destination:
            raise serializers.ValidationError({
                'magasin_destination': 'Le magasin de destination doit être différent du magasin source.'
            })
        
        return attrs


class AjustementStockSerializer(serializers.Serializer):
    """Serializer pour l'ajustement de stock (inventaire)"""
    stock = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.all())
    nouvelle_quantite = serializers.IntegerField(min_value=0)
    motif = serializers.CharField()
    reference_document = serializers.CharField(required=False, allow_blank=True)
