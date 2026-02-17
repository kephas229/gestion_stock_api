"""
Views pour la gestion de l'historique
"""
from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from apps.historique.models import Historique
from apps.historique.serializers import HistoriqueSerializer
from core.permissions import IsAdmin, IsAdminOrGerant


class HistoriqueViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour consulter l'historique des actions
    Admin: Accès complet à tout l'historique
    Gérant: Accès à l'historique de son magasin uniquement
    Lecture seule pour tous
    """
    queryset = Historique.objects.select_related('utilisateur', 'magasin').all()
    serializer_class = HistoriqueSerializer
    permission_classes = [IsAdminOrGerant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_action', 'utilisateur', 'magasin']
    search_fields = ['description']
    ordering_fields = ['date_action']
    ordering = ['-date_action']
    
    def get_queryset(self):
        """Filtrer l'historique selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que l'historique de leur magasin
        if user.role == 'GERANT':
            queryset = queryset.filter(magasin=user.magasin)
        
        # Filtrer par période si demandé
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(date_action__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_action__lte=date_fin)
        
        return queryset
