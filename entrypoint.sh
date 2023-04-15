python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py loaddata faces documents avatars related
python manage.py createsuperuser_if_none_exists --user=admin --password=admin
gunicorn face_search.wsgi:application --bind 0.0.0.0:8000