# Manuel Installation Guide

**We are assuming that the system user `www-data` will run all processes!**

### API Setup

##### Preparation

- install **mediainfo** (we need the lib)
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
- copy **docs/ffplayout-api.conf** to **/etc/nginx/sites-available/**
- symlink config: `ln -s /etc/nginx/sites-available/ffplayout-api.conf /etc/nginx/sites-enabled/`
- restart nginx
- set correct timezone in **ffplayout/settings/common.py**

##### Single Channel extra Settings

- run `visudo` and add:

    ```
    www-data ALL = NOPASSWD: /bin/systemctl start ffplayout_engine.service, /bin/systemctl stop ffplayout_engine.service, /bin/systemctl reload ffplayout_engine.service, /bin/systemctl restart ffplayout_engine.service, /bin/systemctl status ffplayout_engine.service, /bin/systemctl is-active ffplayout_engine.service
    ```
- set in **ffplayout/settings/common.py** `MULTI_CHANNEL = False`

##### Multi Channel extra Settings

- set in **ffplayout/settings/common.py** `MULTI_CHANNEL = True`
- set permissions to: `chown www-data. -R /var/log/ffplayout` and `chown www-data. -R /etc/ffplayout/*`
