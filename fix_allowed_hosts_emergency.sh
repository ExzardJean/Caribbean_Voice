#!/bin/bash

# 🚨 Script d'urgence pour résoudre le problème ALLOWED_HOSTS
# Ce script active temporairement la désactivation des vérifications d'hôtes

echo "🚨 Activation du mode urgence ALLOWED_HOSTS..."

# Modifier render.yaml pour désactiver temporairement les vérifications
sed -i 's/DISABLE_HOST_CHECK.*value: "False"/DISABLE_HOST_CHECK\n        value: "True"/' render.yaml

echo "✅ Configuration d'urgence activée dans render.yaml"
echo "📝 Changements apportés:"
grep -A 1 "DISABLE_HOST_CHECK" render.yaml

echo ""
echo "🔄 Pour appliquer les changements:"
echo "1. git add render.yaml"
echo "2. git commit -m 'Emergency: Disable host check temporarily'"
echo "3. git push origin main"
echo ""
echo "⚠️  N'oubliez pas de désactiver ce mode une fois le problème résolu!"
echo "⚠️  Ce mode accepte TOUS les hôtes - à utiliser temporairement uniquement!"