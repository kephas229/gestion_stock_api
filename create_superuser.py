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
