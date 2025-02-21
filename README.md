## URL Shortener

Purpose: To condense long web URLs to shareable URLs using an alias code.

Example: https://yourdomain.com/a1b2c3

Operating System: Ubuntu 22.04 LTS with Python 3.10+

## Dev Environment

- Ubuntu 22 VM with 1 Core & 2 GB memory
- Virtualbox

### System packages

```code
sudo apt-get install python3 python3-dev python3-pip virtualenv
```

### Python packages

```code
git clone https://github.com/acrawford73/psinergy.link.git

virtualenv -p /usr/bin/python3 psinergy.link
cd psinergy.link
source bin/activate
pip install -r requirements.txt
playwright install-deps
playwright install
```

## Prod Environment

Digital Ocean

Beta:

- Single Django marketplace droplet with minimum 2 Core & 4 GB memory.

Production:

- Load Balancer
- Memcached host, internal network
- PostgreSQL Database host, internal network
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

Follow the [Installation](deploy/installation.md) instructions.

### Server Configuration

Follow the [Configuration](deploy/configuration.md) instructions.
