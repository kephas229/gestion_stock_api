"""
Views pour la gestion des produits et catégories
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from apps.produits.models import Categorie, Produit
from apps.produits.serializers import (
    CategorieSerializer, CategorieTreeSerializer,
    ProduitSerializer, ProduitCreateSerializer, ProduitDetailSerializer
)
from core.permissions import IsAdmin, IsAdminOrReadOnly
from apps.historique.models import Historique


class CategorieViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des catégories
    Admin: CRUD complet
    Gérant: Lecture seule
    """
    queryset = Categorie.objects.select_related('parent', 'created_by').prefetch_related('sous_categories').all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['nom', 'code', 'description']
    ordering_fields = ['nom', 'created_at']
    ordering = ['nom']
    
    def perform_create(self, serializer):
        """Créer une catégorie et enregistrer dans l'historique"""
        categorie = serializer.save(created_by=self.request.user)
        
        Historique.enregistrer_action(
            type_action='CATEGORIE_CREEE',
            utilisateur=self.request.user,
            description=f'Création de la catégorie {categorie.nom}',
            objet=categorie,
            donnees_apres={'nom': categorie.nom, 'code': categorie.code},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        """Mettre à jour une catégorie et enregistrer dans l'historique"""
        donnees_avant = {
            'nom': serializer.instance.nom,
            'code': serializer.instance.code,
            'is_active': serializer.instance.is_active
        }
        
        categorie = serializer.save()
        
        Historique.enregistrer_action(
            type_action='CATEGORIE_MODIFIEE',
            utilisateur=self.request.user,
            description=f'Modification de la catégorie {categorie.nom}',
            objet=categorie,
            donnees_avant=donnees_avant,
            donnees_apres={'nom': categorie.nom, 'code': categorie.code},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Obtenir l'arborescence des catégories"""
        categories = self.get_queryset().filter(parent__isnull=True, is_active=True)
        serializer = CategorieTreeSerializer(categories, many=True)
        return Response(serializer.data)


class ProduitViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des produits
    Admin: CRUD complet
    Gérant: Lecture avec filtrage par magasin
    """
    queryset = Produit.objects.select_related('categorie', 'created_by').prefetch_related('stocks').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'categorie', 'is_perishable']
    search_fields = ['nom', 'code_barre', 'reference', 'fournisseur']
    ordering_fields = ['nom', 'prix_vente', 'created_at']
    ordering = ['nom']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return ProduitCreateSerializer
        elif self.action == 'retrieve':
            return ProduitDetailSerializer
        return ProduitSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAdminOrReadOnly()]
    
    def get_queryset(self):
        """Filtrer les produits selon le rôle et les paramètres"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Filtrer par magasin si demandé
        magasin_id = self.request.query_params.get('magasin')
        if magasin_id:
            # Produits disponibles dans ce magasin
            queryset = queryset.filter(stocks__magasin_id=magasin_id, stocks__quantite__gt=0)
        
        # Les gérants voient uniquement les produits de leur magasin
        if user.role == 'GERANT' and not magasin_id:
            queryset = queryset.filter(
                stocks__magasin=user.magasin,
                stocks__quantite__gt=0
            )
        
        return queryset.distinct()
    
    def perform_create(self, serializer):
        """Créer un produit et enregistrer dans l'historique"""
        produit = serializer.save(created_by=self.request.user)
        
        Historique.enregistrer_action(
            type_action='PRODUIT_CREE',
            utilisateur=self.request.user,
            description=f'Création du produit {produit.nom} ({produit.reference})',
            objet=produit,
            donnees_apres={
                'nom': produit.nom,
                'reference': produit.reference,
                'prix_vente': str(produit.prix_vente)
            },
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        """Mettre à jour un produit et enregistrer dans l'historique"""
        donnees_avant = {
            'nom': serializer.instance.nom,
            'prix_achat': str(serializer.instance.prix_achat),
            'prix_vente': str(serializer.instance.prix_vente),
            'is_active': serializer.instance.is_active
        }
        
        produit = serializer.save()
        
        donnees_apres = {
            'nom': produit.nom,
            'prix_achat': str(produit.prix_achat),
            'prix_vente': str(produit.prix_vente),
            'is_active': produit.is_active
        }
        
        Historique.enregistrer_action(
            type_action='PRODUIT_MODIFIE',
            utilisateur=self.request.user,
            description=f'Modification du produit {produit.nom}',
            objet=produit,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
