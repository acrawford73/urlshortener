## URL Shortener

Purpose: To condense long URLs so they're shareable.

Example: `https://yourdomain.com/a1b2c3`

## Domain

Register one domain name for this project.

## Dev Environment

- Ubuntu 22.04 LTS VM with 1 Core, 2 GB memory
- Python 3.10+

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
- Redis host, internal network
- PostgreSQL Database host, internal network
- Minimum two hosts with Django marketplace droplets with minimum 2 Core & 4 GB memory.
- Staging host

## Setup

### Server Installation

Follow the [Installation](deploy/installation.md) instructions.

### Server Configuration

Follow the [Configuration](deploy/configuration.md) instructions.

## Access Levels

### User

- Create, update, delete your own links
- View all links
- View all topics

### Staff

- Create, update, delete all links
- Create, update, delete topics


## Incomplete apps

- news
- subscriptions
