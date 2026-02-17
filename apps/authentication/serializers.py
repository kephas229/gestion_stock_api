"""
Serializers pour l'authentification et la gestion des utilisateurs
"""
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.authentication.models import User
from apps.magasins.models import Magasin


class MagasinSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple pour le magasin (évite la récursion)"""
    class Meta:
        model = Magasin
        fields = ['id', 'nom', 'code', 'ville']
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les utilisateurs"""
    magasin_details = MagasinSimpleSerializer(source='magasin', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'full_name', 'telephone',
            'role', 'role_display', 'magasin', 'magasin_details',
            'is_active', 'date_joined', 'last_login', 'created_by'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_by']
        extra_kwargs = {
            'magasin': {'required': False}
        }
    
    def validate(self, attrs):
        """Validation personnalisée"""
        role = attrs.get('role')
        magasin = attrs.get('magasin')
        
        # Si le rôle est GERANT, le magasin est obligatoire
        if role == User.GERANT and not magasin:
            raise serializers.ValidationError({
                'magasin': 'Un gérant doit être assigné à un magasin.'
            })
        
        # Si le rôle est ADMIN, pas de magasin
        if role == User.ADMIN and magasin:
            raise serializers.ValidationError({
                'magasin': 'Un administrateur ne peut pas être assigné à un magasin.'
            })
        
        return attrs


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'utilisateurs"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'nom', 'prenom',
            'telephone', 'role', 'magasin'
        ]
        extra_kwargs = {
            'magasin': {'required': False}
        }
    
    def validate(self, attrs):
        """Validation personnalisée"""
        # Vérifier que les mots de passe correspondent
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        
        # Valider le mot de passe avec les validateurs Django
        try:
            validate_password(attrs.get('password'))
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        
        # Validation du rôle et magasin
        role = attrs.get('role')
        magasin = attrs.get('magasin')
        
        if role == User.GERANT and not magasin:
            raise serializers.ValidationError({
                'magasin': 'Un gérant doit être assigné à un magasin.'
            })
        
        if role == User.ADMIN and magasin:
            raise serializers.ValidationError({
                'magasin': 'Un administrateur ne peut pas être assigné à un magasin.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Créer un utilisateur"""
        # Retirer password_confirm et password
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des utilisateurs"""
    class Meta:
        model = User
        fields = ['nom', 'prenom', 'telephone', 'role', 'magasin', 'is_active']
        extra_kwargs = {
            'magasin': {'required': False}
        }
    
    def validate(self, attrs):
        """Validation personnalisée"""
        role = attrs.get('role', self.instance.role)
        magasin = attrs.get('magasin', self.instance.magasin)
        
        if role == User.GERANT and not magasin:
            raise serializers.ValidationError({
                'magasin': 'Un gérant doit être assigné à un magasin.'
            })
        
        if role == User.ADMIN and magasin:
            raise serializers.ValidationError({
                'magasin': 'Un administrateur ne peut pas être assigné à un magasin.'
            })
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validation personnalisée"""
        if attrs.get('new_password') != attrs.get('new_password_confirm'):
            raise serializers.ValidationError({
                'new_password_confirm': 'Les nouveaux mots de passe ne correspondent pas.'
            })
        
        try:
            validate_password(attrs.get('new_password'))
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personnalisé pour JWT avec informations utilisateur"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Ajouter des informations supplémentaires dans la réponse
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': self.user.get_full_name(),
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
            'magasin': self.user.magasin.id if self.user.magasin else None,
            'magasin_nom': self.user.magasin.nom if self.user.magasin else None,
        }
        
        return data
