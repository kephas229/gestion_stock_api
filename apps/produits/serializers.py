"""
Serializers pour la gestion des produits et catégories
"""
from rest_framework import serializers
from apps.produits.models import Categorie, Produit


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    parent_name = serializers.CharField(source='parent.nom', read_only=True)
    nombre_produits = serializers.IntegerField(read_only=True)
    sous_categories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Categorie
        fields = [
            'id', 'nom', 'code', 'description', 'parent', 'parent_name',
            'nombre_produits', 'sous_categories_count', 'is_active',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_sous_categories_count(self, obj):
        """Retourne le nombre de sous-catégories"""
        return obj.sous_categories.count()


class CategorieTreeSerializer(serializers.ModelSerializer):
    """Serializer pour afficher l'arborescence des catégories"""
    sous_categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'code', 'description', 'sous_categories']
    
    def get_sous_categories(self, obj):
        """Récursion pour obtenir toutes les sous-catégories"""
        sous_cats = obj.sous_categories.filter(is_active=True)
        return CategorieTreeSerializer(sous_cats, many=True).data


class ProduitSerializer(serializers.ModelSerializer):
    """Serializer pour les produits"""
    categorie_name = serializers.CharField(source='categorie.nom', read_only=True)
    unite_mesure_display = serializers.CharField(source='get_unite_mesure_display', read_only=True)
    marge_beneficiaire = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    benefice_unitaire = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    stock_total = serializers.SerializerMethodField()
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'code_barre', 'reference', 'categorie', 'categorie_name',
            'description', 'specifications', 'prix_achat', 'prix_vente',
            'unite_mesure', 'unite_mesure_display', 'seuil_alerte', 
            'stock_minimal', 'stock_maximal', 'image', 'poids', 'dimensions',
            'fournisseur', 'is_active', 'is_perishable', 'marge_beneficiaire',
            'benefice_unitaire', 'stock_total', 'created_at', 'updated_at',
            'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_stock_total(self, obj):
        """Retourne le stock total du produit"""
        return obj.stock_total()
    
    def validate(self, attrs):
        """Validation personnalisée"""
        prix_achat = attrs.get('prix_achat', getattr(self.instance, 'prix_achat', None))
        prix_vente = attrs.get('prix_vente', getattr(self.instance, 'prix_vente', None))
        
        if prix_vente and prix_achat and prix_vente < prix_achat:
            raise serializers.ValidationError({
                'prix_vente': 'Le prix de vente ne peut pas être inférieur au prix d\'achat.'
            })
        
        stock_minimal = attrs.get('stock_minimal', getattr(self.instance, 'stock_minimal', None))
        stock_maximal = attrs.get('stock_maximal', getattr(self.instance, 'stock_maximal', None))
        
        if stock_minimal and stock_maximal and stock_minimal > stock_maximal:
            raise serializers.ValidationError({
                'stock_minimal': 'Le stock minimal ne peut pas être supérieur au stock maximal.'
            })
        
        return attrs


class ProduitCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de produits"""
    class Meta:
        model = Produit
        fields = [
            'nom', 'code_barre', 'reference', 'categorie', 'description',
            'specifications', 'prix_achat', 'prix_vente', 'unite_mesure',
            'seuil_alerte', 'stock_minimal', 'stock_maximal', 'image',
            'poids', 'dimensions', 'fournisseur', 'is_perishable'
        ]
    
    def validate(self, attrs):
        """Validation personnalisée"""
        if attrs.get('prix_vente') < attrs.get('prix_achat'):
            raise serializers.ValidationError({
                'prix_vente': 'Le prix de vente ne peut pas être inférieur au prix d\'achat.'
            })
        
        if attrs.get('stock_minimal') > attrs.get('stock_maximal'):
            raise serializers.ValidationError({
                'stock_minimal': 'Le stock minimal ne peut pas être supérieur au stock maximal.'
            })
        
        return attrs


class ProduitDetailSerializer(ProduitSerializer):
    """Serializer détaillé pour un produit avec informations de stock par magasin"""
    stocks_par_magasin = serializers.SerializerMethodField()
    
    class Meta(ProduitSerializer.Meta):
        fields = ProduitSerializer.Meta.fields + ['stocks_par_magasin']
    
    def get_stocks_par_magasin(self, obj):
        """Retourne les stocks par magasin"""
        stocks = obj.stocks.select_related('magasin').all()
        return [{
            'magasin_id': stock.magasin.id,
            'magasin_nom': stock.magasin.nom,
            'quantite': stock.quantite,
            'quantite_disponible': stock.quantite_disponible,
            'est_en_alerte': stock.est_en_alerte,
            'emplacement': stock.emplacement
        } for stock in stocks]
