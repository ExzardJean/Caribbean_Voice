#!/bin/sh
set -e

echo "=== [1/4] Application des migrations Django ==="
python manage.py migrate --noinput

echo "=== [2/4] Nettoyage du dossier static collecté ==="
rm -rf /app/staticfiles/

echo "=== [3/4] Collecte des fichiers statiques Django ==="
python manage.py collectstatic --noinput

echo "=== [4/4] Lancement Gunicorn ==="
exec gunicorn caribbean_stock.wsgi:application --bind 0.0.0.0:8000
