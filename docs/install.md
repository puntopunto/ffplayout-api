# Manuel Installation Guide

**We are assuming that the system user `www-data` will run all processes!**

### API Setup

##### Preparation
- clone repo to `/var/www/ffplayout-api`
- cd in root folder from repo
- add virtual environment: `virtualenv -p python3 venv`
- run `source ./venv/bin/activate`
- install dependencies: `pip install -r requirements-base.txt`
- cd in `ffplayout`
- generate and copy secret: `python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())'`
- open **ffplayout/settings/production.py**
- past secret key in variable `SECRET_KEY`
- set `ALLOWED_HOSTS` with correct URL
- set URL in `CORS_ORIGIN_WHITELIST`
- migrate database: `python manage.py makemigrations && python manage.py migrate`
- collect static files: `python manage.py collectstatic`
- add super user to db: `python manage.py createsuperuser`
- populate some data to db: `python manage.py loaddata ../docs/db_data.json`
- run: `chown www-data. -R /var/www/ffplayout-api`

##### System Setup
- copy **docs/ffplayout-api.service** from root folder to **/etc/systemd/system/**
- enable service and start it: `systemctl enable ffplayout-api.service && systemctl start ffplayout-api.service`
- install **nginx**
- edit **docs/ffplayout-api.conf**
    - set correct IP and `server_name`
    - add domain `http_origin` test value
    - add https redirection and SSL if is necessary
- copy **docs/ffplayout.conf** to **/etc/nginx/sites-available/**
- symlink config: `ln -s /etc/nginx/sites-available/ffplayout-api.conf /etc/nginx/sites-enabled/`
- restart nginx
- run `visudo` and add:
    ```
    www-data ALL = NOPASSWD: /bin/systemctl start ffplayout-engine.service, /bin/systemctl stop ffplayout-engine.service, /bin/systemctl reload ffplayout-engine.service, /bin/systemctl restart ffplayout-engine.service, /bin/systemctl status ffplayout-engine.service, /bin/systemctl is-active ffplayout-engine.service
    ```
