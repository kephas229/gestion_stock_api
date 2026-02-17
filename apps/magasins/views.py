"""
Views pour la gestion des magasins
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Sum, F, Q, DecimalField
from django.utils import timezone
from datetime import timedelta

from apps.magasins.models import Magasin
from apps.magasins.serializers import (
    MagasinSerializer, MagasinCreateSerializer, MagasinStatistiquesSerializer
)
from core.permissions import IsAdmin, IsAdminOrReadOnly, IsOwnerMagasin
from apps.historique.models import Historique


class MagasinViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des magasins
    Admin: CRUD complet
    Gérant: Lecture seule de son magasin
    """
    queryset = Magasin.objects.prefetch_related('utilisateurs', 'stocks').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'ville', 'pays']
    search_fields = ['nom', 'code', 'adresse', 'ville']
    ordering_fields = ['nom', 'created_at', 'ville']
    ordering = ['nom']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return MagasinCreateSerializer
        elif self.action == 'statistiques':
            return MagasinStatistiquesSerializer
        return MagasinSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        elif self.action in ['retrieve', 'list']:
            return [IsAdminOrReadOnly()]
        return [IsOwnerMagasin()]
    
    def get_queryset(self):
        """Filtrer les magasins selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que leur magasin
        if user.role == 'GERANT':
            return queryset.filter(id=user.magasin.id)
        
        # Les admins voient tous les magasins
        return queryset
    
    def perform_create(self, serializer):
        """Créer un magasin et enregistrer dans l'historique"""
        magasin = serializer.save(created_by=self.request.user)
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='MAGASIN_CREE',
            utilisateur=self.request.user,
            description=f'Création du magasin {magasin.nom} ({magasin.code})',
            magasin=magasin,
            objet=magasin,
            donnees_apres={
                'nom': magasin.nom,
                'code': magasin.code,
                'ville': magasin.ville
            },
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        """Mettre à jour un magasin et enregistrer dans l'historique"""
        donnees_avant = {
            'nom': serializer.instance.nom,
            'code': serializer.instance.code,
            'ville': serializer.instance.ville,
            'is_active': serializer.instance.is_active
        }
        
        magasin = serializer.save()
        
        donnees_apres = {
            'nom': magasin.nom,
            'code': magasin.code,
            'ville': magasin.ville,
            'is_active': magasin.is_active
        }
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='MAGASIN_MODIFIE',
            utilisateur=self.request.user,
            description=f'Modification du magasin {magasin.nom}',
            magasin=magasin,
            objet=magasin,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Obtenir les statistiques d'un magasin"""
        magasin = self.get_object()
        
        # Calculer les statistiques
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Ventes
        ventes = magasin.ventes.filter(statut='VALIDEE')
        ventes_annulees = magasin.ventes.filter(est_annulee=True)
        
        montant_ventes_total = ventes.aggregate(
            total=Sum('montant_total')
        )['total'] or 0
        
        montant_ventes_jour = ventes.filter(
            date_vente__gte=today_start
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        
        montant_ventes_mois = ventes.filter(
            date_vente__gte=month_start
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        
        # Stocks
        stocks = magasin.stocks.select_related('produit')
        nombre_produits = stocks.filter(quantite__gt=0).count()
        produits_en_alerte = stocks.filter(
            quantite__lte=F('produit__seuil_alerte')
        ).count()
        
        valeur_stock_total = stocks.aggregate(
            total=Sum(F('quantite') * F('produit__prix_vente'), output_field=DecimalField())
        )['total'] or 0
        
        data = {
            'magasin': magasin,
            'nombre_produits': nombre_produits,
            'nombre_ventes': ventes.count(),
            'montant_ventes_total': montant_ventes_total,
            'montant_ventes_jour': montant_ventes_jour,
            'montant_ventes_mois': montant_ventes_mois,
            'nombre_ventes_annulees': ventes_annulees.count(),
            'produits_en_alerte': produits_en_alerte,
            'valeur_stock_total': valeur_stock_total,
        }
        
        serializer = MagasinStatistiquesSerializer(data)
        return Response(serializer.data)
