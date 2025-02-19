#!/bin/bash
# should be run as root and only on Ubuntu 22 version!


### !!! WORK IN PROGRESS - DO NOT RUN !!!


echo "Welcome to the URL Shortener installation script!";

if [ `id -u` -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Confirm installing on a fresh machine
while true; do
    read -p "
This script will attempt to perform a system update, install required dependencies, install and configure PostgreSQL, NGINX, Memcached and a few other utilities.
It is expected to run on a new system **with no running instances of any these services**. Make sure you check the script before you continue. Then enter yes or no
" yn
    case $yn in
        [Yy]* ) echo "OK!"; break;;
        [Nn]* ) echo "Have a great day"; exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

# OS Check
osVersion=$(lsb_release -d)
if [[ $osVersion == *"Ubuntu 22"* ]]; then
    echo 'Performing system update and dependency installation, this will take a few minutes'
    apt-get update && apt-get -y upgrade && apt-get install python3 python3-dev python3-venv virtualenv memcached postgresql gunicorn nginx git python3-certbot-nginx certbot wget -y
else
    echo "This script is tested for Ubuntu 22.04 only, if you want to try URL Shortener on another system you have to perform the manual installation."
    exit
fi

# Host and Portal names
read -p "Enter portal domain name without https://, or press enter for localhost : " FRONTEND_HOST
read -p "Enter portal name, or press enter for 'URL Shortener : " PORTAL_NAME
[ -z "$PORTAL_NAME" ] && PORTAL_NAME='URL Shortener'
[ -z "$FRONTEND_HOST" ] && FRONTEND_HOST='localhost'

# Database
echo 'Creating database to be used for URL Shortener'
su -c "psql -c \"CREATE DATABASE urlshortener\"" postgres
su -c "psql -c \"CREATE USER urlshortener WITH ENCRYPTED PASSWORD 'urlshortening'\"" postgres
su -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE urlshortener TO urlshortener\"" postgres

# Create Django user
echo 'Creating django user'
useradd -m django
usermod -aG admin django
passwd django

# Deploy source code
cd /home/django
git clone git@github.com:acrawford73/urlshortener.git
chown -R django:django ulshortener

# cd /home/mediacms.io
# virtualenv . --python=python3
# source  /home/mediacms.io/bin/activate
cd urlshortener
pip install -r requirements.txt

# Secret keys
SECRET_KEY=`python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`

# remove http or https prefix
FRONTEND_HOST=`echo "$FRONTEND_HOST" | sed -r 's/http:\/\///g'`
FRONTEND_HOST=`echo "$FRONTEND_HOST" | sed -r 's/https:\/\///g'`
sed -i s/localhost/$FRONTEND_HOST/g deploy/local_install/mediacms.io
FRONTEND_HOST_HTTP_PREFIX='http://'$FRONTEND_HOST

# Update settings.py
echo 'FRONTEND_HOST='\'"$FRONTEND_HOST_HTTP_PREFIX"\' >> cms/local_settings.py
echo 'PORTAL_NAME='\'"$PORTAL_NAME"\' >> cms/local_settings.py
echo "SSL_FRONTEND_HOST = FRONTEND_HOST.replace('http', 'https')" >> cms/local_settings.py
echo 'SECRET_KEY='\'"$SECRET_KEY"\' >> cms/local_settings.py
#echo "LOCAL_INSTALL = True" >> cms/local_settings.py

# Migrate database
mkdir logs
mkdir pids
python manage.py makemigrations
python manage.py migrate
#python manage.py loaddata fixtures/encoding_profiles.json
#python manage.py loaddata fixtures/categories.json
python manage.py collectstatic --noinput

# Prep admin password
ADMIN_PASS=`python -c "import secrets;chars = 'abcdefghijklmnopqrstuvwxyz0123456789';print(''.join(secrets.choice(chars) for i in range(10)))"`
echo "from users.models import User; User.objects.create_superuser('admin', 'admin@example.com', '$ADMIN_PASS')" | python manage.py shell
echo "from django.contrib.sites.models import Site; Site.objects.update(name='$FRONTEND_HOST', domain='$FRONTEND_HOST')" | python manage.py shell

# Deploy project files
chown -R www-data. /home/django/urlshortener/
#cp deploy/local_install/celery_long.service /etc/systemd/system/celery_long.service && systemctl enable celery_long && systemctl start celery_long
#cp deploy/local_install/celery_short.service /etc/systemd/system/celery_short.service && systemctl enable celery_short && systemctl start celery_short
#cp deploy/local_install/celery_beat.service /etc/systemd/system/celery_beat.service && systemctl enable celery_beat &&systemctl start celery_beat
#cp deploy/local_install/mediacms.service /etc/systemd/system/mediacms.service && systemctl enable mediacms.service && systemctl start mediacms.service
cp deploy/local_install/gunicorn.service /etc/systemd/system/gunicorn.service && systemctl enable gunicorn.service && systemctl start gunicorn.service

mkdir -p /etc/letsencrypt/live/urlshortener/
mkdir -p /etc/letsencrypt/live/$FRONTEND_HOST
mkdir -p /etc/nginx/sites-enabled
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/dhparams/
rm -rf /etc/nginx/conf.d/default.conf
rm -rf /etc/nginx/sites-enabled/default
cp deploy/local_install/mediacms.io_fullchain.pem /etc/letsencrypt/live/$FRONTEND_HOST/fullchain.pem
cp deploy/local_install/mediacms.io_privkey.pem /etc/letsencrypt/live/$FRONTEND_HOST/privkey.pem
cp deploy/local_install/dhparams.pem /etc/nginx/dhparams/dhparams.pem
cp deploy/local_install/mediacms.io /etc/nginx/sites-available/mediacms.io
ln -s /etc/nginx/sites-available/mediacms.io /etc/nginx/sites-enabled/mediacms.io
cp deploy/local_install/uwsgi_params /etc/nginx/sites-enabled/uwsgi_params
cp deploy/local_install/nginx.conf /etc/nginx/
systemctl stop nginx
systemctl start nginx

# attempt to get a valid certificate for specified domain

if [ "$FRONTEND_HOST" != "localhost" ]; then
    echo 'attempt to get a valid certificate for specified url $FRONTEND_HOST'
    certbot --nginx -n --agree-tos --register-unsafely-without-email -d $FRONTEND_HOST
    certbot --nginx -n --agree-tos --register-unsafely-without-email -d $FRONTEND_HOST
    # unfortunately for some reason it needs to be run two times in order to create the entries
    # and directory structure!!!
    systemctl restart nginx
else
    echo "will not call certbot utility to update ssl certificate for url 'localhost', using default ssl certificate"
fi

# Generate individual DH params
if [ "$FRONTEND_HOST" != "localhost" ]; then
    # Only generate new DH params when using "real" certificates.
    openssl dhparam -out /etc/nginx/dhparams/dhparams.pem 4096
    systemctl restart nginx
else
    echo "will not generate new DH params for url 'localhost', using default DH params"
fi

# last, set default owner
chown -R www-data. /home/mediacms.io/

echo 'ShortURL installation completed, open browser on http://'"$FRONTEND_HOST"' and login with user admin and password '"$ADMIN_PASS"''