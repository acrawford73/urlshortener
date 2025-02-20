## URL Shortener

Purpose: To shorten URLs with an alias.

Example: https://psinergy.link/abc123

OS Requirement: Ubuntu Linux with Python 3.10+

Tested on Ubuntu 22.04 LTS

## Dev Install

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

## Prod Install

Digital Ocean

Beta:

- Single Django marketplace droplet with minimum 2 Core & 4 GB memory.

Production:

- Load Balancer
- Memcached host
- PostgreSQL Database host
- Minimum two hosts with Django marketplace droplets with minimum 2 Core & 4 GB memory.

### Python packages

```code
git clone https://github.com/acrawford73/psinergy.link.git

cd psinergy.link

pip install -r requirements.txt
pip install playwright
playwright install-deps
playwright install
```

## Setup

### Server Installation

Follow the ServerInstallation.md instructions.

### Server Configuration

Follow the ServerConfiguration.md instructions.
