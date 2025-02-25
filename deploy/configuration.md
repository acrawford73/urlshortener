# Configuration Guide

## Summary

1. Update DNS records
2. Configure Gunicorn
3. Configure Nginx
4. Create LetsEncrypt Certificates
5. Final Test
6. Backup Cron

## Update DNS records

1. The domain you purchased at the domain registrar must point to Digital Ocean nameservers.

```
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

2. In the Network section of your Digital Ocean account, add the domain.

3. Three DNS records are added: A, CNAME, and CAA.

The A record points to the droplet created.

The CNAME is 'www' and points to the A record.

The CAA record is for whitelisting 'letsencrypt.com'. Settings:

- Hostname = @
- Authority Granted For = letsencrypt.com
- Tag = issue
- Flags = 0
- TTL = 3600 (default)

## Configure Gunicorn Service

### /etc/systemd/system/gunicorn.service

```
[Unit]
Description=Gunicorn daemon for Django
Before=nginx.service
After=network.target

[Service]
WorkingDirectory=/home/django/psinergy.link/src
ExecStart=/usr/bin/gunicorn3 --name=psinergy --bind unix:/home/django/gunicorn.socket --config /etc/gunicorn.d/gunicorn.py psinergy.wsgi:application
Restart=always
SyslogIdentifier=gunicorn
User=django
Group=django

[Install]
WantedBy=multi-user.target
```

#### NOTE: /etc/gunicorn.d/gunicorn.py

For reference only.

```
"""gunicorn WSGI server configuration."""
from multiprocessing import cpu_count
from os import environ

def max_workers():
    return cpu_count() * 2 + 1

max_requests = 1000
worker_class = 'gevent'
workers = max_workers()
```

### After any Gunicorn changes:

```
sudo systemctl daemon-reload
sudo systemctl restart gunicorn.service
```

## Configure NGINX

1. Add a new website configuration.

#### /etc/nginx/nginx.conf

```
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
        # multi_accept on;
}

http {

        ##
        # Basic Settings
        ##

        sendfile on;
        tcp_nopush on;
        types_hash_max_size 2048;
        server_tokens off;

        server_names_hash_bucket_size 64;
        # server_name_in_redirect off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ##
        # SSL Settings
        ##

        ssl_protocols TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
        ssl_prefer_server_ciphers on;

        ##
        # Logging Settings
        ##

        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        ##
        # Gzip Settings
        ##

        gzip on;

        # gzip_vary on;
        # gzip_proxied any;
        # gzip_comp_level 6;
        # gzip_buffers 16 8k;
        # gzip_http_version 1.1;
        # gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        ##
        # Virtual Host Configs
        ##

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
```

2. Copy default server config to psinergy.link, then create symlink.

```
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/psinergy.link

ln -s /etc/nginx/sites-available/psinergy.link /etc/nginx/sites-enabled/psinergy.link
```

3. Configure /etc/nginx/sites-available/psinergy.link

The SSL configurations will be missing from the configuration file. SSL configurations are added by the Certbot installer).

```
upstream app_server {
    server unix:/home/django/gunicorn.socket fail_timeout=0;
}

server {
    listen 80;
    #listen [::]:80;
    server_name psinergy.link;
    return 302 https://$server_name$request_uri;
}

server {
    if ($request_method ~ ^(OPTIONS)$ ) {
		return 403;
    }
    
    listen 443 ssl;
    #listen [::]:80 ipv6only=on;

    root /usr/share/nginx/html;
    index index.html index.htm;

    client_max_body_size 4G;

    server_name psinergy.link;

    keepalive_timeout 5;

    # Your Django project's media files - amend as required
    location /media  {
        alias /home/django/psinergy.link/media;
    }

    # your Django project's static files - amend as required
    location /static {
        alias /home/django/psinergy.link/static_cdn/static;
    }

    # Proxy the static assests for the Django Admin panel
    location /static/admin {
       #alias /usr/lib/python3/dist-packages/django/contrib/admin/static/admin/;
       alias /home/django/psinergy.link/static_cdn/static/admin;
    }

    location / {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Host $host;
            proxy_redirect off;
            proxy_buffering off;
            proxy_pass http://app_server;
    }

}

```

4. After any Nginx configuration changes:

- Check for valid configuration.

```
sudo nginx -t
```

- Restart Nginx.

```
sudo systemctl reload nginx
sudo systemctl restart nginx
```

## Create LetsEncrypt Certificates

[Certbot Commands](https://eff-certbot.readthedocs.io/en/stable/using.html#certbot-commands)

### Create LetsEncrypt Certificates with Certbot

The **--nginx** parameter installs certificate, key, and configures Nginx configuration files.

1. Register and create certificates for the domain.

```
sudo certbot --nginx -d psinergy.link
```

2. Certbot adds a few lines to the Nginx configuration. Review the sites-enabled/psinergy.link file. 

```
listen 443 ssl;
...
ssl_certificate /etc/letsencrypt/live/psinergy.link/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/psinergy.link/privkey.pem;
include /etc/letsencrypt/options-ssl-nginx.conf;
ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
ssl_prefer_server_ciphers on;
...
```

If the configuration appears okay then run:

```
sudo nginx -t

# Reload configuration files
sudo systemctl reload nginx

# Full restart
sudo systemctl restart nginx
```

## Final Test

Using your browser, navigate to your custom domain [https://domain.com](https://domain.com).

The website should appear successfully. Login with the admin user that was created during the installation guide.

## Backup Cron

1. Update the backup script `scripts/backupdb.sh` for your setup.

```
#!/bin/bash
DB_NAME="database_name"
DB_USER="database_user"
BACKUP_DIR="/home/user/backups"
TIMESTAMP=$(date +"%Y%m%d%H%M")

# Dump the database with pg_dump and compress the output
/usr/lib/postgresql/14/bin/pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"
```

2. Set the script permissions.

```
chmod 750 backupdb.sh
```

3. Add configuration to crontab. Adjust the cron timing as required.

```
crontab -e

0 6 * * * /home/user/project_folder/scripts/backupdb.sh >> /home/user/backups/backup.log 2>&1
```
