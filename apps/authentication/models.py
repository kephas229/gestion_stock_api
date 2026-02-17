"""
Modèle User personnalisé pour la gestion des utilisateurs
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager personnalisé pour le modèle User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Créer et sauvegarder un utilisateur standard"""
        if not email:
            raise ValueError(_('L\'email est obligatoire'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Créer et sauvegarder un superutilisateur"""
        extra_fields.setdefault('role', User.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('role') != User.ADMIN:
            raise ValueError(_('Le superutilisateur doit avoir le rôle ADMIN'))
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle User personnalisé avec deux rôles: Admin et Gérant
    """
    # Choix de rôles
    ADMIN = 'ADMIN'
    GERANT = 'GERANT'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrateur'),
        (GERANT, 'Gérant'),
    ]
    
    # Champs de base
    email = models.EmailField(_('email'), unique=True, db_index=True)
    nom = models.CharField(_('nom'), max_length=100)
    prenom = models.CharField(_('prénom'), max_length=100)
    telephone = models.CharField(_('téléphone'), max_length=20, blank=True)
    
    # Rôle et magasin
    role = models.CharField(
        _('rôle'),
        max_length=10,
        choices=ROLE_CHOICES,
        default=GERANT
    )
    magasin = models.ForeignKey(
        'magasins.Magasin',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name=_('magasin assigné')
    )
    
    # Statuts
    is_active = models.BooleanField(_('actif'), default=True)
    is_staff = models.BooleanField(_('membre du staff'), default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(_('date d\'inscription'), auto_now_add=True)
    updated_at = models.DateTimeField(_('dernière modification'), auto_now=True)
    last_login = models.DateTimeField(_('dernière connexion'), null=True, blank=True)
    
    # Utilisateur qui a créé ce compte
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_created',
        verbose_name=_('créé par')
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.prenom} {self.nom}".strip()
    
    def get_short_name(self):
        """Retourne le prénom de l'utilisateur"""
        return self.prenom
    
    @property
    def is_admin(self):
        """Vérifie si l'utilisateur est un admin"""
        return self.role == self.ADMIN
    
    @property
    def is_gerant(self):
        """Vérifie si l'utilisateur est un gérant"""
        return self.role == self.GERANT
    
    def save(self, *args, **kwargs):
        """Override save pour des validations supplémentaires"""
        # Si c'est un admin, pas besoin de magasin
        if self.role == self.ADMIN:
            self.magasin = None
            self.is_staff = True
        # Si c'est un gérant, le magasin est obligatoire
        elif self.role == self.GERANT and not self.magasin:
            raise ValueError(_('Un gérant doit être assigné à un magasin'))
        
        super().save(*args, **kwargs)
