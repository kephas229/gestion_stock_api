"""
Serializers pour la gestion des ventes
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from apps.ventes.models import Vente, LigneVente
from apps.produits.models import Produit
from apps.stocks.models import Stock, MouvementStock
from core.exceptions import StockInsuffisantException


class LigneVenteSerializer(serializers.ModelSerializer):
    """Serializer pour les lignes de vente"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_reference = serializers.CharField(source='produit.reference', read_only=True)
    montant_ligne = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    montant_brut = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = LigneVente
        fields = [
            'id', 'produit', 'produit_nom', 'produit_reference',
            'quantite', 'prix_unitaire', 'remise_ligne',
            'montant_ligne', 'montant_brut', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VenteSerializer(serializers.ModelSerializer):
    """Serializer pour les ventes"""
    lignes = LigneVenteSerializer(many=True, read_only=True)
    magasin_nom = serializers.CharField(source='magasin.nom', read_only=True)
    vendeur_nom = serializers.CharField(source='vendeur.get_full_name', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    methode_paiement_display = serializers.CharField(
        source='get_methode_paiement_display',
        read_only=True
    )
    montant_restant = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    montant_net = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    est_payee = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Vente
        fields = [
            'id', 'numero_vente', 'magasin', 'magasin_nom',
            'vendeur', 'vendeur_nom', 'nom_client', 'telephone_client',
            'email_client', 'montant_total', 'montant_paye', 'remise',
            'montant_restant', 'montant_net', 'methode_paiement',
            'methode_paiement_display', 'statut', 'statut_display',
            'notes', 'est_annulee', 'date_annulation', 'motif_annulation',
            'annulee_par', 'est_payee', 'date_vente', 'created_at',
            'updated_at', 'lignes'
        ]
        read_only_fields = [
            'id', 'numero_vente', 'vendeur', 'est_annulee',
            'date_annulation', 'motif_annulation', 'annulee_par',
            'date_vente', 'created_at', 'updated_at'
        ]


class LigneVenteCreateSerializer(serializers.Serializer):
    """Serializer pour créer une ligne de vente"""
    produit = serializers.PrimaryKeyRelatedField(queryset=Produit.objects.all())
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    remise_ligne = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )


class VenteCreateSerializer(serializers.Serializer):
    """Serializer pour créer une vente"""
    magasin = serializers.IntegerField()
    nom_client = serializers.CharField(required=False, allow_blank=True)
    telephone_client = serializers.CharField(required=False, allow_blank=True)
    email_client = serializers.EmailField(required=False, allow_blank=True)
    methode_paiement = serializers.ChoiceField(choices=Vente.METHODE_PAIEMENT_CHOICES)
    montant_paye = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.00')
    )
    remise = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    lignes = LigneVenteCreateSerializer(many=True)
    
    def validate_lignes(self, value):
        """Valider qu'il y a au moins une ligne"""
        if not value:
            raise serializers.ValidationError('La vente doit contenir au moins une ligne.')
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Créer la vente avec ses lignes"""
        lignes_data = validated_data.pop('lignes')
        vendeur = self.context['request'].user
        
        # Calculer le montant total
        montant_total = Decimal('0.00')
        lignes_objets = []
        
        for ligne_data in lignes_data:
            produit = ligne_data['produit']
            quantite = ligne_data['quantite']
            prix_unitaire = ligne_data.get('prix_unitaire') or produit.prix_vente
            remise_ligne = ligne_data.get('remise_ligne', Decimal('0.00'))
            
            # Vérifier le stock
            try:
                stock = Stock.objects.get(
                    produit=produit,
                    magasin_id=validated_data['magasin']
                )
                if stock.quantite_disponible < quantite:
                    raise StockInsuffisantException(
                        f'Stock insuffisant pour {produit.nom}. '
                        f'Disponible: {stock.quantite_disponible}, '
                        f'Demandé: {quantite}'
                    )
            except Stock.DoesNotExist:
                raise StockInsuffisantException(
                    f'Aucun stock disponible pour {produit.nom} dans ce magasin.'
                )
            
            montant_ligne = (prix_unitaire * quantite) - remise_ligne
            montant_total += montant_ligne
            
            lignes_objets.append({
                'produit': produit,
                'quantite': quantite,
                'prix_unitaire': prix_unitaire,
                'remise_ligne': remise_ligne,
                'stock': stock
            })
        
        # Créer la vente
        vente = Vente.objects.create(
            magasin_id=validated_data['magasin'],
            vendeur=vendeur,
            nom_client=validated_data.get('nom_client', ''),
            telephone_client=validated_data.get('telephone_client', ''),
            email_client=validated_data.get('email_client', ''),
            montant_total=montant_total,
            montant_paye=validated_data['montant_paye'],
            remise=validated_data.get('remise', Decimal('0.00')),
            methode_paiement=validated_data['methode_paiement'],
            notes=validated_data.get('notes', ''),
            statut='VALIDEE' if validated_data['montant_paye'] >= montant_total else 'EN_COURS'
        )
        
        # Créer les lignes et mettre à jour les stocks
        for ligne_obj in lignes_objets:
            LigneVente.objects.create(
                vente=vente,
                produit=ligne_obj['produit'],
                quantite=ligne_obj['quantite'],
                prix_unitaire=ligne_obj['prix_unitaire'],
                remise_ligne=ligne_obj['remise_ligne']
            )
            
            # Mettre à jour le stock
            stock = ligne_obj['stock']
            quantite_avant = stock.quantite
            stock.quantite -= ligne_obj['quantite']
            stock.save()
            
            # Enregistrer le mouvement
            MouvementStock.objects.create(
                stock=stock,
                type_mouvement='SORTIE',
                quantite=ligne_obj['quantite'],
                quantite_avant=quantite_avant,
                quantite_apres=stock.quantite,
                vente=vente,
                motif=f'Vente #{vente.numero_vente}',
                effectue_par=vendeur
            )
        
        return vente


class AnnulationVenteSerializer(serializers.Serializer):
    """Serializer pour annuler une vente"""
    motif = serializers.CharField(required=True)
    
    def validate_motif(self, value):
        """Valider que le motif n'est pas vide"""
        if not value.strip():
            raise serializers.ValidationError('Le motif d\'annulation est obligatoire.')
        return value
