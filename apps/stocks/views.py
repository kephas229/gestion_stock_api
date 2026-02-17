"""
Views pour la gestion des stocks
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import transaction
from django.utils import timezone

from apps.stocks.models import Stock, MouvementStock
from apps.stocks.serializers import (
    StockSerializer, StockCreateSerializer, StockUpdateSerializer,
    MouvementStockSerializer, ReapprovisionnementSerializer,
    TransfertStockSerializer, AjustementStockSerializer
)
from core.permissions import IsAdmin, IsAdminOrReadOnly, CanManageStock
from apps.historique.models import Historique
from core.exceptions import StockInsuffisantException


class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des stocks
    Admin: CRUD complet sur tous les stocks
    Gérant: Lecture uniquement de son magasin
    """
    queryset = Stock.objects.select_related('produit', 'magasin').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['magasin', 'produit', 'produit__categorie']
    search_fields = ['produit__nom', 'produit__reference', 'emplacement']
    ordering_fields = ['quantite', 'updated_at']
    ordering = ['produit__nom']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return StockCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StockUpdateSerializer
        return StockSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create']:
            return [IsAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [CanManageStock()]
        return [IsAdminOrReadOnly()]
    
    def get_queryset(self):
        """Filtrer les stocks selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que le stock de leur magasin
        if user.role == 'GERANT':
            return queryset.filter(magasin=user.magasin)
        
        # Filtrer les produits en alerte si demandé
        if self.request.query_params.get('en_alerte') == 'true':
            from django.db.models import F
            queryset = queryset.filter(quantite__lte=F('produit__seuil_alerte'))
        
        return queryset
    
    def perform_create(self, serializer):
        """Créer un stock et enregistrer dans l'historique"""
        stock = serializer.save()
        
        Historique.enregistrer_action(
            type_action='STOCK_REAPPROVISIONNE',
            utilisateur=self.request.user,
            magasin=stock.magasin,
            description=f'Création du stock pour {stock.produit.nom} dans {stock.magasin.nom}',
            objet=stock,
            donnees_apres={'quantite': stock.quantite},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        # Enregistrer le mouvement
        MouvementStock.objects.create(
            stock=stock,
            type_mouvement='ENTREE',
            quantite=stock.quantite,
            quantite_avant=0,
            quantite_apres=stock.quantite,
            motif='Stock initial',
            effectue_par=self.request.user
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    @transaction.atomic
    def reapprovisionner(self, request):
        """Réapprovisionner le stock d'un produit dans un magasin"""
        serializer = ReapprovisionnementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        produit = serializer.validated_data['produit']
        magasin = serializer.validated_data['magasin']
        quantite = serializer.validated_data['quantite']
        motif = serializer.validated_data.get('motif', '')
        reference = serializer.validated_data.get('reference_document', '')
        
        # Créer ou mettre à jour le stock
        stock, created = Stock.objects.get_or_create(
            produit=produit,
            magasin=magasin,
            defaults={'quantite': 0}
        )
        
        quantite_avant = stock.quantite
        stock.quantite += quantite
        stock.save()
        
        # Enregistrer le mouvement
        MouvementStock.objects.create(
            stock=stock,
            type_mouvement='ENTREE',
            quantite=quantite,
            quantite_avant=quantite_avant,
            quantite_apres=stock.quantite,
            motif=motif or 'Réapprovisionnement',
            reference_document=reference,
            effectue_par=request.user
        )
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='STOCK_REAPPROVISIONNE',
            utilisateur=request.user,
            magasin=magasin,
            description=f'Réapprovisionnement de {produit.nom}: +{quantite} unités',
            objet=stock,
            donnees_avant={'quantite': quantite_avant},
            donnees_apres={'quantite': stock.quantite},
            metadata={'quantite_ajoutee': quantite},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {
                'success': True,
                'message': f'Stock réapprovisionné avec succès. Nouvelle quantité: {stock.quantite}',
                'stock': StockSerializer(stock).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    @transaction.atomic
    def transferer(self, request):
        """Transférer du stock d'un magasin à un autre"""
        serializer = TransfertStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        produit = serializer.validated_data['produit']
        magasin_source = serializer.validated_data['magasin_source']
        magasin_destination = serializer.validated_data['magasin_destination']
        quantite = serializer.validated_data['quantite']
        motif = serializer.validated_data.get('motif', '')
        reference = serializer.validated_data.get('reference_document', '')
        
        # Vérifier le stock source
        try:
            stock_source = Stock.objects.get(produit=produit, magasin=magasin_source)
        except Stock.DoesNotExist:
            raise StockInsuffisantException('Aucun stock disponible dans le magasin source.')
        
        if stock_source.quantite_disponible < quantite:
            raise StockInsuffisantException(
                f'Stock insuffisant. Disponible: {stock_source.quantite_disponible}, Demandé: {quantite}'
            )
        
        # Mettre à jour le stock source
        quantite_avant_source = stock_source.quantite
        stock_source.quantite -= quantite
        stock_source.save()
        
        # Enregistrer le mouvement de sortie
        MouvementStock.objects.create(
            stock=stock_source,
            type_mouvement='TRANSFERT',
            quantite=quantite,
            quantite_avant=quantite_avant_source,
            quantite_apres=stock_source.quantite,
            magasin_destination=magasin_destination,
            motif=motif or f'Transfert vers {magasin_destination.nom}',
            reference_document=reference,
            effectue_par=request.user
        )
        
        # Créer ou mettre à jour le stock destination
        stock_destination, created = Stock.objects.get_or_create(
            produit=produit,
            magasin=magasin_destination,
            defaults={'quantite': 0}
        )
        
        quantite_avant_dest = stock_destination.quantite
        stock_destination.quantite += quantite
        stock_destination.save()
        
        # Enregistrer le mouvement d'entrée
        MouvementStock.objects.create(
            stock=stock_destination,
            type_mouvement='ENTREE',
            quantite=quantite,
            quantite_avant=quantite_avant_dest,
            quantite_apres=stock_destination.quantite,
            motif=motif or f'Transfert depuis {magasin_source.nom}',
            reference_document=reference,
            effectue_par=request.user
        )
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='STOCK_TRANSFERE',
            utilisateur=request.user,
            magasin=magasin_source,
            description=f'Transfert de {quantite} unités de {produit.nom} de {magasin_source.nom} vers {magasin_destination.nom}',
            metadata={
                'produit': produit.nom,
                'quantite': quantite,
                'magasin_source': magasin_source.nom,
                'magasin_destination': magasin_destination.nom
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {
                'success': True,
                'message': 'Transfert effectué avec succès.',
                'stock_source': StockSerializer(stock_source).data,
                'stock_destination': StockSerializer(stock_destination).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    @transaction.atomic
    def ajuster(self, request):
        """Ajuster le stock (inventaire)"""
        serializer = AjustementStockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        stock = serializer.validated_data['stock']
        nouvelle_quantite = serializer.validated_data['nouvelle_quantite']
        motif = serializer.validated_data['motif']
        reference = serializer.validated_data.get('reference_document', '')
        
        quantite_avant = stock.quantite
        difference = nouvelle_quantite - quantite_avant
        stock.quantite = nouvelle_quantite
        stock.last_inventory_date = timezone.now()
        stock.save()
        
        # Enregistrer le mouvement
        MouvementStock.objects.create(
            stock=stock,
            type_mouvement='AJUSTEMENT',
            quantite=abs(difference),
            quantite_avant=quantite_avant,
            quantite_apres=nouvelle_quantite,
            motif=motif,
            reference_document=reference,
            effectue_par=request.user
        )
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='STOCK_AJUSTE',
            utilisateur=request.user,
            magasin=stock.magasin,
            description=f'Ajustement du stock de {stock.produit.nom}: {quantite_avant} → {nouvelle_quantite}',
            objet=stock,
            donnees_avant={'quantite': quantite_avant},
            donnees_apres={'quantite': nouvelle_quantite},
            metadata={'difference': difference},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {
                'success': True,
                'message': 'Stock ajusté avec succès.',
                'stock': StockSerializer(stock).data
            },
            status=status.HTTP_200_OK
        )


class MouvementStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter l'historique des mouvements de stock
    Lecture seule
    """
    queryset = MouvementStock.objects.select_related(
        'stock', 'stock__produit', 'stock__magasin', 'effectue_par'
    ).all()
    serializer_class = MouvementStockSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type_mouvement', 'stock__magasin', 'stock__produit', 'effectue_par']
    ordering_fields = ['date_mouvement']
    ordering = ['-date_mouvement']
    
    def get_queryset(self):
        """Filtrer les mouvements selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que les mouvements de leur magasin
        if user.role == 'GERANT':
            return queryset.filter(stock__magasin=user.magasin)
        
        return queryset
