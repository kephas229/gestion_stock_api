"""
Views pour l'authentification et la gestion des utilisateurs
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from apps.authentication.models import User
from apps.authentication.serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, CustomTokenObtainPairSerializer
)
from core.permissions import IsAdmin
from apps.historique.models import Historique


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vue personnalisée pour obtenir le token JWT avec informations utilisateur"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs
    Seuls les admins peuvent créer, modifier et supprimer des utilisateurs
    """
    queryset = User.objects.select_related('magasin', 'created_by').all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'magasin']
    search_fields = ['email', 'nom', 'prenom', 'telephone']
    ordering_fields = ['date_joined', 'nom', 'prenom']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Définir les permissions selon l'action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filtrer les utilisateurs selon le rôle"""
        user = self.request.user
        queryset = super().get_queryset()
        
        # Les gérants ne voient que leur propre profil
        if user.role == 'GERANT':
            return queryset.filter(id=user.id)
        
        # Les admins voient tous les utilisateurs
        return queryset
    
    def perform_create(self, serializer):
        """Créer un utilisateur et enregistrer dans l'historique"""
        user = serializer.save(created_by=self.request.user)
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='UTILISATEUR_CREE',
            utilisateur=self.request.user,
            description=f'Création de l\'utilisateur {user.get_full_name()} ({user.get_role_display()})',
            objet=user,
            donnees_apres={
                'email': user.email,
                'role': user.role,
                'magasin': user.magasin.nom if user.magasin else None
            },
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_update(self, serializer):
        """Mettre à jour un utilisateur et enregistrer dans l'historique"""
        donnees_avant = {
            'nom': serializer.instance.nom,
            'prenom': serializer.instance.prenom,
            'role': serializer.instance.role,
            'magasin': serializer.instance.magasin.nom if serializer.instance.magasin else None,
            'is_active': serializer.instance.is_active
        }
        
        user = serializer.save()
        
        donnees_apres = {
            'nom': user.nom,
            'prenom': user.prenom,
            'role': user.role,
            'magasin': user.magasin.nom if user.magasin else None,
            'is_active': user.is_active
        }
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='UTILISATEUR_MODIFIE',
            utilisateur=self.request.user,
            description=f'Modification de l\'utilisateur {user.get_full_name()}',
            objet=user,
            donnees_avant=donnees_avant,
            donnees_apres=donnees_apres,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
    
    def perform_destroy(self, instance):
        """Supprimer un utilisateur et enregistrer dans l'historique"""
        donnees_avant = {
            'email': instance.email,
            'nom': instance.nom,
            'prenom': instance.prenom,
            'role': instance.role
        }
        
        # Enregistrer dans l'historique avant la suppression
        Historique.enregistrer_action(
            type_action='UTILISATEUR_SUPPRIME',
            utilisateur=self.request.user,
            description=f'Suppression de l\'utilisateur {instance.get_full_name()}',
            donnees_avant=donnees_avant,
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        instance.delete()
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Obtenir les informations de l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Changer le mot de passe de l'utilisateur connecté"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Vérifier l'ancien mot de passe
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {
                    'success': False,
                    'errors': {'old_password': 'Mot de passe incorrect.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Définir le nouveau mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='UTILISATEUR_MODIFIE',
            utilisateur=user,
            description='Changement de mot de passe',
            objet=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {'success': True, 'message': 'Mot de passe changé avec succès.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def reset_password(self, request, pk=None):
        """Réinitialiser le mot de passe d'un utilisateur (Admin seulement)"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {
                    'success': False,
                    'errors': {'new_password': 'Le nouveau mot de passe est obligatoire.'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        # Enregistrer dans l'historique
        Historique.enregistrer_action(
            type_action='UTILISATEUR_MODIFIE',
            utilisateur=request.user,
            description=f'Réinitialisation du mot de passe de {user.get_full_name()}',
            objet=user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {'success': True, 'message': 'Mot de passe réinitialisé avec succès.'},
            status=status.HTTP_200_OK
        )
