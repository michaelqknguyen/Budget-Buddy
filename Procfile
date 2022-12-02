release: python manage.py migrate
web: gunicorn --timeout 120 config.wsgi:application

