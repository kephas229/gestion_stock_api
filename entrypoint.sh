#!/bin/bash
set -e

echo "🚀 Démarrage de l'application..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
python << 'EOF'
import os
import sys
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from django.db.utils import OperationalError

max_retries = 30
retry_interval = 2

for attempt in range(max_retries):
    try:
        conn = connections['default']
        conn.ensure_connection()
        print(f"✅ Base de données prête !")
        break
    except OperationalError as e:
        print(f"⏳ Tentative {attempt + 1}/{max_retries} - DB pas encore prête: {e}")
        if attempt < max_retries - 1:
            time.sleep(retry_interval)
        else:
            print("❌ Impossible de se connecter à la base de données")
            sys.exit(1)
EOF

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer un superutilisateur si pas encore existant
echo "👤 Vérification du superutilisateur..."
python << 'EOF'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

if not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser(
        email=admin_email,
        password=admin_password,
        nom="Admin",
        prenom="Principal",
        role=User.ADMIN
    )
    print(f"✅ Superutilisateur '{admin_email}' créé")
else:
    print(f"ℹ️  Superutilisateur '{admin_email}' déjà existant")
EOF


# Démarrer Gunicorn
echo "🌐 Démarrage de Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
