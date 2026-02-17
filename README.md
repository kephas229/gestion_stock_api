# API de Gestion de Stock Multi-Magasins

API REST professionnelle développée avec Django REST Framework pour la gestion de stock de plusieurs magasins avec gestion des rôles (Admin et Gérant).

## 📋 Caractéristiques

### Fonctionnalités Admin
- ✅ Gestion complète des produits (CRUD)
- ✅ Gestion des catégories
- ✅ Gestion des stocks (réapprovisionnement, transferts, ajustements)
- ✅ Gestion des magasins
- ✅ Gestion des utilisateurs (création, rôles, assignation aux magasins)
- ✅ Historique complet de toutes les actions
- ✅ Bilans et statistiques globales

### Fonctionnalités Gérant
- ✅ Consultation des produits de son magasin
- ✅ Statistiques spécifiques à son magasin
- ✅ Effectuer des ventes
- ✅ Annuler des ventes avec justificatif
- ✅ Consulter l'historique de son magasin

### Sécurité
- 🔒 Authentification JWT (JSON Web Tokens)
- 🔒 Permissions granulaires par rôle
- 🔒 Validation des données
- 🔒 Protection CSRF
- 🔒 CORS configuré
- 🔒 Logs des actions sensibles
- 🔒 Historique complet des opérations

## 🚀 Installation

### Prérequis
- Python 3.10 ou supérieur
- PostgreSQL 14 ou supérieur
- pip et virtualenv

### 1. Cloner le projet
```bash
git clone <url-du-repo>
cd gestion_stock_api
```

### 2. Créer un environnement virtuel
```bash
python -m venv venv

# Sur Windows
venv\Scripts\activate

# Sur Linux/Mac
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configuration de la base de données

Créer une base de données PostgreSQL:
```sql
CREATE DATABASE gestion_stock_db;
CREATE USER gestion_stock_user WITH PASSWORD 'votre_mot_de_passe';
ALTER ROLE gestion_stock_user SET client_encoding TO 'utf8';
ALTER ROLE gestion_stock_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE gestion_stock_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE gestion_stock_db TO gestion_stock_user;
```

### 5. Configuration des variables d'environnement

Copier le fichier `.env.example` en `.env`:
```bash
cp .env.example .env
```

Modifier le fichier `.env` avec vos paramètres:
```env
SECRET_KEY=votre-cle-secrete-tres-complexe
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=gestion_stock_db
DB_USER=gestion_stock_user
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

### 6. Appliquer les migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

### 8. Lancer le serveur de développement
```bash
python manage.py runserver
```

L'API sera accessible sur `http://localhost:8000`

## 📚 Documentation de l'API

### Documentation Interactive

Une fois le serveur lancé, accédez à la documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema OpenAPI**: http://localhost:8000/api/schema/

### Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification.

#### Obtenir un token
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
    "email": "admin@example.com",
    "password": "votre_mot_de_passe"
}
```

Réponse:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "email": "admin@example.com",
        "full_name": "Admin Système",
        "role": "ADMIN",
        "role_display": "Administrateur",
        "magasin": null,
        "magasin_nom": null
    }
}
```

#### Utiliser le token

Ajouter le header d'autorisation à toutes les requêtes:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### Rafraîchir le token
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## 🔐 Endpoints Principaux

### Utilisateurs
- `GET /api/v1/users/` - Liste des utilisateurs
- `POST /api/v1/users/` - Créer un utilisateur (Admin)
- `GET /api/v1/users/{id}/` - Détails d'un utilisateur
- `PUT /api/v1/users/{id}/` - Modifier un utilisateur (Admin)
- `DELETE /api/v1/users/{id}/` - Supprimer un utilisateur (Admin)
- `GET /api/v1/users/me/` - Profil de l'utilisateur connecté
- `POST /api/v1/users/change_password/` - Changer son mot de passe
- `POST /api/v1/users/{id}/reset_password/` - Réinitialiser un mot de passe (Admin)

### Magasins
- `GET /api/v1/magasins/` - Liste des magasins
- `POST /api/v1/magasins/` - Créer un magasin (Admin)
- `GET /api/v1/magasins/{id}/` - Détails d'un magasin
- `PUT /api/v1/magasins/{id}/` - Modifier un magasin (Admin)
- `GET /api/v1/magasins/{id}/statistiques/` - Statistiques d'un magasin

