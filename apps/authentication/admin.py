"""
Configuration de l'interface d'administration pour les utilisateurs
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.authentication.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'get_full_name', 'role', 'magasin', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'magasin']
    search_fields = ['email', 'nom', 'prenom']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone')}),
        ('Rôle et magasin', {'fields': ('role', 'magasin')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nom', 'prenom', 'password1', 'password2', 'role', 'magasin'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']
