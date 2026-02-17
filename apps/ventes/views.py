"""
Views pour la gestion des ventes
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db import transaction
from django.utils import timezone

from apps.ventes.models import Vente, LigneVente
from apps.ventes.serializers import (
    VenteSerializer, VenteCreateSerializer, AnnulationVenteSerializer
)
from core.permissions import IsAdminOrGerant, CanManageVente
from apps.historique.models import Historique
from apps.stocks.models import Stock, MouvementStock
from core.exceptions import VenteAnnuleeException


class VenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des ventes
    Admin: CRUD complet sur toutes les ventes
    Gérant: Création et lecture des ventes de son magasin, annulation avec justificatif
    """
    queryset = Vente.objects.select_related('magasin', 'vendeur').prefetch_related('lignes').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['statut', 'magasin', 'vendeur', 'est_annulee', 'methode_paiement']
    search_fields = ['numero_vente', 'nom_client', 'telephone_client']
    ordering_fields = ['date_vente', 'montant_total']
    ordering = ['-date_vente']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return VenteCreateSerializer
        elif self.action == 'annuler':
            return AnnulationVenteSerializer
        return VenteSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'annuler']:
            return [IsAdminOrGerant()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [CanManageVente()]
        return [IsAdminOrGerant()]
    
    def get_queryset(self):
        """Filtrer les ventes selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que les ventes de leur magasin
        if user.role == 'GERANT':
            queryset = queryset.filter(magasin=user.magasin)
        
        # Filtrer par période si demandé
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date_vente__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_vente__lte=date_fin)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Créer une vente"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        vente = serializer.save()
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='VENTE_EFFECTUEE',
            utilisateur=request.user,
            magasin=vente.magasin,
            description=f'Vente #{vente.numero_vente} - Montant: {vente.montant_total} FCFA',
            objet=vente,
            donnees_apres={
                'numero_vente': vente.numero_vente,
                'montant_total': str(vente.montant_total),
                'nombre_articles': vente.lignes.count()
            },
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {
                'success': True,
                'message': 'Vente créée avec succès.',
                'data': VenteSerializer(vente).data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def annuler(self, request, pk=None):
        """Annuler une vente avec justificatif"""
        vente = self.get_object()
        
        # Vérifier que la vente n'est pas déjà annulée
        if vente.est_annulee:
            raise VenteAnnuleeException('Cette vente est déjà annulée.')
        
        serializer = AnnulationVenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        motif = serializer.validated_data['motif']
        
        # Restaurer les stocks
        for ligne in vente.lignes.all():
            try:
                stock = Stock.objects.get(
                    produit=ligne.produit,
                    magasin=vente.magasin
                )
                quantite_avant = stock.quantite
                stock.quantite += ligne.quantite
                stock.save()
                
                # Enregistrer le mouvement de retour
                MouvementStock.objects.create(
                    stock=stock,
                    type_mouvement='RETOUR',
                    quantite=ligne.quantite,
                    quantite_avant=quantite_avant,
                    quantite_apres=stock.quantite,
                    vente=vente,
                    motif=f'Annulation vente #{vente.numero_vente}: {motif}',
                    effectue_par=request.user
                )
            except Stock.DoesNotExist:
                # Si le stock n'existe pas, le créer
                stock = Stock.objects.create(
                    produit=ligne.produit,
                    magasin=vente.magasin,
                    quantite=ligne.quantite
                )
                
                MouvementStock.objects.create(
                    stock=stock,
                    type_mouvement='RETOUR',
                    quantite=ligne.quantite,
                    quantite_avant=0,
                    quantite_apres=ligne.quantite,
                    vente=vente,
                    motif=f'Annulation vente #{vente.numero_vente}: {motif}',
                    effectue_par=request.user
                )
        
        # Annuler la vente
        vente.annuler(request.user, motif)
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='VENTE_ANNULEE',
            utilisateur=request.user,
            magasin=vente.magasin,
            description=f'Annulation de la vente #{vente.numero_vente}',
            objet=vente,
            donnees_avant={'statut': 'VALIDEE'},
            donnees_apres={'statut': 'ANNULEE', 'motif': motif},
            metadata={'montant': str(vente.montant_total)},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {
                'success': True,
                'message': 'Vente annulée avec succès.',
                'data': VenteSerializer(vente).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Obtenir les statistiques des ventes"""
        user = request.user
        queryset = self.get_queryset().filter(statut='VALIDEE', est_annulee=False)
        
        # Calculer les statistiques
        from django.db.models import Sum, Count, Avg
        
        stats = queryset.aggregate(
            nombre_ventes=Count('id'),
            montant_total=Sum('montant_total'),
            montant_moyen=Avg('montant_total')
        )
        
        # Ventes du jour
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ventes_jour = queryset.filter(date_vente__gte=today_start).aggregate(
            nombre=Count('id'),
            montant=Sum('montant_total')
        )
        
        # Ventes du mois
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ventes_mois = queryset.filter(date_vente__gte=month_start).aggregate(
            nombre=Count('id'),
            montant=Sum('montant_total')
        )
        
        return Response({
            'total': {
                'nombre_ventes': stats['nombre_ventes'] or 0,
                'montant_total': stats['montant_total'] or 0,
                'montant_moyen': stats['montant_moyen'] or 0
            },
            'aujourd_hui': {
                'nombre_ventes': ventes_jour['nombre'] or 0,
                'montant': ventes_jour['montant'] or 0
            },
            'ce_mois': {
                'nombre_ventes': ventes_mois['nombre'] or 0,
                'montant': ventes_mois['montant'] or 0
            }
        })
