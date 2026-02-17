"""
Permissions personnalisées pour l'API
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission qui permet l'accès uniquement aux administrateurs
    """
    message = "Vous devez être administrateur pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'ADMIN'
        )


class IsGerant(permissions.BasePermission):
    """
    Permission qui permet l'accès uniquement aux gérants
    """
    message = "Vous devez être gérant pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'GERANT'
        )


class IsAdminOrGerant(permissions.BasePermission):
    """
    Permission qui permet l'accès aux administrateurs et aux gérants
    """
    message = "Vous devez être administrateur ou gérant pour accéder à cette ressource."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['ADMIN', 'GERANT']
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission qui permet la modification uniquement aux administrateurs,
    mais la lecture à tous les utilisateurs authentifiés
    """
    message = "Seuls les administrateurs peuvent modifier cette ressource."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modification uniquement pour les admins
        return request.user.role == 'ADMIN'


class IsOwnerMagasin(permissions.BasePermission):
    """
    Permission qui vérifie que le gérant accède uniquement aux données de son magasin
    """
    message = "Vous ne pouvez accéder qu'aux données de votre magasin."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Les admins ont accès à tout
        if request.user.role == 'ADMIN':
            return True
        
        # Les gérants n'ont accès qu'à leur magasin
        if request.user.role == 'GERANT':
            # Vérifie si l'objet a un attribut magasin
            if hasattr(obj, 'magasin'):
                return obj.magasin == request.user.magasin
            # Si l'objet est un magasin lui-même
            if obj.__class__.__name__ == 'Magasin':
                return obj == request.user.magasin
        
        return False


class CanManageStock(permissions.BasePermission):
    """
    Permission pour gérer le stock (Admin ou Gérant de son magasin)
    """
    message = "Vous n'avez pas la permission de gérer ce stock."
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin peut tout gérer
        if request.user.role == 'ADMIN':
            return True
        
        # Gérant peut gérer uniquement le stock de son magasin
        if request.user.role == 'GERANT':
            return obj.magasin == request.user.magasin
        
        return False


class CanManageVente(permissions.BasePermission):
    """
    Permission pour gérer les ventes (Admin ou Gérant de son magasin)
    """
    message = "Vous n'avez pas la permission de gérer cette vente."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin peut tout gérer
        if request.user.role == 'ADMIN':
            return True
        
        # Gérant peut gérer uniquement les ventes de son magasin
        if request.user.role == 'GERANT':
            return obj.magasin == request.user.magasin
        
        return False
