"""
Script pour créer des données de test
Exécuter avec: python manage.py shell < create_test_data.py
"""
from django.contrib.auth import get_user_model
from apps.magasins.models import Magasin
from apps.produits.models import Categorie, Produit
from apps.stocks.models import Stock
from decimal import Decimal

User = get_user_model()

print("🚀 Création des données de test...")

# Créer un admin
print("👤 Création de l'admin...")
admin, created = User.objects.get_or_create(
    email='admin@gestionstock.com',
    defaults={
        'nom': 'Admin',
        'prenom': 'Système',
        'role': 'ADMIN',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin.set_password('Admin@123')
    admin.save()
    print("✅ Admin créé: admin@gestionstock.com / Admin@123")
else:
    print("ℹ️ Admin existe déjà")

# Créer des magasins
print("\n🏪 Création des magasins...")
magasins_data = [
    {
        'nom': 'Magasin Cotonou Centre',
        'code': 'CTN001',
        'adresse': '123 Avenue Jean-Paul II',
        'ville': 'Cotonou',
        'telephone': '+229 21 30 40 50'
    },
    {
        'nom': 'Magasin Porto-Novo',
        'code': 'PNV001',
        'adresse': '45 Boulevard de la Marina',
        'ville': 'Porto-Novo',
        'telephone': '+229 20 21 22 23'
    },
    {
        'nom': 'Magasin Parakou',
        'code': 'PRK001',
        'adresse': '78 Route de Tchaourou',
        'ville': 'Parakou',
        'telephone': '+229 23 61 50 40'
    }
]

magasins = []
for mag_data in magasins_data:
    mag, created = Magasin.objects.get_or_create(
        code=mag_data['code'],
        defaults={**mag_data, 'created_by': admin}
    )
    magasins.append(mag)
    if created:
        print(f"✅ Magasin créé: {mag.nom}")
    else:
        print(f"ℹ️ Magasin existe: {mag.nom}")

# Créer des gérants
print("\n👥 Création des gérants...")
gerants_data = [
    {
        'email': 'gerant.cotonou@gestionstock.com',
        'nom': 'Koudjo',
        'prenom': 'Jean',
        'telephone': '+229 97 11 22 33',
        'magasin': magasins[0]
    },
    {
        'email': 'gerant.portonovo@gestionstock.com',
        'nom': 'Ayodele',
        'prenom': 'Marie',
        'telephone': '+229 96 44 55 66',
        'magasin': magasins[1]
    },
    {
        'email': 'gerant.parakou@gestionstock.com',
        'nom': 'Tunde',
        'prenom': 'Paul',
        'telephone': '+229 95 77 88 99',
        'magasin': magasins[2]
    }
]

for gerant_data in gerants_data:
    gerant, created = User.objects.get_or_create(
        email=gerant_data['email'],
        defaults={
            'nom': gerant_data['nom'],
            'prenom': gerant_data['prenom'],
            'telephone': gerant_data['telephone'],
            'role': 'GERANT',
            'magasin': gerant_data['magasin'],
            'created_by': admin
        }
    )
    if created:
        gerant.set_password('Gerant@123')
        gerant.save()
        print(f"✅ Gérant créé: {gerant.email} / Gerant@123 - {gerant_data['magasin'].nom}")
    else:
        print(f"ℹ️ Gérant existe: {gerant.email}")

# Créer des catégories
print("\n📁 Création des catégories...")
categories_data = [
    {'nom': 'Électronique', 'code': 'ELEC'},
    {'nom': 'Informatique', 'code': 'INFO'},
    {'nom': 'Électroménager', 'code': 'ELME'},
    {'nom': 'Téléphonie', 'code': 'TEL'},
    {'nom': 'Accessoires', 'code': 'ACC'}
]

categories = []
for cat_data in categories_data:
    cat, created = Categorie.objects.get_or_create(
        code=cat_data['code'],
        defaults={**cat_data, 'created_by': admin}
    )
    categories.append(cat)
    if created:
        print(f"✅ Catégorie créée: {cat.nom}")

# Créer des produits
print("\n📦 Création des produits...")
produits_data = [
    {
        'nom': 'iPhone 14 Pro',
        'code_barre': '1234567890101',
        'reference': 'IP14PRO',
        'categorie': categories[3],
        'prix_achat': Decimal('450000'),
        'prix_vente': Decimal('550000'),
        'seuil_alerte': 5
    },
    {
        'nom': 'Samsung Galaxy S23',
        'code_barre': '1234567890102',
        'reference': 'SGS23',
        'categorie': categories[3],
        'prix_achat': Decimal('380000'),
        'prix_vente': Decimal('480000'),
        'seuil_alerte': 5
    },
    {
        'nom': 'MacBook Pro 14"',
        'code_barre': '1234567890103',
        'reference': 'MBP14',
        'categorie': categories[1],
        'prix_achat': Decimal('1200000'),
        'prix_vente': Decimal('1500000'),
        'seuil_alerte': 3
    },
    {
        'nom': 'Dell XPS 15',
        'code_barre': '1234567890104',
        'reference': 'DXPS15',
        'categorie': categories[1],
        'prix_achat': Decimal('950000'),
        'prix_vente': Decimal('1200000'),
        'seuil_alerte': 3
    },
    {
        'nom': 'AirPods Pro 2',
        'code_barre': '1234567890105',
        'reference': 'APP2',
        'categorie': categories[4],
        'prix_achat': Decimal('120000'),
        'prix_vente': Decimal('160000'),
        'seuil_alerte': 10
    },
    {
        'nom': 'Samsung TV 55" QLED',
        'code_barre': '1234567890106',
        'reference': 'STV55Q',
        'categorie': categories[2],
        'prix_achat': Decimal('350000'),
        'prix_vente': Decimal('450000'),
        'seuil_alerte': 5
    },
    {
        'nom': 'Réfrigérateur LG 350L',
        'code_barre': '1234567890107',
        'reference': 'LGR350',
        'categorie': categories[2],
        'prix_achat': Decimal('280000'),
        'prix_vente': Decimal('350000'),
        'seuil_alerte': 3
    },
    {
        'nom': 'Machine à laver Samsung 8kg',
        'code_barre': '1234567890108',
        'reference': 'SML8',
        'categorie': categories[2],
        'prix_achat': Decimal('200000'),
        'prix_vente': Decimal('260000'),
        'seuil_alerte': 3
    }
]

produits = []
for prod_data in produits_data:
    prod, created = Produit.objects.get_or_create(
        reference=prod_data['reference'],
        defaults={**prod_data, 'created_by': admin}
    )
    produits.append(prod)
    if created:
        print(f"✅ Produit créé: {prod.nom}")

# Créer des stocks pour chaque produit dans chaque magasin
print("\n📊 Création des stocks...")
for produit in produits:
    for magasin in magasins:
        stock, created = Stock.objects.get_or_create(
            produit=produit,
            magasin=magasin,
            defaults={'quantite': 20}  # Stock initial de 20 unités
        )
        if created:
            print(f"✅ Stock créé: {produit.nom} dans {magasin.nom} - 20 unités")

print("\n✨ Données de test créées avec succès!")
print("\n📝 Comptes créés:")
print("- Admin: admin@gestionstock.com / Admin@123")
print("- Gérant Cotonou: gerant.cotonou@gestionstock.com / Gerant@123")
print("- Gérant Porto-Novo: gerant.portonovo@gestionstock.com / Gerant@123")
print("- Gérant Parakou: gerant.parakou@gestionstock.com / Gerant@123")
print("\n🎉 Vous pouvez maintenant tester l'API!")
