## URL Shortener

Purpose: To shorten URLs with an alias.

Example: https://psinergy.link/abc123

## Install

OS Requirement: Ubuntu Linux with Python 3.10+

Tested on Ubuntu 22.04 LTS

### System packages

```code
sudo apt-get install python3 python3-pip virtualenv
```

### Python packages

```code
git clone https://github.com/acrawford73/psinergy.link.git

virtualenv -p /usr/bin/python3 psinergy.link
cd psinergy.link
source bin/activate
pip install Django==4.2.18
pip install django-registration django[argon2] bs4 requests playwright python-decouple psycopg[binary] django-crispy-forms crispy-bootstrap5
pip install playwright
playwright install-deps
playwright install
```

