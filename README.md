# Caribbean Voice Stock - Système de Gestion de Stock

## 📋 Description

Système moderne de gestion de stock développé avec **Django 5.2.8**, **HTML**, **CSS** et **Tailwind CSS** (sans React), adapté aux besoins spécifiques de distribution de produits électroniques et solaires.

## 🎨 Design

Interface inspirée du thème **Velonic** avec :
- Sidebar bleu foncé (slate-900)
- Cartes KPI colorées (rose, violet, cyan, vert)
- Design moderne et responsive
- Interface 100% en français

## 🚀 Fonctionnalités

### Dashboard Principal
- ✅ Cartes KPI avec statistiques en temps réel
- ✅ Ventes des 30 derniers jours
- ✅ Chiffre d'affaires (admin/manager uniquement)
- ✅ Nombre de clients
- ✅ Nombre de produits
- ✅ Alertes de stock en temps réel
- ✅ Produits les plus vendus
- ✅ Statistiques rapides

### Gestion des Produits
- ✅ Vue en grille moderne
- ✅ Recherche par nom, SKU, code-barres
- ✅ Filtrage par catégorie
- ✅ Badges de statut (En stock, Stock faible, Rupture)
- ✅ Catégories colorées
- ✅ Prix et stock visibles
- ✅ Support pour produits électroniques et solaires

### Gestion des Ventes
- ✅ Liste des commandes
- ✅ Filtrage par statut
- ✅ Suivi des paiements
- ✅ Point de Vente (POS)

### Gestion des Clients
- ✅ Clients particuliers et entreprises
- ✅ Historique des achats
- ✅ Points de fidélité

### Gestion des Fournisseurs
- ✅ Informations de contact
- ✅ Évaluation des fournisseurs
- ✅ Historique des commandes

### Alertes de Stock
- ✅ Alertes automatiques (stock faible, rupture, surstock)
- ✅ Notifications en temps réel
- ✅ Badge de compteur dans la navigation

### Rapports
- ✅ Rapports de ventes
- ✅ Rapports de stock
- ✅ Analytics (admin/manager uniquement)

### Gestion des Rôles
- ✅ **Admin** : Accès complet
- ✅ **Manager** : Accès étendu (pas de CA global)
- ✅ **Vendeur** : Accès limité (produits, ventes, clients)

## 🗄️ Base de Données

### Modèles Django
- **User** : Utilisateurs avec rôles (admin, manager, vendeur)
- **Category** : Catégories et sous-catégories
- **Product** : Produits avec spécifications électroniques/solaires
- **Supplier** : Fournisseurs
- **Customer** : Clients (particuliers/entreprises)
- **SalesOrder** : Commandes de vente
- **SalesOrderItem** : Articles de commande
- **StockMovement** : Mouvements de stock
- **StockAlert** : Alertes automatiques

## 🛠️ Technologies

- **Backend** : Django 5.2.8
- **Frontend** : HTML5, CSS3, Tailwind CSS (CDN)
- **Base de données** : SQLite (dev) / MySQL/PostgreSQL (production)
- **Langue** : Français
- **Timezone** : America/Port-au-Prince (Haïti)

## 📦 Installation

### Prérequis
- Python 3.11+
- pip

### Installation
```bash
# Cloner le projet
cd /home/ubuntu/caribbean_stock

# Installer Django
pip install django

# Appliquer les migrations
python3.11 manage.py migrate

# Créer un super-utilisateur
python3.11 manage.py createsuperuser

# Charger les données de test
python3.11 seed_data.py

# Lancer le serveur
python3.11 manage.py runserver 0.0.0.0:8000
```

## 🔐 Accès

### Dashboard Principal
- URL : `http://localhost:8000/`
- Connexion requise

### Administration Django
- URL : `http://localhost:8000/admin/`
- Accès : Administrateurs uniquement

### Compte de Test
- **Utilisateur** : `admin`
- **Mot de passe** : `admin123`
- **Rôle** : Administrateur
- **Nom** : Jean Abellard Exzard

## 📊 Données de Test

