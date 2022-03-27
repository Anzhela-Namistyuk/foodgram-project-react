python manage.py migrate --noinput && \
#python manage.py import_ingredients && \
python manage.py loaddata fixtures.json && \
python manage.py collectstatic --no-input && \
gunicorn api_foodgram.wsgi:application --bind 0:8000
