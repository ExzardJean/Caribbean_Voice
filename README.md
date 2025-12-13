# Caribbean Voice Stock - Système de Gestion de Stock

## 🚀 Fonctionnalités

### Dashboard Principal
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
