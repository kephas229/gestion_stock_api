# Guide de Démarrage Rapide - API Gestion de Stock

## Installation Express

### 1. Installation rapide (Linux/Mac)
```bash
# Cloner le projet
git clone <url-repo>
cd gestion_stock_api

# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres

# Créer la base de données PostgreSQL
createdb gestion_stock_db

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### 2. Installation rapide (Windows)
```cmd
git clone <url-repo>
cd gestion_stock_api

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

copy .env.example .env
REM Éditer .env avec vos paramètres

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
ndkVersion = "26.1.10909125"
crée une application flutter de gestion stock de produitts de plusieurs magasins avec deux rôles utilisateurs : gerant et admin. l'admin à une vu globale de tout l'application à savoir :  dashboard de statistique par magasin ,gestion de produit, de categorie, de stock, de magasin, des utlisateurs et leurs assignés des magasins, bilan  et historique. le gerant voit les statistiques de son magasin sur son dashboards, consulte l'ensemble des produits existants dans son magasin, effectuer une vente ou annuler une vente. utilise un design moderne parfait et professionnel sans backend, j'ai developpé mon propre backend je veux juste l'UI de l'application flutter et le connecter à mon backend
## Premiers Pas

### 1. Se connecter
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "votre_email@example.com",
    "password": "votre_mot_de_passe"
  }'
```

### 2. Créer un magasin (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/magasins/ \
  -H "Authorization: Bearer {votre_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Magasin Principal",
    "code": "MAG001",
    "adresse": "123 Rue de la Liberté",
    "ville": "Cotonou",
    "pays": "Bénin",
    "telephone": "+229 12345678"
  }'
```

### 3. Créer une catégorie (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/categories/ \
  -H "Authorization: Bearer {votre_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Électronique",
    "code": "ELEC",
    "description": "Produits électroniques"
  }'
```

### 4. Créer un produit (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/produits/ \
  -H "Authorization: Bearer {votre_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Smartphone XYZ",
    "code_barre": "1234567890123",
    "reference": "PROD001",
    "categorie": 1,
    "prix_achat": 150000,
    "prix_vente": 200000,
    "unite_mesure": "PIECE",
    "seuil_alerte": 5,
    "stock_minimal": 3,
    "stock_maximal": 100
  }'
```

### 5. Créer un gérant (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer {votre_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "gerant@magasin.com",
    "password": "MotDePasse123!",
    "password_confirm": "MotDePasse123!",
    "nom": "Dupont",
    "prenom": "Marie",
    "telephone": "+229 98765432",
    "role": "GERANT",
    "magasin": 1
  }'
```

### 6. Réapprovisionner le stock (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/stocks/reapprovisionner/ \
  -H "Authorization: Bearer {votre_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "produit": 1,
    "magasin": 1,
    "quantite": 50,
    "motif": "Réapprovisionnement initial"
  }'
```

### 7. Effectuer une vente (Gérant)
```bash
curl -X POST http://localhost:8000/api/v1/ventes/ \
  -H "Authorization: Bearer {token_gerant}" \
  -H "Content-Type: application/json" \
  -d '{
    "magasin": 1,
    "nom_client": "Client Test",
    "methode_paiement": "ESPECES",
    "montant_paye": 200000,
    "remise": 0,
    "lignes": [
      {
        "produit": 1,
        "quantite": 1,
        "remise_ligne": 0
      }
    ]
  }'
```

## Scénario Complet

### Scénario: Gestion d'une journée type

1. **Admin crée l'infrastructure**
   - Créer 2 magasins
   - Créer 3 catégories
   - Créer 10 produits
   - Créer 2 gérants (un par magasin)
   - Réapprovisionner les stocks

2. **Gérant du Magasin 1**
   - Se connecte
   - Consulte les produits disponibles
   - Effectue 5 ventes
   - Annule 1 vente (erreur de saisie)
   - Consulte les statistiques

3. **Admin en fin de journée**
   - Consulte l'historique global
   - Vérifie les stocks en alerte
   - Transfère du stock entre magasins
   - Génère les bilans

## Commandes Utiles

### Gestion de la base de données
```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Réinitialiser la base de données
python manage.py flush

# Créer des données de test
python manage.py shell
```

### Gestion des utilisateurs
```bash
# Créer un superutilisateur
python manage.py createsuperuser

# Changer le mot de passe d'un utilisateur
python manage.py changepassword email@example.com
```

### Tests
```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=apps --cov-report=html

# Tests d'une app spécifique
pytest apps/ventes/
```

### Production
```bash
# Collecter les fichiers statiques
python manage.py collectstatic

# Vérifier les problèmes de déploiement
python manage.py check --deploy

# Lancer avec Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## Résolution des Problèmes Courants

### Erreur de connexion à la base de données
- Vérifier que PostgreSQL est démarré
- Vérifier les paramètres dans `.env`
- Vérifier que la base de données existe

### Erreur d'import
```bash
# Réinstaller les dépendances
pip install -r requirements.txt --upgrade
```

### Erreur de migration
```bash
# Supprimer les migrations et recommencer
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
python manage.py makemigrations
python manage.py migrate
```

## Variables d'Environnement Importantes

```env
# Développement
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Production
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# JWT (optionnel)
JWT_ACCESS_TOKEN_LIFETIME=60  # en minutes
JWT_REFRESH_TOKEN_LIFETIME=1440  # en minutes
```

## Codes d'Erreur Courants

- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Token manquant ou invalide
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource introuvable
- `500 Internal Server Error`: Erreur serveur

## Support et Documentation

- Documentation API: http://localhost:8000/api/docs/
- Admin Django: http://localhost:8000/admin/
- README complet: README.md