### Catégories
- `GET /api/v1/categories/` - Liste des catégories
- `POST /api/v1/categories/` - Créer une catégorie (Admin)
- `GET /api/v1/categories/tree/` - Arborescence des catégories

### Produits
- `GET /api/v1/produits/` - Liste des produits
- `POST /api/v1/produits/` - Créer un produit (Admin)
- `GET /api/v1/produits/{id}/` - Détails d'un produit
- `PUT /api/v1/produits/{id}/` - Modifier un produit (Admin)

### Stocks
- `GET /api/v1/stocks/` - Liste des stocks
- `POST /api/v1/stocks/` - Créer un stock (Admin)
- `POST /api/v1/stocks/reapprovisionner/` - Réapprovisionner (Admin)
- `POST /api/v1/stocks/transferer/` - Transférer entre magasins (Admin)
- `POST /api/v1/stocks/ajuster/` - Ajuster le stock (Admin)

### Ventes
- `GET /api/v1/ventes/` - Liste des ventes
- `POST /api/v1/ventes/` - Créer une vente
- `GET /api/v1/ventes/{id}/` - Détails d'une vente
- `POST /api/v1/ventes/{id}/annuler/` - Annuler une vente
- `GET /api/v1/ventes/statistiques/` - Statistiques des ventes

### Historique
- `GET /api/v1/historique/` - Liste de l'historique

## 📝 Exemples d'utilisation

### Créer un utilisateur gérant
```http
POST /api/v1/users/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "email": "gerant@magasin1.com",
    "password": "MotDePasse123!",
    "password_confirm": "MotDePasse123!",
    "nom": "Dupont",
    "prenom": "Jean",
    "telephone": "+229 12345678",
    "role": "GERANT",
    "magasin": 1
}
```

### Créer une vente
```http
POST /api/v1/ventes/
Authorization: Bearer {gerant_token}
Content-Type: application/json

{
    "magasin": 1,
    "nom_client": "Client Test",
    "telephone_client": "+229 98765432",
    "methode_paiement": "ESPECES",
    "montant_paye": 50000,
    "remise": 0,
    "lignes": [
        {
            "produit": 1,
            "quantite": 2,
            "remise_ligne": 0
        },
        {
            "produit": 2,
            "quantite": 1,
            "remise_ligne": 500
        }
    ]
}
```

### Annuler une vente
```http
POST /api/v1/ventes/1/annuler/
Authorization: Bearer {gerant_token}
Content-Type: application/json

{
    "motif": "Erreur de saisie du client"
}
```

### Réapprovisionner le stock
```http
POST /api/v1/stocks/reapprovisionner/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "produit": 1,
    "magasin": 1,
    "quantite": 100,
    "motif": "Livraison fournisseur",
    "reference_document": "BL-2024-001"
}
```

## 🧪 Tests

Exécuter les tests:
```bash
pytest
```

Avec couverture:
```bash
pytest --cov=apps
```

## 🚀 Déploiement en Production

### 1. Configuration de production

Dans `.env`:
```env
DEBUG=False
SECRET_KEY=une-cle-secrete-tres-longue-et-complexe
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
```

### 2. Collecter les fichiers statiques
```bash
python manage.py collectstatic --no-input
```

### 3. Utiliser Gunicorn
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 4. Configuration Nginx (exemple)
```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location /static/ {
        alias /chemin/vers/staticfiles/;
    }

    location /media/ {
        alias /chemin/vers/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Structure du Projet

```
gestion_stock_api/
├── apps/
│   ├── authentication/     # Gestion des utilisateurs
│   ├── magasins/          # Gestion des magasins
│   ├── produits/          # Gestion des produits et catégories
│   ├── stocks/            # Gestion des stocks
│   ├── ventes/            # Gestion des ventes
│   └── historique/        # Historique des actions
├── config/                # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                  # Fonctions communes
│   ├── permissions.py
│   └── exceptions.py
├── logs/                  # Fichiers de logs
├── media/                 # Fichiers uploadés
├── staticfiles/           # Fichiers statiques
├── manage.py
├── requirements.txt
└── README.md
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez suivre ces étapes:

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout d'une fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.

## 👥 Support

Pour toute question ou assistance, contactez:
- Email: support@example.com
- Documentation: https://docs.example.com

## 🔄 Mises à jour

Vérifier les mises à jour:
```bash
git pull origin main
pip install -r requirements.txt
python manage.py migrate
```

---

Développé avec ❤️ pour la gestion efficace des stocks multi-magasins.
