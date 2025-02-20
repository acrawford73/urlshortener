# Installation Guide

The following project installation guide is based on Digital Ocean's Marketplace Django pre-installed image. This image uses Django v5.0, but will be changed to v4.2.18.

For demonstration purposes, the guide will use "psinergy.link" as the web domain.

## Summary

1. Install and Update System Packages
2. Configure SSH.
3. Set system passwords.
4. Install and update system packages.
5. Prepare new PostgreSQL database.
6. Deploy new Django project source.
7. Install Pip packages.
8. Prepare new Django project with database.
9. Complete Server Configuration Guide.


## Update System Packages

```
sudo apt-get update
sudo apt-get upgrade
```

## Change server hostname to the domain

```
sudo hostnamectl psinergy.link
```

## Configure SSH

1. Create SSH keys for the django user.

```
su - django
ssh-keygen -t rsa -b 4096
exit
```

2. As the 'root' user, copy root's authorized keys to the 'django' user.

```
cp .ssh/authorized_keys /home/django/.ssh/
chown django:django /home/django/.ssh/authorized_keys
```

3. Configure the SSHD service to only accept logins from the 'django' user.

```
vi /etc/ssh/sshd_config
```

4. Allow logins for the 'django' user.

```
AllowUsers django
```

5. Disable logins for the 'root' user.

```
PermitRootLogin no
```

6. Restart the SSHD service.

```
systemctl restart sshd
```

## Set system passwords

1. As root, set the password.

```
sudo passwd
```

2. As root, set the password for the 'postgres' user.

```
sudo passwd postgres
```

## Install system packages for project

**NOTE:** The remainder of the installation will be performed as the 'django' user.

1. Disable unattended upgrades.

```
sudo dpkg-reconfigure unattended-upgrades
```

2. Install Memcached caching service. 

```
sudo apt-get install memcached
```

3. Memcache configuration in Django settings.py (done later):

- For Memcached local:

```
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': ['127.0.0.1:11211'],
    },
}
```

- For Memcached cluster (replace IPs):

```
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': ['1.2.3.4:11211','1.2.3.5:11211','1.2.3.6:11211'],
    },
}
```

## Database

### Prepare new **PostgreSQL** database on the same droplet.

1. Switch to 'postgres' user.

```
su - postgres
```

2. Create database and assign user 'django' to it. Use database name that represents your project.

```
createdb psinergydb
psql
GRANT ALL PRIVILEGES ON DATABASE psinergydb TO django;
ALTER ROLE django SET client_encoding TO 'UTF8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET timezone TO 'UTC';
\q
exit
```

### Prepare Timezone (optional)

NOTE: Verify server timezone configurations first before setting timezone in database. For this install, the timezone will be kept as UTC.

1. In Django, settings.py:

```
TIME_ZONE = 'UTC'
```

or as an example:

```
TIME_ZONE = 'America/New_York'
```

2. For the server, get a list of timezones:

```
timedatectl list-timezones
```

3. Set the timezone:

```
sudo timedatectl set-timezone America/New_York
```

### Prepare new **PostgreSQL** managed database on Digital Ocean.

1. TBD


## Deploy Django project source.

- Navigate to **/home/django**
- Get the project source from Github.

```
cd /home/django
git clone git@github.com:acrawford73/psinergy.link.git
```

### Configure Environment File

1. Copy the sample environment file.

```
cp /home/django/psinergy.link/deploy/env_example /home/django/psinergy.link/.env
chmod 644 /home/django/psinergy.link/.env
```

2. Adjust `.env` parameters.

- PRODUCTION = True
- Add unique SECRET_KEYS by going to [https://djecrety.ir/](https://djecrety.ir/)
- Add Domain information.
- Add Database information.
- Modify the file according to this example

```
PRODUCTION=True
PROD_SECRET_KEY=
PROD_SECRET_KEY_FALLBACK=
PROD_ALLOWED_HOSTS='www.psinergy.link,psinergy.link,163.35.184.78'
SECURE_SSL_HOST='psinergy.link'
SECURE_SSL_REDIRECT=False
SECURE_REFERRER_POLICY='same-origin'
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_PRELOAD=True
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_CROSS_ORIGIN_OPENER_POLICY='same-origin'
X_FRAME_OPTIONS='DENY'
CSRF_USE_SESSIONS=True
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_DOMAIN='.psinergy.link'
CSRF_TRUSTED_ORIGINS='https://psinergy.link'
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_AGE=1209600
SESSION_COOKIE_NAME='sessionid'
SESSION_COOKIE_DOMAIN='.psinergy.link'
SESSION_COOKIE_SAMESITE='Lax'
SESSION_CACHE_ALIAS='default'
DEBUG_SECRET_KEY=
DEBUG_ALLOWED_HOSTS='localhost,127.0.0.1'
DB_ENGINE=django.db.backends.postgresql
DB_NAME=psinergydb
DB_USER=django
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
SITE_ID=1
REGISTRATION_OPEN=True
REGISTRATION_AUTO_LOGIN=False
```

## Install Pip Packages

The Python binary is at **/usr/bin/local/python3**, so Pip packages are installed right on the server.

1. Create a symlink for **python**.

```
sudo ln -s /usr/bin/local/python3 /usr/bin/local/python
```

2. Install project Pip packages.

```
cd /home/django/psinergy.link/

pip install -r requirements.txt
```

## Prepare Django Project

1. Migrate database.

```
cd /home/django/psinergy.link/src

python manage.py makemigrations
python manage.py migrate
```

2. Copy static files to publicly accessible area.

```
python manage.py collectstatic
```

3. Create the first admin user for Django.

```
python manage.py createsuperuser
```

4. Create cache tables for Memcached.

```
python manage.py createcachetable
```

## Server Configuration Guide

Complete the [Configuration Guide](configuration.md)

- Configure Gunicorn & Nginx.
- Install LetsEncrypt certificate with Certbot.
- Review configurations and test.
