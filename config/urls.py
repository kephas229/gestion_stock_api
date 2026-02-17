"""
Configuration des URLs principales du projet
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

from apps.authentication.views import UserViewSet, CustomTokenObtainPairView
from apps.magasins.views import MagasinViewSet
from apps.produits.views import CategorieViewSet, ProduitViewSet
from apps.stocks.views import StockViewSet, MouvementStockViewSet
from apps.ventes.views import VenteViewSet
from apps.historique.views import HistoriqueViewSet
from rest_framework_simplejwt.views import TokenRefreshView

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'magasins', MagasinViewSet, basename='magasin')
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'produits', ProduitViewSet, basename='produit')
router.register(r'stocks', StockViewSet, basename='stock')
router.register(r'mouvements-stock', MouvementStockViewSet, basename='mouvement-stock')
router.register(r'ventes', VenteViewSet, basename='vente')
router.register(r'historique', HistoriqueViewSet, basename='historique')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication endpoints
    path('api/v1/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('api/v1/', include(router.urls)),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