### Catégories (4)
- Systèmes Solaires
- Ordinateurs
- Électronique
- Électroménager

### Produits (8)
- Panneau Solaire 300W (45 unités)
- Batterie Solaire 200Ah (30 unités)
- Laptop Dell Inspiron 15 (12 unités)
- Desktop HP ProDesk (8 unités)
- Samsung Galaxy A54 (25 unités)
- iPhone 13 (15 unités)
- Réfrigérateur LG 450L (6 unités)
- Climatiseur Samsung 12000 BTU (10 unités)

### Clients (3)
- Pierre Duval (Particulier)
- Marie Joseph (Particulier)
- Tech Solutions Haiti (Entreprise)

### Fournisseurs (2)
- Solar Tech Haiti
- Tech Import SA

### Ventes (2)
- SO-20251116-001 : Panneau Solaire (220 HTG)
- SO-20251116-002 : Laptop Dell (650 HTG)

## 🎯 Pages Disponibles

1. **Dashboard** (`/`) - Tableau de bord principal
2. **Produits** (`/products/`) - Gestion des produits
3. **Catégories** (`/categories/`) - Gestion des catégories (admin/manager)
4. **Ventes** (`/sales/`) - Liste des ventes
5. **POS** (`/pos/`) - Point de Vente
6. **Clients** (`/customers/`) - Gestion des clients
7. **Fournisseurs** (`/suppliers/`) - Gestion des fournisseurs (admin/manager)
8. **Alertes** (`/alerts/`) - Alertes de stock
9. **Rapports** (`/reports/`) - Rapports et analytics (admin/manager)

## 🎨 Personnalisation

### Couleurs Tailwind
- **Primary** : #2563EB (Bleu)
- **Secondary** : #64748B (Gris)
- **Success** : #10B981 (Vert)
- **Danger** : #EF4444 (Rouge)
- **Warning** : #F59E0B (Orange)
- **Info** : #06B6D4 (Cyan)

### Sidebar
- Couleur : slate-900
- Logo : Caribbean Voice
- Navigation adaptée aux rôles

## 📝 Notes Importantes

1. **Pas de React** : L'application utilise uniquement Django, HTML et Tailwind CSS
2. **Interface en français** : Tous les textes sont en français
3. **Responsive** : Design adaptatif pour mobile, tablette et desktop
4. **Permissions** : Navigation filtrée selon le rôle de l'utilisateur
5. **Sécurité** : CSRF protection activée

## 🔧 Configuration

### Settings Django
- `DEBUG = True` (développement uniquement)
- `LANGUAGE_CODE = 'fr-fr'`
- `TIME_ZONE = 'America/Port-au-Prince'`
- `AUTH_USER_MODEL = 'inventory.User'`
- `CSRF_TRUSTED_ORIGINS` configuré

## 📈 Prochaines Étapes

- [ ] Ajouter les formulaires de création/modification
- [ ] Implémenter le POS complet
- [ ] Ajouter les graphiques de ventes
- [ ] Implémenter l'export PDF des rapports
- [ ] Ajouter la gestion des images produits
- [ ] Implémenter le multilingue (FR/EN)
- [ ] Ajouter le changement de thème (clair/sombre)
- [ ] Implémenter les notifications en temps réel
- [ ] Ajouter l'historique des modifications
- [ ] Déploiement en production

## 👨‍💻 Développement

### Structure du Projet
```
caribbean_stock/
├── caribbean_stock/        # Configuration Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── inventory/              # Application principale
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues Django
│   ├── admin.py           # Configuration Admin
│   └── migrations/        # Migrations de base de données
├── templates/             # Templates HTML
│   ├── base.html
│   ├── dashboard_base.html
│   ├── login.html
│   ├── dashboard.html
│   └── products.html
├── static/                # Fichiers statiques
├── media/                 # Fichiers uploadés
└── seed_data.py          # Script de données de test
```

## 📧 Support

Pour toute question ou assistance, contactez l'administrateur système.

---

**Caribbean Voice Stock** - Système de Gestion de Stock Moderne
© 2024 Caribbean Voice. Tous droits réservés.
