"""
Gestionnaire d'exceptions personnalisé pour l'API
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour fournir des réponses d'erreur cohérentes
    """
    # Appeler le gestionnaire d'exceptions par défaut de DRF
    response = exception_handler(exc, context)
    
    # Gérer les ValidationError de Django
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            errors = exc.message_dict
        elif hasattr(exc, 'messages'):
            errors = {'detail': exc.messages}
        else:
            errors = {'detail': str(exc)}
        
        return Response(
            {
                'success': False,
                'errors': errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Gérer les Http404
    if isinstance(exc, Http404):
        return Response(
            {
                'success': False,
                'errors': {'detail': 'Ressource non trouvée.'}
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Si on a une réponse du gestionnaire par défaut
    if response is not None:
        # Formater la réponse de manière cohérente
        custom_response_data = {
            'success': False,
            'errors': {}
        }
        
        # Si les données sont un dictionnaire
        if isinstance(response.data, dict):
            custom_response_data['errors'] = response.data
        # Si c'est une liste
        elif isinstance(response.data, list):
            custom_response_data['errors'] = {'detail': response.data}
        # Sinon, traiter comme une chaîne
        else:
            custom_response_data['errors'] = {'detail': str(response.data)}
        
        response.data = custom_response_data
    
    return response


class StockInsuffisantException(ValidationError):
    """Exception levée lorsque le stock est insuffisant"""
    default_detail = "Stock insuffisant pour effectuer cette opération."
    default_code = 'stock_insuffisant'


class VenteAnnuleeException(ValidationError):
    """Exception levée lors de tentative d'opération sur une vente annulée"""
    default_detail = "Cette vente a été annulée."
    default_code = 'vente_annulee'


class MagasinNonAutoriseException(ValidationError):
    """Exception levée lorsqu'un gérant tente d'accéder à un autre magasin"""
    default_detail = "Vous n'avez pas accès à ce magasin."
    default_code = 'magasin_non_autorise'
