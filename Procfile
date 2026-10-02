release: python manage.py migrate --noinput && python manage.py setup_roles
web: gunicorn EduManage.wsgi --log-file -
